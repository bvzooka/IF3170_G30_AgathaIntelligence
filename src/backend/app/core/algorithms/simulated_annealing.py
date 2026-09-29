from ..models import Problem, SearchResult, State
from ..objective import ObjectiveConfig
from ..results import register

def search(problem: Problem, initial: State, *, seed: int | None = None, objective: ObjectiveConfig = ObjectiveConfig(), **params) -> SearchResult:
    raise NotImplementedError("Implement simulated annealing here")

register("simulated_annealing", search)
