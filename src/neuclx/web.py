"""Dependency-free NeuCLX single-page chat server."""

import json
from argparse import ArgumentParser
from datetime import UTC, datetime
from hashlib import sha256
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
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
from .learning import LearningStore
from .hybrid_fluid import HybridFluidError, HybridFluidPipeline
from .megalayer import MegaLayerAdapter, MegaLayerError
from .web_evidence import MAX_URLS, PublicWebReadError, PublicWebReader
from .self_learning import SelfLearning
from .cited_answer import CITATION_INSTRUCTION, enforce, numbered_context, refusal

HYBRID_EXCERPTS = 5

STATIC = Path(__file__).with_name("static")
MIME = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8"}


class NeuCLXApplication:
    def __init__(self, ledger_path="data/neuclx.sqlite3"):
        ledger_path = str(ledger_path)
        self.kernel = CognitiveKernel(layers=8)
        self.learning = LearningStore(str(Path(ledger_path).with_name(Path(ledger_path).stem + "_learning.sqlite3")))
        self.ledger = JourneyLedger(ledger_path)
        memory_path = str(Path(ledger_path).with_name(Path(ledger_path).stem + "_memory.sqlite3"))
        self.memory = EvidenceMemory(memory_path)
        stable_memory_path = str(Path(ledger_path).with_name(Path(ledger_path).stem + "_stable_memory.sqlite3"))
        self.stable_memory = EvidenceMemory(stable_memory_path)
        self.model_adapter = ModelAdapter.from_environment()
        self.reasoning_engine = ReasoningEngine(memory=self.memory, model=self.model_adapter)
        self.megalayer = MegaLayerAdapter.from_environment()
        self.hybrid_fluid = HybridFluidPipeline.from_environment(
            self.reasoning_engine.jona,
            self.ledger,
        )
        self.web_reader = PublicWebReader(sandbox=self.reasoning_engine.jona)
        self.self_learning = SelfLearning(self.learning, self.ledger, self.reasoning_engine.jona)
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
                "endpoints": [
                    "/api/status",
                    "/api/agents",
                    "/api/reason",
                    "/api/respond",
                    "/api/registry",
                    "/api/platform",
                    "/api/vision/inspect",
                    "/api/create",
                ],
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

    def _read_web_sources(self, query: str, source_urls=(), max_excerpts: int = 1):
        if source_urls is None:
            source_urls = []
        if not isinstance(source_urls, list):
            raise TypeError("source_urls must be a list")
        if len(source_urls) > MAX_URLS:
            raise ValueError(f"at most {MAX_URLS} source URLs are allowed per request")
        hits = []
        report = []
        for url in source_urls:
            if not isinstance(url, str) or not url.strip():
                raise ValueError("source URLs must be non-empty strings")
            try:
                datum = self.web_reader.read(query, url.strip(), max_excerpts)
            except PublicWebReadError as exc:
                report.append({"source": url, "state": EvidenceState.UNAVAILABLE.value, "reason": str(exc)})
                continue
            hits.extend(datum.metadata.get("evidence_chain", []))
            report.append({"source": url, "state": datum.state.value, "method": datum.method})
        return hits, report

    def _attach_web_evidence(self, answer: Datum, hits, report):
        metadata = {**answer.metadata, "web_sources": report}
        if not hits:
            result = Datum(answer.value, answer.state, answer.source, answer.method, metadata)
            return self.reasoning_engine.jona.release(result)
        evidence_chain = [*metadata.get("evidence_chain", []), *hits]
        excerpts = [f"[{hit['source']}]\n{hit['excerpt']}" for hit in evidence_chain if hit.get("excerpt")]
        result = Datum(
            "\n\n".join(excerpts),
            EvidenceState.DECLARED,
            source="neuclx:evidence-chain",
            method="local-and-public-web-excerpts",
            metadata={
                **metadata,
                "evidence_chain": evidence_chain,
                "jona_decision": "sandbox_only",
                "claim_status": "Source excerpts are declared and are not independently verified.",
            },
        )
        return self.reasoning_engine.jona.release(result)

    def respond(self, prompt, facts=(), source_urls=None):
        fact_list = [fact.strip() for fact in (facts or ()) if isinstance(fact, str) and fact.strip()]
        for fact in fact_list:
            digest = sha256(fact.encode("utf-8")).hexdigest()
            self.learning.ingest("chat:user-declared:" + digest, "sha256:" + digest, fact)
        hits, web_report = self._read_web_sources(prompt, source_urls)
        answer = self._attach_web_evidence(self.learning.answer(prompt), hits, web_report)
        if self.model_adapter.enabled:
            context = fact_list[:]
            context.extend(
                f"[{hit['source']}]\n{hit['excerpt']}"
                for hit in answer.metadata.get("evidence_chain", [])
                if hit.get("excerpt")
            )
            generated = self.reasoning_engine.converse(prompt, context)
            answer = self.reasoning_engine.jona.release(
                Datum(
                    generated.value,
                    generated.state,
                    generated.source,
                    generated.method,
                    {
                        **generated.metadata,
                        "claim_status": "Model-generated response; not independently verified.",
                        "retrieval_state": answer.state.value,
                        "evidence_chain": answer.metadata.get("evidence_chain", []),
                        "web_sources": answer.metadata.get("web_sources", web_report),
                    },
                )
            )
        return self.ledger.record(prompt, answer)

    def reason(
        self,
        task: str,
        facts=(),
        *,
        source_urls=None,
        max_iterations: int = 5,
        mode: str = "native",
    ):
        task_text = (task or "").strip()
        if not task_text:
            raise ValueError("task is required")
        if mode not in {"native", "hybrid-fluid"}:
            raise ValueError("mode must be 'native' or 'hybrid-fluid'")
        if mode == "hybrid-fluid":
            if not isinstance(facts, (list, tuple)):
                raise TypeError("facts must be a list of strings")
            fact_list = [fact.strip() for fact in (facts or []) if isinstance(fact, str) and fact.strip()]
            web_hits, web_report = self._read_web_sources(task_text, source_urls, HYBRID_EXCERPTS)
            learned_count = self.self_learning.learn_web_hits(web_hits)
            result = self.hybrid_fluid.run(task_text, fact_list)
            trace = result.metadata.get("stages", [])
            value = result.value if isinstance(result.value, dict) else {}
            model_answer = None
            memory = None
            if self.model_adapter.enabled and result.state is EvidenceState.COMPUTED:
                retrieved = self.learning.answer(task_text, limit=HYBRID_EXCERPTS)
                hits = [hit for hit in retrieved.metadata.get("evidence_chain", []) if hit.get("excerpt")]
                signals = []
                mega = value.get("megalayer")
                if isinstance(mega, dict) and isinstance(mega.get("value"), dict):
                    signals.append(
                        "MegaLayer unique_signature=%s meta_level_name=%s"
                        % (mega["value"].get("unique_signature"), mega["value"].get("meta_level_name"))
                    )
                alpha = value.get("alphabet_result")
                if isinstance(alpha, dict) and isinstance(alpha.get("value"), dict):
                    signals.append(
                        "Alphabet total_complexity=%s (computed index)" % alpha["value"].get("total_complexity")
                    )
                context = [
                    *fact_list,
                    *numbered_context(hits),
                    *signals,
                ]
                if hits:
                    raw = self.reasoning_engine.converse(task_text, context, CITATION_INSTRUCTION)
                    generated = enforce(str(raw.value or ""), hits)
                    generated.metadata["model"] = raw.source
                    generated.metadata["raw_output_sha256"] = sha256(str(raw.value or "").encode("utf-8")).hexdigest()
                else:
                    generated = refusal("no retrieved source")
                facets = {
                    "mode": "hybrid-fluid",
                    "model": str(generated.source),
                    "sources": ",".join(sorted({urlparse(str(h.get("source", ""))).hostname or "" for h in hits})),
                }
                memory = self.self_learning.remember_answer(task_text, generated, hits, facets)
                model_answer = memory["answer"]
                self.self_learning.record_use(hits)
            return {
                "assistant_response": model_answer.as_dict() if model_answer is not None else None,
                "mode": "hybrid-fluid",
                "task": task_text,
                "intent": "hybrid-fluid-11-stage",
                "state": result.state.value,
                "conclusion": (
                    "Hybrid-Fluid execution completed; raw service outputs are attached."
                    if result.state is EvidenceState.COMPUTED
                    else "Hybrid-Fluid result was not released by JONA."
                ),
                "confidence": None,
                "confidence_state": EvidenceState.UNAVAILABLE.value,
                "evidence_path": [
                    nested.get("source")
                    for key in ("alphabet_profile", "alphabet_result", "wave_indices", "megalayer", "fluid_engine")
                    if isinstance((nested := value.get(key)), dict) and nested.get("source")
                ],
                "trace": {
                    "steps": [
                        {
                            "reasoning_type": stage["name"],
                            "status": stage["output_state"],
                            "hypothesis": stage["jona_decision"],
                        }
                        for stage in trace
                    ]
                },
                "status": result.state.value,
                "ledger": value.get("ledger"),
                "alphabet_profile": value.get("alphabet_profile"),
                "alphabet_result": value.get("alphabet_result"),
                "wave_indices": value.get("wave_indices"),
                "megalayer": value.get("megalayer"),
                "fluid_engine": value.get("fluid_engine"),
                "response": result.as_dict(),
                "web_sources": web_report,
                "learned_excerpts": learned_count,
                "self_memory": (
                    {
                        "stone": memory["stone"]["number"],
                        "stigma_frame": memory["stone"]["stigma_frame"],
                        "grounding": memory["grounding"],
                        "novelty": memory["novelty"],
                    }
                    if memory is not None
                    else None
                ),
                "knowledge_tiers": self.self_learning.tiers().as_dict(),
            }
        web_hits, web_report = self._read_web_sources(task_text, source_urls)
        megalayer = self.megalayer.analyze(task_text, self.reasoning_engine.jona).as_dict()
        fact_list = [str(fact).strip() for fact in (facts or []) if isinstance(fact, str) and str(fact).strip()]
        assistant_response = self.reasoning_engine.converse(
            task_text,
            [
                *fact_list,
                *(f"[{hit['source']}]\n{hit['excerpt']}" for hit in web_hits if hit.get("excerpt")),
            ],
        )
        if not fact_list:
            from .simple_logic_engine import SimpleLogicEngine

            is_simple, simple_answer, simple_confidence = SimpleLogicEngine.detect_and_solve(task_text)
            if is_simple and simple_answer is not None:
                computed = Datum(
                    simple_answer,
                    EvidenceState.COMPUTED,
                    source="simple_logic_engine",
                    method="symbolic:detect_and_solve",
                    metadata={
                        "confidence": simple_confidence,
                        "intent": "arithmetic.word_problem",
                        "evidence_chain": web_hits,
                        "web_sources": web_report,
                    },
                )
                computed = self.reasoning_engine.jona.release(computed)
                stored = self.ledger.record(task_text, computed)
                return {
                    "task": task_text,
                    "intent": "arithmetic.word_problem",
                    "state": "computed",
                    "conclusion": simple_answer,
                    "confidence": simple_confidence,
                    "confidence_state": "computed",
                    "evidence_path": [],
                    "trace": {
                        "steps": [{"reasoning_type": "symbolic", "status": "success", "hypothesis": simple_answer}]
                    },
                    "status": "ok",
                    "ledger": stored,
                    "megalayer": megalayer,
                    "evidence_chain": web_hits,
                    "web_sources": web_report,
                    "assistant_response": assistant_response.as_dict(),
                }
            evidence = self._attach_web_evidence(self.learning.answer(task_text), web_hits, web_report)
            stored = self.ledger.record(task_text, evidence)
            return {
                "task": task_text,
                "intent": "document-retrieval",
                "state": evidence.state.value,
                "conclusion": evidence.value or "Nuk ka evidencë të disponueshme për këtë pyetje.",
                "confidence": None,
                "confidence_state": evidence.state.value,
                "evidence_path": [hit["source"] for hit in evidence.metadata.get("evidence_chain", [])],
                "evidence_chain": evidence.metadata.get("evidence_chain", []),
                "trace": {"steps": []},
                "status": "ok",
                "ledger": stored,
                "megalayer": megalayer,
                "web_sources": web_report,
                "assistant_response": assistant_response.as_dict(),
            }
        result = self.reasoning_engine.reason(task_text, fact_list, max_iterations=max_iterations)
        conclusion = self.reasoning_engine.jona.release(
            Datum(
                result["conclusion"],
                EvidenceState.COMPUTED if result["status"] == "ok" else EvidenceState.UNAVAILABLE,
                source="reasoning_engine",
                method="reasoning:api",
                metadata={
                    "intent": result["intent"],
                    "confidence": result["confidence"],
                    "evidence_chain": web_hits,
                    "web_sources": web_report,
                },
            )
        )
        stored = self.ledger.record(
            task_text,
            conclusion,
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
            "megalayer": megalayer,
            "evidence_chain": web_hits,
            "web_sources": web_report,
            "assistant_response": assistant_response.as_dict(),
        }

    def inspect_vision(
        self,
        image_path: str | None = None,
        image_bytes_b64: str | None = None,
        *,
        author: str | None = None,
        task: str | None = None,
    ):
        if not image_path and not image_bytes_b64:
            raise ValueError("image_path or image_bytes_b64 is required")
        if image_path:
            datum = self.vision_encoder.inspect_path(image_path, author=author, task=task)
        else:
            datum = self.vision_encoder.inspect_base64(
                image_bytes_b64 or "", source="inline-base64", author=author, task=task
            )
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
        server_version = "NeuCLX/0.1"

        def _json(self, payload, status=HTTPStatus.OK):
            body = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

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
            source_urls = payload.get("source_urls", [])
            if not isinstance(prompt, str) or not prompt.strip():
                raise ValueError("prompt is required")
            if not isinstance(facts, list):
                raise TypeError("facts must be a list")
            if not isinstance(source_urls, list):
                raise TypeError("source_urls must be a list")
            try:
                return app.respond(prompt.strip(), facts, source_urls)
            except PermissionError as exc:
                raise PermissionError(f"JONA rejected web source: {exc}") from exc

        def _handle_reason_request(self, payload):
            task = payload.get("task", payload.get("prompt", payload.get("question", "")))
            facts = payload.get("facts", payload.get("context", []))
            source_urls = payload.get("source_urls", [])
            mode = payload.get("mode", "native")
            if not isinstance(task, str) or not task.strip():
                raise ValueError("task is required")
            if not isinstance(facts, list):
                facts = [str(facts)] if facts else []
            if not isinstance(source_urls, list):
                raise TypeError("source_urls must be a list")
            if not isinstance(mode, str):
                raise TypeError("mode must be a string")
            return app.reason(task.strip(), facts, source_urls=source_urls, mode=mode)

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
            return app.inspect_vision(
                image_path=image_path, image_bytes_b64=image_bytes_b64, author=author, task=(task or "").strip() or None
            )

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
                except PermissionError as exc:
                    self._json({"error": "jona_rejected", "detail": str(exc)}, HTTPStatus.FORBIDDEN)
                except (ValueError, json.JSONDecodeError) as exc:
                    self._json({"error": "invalid_request", "detail": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            if parsed.path in {"/api/reason", "/api/v1/reason"}:
                try:
                    data = self._parse_json_body()
                    self._json(self._handle_reason_request(data))
                except HybridFluidError as exc:
                    self._json(
                        {"error": exc.error_code, "detail": str(exc)},
                        exc.status_code,
                    )
                except MegaLayerError as exc:
                    self._json({"error": "megalayer_unavailable", "detail": str(exc)}, HTTPStatus.BAD_GATEWAY)
                except PermissionError as exc:
                    self._json({"error": "jona_rejected", "detail": str(exc)}, HTTPStatus.FORBIDDEN)
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
            parsed = urlparse(self.path)
            if parsed.path == "/api/learning":
                return self._json(app.learning.status().as_dict())
            if parsed.path in {"/api/journey", "/api/v1/journey"}:
                try:
                    return self._json({"stones": app.ledger.recent(parse_qs(parsed.query).get("limit", ["50"])[0])})
                except ValueError:
                    return self._json({"error": "invalid_limit"}, HTTPStatus.BAD_REQUEST)
            if parsed.path in {"/api/registry", "/api/v1/registry"}:
                query = parse_qs(parsed.query)
                search = query.get("query", [""])[0].strip()
                if search:
                    return self._json(
                        {"sources": app.source_registry.find(search), "summary": app.source_registry.summary()}
                    )
                return self._json(
                    {"sources": app.source_registry.list_sources(), "summary": app.source_registry.summary()}
                )
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
                return self._json(
                    {
                        "status": "ok",
                        "app": "neuclx",
                        "version": "0.1.0",
                        "layers": app.kernel.layers,
                        "multilingual": True,
                    }
                )
            if parsed.path in {"/api/reason", "/api/v1/reason"}:
                query = parse_qs(parsed.query)
                task = query.get("task", query.get("question", [""]))[0]
                facts = query.get("facts", [""])[0]
                try:
                    context = [fact.strip() for fact in facts.split("|") if fact.strip()]
                    return self._json(app.reason(task, context))
                except MegaLayerError as exc:
                    return self._json({"error": "megalayer_unavailable", "detail": str(exc)}, HTTPStatus.BAD_GATEWAY)
                except PermissionError as exc:
                    return self._json({"error": "jona_rejected", "detail": str(exc)}, HTTPStatus.FORBIDDEN)
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
            relative = "index.html" if parsed.path == "/" else parsed.path.lstrip("/")
            if relative not in {"index.html", "app.css", "app.js"}:
                return self._json({"error": "not_found"}, HTTPStatus.NOT_FOUND)
            path = STATIC / relative
            body = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", MIME[path.suffix])
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            return

    return Handler


def main(argv=None):
    parser = ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--ledger", default="data/neuclx.sqlite3")
    args = parser.parse_args(argv)
    server = ThreadingHTTPServer((args.host, args.port), handler_factory(NeuCLXApplication(args.ledger)))
    print(f"NeuCLX: http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
