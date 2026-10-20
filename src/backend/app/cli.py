import argparse
import json
from .core.objective import ObjectiveConfig
from .core.parser import read_problem
from .core.results import run
from .core.writer import write_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("algorithm", choices=("hill_climbing", "simulated_annealing", "genetic_algorithm"))
    parser.add_argument("--output", default="output/run.json")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--params", default="{}")
    parser.add_argument("--objective", choices=("value", "eta_weighted"), default="value")
    parser.add_argument("--eta-bonus", type=float, default=0.0)
    args = parser.parse_args()
    result = run(read_problem(args.input), args.algorithm, seed=args.seed, params=json.loads(args.params), objective=ObjectiveConfig(args.objective, args.eta_bonus))
    write_json(args.output, result)
    print(args.output)


if __name__ == "__main__": main()
