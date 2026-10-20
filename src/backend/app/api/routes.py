import re
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from ..core.objective import ObjectiveConfig
from ..core.parser import parse_problem
from ..core.results import REGISTRY, run
from ..core.writer import write_json

router = APIRouter()
OUTPUT_DIR = Path(__file__).resolve().parents[4] / "output"

class RunRequest(BaseModel):
    problem: dict
    algorithm: str
    seed: int | None = None
    params: dict = Field(default_factory=dict)
    objective: dict = Field(default_factory=dict)
    dataset: str = "dataset"


# <dataset>_<mode>_<param ringkas>_seed<n>.json
# contoh: medium-2trucks_eta300_pop50_it100_seed1.json
SHORT_PARAMS = {
    "simulated_annealing": ("", (("initial_temperature", "t"), ("cooling_rate", "cr"), ("max_iterations", "it"))),
    "hill_climbing": ("hc", (("max_iterations", "it"), ("max_sideways_moves", "sw"), ("max_restarts", "rs"), ("max_iterations_per_restart", "it"))),
    "genetic_algorithm": ("", (("population_size", "pop"), ("max_iterations", "it"))),
}


def output_filename(request: RunRequest) -> str:
    objective = request.objective
    mode = "value" if objective.get("mode", "value") == "value" else f"eta{objective.get('eta_bonus', 0):g}"
    prefix, keys = SHORT_PARAMS[request.algorithm]
    parts = [prefix] if prefix else []
    if request.algorithm == "hill_climbing":
        parts[0] += "-" + request.params.get("variant", "steepest").replace("random_restart", "restart")
    parts += [f"{short}{request.params[key]:g}" for key, short in keys if key in request.params]
    dataset = re.sub(r"[^\w.-]", "-", request.dataset)
    return f"{dataset}_{mode}_{'_'.join(parts)}_seed{request.seed}.json"


@router.get("/health")
def health() -> dict:
    from ..core.algorithms import genetic_algorithm, hill_climbing, simulated_annealing  # noqa: F401
    return {"status": "ok", "algorithms": list(REGISTRY)}


@router.post("/runs")
def create_run(request: RunRequest) -> dict:
    try:
        result = run(parse_problem(request.problem), request.algorithm, seed=request.seed, params=request.params, objective=ObjectiveConfig(**request.objective))
        write_json(OUTPUT_DIR / output_filename(request), result)
        return result
    except NotImplementedError as exc: raise HTTPException(status_code=501, detail=str(exc)) from exc
    except (ValueError, TypeError, KeyError) as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc
