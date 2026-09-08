"""Dependency-free NeuCLX single-page chat server."""

import json
from argparse import ArgumentParser
from datetime import UTC, datetime
from hashlib import sha256
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .agents import ASIAgent, ASITrinityAgent, AlbaAgent, AlbiAgent, BlerinaAgent, JonaAgent
from .evidence import Datum, EvidenceState
from .engine import CognitiveKernel
from .journey import JourneyLedger
from .hvwo import Axis
from .memory import EvidenceMemory, MemoryEntry
from .model_adapter import ModelAdapter
from .open_data_registry import OpenDataRegistry
from .reasoning_engine import ReasoningEngine
from .stable_reasoning_engine import StableReasoningEngine
from .vision_encoder import VisionEncoder
from .creative_engine import CreativeEngine

STATIC=Path(__file__).with_name("static")
MIME={".html":"text/html; charset=utf-8",".css":"text/css; charset=utf-8",".js":"text/javascript; charset=utf-8"}

class NeuCLXApplication:
    def __init__(self, ledger_path="data/neuclx.sqlite3"):
        ledger_path = str(ledger_path)
        self.kernel=CognitiveKernel(layers=8)
        self.ledger=JourneyLedger(ledger_path)
        memory_path = str(Path(ledger_path).with_name(Path(ledger_path).stem + "_memory.sqlite3"))
        self.memory = EvidenceMemory(memory_path)
        stable_memory_path = str(Path(ledger_path).with_name(Path(ledger_path).stem + "_stable_memory.sqlite3"))
        self.stable_memory = EvidenceMemory(stable_memory_path)
        self.model_adapter = ModelAdapter(provider="local", model_name="neuclx-core", enabled=True)
        self.reasoning_engine = ReasoningEngine(memory=self.memory, model=self.model_adapter)
        self.stable_reasoning_engine = StableReasoningEngine(self.stable_memory, model_adapter=None)
        self.vision_encoder = VisionEncoder()
        self.creative_engine = CreativeEngine(self.ledger)
        self.source_registry = OpenDataRegistry()
        self.platform_profile = {
            "multilingual": True,
            "layers": self.kernel.layers,
            "hvo_axes": [axis.value for axis in Axis],
            "saas_api": {
                "enabled": True,
                "endpoints": ["/api/status", "/api/agents", "/api/reason", "/api/respond", "/api/registry", "/api/platform", "/api/vision/inspect", "/api/create"],
            },
            "creative": {
                "enabled": True,
                "modalities": ["image", "text", "audio", "code", "video", "cad"],
                "artifact_format": "svg|wav|py|json|obj",
            },
            "vision": {
                "enabled": True,
                "mode": "stdlib-header-inspection",
            },
            "asi": {
                "available": True,
                "routing_agent": "asi",
                "trinity_agent": "asi-trinity",
            },
            "agents": ["alba", "albi", "jona", "asi", "asi-trinity", "blerina"],
        }
        self.agents = {
            "alba": AlbaAgent(),
            "albi": AlbiAgent(),
            "jona": JonaAgent(),
            "asi": ASIAgent(),
            "asi-trinity": ASITrinityAgent(),
            "blerina": BlerinaAgent(),
        }

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False

    def close(self):
        if hasattr(self, "ledger"):
            self.ledger.close()
        if hasattr(self, "memory"):
            self.memory.close()
        if hasattr(self, "stable_memory"):
            self.stable_memory.close()

    def __del__(self):
        try:
            self.close()
        except (AttributeError, OSError, TypeError):
            pass

    def _remember_fact(self, fact: str):
        digest = sha256(fact.encode("utf-8")).hexdigest()
        entry = MemoryEntry(
            key=f"fact:{digest}",
            content=fact,
            source_id="chat:user-declared",
            evidence_state="computed",
            created_at=datetime.now(UTC).isoformat(),
        )
        self.memory.store(entry)

    def ask_agent(self, agent_name: str, question: str):
        name = (agent_name or "alba").strip().lower()
        question = (question or "").strip()
        if not question:
            raise ValueError("question is required")
        agent = self.agents.get(name)
        if agent is None:
            raise ValueError(f"unknown agent '{name}'")
        return {
            "agent": name,
            "question": question,
            "answer": agent.answer(question),
        }

    def respond(self,prompt,facts=()):
        for fact in facts:
            if isinstance(fact,str) and fact.strip():
                self.kernel.ingest("chat:user-declared", fact)
                self._remember_fact(fact)
        answer = self.kernel.answer(prompt)
        if answer.state.value in {"measured", "computed"}:
            self.memory.store(self.memory._entry_from_datum(answer))
        return self.ledger.record(prompt, answer)

    def reason(self, task: str, facts=(), *, max_iterations: int = 5):
        task_text = (task or "").strip()
        if not task_text:
            raise ValueError("task is required")
        fact_list = [str(fact).strip() for fact in (facts or []) if isinstance(fact, str) and str(fact).strip()]
        result = self.reasoning_engine.reason(task_text, fact_list, max_iterations=max_iterations)
        stored = self.ledger.record(
            task_text,
            Datum(
                result["conclusion"],
                EvidenceState.COMPUTED,
                source="reasoning_engine",
                method="reasoning:api",
                metadata={"intent": result["intent"], "confidence": result["confidence"]},
            ),
        )
        return {
            "task": task_text,
            "intent": result["intent"],
            "conclusion": result["conclusion"],
            "confidence": result["confidence"],
            "confidence_breakdown": result.get("confidence_breakdown", {}),
            "input_evidence": result.get("input_evidence", fact_list),
            "derived_facts": result.get("derived_facts", []),
            "operations": result.get("operations", []),
            "evidence_path": result["evidence_path"],
            "trace": result["trace"],
            "status": result["status"],
            "ledger": stored,
        }

    def inspect_vision(self, image_path: str | None = None, image_bytes_b64: str | None = None, *, author: str | None = None, task: str | None = None):
        if not image_path and not image_bytes_b64:
            raise ValueError("image_path or image_bytes_b64 is required")
        if image_path:
            datum = self.vision_encoder.inspect_path(image_path, author=author, task=task)
        else:
            datum = self.vision_encoder.inspect_base64(image_bytes_b64 or "", source="inline-base64", author=author, task=task)
        stored = self.ledger.record(task or f"inspect image: {image_path or 'inline-base64'}", datum)
        if datum.state.value in {"measured", "computed"}:
            self.memory.store(self.memory._entry_from_datum(datum))
        return {
            "task": task or "inspect image",
            "status": "ok",
            "conclusion": "Image evidence recorded.",
            "confidence": datum.metadata.get("confidence", 1.0),
            "image": datum.value,
            "evidence_chain": [datum.as_dict()],
            "datum": datum.as_dict(),
            "ledger": stored,
        }

def handler_factory(app):
    class Handler(BaseHTTPRequestHandler):
        server_version="NeuCLX/0.1"
        def _json(self,payload,status=HTTPStatus.OK):
            body=json.dumps(payload,ensure_ascii=False,sort_keys=True).encode(); self.send_response(status); self.send_header("Content-Type","application/json; charset=utf-8"); self.send_header("Content-Length",str(len(body))); self.send_header("Cache-Control","no-store"); self.end_headers(); self.wfile.write(body)

        def _parse_json_body(self):
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 1_000_000:
                raise ValueError("invalid body length")
            body = self.rfile.read(length)
            try:
                return json.loads(body)
            except json.JSONDecodeError as exc:
                raise TypeError("invalid JSON body") from exc

        def _handle_agent_request(self, payload):
            agent_name = payload.get("agent", payload.get("name", "alba"))
            question = payload.get("question", payload.get("prompt", ""))
            return app.ask_agent(agent_name, question)

        def _handle_respond_request(self, payload):
            prompt = payload.get("prompt", "")
            facts = payload.get("facts", [])
            if not isinstance(prompt, str) or not prompt.strip():
                raise ValueError("prompt is required")
            if not isinstance(facts, list):
                raise TypeError("facts must be a list")
            return app.respond(prompt.strip(), facts)

        def _handle_reason_request(self, payload):
            task = payload.get("task", payload.get("prompt", payload.get("question", "")))
            facts = payload.get("facts", payload.get("context", []))
            if not isinstance(task, str) or not task.strip():
                raise ValueError("task is required")
            if not isinstance(facts, list):
                facts = [str(facts)] if facts else []
            return app.reason(task.strip(), facts)

        def _handle_stable_reason_request(self, payload):
            task = payload.get("task", payload.get("prompt", payload.get("question", "")))
            facts = payload.get("facts", payload.get("context", []))
            policy_mode = payload.get("policy_mode", "balanced")
            if not isinstance(task, str) or not task.strip():
                raise ValueError("task is required")
            if not isinstance(facts, list):
                facts = [str(facts)] if facts else []
            return app.stable_reasoning_engine.process(task.strip(), facts, policy_mode=policy_mode)

        def _handle_vision_inspect_request(self, payload):
            image_path = payload.get("image_path")
            image_bytes_b64 = payload.get("image_bytes_b64")
            author = payload.get("author")
            task = payload.get("task", payload.get("prompt", ""))
            if image_path is not None and not isinstance(image_path, str):
                raise ValueError("image_path must be a string")
            if image_bytes_b64 is not None and not isinstance(image_bytes_b64, str):
                raise ValueError("image_bytes_b64 must be a string")
            if author is not None and not isinstance(author, str):
                raise ValueError("author must be a string")
            if task is not None and not isinstance(task, str):
                raise ValueError("task must be a string")
            return app.inspect_vision(image_path=image_path, image_bytes_b64=image_bytes_b64, author=author, task=(task or "").strip() or None)

        def _handle_create_request(self, payload):
            prompt = payload.get("prompt", "")
            modality = payload.get("modality", "image")
            if not isinstance(prompt, str) or not prompt.strip():
                raise ValueError("prompt is required")
            if not isinstance(modality, str) or not modality.strip():
                raise ValueError("modality is required")
            kwargs = {
                "seed": payload.get("seed", 42),
                "style": payload.get("style", "clean"),
                "author": payload.get("author"),
            }
            return app.creative_engine.create(prompt.strip(), modality=modality.strip(), **kwargs)

        def do_POST(self):
            parsed = urlparse(self.path)
            if parsed.path in {"/api/agents", "/api/v1/agents"}:
                try:
                    data = self._parse_json_body()
                    self._json(self._handle_agent_request(data))
                except (ValueError, json.JSONDecodeError) as exc:
                    self._json({"error": "invalid_request", "detail": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            if parsed.path in {"/api/respond", "/api/v1/respond"}:
                try:
                    data = self._parse_json_body()
                    self._json(self._handle_respond_request(data))
                except (ValueError, json.JSONDecodeError) as exc:
                    self._json({"error": "invalid_request", "detail": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            if parsed.path in {"/api/reason", "/api/v1/reason"}:
                try:
                    data = self._parse_json_body()
                    self._json(self._handle_reason_request(data))
                except (ValueError, json.JSONDecodeError) as exc:
                    self._json({"error": "invalid_request", "detail": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            if parsed.path in {"/api/stable-reason", "/api/v1/stable-reason"}:
                try:
                    data = self._parse_json_body()
                    self._json(self._handle_stable_reason_request(data))
                except (ValueError, TypeError, json.JSONDecodeError) as exc:
                    self._json({"error": "invalid_request", "detail": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            if parsed.path in {"/api/vision/inspect", "/api/v1/vision/inspect"}:
                try:
                    data = self._parse_json_body()
                    self._json(self._handle_vision_inspect_request(data))
                except (ValueError, TypeError, json.JSONDecodeError) as exc:
                    self._json({"error": "invalid_request", "detail": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            if parsed.path in {"/api/create", "/api/v1/create"}:
                try:
                    data = self._parse_json_body()
                    self._json(self._handle_create_request(data))
                except (ValueError, TypeError, json.JSONDecodeError) as exc:
                    self._json({"error": "invalid_request", "detail": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            return self._json({"error": "not_found"}, HTTPStatus.NOT_FOUND)

        def do_GET(self):
            parsed=urlparse(self.path)
            if parsed.path in {"/api/journey", "/api/v1/journey"}:
                try:
                    return self._json({"stones": app.ledger.recent(parse_qs(parsed.query).get("limit", ["50"])[0])})
                except ValueError:
                    return self._json({"error": "invalid_limit"}, HTTPStatus.BAD_REQUEST)
            if parsed.path in {"/api/registry", "/api/v1/registry"}:
                query = parse_qs(parsed.query)
                search = query.get("query", [""])[0].strip()
                if search:
                    return self._json({"sources": app.source_registry.find(search), "summary": app.source_registry.summary()})
                return self._json({"sources": app.source_registry.list_sources(), "summary": app.source_registry.summary()})
            if parsed.path in {"/api/platform", "/api/v1/platform"}:
                return self._json(app.platform_profile)
            if parsed.path in {"/api/agents", "/api/v1/agents"}:
                query = parse_qs(parsed.query)
                agent_name = query.get("agent", ["alba"])[0]
                question = query.get("question", [""])[0]
                try:
                    return self._json(app.ask_agent(agent_name, question))
                except ValueError as exc:
                    return self._json({"error": "invalid_request", "detail": str(exc)}, HTTPStatus.BAD_REQUEST)
            if parsed.path in {"/api/status", "/api/v1/status"}:
                return self._json({"status": "ok", "app": "neuclx", "version": "0.1.0", "layers": app.kernel.layers, "multilingual": True})
            if parsed.path in {"/api/reason", "/api/v1/reason"}:
                query = parse_qs(parsed.query)
                task = query.get("task", query.get("question", [""]))[0]
                facts = query.get("facts", [""])[0]
                try:
                    context = [fact.strip() for fact in facts.split("|") if fact.strip()]
                    return self._json(app.reason(task, context))
                except ValueError as exc:
                    return self._json({"error": "invalid_request", "detail": str(exc)}, HTTPStatus.BAD_REQUEST)
            if parsed.path in {"/api/stable-reason", "/api/v1/stable-reason"}:
                query = parse_qs(parsed.query)
                task = query.get("task", query.get("question", [""]))[0]
                facts = query.get("facts", [""])[0]
                policy_mode = query.get("policy_mode", ["balanced"])[0]
                try:
                    context = [fact.strip() for fact in facts.split("|") if fact.strip()]
                    return self._json(app.stable_reasoning_engine.process(task, context, policy_mode=policy_mode))
                except ValueError as exc:
                    return self._json({"error": "invalid_request", "detail": str(exc)}, HTTPStatus.BAD_REQUEST)
            if parsed.path in {"/api/stable-status", "/api/v1/stable-status"}:
                return self._json(app.stable_reasoning_engine.get_clean_reasoning_score())
            relative="index.html" if parsed.path=="/" else parsed.path.lstrip("/")
            if relative not in {"index.html","app.css","app.js"}: return self._json({"error":"not_found"},HTTPStatus.NOT_FOUND)
            path=STATIC/relative; body=path.read_bytes(); self.send_response(200); self.send_header("Content-Type",MIME[path.suffix]); self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body)
        def log_message(self,format,*args): return
    return Handler

def main(argv=None):
    parser=ArgumentParser(); parser.add_argument("--host",default="127.0.0.1"); parser.add_argument("--port",type=int,default=8787); parser.add_argument("--ledger",default="data/neuclx.sqlite3"); args=parser.parse_args(argv)
    server=ThreadingHTTPServer((args.host,args.port),handler_factory(NeuCLXApplication(args.ledger))); print(f"NeuCLX: http://{args.host}:{args.port}"); server.serve_forever()

if __name__=="__main__": main()

