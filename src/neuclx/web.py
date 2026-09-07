"""Dependency-free NeuCLX single-page chat server."""

from argparse import ArgumentParser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from .engine import CognitiveKernel
from .journey import JourneyLedger

STATIC=Path(__file__).with_name("static")
MIME={".html":"text/html; charset=utf-8",".css":"text/css; charset=utf-8",".js":"text/javascript; charset=utf-8"}

class NeuCLXApplication:
    def __init__(self, ledger_path="data/neuclx.sqlite3"):
        self.kernel=CognitiveKernel(layers=8); self.ledger=JourneyLedger(ledger_path)
    def respond(self,prompt,facts=()):
        for fact in facts:
            if isinstance(fact,str) and fact.strip(): self.kernel.ingest("chat:user-declared",fact)
        return self.ledger.record(prompt,self.kernel.answer(prompt))

def handler_factory(app):
    class Handler(BaseHTTPRequestHandler):
        server_version="NeuCLX/0.1"
        def _json(self,payload,status=HTTPStatus.OK):
            body=json.dumps(payload,ensure_ascii=False,sort_keys=True).encode(); self.send_response(status); self.send_header("Content-Type","application/json; charset=utf-8"); self.send_header("Content-Length",str(len(body))); self.send_header("Cache-Control","no-store"); self.end_headers(); self.wfile.write(body)
        def do_POST(self):
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
            relative="index.html" if parsed.path=="/" else parsed.path.lstrip("/")
            if relative not in {"index.html","app.css","app.js"}: return self._json({"error":"not_found"},404)
            path=STATIC/relative; body=path.read_bytes(); self.send_response(200); self.send_header("Content-Type",MIME[path.suffix]); self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body)
        def log_message(self,format,*args): return
    return Handler

def main(argv=None):
    parser=ArgumentParser(); parser.add_argument("--host",default="127.0.0.1"); parser.add_argument("--port",type=int,default=8787); parser.add_argument("--ledger",default="data/neuclx.sqlite3"); args=parser.parse_args(argv)
    server=ThreadingHTTPServer((args.host,args.port),handler_factory(NeuCLXApplication(args.ledger))); print(f"NeuCLX: http://{args.host}:{args.port}"); server.serve_forever()

if __name__=="__main__": main()

