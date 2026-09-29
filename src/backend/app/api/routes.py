from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from ..core.objective import ObjectiveConfig
from ..core.parser import parse_problem
from ..core.results import REGISTRY, run

router = APIRouter()

class RunRequest(BaseModel):
    problem: dict
    algorithm: str
    seed: int | None = None
    params: dict = Field(default_factory=dict)
    objective: dict = Field(default_factory=dict)


@router.get("/health")
def health() -> dict:
    from ..core.algorithms import genetic_algorithm, hill_climbing, simulated_annealing  # noqa: F401
    return {"status": "ok", "algorithms": list(REGISTRY)}


@router.post("/runs")
def create_run(request: RunRequest) -> dict:
    try: return run(parse_problem(request.problem), request.algorithm, seed=request.seed, params=request.params, objective=ObjectiveConfig(**request.objective))
    except NotImplementedError as exc: raise HTTPException(status_code=501, detail=str(exc)) from exc
    except (ValueError, TypeError, KeyError) as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc
