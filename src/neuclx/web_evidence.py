"""Bounded public-page reading that produces short, cited evidence excerpts."""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from html.parser import HTMLParser
import http.client
import ipaddress
import json
import re
import socket
import ssl
from urllib.parse import parse_qsl, urlsplit, urlunsplit

from .evidence import Datum, EvidenceState
from .jona import JonaSandbox
from .learning import terms


MAX_URLS = 10
MAX_URL_LENGTH = 2048
MAX_RESPONSE_BYTES = 1_000_000
MAX_EXCERPT_CHARACTERS = 600
DEFAULT_TIMEOUT_SECONDS = 8
_USER_AGENT = "NeuCLX/0.1 (public evidence retrieval)"
_IGNORED_TAGS = {"script", "style", "noscript", "svg", "nav", "footer", "header"}


class PublicWebReadError(ValueError):
    """A public page could not be fetched or did not match the text contract."""


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in _IGNORED_TAGS:
            self._ignored_depth += 1
        elif tag in {"p", "div", "li", "h1", "h2", "h3", "h4", "br"} and not self._ignored_depth:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in _IGNORED_TAGS and self._ignored_depth:
            self._ignored_depth -= 1
        elif tag in {"p", "div", "li", "h1", "h2", "h3", "h4", "br"} and not self._ignored_depth:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self._ignored_depth:
            cleaned = " ".join(data.split())
            if cleaned:
                self.parts.append(cleaned)


class PublicWebReader:
    def __init__(
        self,
        sandbox=None,
        *,
        timeout=DEFAULT_TIMEOUT_SECONDS,
        max_bytes=MAX_RESPONSE_BYTES,
        resolver=None,
        transport=None,
    ):
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        if not 1 <= max_bytes <= MAX_RESPONSE_BYTES:
            raise ValueError("max_bytes must be between 1 and 1000000")
        self.sandbox = sandbox if sandbox is not None else JonaSandbox()
        self.timeout = timeout
        self.max_bytes = max_bytes
        self.resolver = resolver if resolver is not None else socket.getaddrinfo
        self.transport = transport if transport is not None else self._request

    def read(self, query: str, url: str) -> Datum:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query is required")
        parsed, resolver_host = self._validate_url(url)
        request_datum = Datum(
            url,
            EvidenceState.DECLARED,
            source="neuclx:user-provided-url",
            method="public-web-read-request",
        )
        self.sandbox.release(request_datum)

        address = self._resolve_public_address(resolver_host, parsed.port or 443)
        status, headers, body = self.transport(parsed, address)
        if status != 200:
            raise PublicWebReadError(f"source returned HTTP {status}")
        if len(body) > self.max_bytes:
            raise PublicWebReadError("source response exceeded the configured byte limit")
        content_type = headers.get("content-type", "").split(";", 1)[0].strip().casefold()
        if content_type not in {"text/html", "application/xhtml+xml", "text/plain", "application/json"}:
            raise PublicWebReadError(f"unsupported content type: {content_type or 'unavailable'}")
        try:
            text = self._extract(body, content_type)
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise PublicWebReadError("source body is not valid supported text") from exc
        excerpt = self._select_excerpt(query, text)
        if not excerpt:
            raise PublicWebReadError("no query-matching text was found on the page")

        digest = sha256(body).hexdigest()
        retrieval_method = {
            "text/html": "https-get:html-text-excerpt",
            "application/xhtml+xml": "https-get:html-text-excerpt",
            "text/plain": "https-get:plain-text-excerpt",
            "application/json": "https-get:json-excerpt",
        }[content_type]
        entry = {
            "source": url,
            "revision": "sha256:" + digest,
            "sha256": digest,
            "excerpt": excerpt,
            "state": EvidenceState.DECLARED.value,
            "method": retrieval_method,
            "retrieved_at": datetime.now(UTC).isoformat(),
            "retrieved_at_state": EvidenceState.MEASURED.value,
            "digest_state": EvidenceState.COMPUTED.value,
        }
        result = Datum(
            f"[{url}]\n{excerpt}",
            EvidenceState.DECLARED,
            source=url,
            method="public-web:cited-excerpt",
            metadata={
                "evidence_chain": [entry],
                "jona_decision": self.sandbox.evaluate(request_datum).value,
                "claim_status": "Source text is declared, not independently verified.",
            },
        )
        return self.sandbox.release(result)

    def _validate_url(self, url):
        if not isinstance(url, str) or len(url) > MAX_URL_LENGTH:
            raise PublicWebReadError("URL must be a string no longer than 2048 characters")
        parsed = urlsplit(url.strip())
        if (
            parsed.scheme.casefold() != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.fragment
        ):
            raise PublicWebReadError("only absolute HTTPS URLs without credentials or fragments are allowed")
        query_keys = {
            key.casefold()
            for key, _ in parse_qsl(parsed.query, keep_blank_values=True)
        }
        if query_keys.intersection({
            "key", "api_key", "token", "access_token", "password", "secret",
            "signature", "authorization", "auth",
        }):
            raise PublicWebReadError("URLs containing credential-like query parameters are not allowed")
        host = parsed.hostname
        try:
            ip = ipaddress.ip_address(host)
            host = f"[{host}]" if ip.version == 6 else host
        except ValueError:
            host = host.encode("idna").decode("ascii")
        port = f":{parsed.port}" if parsed.port else ""
        normalized = urlsplit(urlunsplit((
            parsed.scheme,
            host + port,
            parsed.path,
            parsed.query,
            "",
        )))
        resolver_host = parsed.hostname.encode("idna").decode("ascii") if ":" not in parsed.hostname else parsed.hostname
        return normalized, resolver_host

    def _resolve_public_address(self, resolver_host, port):
        try:
            records = self.resolver(resolver_host, port, type=socket.SOCK_STREAM)
        except OSError as exc:
            raise PublicWebReadError(f"source hostname could not be resolved: {resolver_host}") from exc
        addresses = {record[4][0] for record in records}
        if not addresses:
            raise PublicWebReadError(f"source hostname has no addresses: {resolver_host}")
        for value in addresses:
            try:
                address = ipaddress.ip_address(value.split("%", 1)[0])
            except ValueError as exc:
                raise PublicWebReadError("source resolved to an invalid IP address") from exc
            if not address.is_global:
                raise PublicWebReadError("source hostname resolved to a non-public IP address")
        return sorted(addresses)[0]

    def _request(self, parsed, address):
        host = parsed.hostname
        port = parsed.port or 443
        target = parsed.path or "/"
        if parsed.query:
            target += "?" + parsed.query
        connection = _PinnedHTTPSConnection(host, port, address, self.timeout)
        try:
            connection.request(
                "GET",
                target,
                headers={
                    "Host": parsed.netloc,
                    "Accept": "text/html, application/xhtml+xml, text/plain, application/json",
                    "Accept-Encoding": "identity",
                    "User-Agent": _USER_AGENT,
                    "Connection": "close",
                },
            )
            response = connection.getresponse()
            body = response.read(self.max_bytes + 1)
            return response.status, {key.casefold(): value for key, value in response.getheaders()}, body
        except (OSError, http.client.HTTPException, ssl.SSLError) as exc:
            raise PublicWebReadError(f"HTTPS request failed: {exc}") from exc
        finally:
            connection.close()

    @staticmethod
    def _extract(body, content_type):
        text = body.decode("utf-8-sig")
        if content_type == "application/json":
            value = json.loads(text)
            return json.dumps(value, ensure_ascii=False, sort_keys=True)
        if content_type in {"text/html", "application/xhtml+xml"}:
            parser = _TextExtractor()
            parser.feed(text)
            text = "".join(parser.parts)
        return "\n".join(line.strip() for line in text.splitlines() if line.strip())

    @staticmethod
    def _select_excerpt(query, text):
        wanted = terms(query)
        if not wanted:
            return ""
        candidates = []
        for index, sentence in enumerate(re.split(r"(?<=[.!?])\s+|\n+", text)):
            sentence = " ".join(sentence.split())
            if not sentence:
                continue
            overlap = wanted.intersection(terms(sentence))
            if overlap:
                excerpt = sentence[:MAX_EXCERPT_CHARACTERS].rstrip()
                candidates.append((len(overlap) / len(wanted), len(overlap), index, excerpt))
        if not candidates:
            return ""
        candidates.sort(key=lambda item: (-item[0], -item[1], item[2]))
        return candidates[0][3]


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, host, port, address, timeout):
        super().__init__(host, port, timeout=timeout, context=ssl.create_default_context())
        self._address = address

    def connect(self):
        sock = socket.create_connection((self._address, self.port), self.timeout)
        try:
            self.sock = self._context.wrap_socket(sock, server_hostname=self.host)
        except BaseException:
            sock.close()
            raise
