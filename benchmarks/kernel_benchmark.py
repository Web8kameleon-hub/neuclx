"""Reproducible workload definition; timing results are explicitly measured per run."""

import argparse,json,platform,statistics,time
from pathlib import Path
from neuclx import CognitiveKernel

def run(iterations=2000):
    kernel=CognitiveKernel(layers=8)
    kernel.ingest("benchmark:fixture","NeuCLX sovereign cognitive cells use provenance JONA HVWO and Stigma memory")
    samples=[];errors=0;provenance_tagged=0;result=None
    for _ in range(iterations):
        start=time.perf_counter_ns()
        try:
            result=kernel.answer("sovereign provenance cells")
            if result.method:provenance_tagged+=1
        except Exception:
            errors+=1
        samples.append(time.perf_counter_ns()-start)
    ordered=sorted(samples)
    return {"schema_version":"1.0","state":"measured","workload":"deterministic-token-overlap-v1","iterations":iterations,"errors":errors,"successful":iterations-errors,"provenance_tagged":provenance_tagged,"result_state":result.state.value if result else "unavailable","latency_ns":{"median":int(statistics.median(samples)),"p95":ordered[int(.95*(len(ordered)-1))],"min":min(samples),"max":max(samples)},"environment":{"python":platform.python_version(),"platform":platform.platform()}}

def main():
    p=argparse.ArgumentParser();p.add_argument("--iterations",type=int,default=2000);p.add_argument("--output",default="evidence/benchmark.json");a=p.parse_args();result=run(a.iterations);path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");print(json.dumps(result,sort_keys=True))
if __name__=="__main__":main()
