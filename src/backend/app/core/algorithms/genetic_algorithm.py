from ..models import Problem, SearchResult, State
from ..objective import ObjectiveConfig
from ..results import register

def search(problem: Problem, initial: State, *, seed: int | None = None, objective: ObjectiveConfig = ObjectiveConfig(), population_size: int = 50, max_iterations: int = 100, **params) -> SearchResult:
    raise NotImplementedError("Implement genetic algorithm here")

register("genetic_algorithm", search)
