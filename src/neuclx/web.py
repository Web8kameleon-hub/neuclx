"""Dependency-free NeuCLX single-page chat server."""

from argparse import ArgumentParser
from datetime import UTC, datetime
from hashlib import sha256
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from .agents import AlbaAgent, AlbiAgent, JonaAgent
from .engine import CognitiveKernel
from .journey import JourneyLedger
from .memory import EvidenceMemory, MemoryEntry
from .model_adapter import ModelAdapter

STATIC=Path(__file__).with_name("static")
MIME={".html":"text/html; charset=utf-8",".css":"text/css; charset=utf-8",".js":"text/javascript; charset=utf-8"}

class NeuCLXApplication:
    def __init__(self, ledger_path="data/neuclx.sqlite3"):
        ledger_path = str(ledger_path)
        self.kernel=CognitiveKernel(layers=8)
        self.ledger=JourneyLedger(ledger_path)
        memory_path = str(Path(ledger_path).with_name(Path(ledger_path).stem + "_memory.sqlite3"))
        self.memory = EvidenceMemory(memory_path)
        self.model_adapter = ModelAdapter(provider="local", model_name="neuclx-core", enabled=True)
        self.agents = {
            "alba": AlbaAgent(),
            "albi": AlbiAgent(),
            "jona": JonaAgent(),
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

    def __del__(self):
        try:
            self.close()
        except Exception:
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

def handler_factory(app):
    class Handler(BaseHTTPRequestHandler):
        server_version="NeuCLX/0.1"
        def _json(self,payload,status=HTTPStatus.OK):
            body=json.dumps(payload,ensure_ascii=False,sort_keys=True).encode(); self.send_response(status); self.send_header("Content-Type","application/json; charset=utf-8"); self.send_header("Content-Length",str(len(body))); self.send_header("Cache-Control","no-store"); self.end_headers(); self.wfile.write(body)
        def do_POST(self):
            if self.path=="/api/agents":
                try:
                    length=int(self.headers.get("Content-Length","0"))
                    if not 0<length<=1_000_000: raise ValueError("invalid body length")
                    data=json.loads(self.rfile.read(length))
                    agent_name=data.get("agent","alba")
                    question=data.get("question","")
                    self._json(app.ask_agent(agent_name, question))
                except (ValueError,json.JSONDecodeError) as exc: self._json({"error":"invalid_request","detail":str(exc)},400)
                return
            if self.path!="/api/respond": return self._json({"error":"not_found"},404)
            try:
                length=int(self.headers.get("Content-Length","0"))
                if not 0<length<=1_000_000: raise ValueError("invalid body length")
                data=json.loads(self.rfile.read(length)); prompt=data.get("prompt",""); facts=data.get("facts",[])
                if not isinstance(prompt,str) or not prompt.strip(): raise ValueError("prompt is required")
                if not isinstance(facts,list): raise ValueError("facts must be a list")
                self._json(app.respond(prompt.strip(),facts))
            except (ValueError,json.JSONDecodeError) as exc: self._json({"error":"invalid_request","detail":str(exc)},400)
        def do_GET(self):
            parsed=urlparse(self.path)
            if parsed.path=="/api/journey":
                try: return self._json({"stones":app.ledger.recent(parse_qs(parsed.query).get("limit",["50"])[0])})
                except ValueError: return self._json({"error":"invalid_limit"},400)
            if parsed.path=="/api/agents":
                query = parse_qs(parsed.query)
                agent_name = query.get("agent", ["alba"])[0]
                question = query.get("question", [""])[0]
                try:
                    return self._json(app.ask_agent(agent_name, question))
                except ValueError as exc:
                    return self._json({"error":"invalid_request","detail":str(exc)},400)
            relative="index.html" if parsed.path=="/" else parsed.path.lstrip("/")
            if relative not in {"index.html","app.css","app.js"}: return self._json({"error":"not_found"},404)
            path=STATIC/relative; body=path.read_bytes(); self.send_response(200); self.send_header("Content-Type",MIME[path.suffix]); self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body)
        def log_message(self,format,*args): return
    return Handler

def main(argv=None):
    parser=ArgumentParser(); parser.add_argument("--host",default="127.0.0.1"); parser.add_argument("--port",type=int,default=8787); parser.add_argument("--ledger",default="data/neuclx.sqlite3"); args=parser.parse_args(argv)
    server=ThreadingHTTPServer((args.host,args.port),handler_factory(NeuCLXApplication(args.ledger))); print(f"NeuCLX: http://{args.host}:{args.port}"); server.serve_forever()

if __name__=="__main__": main()

