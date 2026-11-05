"""Explicit OpenAI-compatible local and hosted model adapter."""

from __future__ import annotations

from hashlib import sha256
import ipaddress
import json
import math
import os
from typing import Optional
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .evidence import Datum, EvidenceState
from .jona import JonaSandbox, PolicyDecision


MAX_PROMPT_BYTES = 1_048_576
MAX_RESPONSE_BYTES = 1_048_576


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class ModelAdapter:
    """Call an explicitly configured endpoint; never download weights or fall back."""

    def __init__(
        self,
        provider: str = "local",
        model_name: Optional[str] = None,
        enabled: bool = False,
        *,
        endpoint: Optional[str] = None,
        api_key_env: Optional[str] = None,
        timeout: float = 30.0,
        sandbox: Optional[JonaSandbox] = None,
    ):
        self.provider = provider
        self.model_name = model_name
        self.enabled = enabled
        self.endpoint = endpoint
        self.api_key_env = api_key_env
        if type(enabled) is not bool:
            raise TypeError("enabled must be a boolean")
        if type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be a positive finite number")
        if api_key_env is not None and (not isinstance(api_key_env, str) or not api_key_env.strip()):
            raise ValueError("api_key_env must be a nonempty environment variable name")
        self.timeout = timeout
        self.sandbox = sandbox if sandbox is not None else JonaSandbox()
        self._opener = build_opener(_NoRedirectHandler())

    @classmethod
    def from_environment(cls) -> ModelAdapter:
        enabled_value = os.environ.get("NEUCLX_MODEL_ENABLED", "").strip().lower()
        if enabled_value not in {"", "0", "false", "no", "off", "1", "true", "yes", "on"}:
            raise ValueError("NEUCLX_MODEL_ENABLED must be a boolean value")
        enabled = enabled_value in {"1", "true", "yes", "on"}
        if not enabled:
            return cls(enabled=False)

        model_name = os.environ.get("NEUCLX_MODEL_NAME", "").strip()
        endpoint = os.environ.get("NEUCLX_MODEL_ENDPOINT", "").strip()
        if not model_name or not endpoint:
            raise ValueError(
                "NEUCLX_MODEL_NAME and NEUCLX_MODEL_ENDPOINT are required when model inference is enabled"
            )
        timeout_value = os.environ.get("NEUCLX_MODEL_TIMEOUT", "30")
        try:
            timeout = float(timeout_value)
        except ValueError:
            raise ValueError("NEUCLX_MODEL_TIMEOUT must be a positive finite number") from None
        return cls(
            provider=os.environ.get("NEUCLX_MODEL_PROVIDER", "local").strip().lower(),
            model_name=model_name,
            enabled=True,
            endpoint=endpoint,
            api_key_env=os.environ.get("NEUCLX_MODEL_API_KEY_ENV") or None,
            timeout=timeout,
        )

    def generate(
        self, prompt: str, *, temperature: float = 0.0, max_tokens: int = 256
    ) -> Datum:
        if not self.enabled:
            return self.sandbox.release(
                Datum(None, EvidenceState.NOT_IMPLEMENTED,
                      method="model-adapter-disabled-or-no-model")
            )
        if not isinstance(self.model_name, str) or not self.model_name.strip():
            raise ValueError("model_name is required when model inference is enabled")
        if self.provider not in {"local", "hosted"}:
            raise ValueError("provider must be 'local' or 'hosted'")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be a nonempty string")
        if len(prompt.encode("utf-8")) > MAX_PROMPT_BYTES:
            raise ValueError("prompt exceeds the configured size limit")
        if type(temperature) not in (int, float) or not math.isfinite(temperature) or not 0 <= temperature <= 2:
            raise ValueError("temperature must be finite and between 0 and 2")
        if type(max_tokens) is not int or max_tokens < 1:
            raise ValueError("max_tokens must be a positive integer")
        endpoint = self._validate_endpoint()

        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        request_datum = Datum(
            payload,
            EvidenceState.COMPUTED,
            source="neuclx-model-adapter",
            method="openai-compatible-request-v1",
            metadata={"provider": self.provider, "model": self.model_name, "endpoint": endpoint},
        )
        decision = self.sandbox.evaluate(request_datum)
        if decision is PolicyDecision.REJECT:
            self.sandbox.release(request_datum)
        if decision is not PolicyDecision.ALLOW:
            return self._held_result("jona-held-model-request", decision)

        headers = {"Content-Type": "application/json"}
        if self.api_key_env:
            api_key = os.environ.get(self.api_key_env)
            if not api_key:
                raise ValueError(f"required API key environment variable is unset: {self.api_key_env}")
            headers["Authorization"] = f"Bearer {api_key}"
        request = Request(
            endpoint,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with self._opener.open(request, timeout=self.timeout) as response:
                response_body = response.read(MAX_RESPONSE_BYTES + 1)
        except HTTPError as error:
            raise RuntimeError(f"model endpoint returned HTTP {error.code}") from None
        if len(response_body) > MAX_RESPONSE_BYTES:
            raise ValueError("model response exceeds the configured size limit")

        response_data = json.loads(response_body.decode("utf-8"))
        try:
            content = response_data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as error:
            raise ValueError("model response does not match the chat-completions contract") from error
        if not isinstance(content, str) or not content.strip():
            raise ValueError("model response content must be a nonempty string")

        output = Datum(
            content,
            EvidenceState.COMPUTED,
            source=f"{self.provider}:{self.model_name}",
            method="openai-compatible-chat-completions-v1",
            metadata={
                "provider": self.provider,
                "model": self.model_name,
                "input_sha256": sha256(prompt.encode("utf-8")).hexdigest(),
                "output_sha256": sha256(content.encode("utf-8")).hexdigest(),
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        output_decision = self.sandbox.evaluate(output)
        if output_decision is PolicyDecision.REJECT:
            self.sandbox.release(output)
        if output_decision is not PolicyDecision.ALLOW:
            return self._held_result("jona-held-model-output", output_decision)
        return self.sandbox.release(output)

    def _validate_endpoint(self) -> str:
        if not isinstance(self.endpoint, str) or not self.endpoint:
            raise ValueError("an explicit model endpoint is required")
        parsed = urlsplit(self.endpoint)
        if (
            "@" in parsed.netloc
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or not parsed.hostname
            or parsed.path.rstrip("/").split("/")[-2:] != ["chat", "completions"]
        ):
            raise ValueError("endpoint must be a credential-free chat-completions URL")
        if self.provider == "hosted" and parsed.scheme != "https":
            raise ValueError("hosted model endpoints must use HTTPS")
        if self.provider == "local":
            host = parsed.hostname.lower()
            try:
                is_loopback = ipaddress.ip_address(host).is_loopback
            except ValueError:
                is_loopback = host == "localhost"
            if parsed.scheme not in {"http", "https"} or not is_loopback:
                raise ValueError("local model endpoints must use loopback HTTP(S)")
        return self.endpoint

    def _held_result(self, method: str, decision: PolicyDecision) -> Datum:
        held = Datum(
            None,
            EvidenceState.UNAVAILABLE,
            method=method,
            metadata={"jona_decision": decision.value},
        )
        return self.sandbox.release(held)
