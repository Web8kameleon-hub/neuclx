"""Model adapter boundary. The repository allows a model adapter only when the backend is explicitly configured and evidence is preserved."""

from __future__ import annotations

from hashlib import sha256
from typing import Any, Dict, Optional

from .evidence import Datum, EvidenceState
from .jona import JonaSandbox


class ModelAdapter:
    """Thin adapter layer that refuses hidden external model fallbacks."""

    def __init__(self, provider: str = "local", model_name: Optional[str] = None, enabled: bool = False, sandbox: Optional[JonaSandbox] = None):
        self.provider = provider
        self.model_name = model_name
        self.enabled = enabled
        self.sandbox = sandbox or JonaSandbox()

    def generate(self, prompt: str, *, temperature: float = 0.0, max_tokens: int = 0) -> Datum:
        if not self.enabled or not self.model_name:
            return self.sandbox.release(Datum(None, EvidenceState.NOT_IMPLEMENTED, source=None, method="adapter-disabled-or-no-model"))

        if self.provider == "local":
            digest = sha256(prompt.encode("utf-8")).hexdigest()[:16]
            value = f"{self.model_name}:{digest}"
            return self.sandbox.release(
                Datum(
                    value,
                    EvidenceState.COMPUTED,
                    source=self.model_name,
                    method="sha256-deterministic",
                    metadata={"provider": self.provider, "temperature": temperature, "max_tokens": max_tokens},
                )
            )

        return self.sandbox.release(Datum(None, EvidenceState.NOT_IMPLEMENTED, source=None, method=f"provider-{self.provider}-not-supported"))
