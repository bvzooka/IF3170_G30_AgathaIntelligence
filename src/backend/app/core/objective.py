from dataclasses import dataclass
from .models import Problem, State
from .validation import validate_state


@dataclass(frozen=True)
class ObjectiveConfig:
    mode: str = "value"
    eta_bonus: float = 0.0

    def __post_init__(self):
        if self.mode not in ("value", "eta_weighted"):
            raise ValueError("mode harus value atau eta_weighted")
        if type(self.eta_bonus) not in (int, float) or not 0 <= self.eta_bonus < float("inf"):
            raise ValueError("eta_bonus harus berupa angka tidak negatif dan finite")

# hitung value yang ada di truk
# kalau mode == value -> package.value
# kalau mode == eta_weighted -> ETA diperhitungkan
def score(problem: Problem, state: State, config: ObjectiveConfig = ObjectiveConfig(),) -> float:
    validate_state(problem, state)
    return sum(package.value * (1 + config.eta_bonus / (package.eta + 1))
        if config.mode == "eta_weighted"
        else package.value
        for package in problem.packages
        if state.placements[package.id] is not None
    )