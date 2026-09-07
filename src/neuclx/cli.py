import argparse
import json
from .engine import CognitiveKernel


def main(argv=None):
    parser = argparse.ArgumentParser(prog="neuclx")
    parser.add_argument("query")
    parser.add_argument("--fact", action="append", default=[])
    args = parser.parse_args(argv)
    kernel = CognitiveKernel()
    for index, fact in enumerate(args.fact):
        kernel.ingest(f"cli:fact:{index}", fact)
    print(json.dumps(kernel.answer(args.query).as_dict(), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

