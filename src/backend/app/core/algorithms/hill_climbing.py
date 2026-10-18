import random

from ..models import Position, Problem, SearchResult, State
from ..neighbors import move, swap, rotate, neighbors
from ..objective import ObjectiveConfig, score
from ..results import initial_state, register

def positive_int(value:int, name:str) -> None:
    if type(value) is not int or value <= 0: raise ValueError(f"{name} harus integer atau positif")

def nonnegative_int(value:int, name: str) -> None:
    if type(value) is not int or value < 0: raise ValueError(f"{name} harus integer atau tidak negatif")

def best_neighbors(problem: Problem, current: State, objective: ObjectiveConfig):
    best_score = float("-inf") #best score dari -infinite
    best_state = []
    evaluated = 0
    for candidate in neighbors(problem, current): 
        candidate_score = score(problem, candidate, objective)
        evaluated += 1
        if candidate_score > best_score: 
            best_score = candidate_score
            best_state = [candidate]
        elif candidate_score == best_score:
            best_state.append(candidate)
    return best_state, best_score, evaluated

def random_neighbor(problem: Problem, current: State, rng: random.Random) -> State | None: 
    package_ids = list(current.placements)
    if not package_ids: return None

    for _ in range(64):
        package_id = rng.choice(package_ids)
        operation = rng.choice(("move", "swap", "rotate"))

        if operation == "swap":
            if len(package_ids) < 2:
                continue
            other_id = rng.choice([pid for pid in package_ids if pid != package_id])
            candidate = swap(problem, current, package_id, other_id)
        elif operation == "rotate":
            candidate = rotate(problem, current, package_id, rng.choice(("x", "y", "z")))
        elif rng.randrange(len(problem.trucks) + 1) == 0:
            candidate = move(problem, current, package_id, None)
        else:
            truck = rng.choice(problem.trucks)
            dims = truck.dimensions
            position = Position(rng.randrange(dims.w), rng.randrange(dims.l), rng.randrange(dims.h))
            candidate = move(problem, current, package_id, truck.id, position)

        if candidate is not None:
            return candidate
    return None

def steepest(problem: Problem, initial: State, objective: ObjectiveConfig, rng: random.Random, max_iterations: int) -> SearchResult:
    current = initial.copy()
    current_score = score(problem, current, objective)
    history = [current_score]
    evaluated = 0

    for _ in range(max_iterations):
        best_states, best_score, count = best_neighbors(problem, current, objective)
        evaluated += count
        if not best_states or best_score <= current_score:break

        current = rng.choice(best_states)
        current_score = best_score
        history.append(current_score)

    return SearchResult(current, history, len(history) - 1, {"variant": "steepest", "neighbors_evaluated": evaluated})

def sideways(problem: Problem, initial: State, objective: ObjectiveConfig, rng: random.Random, max_iterations: int, max_sideways_moves: int) -> SearchResult:
    current = initial.copy()
    current_score = score(problem, current, objective)
    history = [current_score]
    sideways_moves = 0
    consecutive_sideways = 0
    evaluated = 0

    for _ in range(max_iterations):
        best_states, best_score, count = best_neighbors(problem, current, objective)
        evaluated += count
        if not best_states or best_score < current_score:
            break
        if best_score == current_score and consecutive_sideways >= max_sideways_moves:
            break

        current = rng.choice(best_states)
        if best_score == current_score:
            sideways_moves += 1
            consecutive_sideways += 1
        else:
            consecutive_sideways = 0
        current_score = best_score
        history.append(current_score)

    return SearchResult(current, history, len(history) - 1, {"variant": "sideways", "sideways_moves": sideways_moves, "max_sideways_moves": max_sideways_moves, "neighbors_evaluated": evaluated,})

def stochastic(problem: Problem, initial: State, objective: ObjectiveConfig, rng: random.Random, max_iterations: int) -> SearchResult:
    current = initial.copy()
    current_score = score(problem, current, objective)
    history = [current_score]
    accepted = 0

    for _ in range(max_iterations):
        candidate = random_neighbor(problem, current, rng)
        if candidate is not None:
            candidate_score = score(problem, candidate, objective)
            if candidate_score > current_score:
                current, current_score = candidate, candidate_score
                accepted += 1
        history.append(current_score)

    return SearchResult(current, history, max_iterations, {"variant": "stochastic", "accepted_moves": accepted})

def random_restart(problem: Problem, initial: State, objective: ObjectiveConfig, rng: random.Random, max_restarts: int, max_iterations_per_restart: int) -> SearchResult:
    best = initial.copy()
    best_score = score(problem, best, objective)
    history = [best_score]
    iterations_per_restart = []
    evaluated = 0
    restarts = 0
    current = initial.copy()
    
    upper_bound = 0.0
    for package in problem.packages:
        if objective.mode == "eta_weighted":
            package_score = package.value * (1 + objective.eta_bonus / (package.eta + 1))
        else:
            package_score = package.value
        upper_bound += package_score

    for run_index in range(max_restarts + 1):
        steps = 0
        current_score = score(problem, current, objective)

        if current_score > best_score:
            best = current.copy()
            best_score = current_score
            history[-1] = best_score

        # pindah neighbor kalo skor naik
        for _ in range(max_iterations_per_restart):
            best_states, next_score, count = best_neighbors(problem, current, objective)
            evaluated += count
            if not best_states or next_score <= current_score:
                break

            current = rng.choice(best_states)
            current_score = next_score
            steps += 1
            if current_score > best_score:
                best, best_score = current.copy(), current_score
            history.append(best_score)

        iterations_per_restart.append(steps)
        if best_score >= upper_bound or run_index == max_restarts:
            break
        current = initial_state(problem, seed=rng.randrange(2**63))
        restarts += 1
        history.append(best_score)

    return SearchResult(best, history, len(history) - 1, {
        "variant": "random_restart", "restart_count": restarts,
        "iterations_per_restart": iterations_per_restart,
        "max_restarts": max_restarts, "neighbors_evaluated": evaluated,
        "history_type": "best_so_far",
    })

def search(problem: Problem, initial: State, *, seed: int | None = None, objective: ObjectiveConfig = ObjectiveConfig(), variant: str = "steepest", max_iterations: int = 1000, max_sideways_moves: int = 100, max_restarts: int = 10, max_iterations_per_restart: int = 1000, **params) -> SearchResult:
    if params:
        raise ValueError(f"parameter hill climbing tidak dikenal: {', '.join(params)}")
    if variant not in ("steepest", "sideways", "random_restart", "stochastic"):
        raise ValueError("variant harus steepest, sideways, random_restart, atau stochastic")
    
    positive_int(max_iterations, "max_iterations")
    nonnegative_int(max_sideways_moves, "max_sideways_moves")
    nonnegative_int(max_restarts, "max_restarts")
    positive_int(max_iterations_per_restart, "max_iterations_per_restart")
    rng = random.Random(seed)

    if variant == "steepest": return steepest(problem, initial, objective, rng, max_iterations)
    if variant == "sideways": return sideways(problem, initial, objective, rng, max_iterations, max_sideways_moves)
    if variant == "stochastic": return stochastic(problem, initial, objective, rng, max_iterations)
    return random_restart(problem, initial, objective, rng, max_restarts, max_iterations_per_restart)

register("hill_climbing", search)
