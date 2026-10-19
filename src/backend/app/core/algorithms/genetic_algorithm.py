from random import Random
from ..models import Problem, SearchResult, State, Orientation, Position, oriented_dimensions
from ..objective import ObjectiveConfig, score
from ..results import initial_state, register
from ..neighbors import move, rotate, swap
from ..validation import is_valid

# tournament selection
# ambil beberapa individu acak, yang skornya paling tinggi jadi parent
def select_parent(population, scores, rng, tournament_size):
    population_size = len(population)
    tournament_size = min(tournament_size, population_size)
    participant_indexes = rng.sample(range(population_size), tournament_size)
    
    winner_index = participant_indexes[0]
    winner_score = scores[winner_index]
    for participant_index in participant_indexes:
        participant_score = scores[participant_index]
        if participant_score > winner_score:
            winner_index = participant_index
            winner_score = participant_score

    return population[winner_index]

# pindahin 1 paket ke posisi acak di truk acak
def random_move(problem, state, package, rng):
    truck = rng.choice(problem.trucks)
    
    current = state.placements[package.id]
    if current:
        orientation = current.orientation
    else:
        orientation = Orientation()
    
    size = oriented_dimensions(package, orientation)
    dims = truck.dimensions

    if size.w > dims.w or size.l > dims.l or size.h > dims.h:
        return None

    position = Position(
        rng.randrange(dims.w - size.w + 1),
        rng.randrange(dims.l - size.l + 1),
        rng.randrange(dims.h - size.h + 1),
    )

    return move(problem, state, package.id, truck.id, position)

# ubah state dengan 1 operasi acak, return state baru
def mutate(problem, state, rng, max_attempts=10):
    packages = problem.packages
    if not packages:
        return state.copy()

    for i in range(max_attempts):
        operation = rng.choice(("move", "rotate", "swap", "remove"))
        package = rng.choice(packages)

        if operation == "move":
            candidate = random_move(problem, state, package, rng)
        elif operation == "rotate":
            axis = rng.choice(("x", "y", "z"))
            candidate = rotate(problem, state, package.id, axis)
        elif operation == "swap":
            other = rng.choice(packages)
            candidate = swap(problem, state, package.id, other.id)
        else:
            candidate = move(problem, state, package.id, None)

        if candidate is not None:
            return candidate

    return state.copy()

# ambil z dari pilihan pertama dari sebuah paket
def first_option_z(candidate):
    package_id, options = candidate
    first_placement = options[0]
    return first_placement.position.z

# gabungin 2 parent jadi 1 child
def crossover(problem, parent_a, parent_b, rng):
    empty_placements = {}
    for package in problem.packages:
        empty_placements[package.id] = None
    child = State(empty_placements)

    # tiap paket pilih parent yang dipakai duluan (acak), parent satunya jadi cadangan
    candidates = []
    for package in problem.packages:
        if rng.random() < 0.5:
            sources = (parent_a, parent_b)
        else:
            sources = (parent_b, parent_a)
        
        options = []
        for source in sources:
            placement = source.placements[package.id]
            if placement is not None:
                options.append(placement)

        if options:
            candidates.append((package.id, options))

    # acak biar adil, lalu urutkan dari z kecil
    rng.shuffle(candidates)
    candidates.sort(key=first_option_z)

    for package_id, options in candidates:
        for placement in options:
            child.placements[package_id] = placement
            if is_valid(problem, child):
                break
            child.placements[package_id] = None

    return child

# fungsi scoring
def score_all_individuals(problem, population, objective):
    scores = []
    for individual in population:
        scores.append(score(problem, individual, objective))
    return scores

def search(problem: Problem, initial: State, *, seed: int | None = None, objective: ObjectiveConfig = ObjectiveConfig(), population_size: int = 50, 
           max_iterations: int = 100, tournament_size: int = 2, mutation_rate: float = 0.7, crossover_rate: float = 0.8, **params) -> SearchResult:
    if population_size < 1:
        raise ValueError("population_size harus minimal 1")
    if max_iterations < 0:
        raise ValueError("max_iterations tidak boleh negatif")
    if tournament_size < 1:
        raise ValueError("tournament_size harus minimal 1")
    if not 0 <= mutation_rate <= 1:
        raise ValueError("mutation_rate harus di antara 0 dan 1")
    if not 0 <= crossover_rate <= 1:
        raise ValueError("crossover_rate harus di antara 0 dan 1")
    
    rng = Random(seed)

    # populasi awal, seed acak
    population = [initial.copy()]
    for i in range(population_size - 1):
        individual_seed = rng.randrange(1, 2**31)
        population.append(initial_state(problem, individual_seed))

    scores = score_all_individuals(problem, population, objective)

    best_score = max(scores)
    best_index = scores.index(best_score)
    best_individual = population[best_index]

    best_score_history = [best_score]
    avg_score_history = [sum(scores) / len(scores)]

    crossover_count = 0
    crossover_success = 0
    mutation_count = 0
    mutation_success = 0

    for i in range(max_iterations):
        # elitisme: individu terbaik selalu lolos ke generasi berikutnya
        new_population = [best_individual.copy()]

        # sisanya diisi hasil seleksi
        while len(new_population) < population_size:
            parent_a = select_parent(population, scores, rng, tournament_size)

            if rng.random() < crossover_rate:
                parent_b = select_parent(population, scores, rng, tournament_size)
                crossover_count += 1
                child = crossover(problem, parent_a, parent_b, rng)
                if child != parent_a and child != parent_b:
                    crossover_success += 1
            else:
                child = parent_a.copy()

            if rng.random() < mutation_rate:
                mutation_count += 1
                mutated = mutate(problem, child, rng)
                if mutated != child:
                    mutation_success += 1
                child = mutated

            new_population.append(child)

        population = new_population
        scores = score_all_individuals(problem, population, objective)

        # karena ada elitisme, skor terbaik ga mungkin turun
        best_score = max(scores)
        best_index = scores.index(best_score)
        best_individual = population[best_index]

        best_score_history.append(best_score)
        avg_score_history.append(sum(scores) / len(scores))

    metrics = {"population_size": population_size, "max_iterations": max_iterations, "tournament_size": tournament_size, 
               "mutation_rate": mutation_rate, "mutation_count": mutation_count, "mutation_success": mutation_success,
               "crossover_rate": crossover_rate, "crossover_count": crossover_count, "crossover_success": crossover_success}
        
    return SearchResult(final_state=best_individual, score_history=best_score_history, iterations=max_iterations, metrics=metrics, average_history=avg_score_history)

register("genetic_algorithm", search)