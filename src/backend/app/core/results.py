from collections.abc import Callable
from time import perf_counter
from .models import Problem, SearchResult, State
from .objective import ObjectiveConfig, score
from .validation import validate_state
from .writer import occupancy_dict, state_dict

Algorithm = Callable[..., SearchResult]
REGISTRY: dict[str, Algorithm] = {}


def register(name: str, algorithm: Algorithm) -> None:
    if name in REGISTRY:
        raise ValueError(f"algoritma sudah terdaftar: {name}")
    REGISTRY[name] = algorithm


def initial_state(problem: Problem, seed: int | None = None) -> State:
    from random import Random
    from .models import Orientation, Placement, Position, oriented_dimensions

    rng = Random(seed)
    state = State({p.id: None for p in problem.packages})
    packages = list(problem.packages)
    rng.shuffle(packages)

    for package in packages:
        if rng.random() < 0.25:
            continue

        candidates = []
        for truck in problem.trucks:
            for axes in (
                ("x", "y", "z"),
                ("x", "z", "y"),
                ("y", "x", "z"),
                ("y", "z", "x"),
                ("z", "x", "y"),
                ("z", "y", "x"),
            ):
                orientation = Orientation(*axes)
                size, dims = (
                    oriented_dimensions(package, orientation),
                    truck.dimensions,
                )

                for z in range(dims.h - size.h + 1):
                    for y in range(dims.l - size.l + 1):
                        for x in range(dims.w - size.w + 1):
                            candidates.append(
                                Placement(truck.id, Position(x, y, z), orientation)
                            )

        rng.shuffle(candidates)
        for place in candidates:
            state.placements[package.id] = place
            try:
                validate_state(problem, state)
                break
            except ValueError:
                state.placements[package.id] = None

    return state


def run(problem: Problem, algorithm: str, *, seed: int | None = None, params: dict | None = None, objective: ObjectiveConfig = ObjectiveConfig()) -> dict:
    from .algorithms import genetic_algorithm, hill_climbing, simulated_annealing  

    if algorithm not in REGISTRY:
        raise ValueError(
            f"algoritma tidak dikenal: {algorithm}; tersedia: {', '.join(REGISTRY)}"
        )

    initial = initial_state(problem, seed)
    snapshot = initial.copy()

    started = perf_counter()
    result = REGISTRY[algorithm](
        problem, initial, seed=seed, objective=objective, **(params or {})
    )
    duration = perf_counter() - started

    if not isinstance(result, SearchResult):
        raise TypeError("algoritma harus mengembalikan SearchResult")
    if initial.placements != snapshot.placements:
        raise ValueError("algoritma mengubah state awal")

    final = score(problem, result.final_state, objective)
    if result.iterations < 0 or len(result.score_history) != result.iterations + 1:
        raise ValueError("riwayat skor harus mencakup iterasi 0 dan setiap iterasi")
    if not result.score_history or abs(result.score_history[-1] - final) > 1e-8:
        raise ValueError("skor terakhir pada riwayat harus sama dengan skor state akhir")
    if result.average_history is not None and len(result.average_history) != len(
        result.score_history
    ):
        raise ValueError("panjang riwayat skor rata-rata harus sama dengan riwayat skor")

    resolved = validate_state(problem, result.final_state)
    return {
        "algorithm": algorithm,
        "seed": seed,
        "parameters": params or {},
        "objective": {"mode": objective.mode, "eta_bonus": objective.eta_bonus},
        "initial_state": state_dict(snapshot),
        "initial_score": score(problem, snapshot, objective),
        "final_state": state_dict(result.final_state),
        "final_score": final,
        "occupancy": occupancy_dict(problem, result.final_state),
        "loaded": resolved["loaded"],
        "outside": resolved["outside"],
        "weights": resolved["weights"],
        "score_history": result.score_history,
        "average_history": result.average_history,
        "iterations": result.iterations,
        "duration_seconds": duration,
        "metrics": result.metrics,
    }