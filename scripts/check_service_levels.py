import argparse,json
from pathlib import Path

def evaluate(benchmark,policy):
    total=benchmark["iterations"]
    sli={"p95_latency_ns":benchmark["latency_ns"]["p95"],"error_rate":benchmark["errors"]/total,"provenance_coverage":benchmark["provenance_tagged"]/total}
    slo=policy["slo"]
    checks={"p95_latency":sli["p95_latency_ns"]<=slo["p95_latency_ns_max"],"error_rate":sli["error_rate"]<=slo["error_rate_max"],"provenance_coverage":sli["provenance_coverage"]>=slo["provenance_coverage_min"]}
    return {"schema_version":"1.0","state":"computed","sli":sli,"slo_checks":checks,"passed":all(checks.values()),"sla":policy["sla"],"cd":policy["cd"]}

def main():
    p=argparse.ArgumentParser();p.add_argument("--benchmark",required=True);p.add_argument("--policy",default="service-levels.json");p.add_argument("--output",required=True);a=p.parse_args()
    report=evaluate(json.loads(Path(a.benchmark).read_text()),json.loads(Path(a.policy).read_text()));Path(a.output).write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");print(json.dumps(report,sort_keys=True))
    if not report["passed"]:raise SystemExit("SLI/SLO gate failed")
if __name__=="__main__":main()
