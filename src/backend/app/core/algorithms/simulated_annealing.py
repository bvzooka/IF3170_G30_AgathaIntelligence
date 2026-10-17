import math
from random import Random
from ..models import Problem, SearchResult, State
from ..objective import ObjectiveConfig, score
from ..results import register
from ..neighbors import random_neighbor

def search(problem: Problem, initial: State, *, seed: int | None = None, objective: ObjectiveConfig = ObjectiveConfig(), **params) -> SearchResult:
    initial_temp = float(params.get("initial_temp", 1000.0, ))
    cooling_rate = float(params.get("cooling_rate", 0.995, ))
    min_temp = float(params.get("min_temp", 0.01, ))
    max_iteration = int(params.get("max_iteration", 1000, ))
    max_neighbor_attempts = int(params.get("max_neighbor_attempts", 100, ))
    stuck_threshold = int(params.get("stuck_threshold", 50, ))

    if initial_temp <= 0:
        raise ValueError("initial_temp harus lebih dari 0")
    if not 0 < cooling_rate < 1:
        raise ValueError("cooling_rate harus di antara 0 dan 1")
    if min_temp <= 0:
        raise ValueError("min_temp harus lebih dari 0")
    if max_iteration < 0:
        raise ValueError("max_iteration tidak boleh negatif")
    if max_neighbor_attempts <= 0:
        raise ValueError("max_neighbor_attempts harus lebih dari 0")
    if stuck_threshold <= 0:
        raise ValueError("stuck_threshold harus lebih dari 0")

    rng = Random(seed)
    current_state = initial.copy()
    current_score = score(problem, current_state, objective)
    best_state = current_state.copy()
    best_score = current_score
    temperature = initial_temp

    current_score_history = [current_score]
    best_score_history = [best_score]
    temperature_history = [temperature]

    accepted_better = 0
    accepted_equal = 0
    accepted_worse = 0
    rejected = 0
    neighbor_failed = 0
    iterations_no_improvement = 0
    stuck_freq= 0
    curr_stuck = False
    iterations = 0

    while(iterations < max_iteration and temperature > min_temp):
        # generate 1 random valid neighbor
        candidate_state = random_neighbor(problem, current_state, rng, max_attempt=max_neighbor_attempts)
        if candidate_state is None:
            neighbor_failed += 1
            iterations_no_improvement += 1
        else:
            candidate_score = score(problem, candidate_state, objective)
            delta = (candidate_score - current_score)
            accept = False
            if delta > 0:
                accept = True
                accepted_better += 1
            elif delta == 0:
                accept = True
                accepted_equal +=1
            else:
                acceptance_probability = (math.exp(delta / temperature))
                random_value = rng.random()
                if (random_value < acceptance_probability):
                    accept = True
                    accepted_worse += 1
                else:
                    rejected += 1

            # update current state
            if accept:
                current_state = (candidate_state)
                current_score = (candidate_score)

            if current_score > best_score:
                best_state = (current_state.copy())
                best_score = (current_score)
                iterations_no_improvement = 0
                curr_stuck = False

            else:
                iterations_no_improvement += 1

        if (iterations_no_improvement >= stuck_threshold and not curr_stuck):
            stuck_freq += 1
            curr_stuck = True

        temperature *= cooling_rate
        iterations += 1

        current_score_history.append(current_score)
        best_score_history.append(best_score)
        temperature_history.append(temperature)

    total_accepted = (accepted_better + accepted_equal + accepted_worse)
    acceptance_rate = (total_accepted / iterations if iterations > 0 else 0.0)
    metrics = {"initial_temperature": initial_temp, 
                "final_temperature": temperature,
                "cooling_rate": cooling_rate,
                "min_temperature": min_temp,
                "max_iterations": max_iteration,
                "max_neighbor_attempts": max_neighbor_attempts,
                "accepted_better": accepted_better,
                "accepted_equal": accepted_equal,
                "accepted_worse": accepted_worse,
                "rejected": rejected,
                "acceptance_rate": acceptance_rate,
                "neighbor_failed": neighbor_failed,
                "stuck_frequency": stuck_freq,
                "stuck_threshold": stuck_threshold,
                "current_score_history": current_score_history,
                "temperature_history": temperature_history,
            }
    return SearchResult(final_state=best_state, score_history=best_score_history, iterations=iterations, metrics=metrics)

register("simulated_annealing", search)
