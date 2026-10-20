from collections.abc import Iterator
from .models import Orientation, Placement, Position, Problem, State
from .validation import is_valid
from random import Random

# bisa : 
# - pindahin 1 package ke suatu koordinat di truk
# - pindah ke truk lain
# - atau keluarin package
def move(problem: Problem, state: State, package_id: str, truck_id: str | None, position: Position | None = None) -> State | None:
    if package_id not in state.placements: 
        raise ValueError("unknown package")
    if (truck_id is None) != (position is None): 
        raise ValueError("truck_id dan position harus id set atau None")
    
    current = state.placements[package_id]
    next_state = state.copy()
    next_state.placements[package_id] = None if truck_id is None else Placement(truck_id, position, current.orientation if current else Orientation())

    return next_state if next_state != state and is_valid(problem, next_state) else None

# tukar posisi dari 2 nama package
# bisa 2 2 nya inside sebuah truck, bisa 1 di luar
def swap(problem: Problem, state: State, first: str, second: str) -> State | None:
    if first not in state.placements or second not in state.placements: 
        raise ValueError("unknown package")
    if first == second: 
        return None

    result = state.copy()
    result.placements[first], result.placements[second] = state.placements[second], state.placements[first]

    return result if result != state and is_valid(problem, result) else None

# putar 1 package 90 derajat around sumbu x, y, z
def rotate(problem: Problem, state: State, package_id: str, axis: str) -> State | None:
    if axis not in ("x", "y", "z"): 
        raise ValueError("axis harus x, y, or z")
    if package_id not in state.placements: 
        raise ValueError("unknown package")
    current = state.placements[package_id]

    if current is None: 
        return None
   
    old = current.orientation
    turns = {"x": (old.w, old.h, old.l), "y": (old.h, old.l, old.w), "z": (old.l, old.w, old.h)}
    result = state.copy()
    result.placements[package_id] = Placement(current.truck_id, current.position, Orientation(*turns[axis]))

    return result if result != state and is_valid(problem, result) else None

# generate possible next state 
# misal tukar 2 package, pindahin package, dll
def neighbors(problem: Problem, state: State) -> Iterator[State]:
    ids = list(state.placements)
    
    for i, first in enumerate(ids):
        for second in ids[i + 1:]:
            candidate = swap(problem, state, first, second)
            if candidate is not None: yield candidate
        for axis in ("x", "y", "z"):
            candidate = rotate(problem, state, first, axis)
            if candidate is not None: yield candidate

        candidate = move(problem, state, first, None)
        if candidate is not None: yield candidate

        for truck in problem.trucks:
            for z in range(truck.dimensions.h):
                for y in range(truck.dimensions.l):
                    for x in range(truck.dimensions.w):
                        candidate = move(problem, state, first, truck.id, Position(x, y, z))
                        if candidate is not None: yield candidate


def random_neighbor(problem: Problem, state: State, rng: Random, max_attempt: int = 100) -> State | None:
    if max_attempt <= 0:
        raise ValueError("max_attempt harus lebih dari 0")

    package_ids = list(state.placements.keys())
    if not package_ids:
        return None
    if not problem.trucks:
        return None

    for _ in range(max_attempt):
        operation = rng.choice(("swap", "move", "rotate"))
        if operation == "swap":
            if len(package_ids) < 2:
                continue
            first, second = rng.sample(package_ids, 2)
            candidate = swap(problem, state, first, second)
            if candidate is not None: 
                return candidate

        elif operation == "rotate":
            package_id = rng.choice(package_ids)
            if state.placements[package_id] is None:
                continue
            axis = rng.choice(("x", "y", "z"))
            candidate = rotate(problem, state, package_id, axis)
            if candidate is not None:
                return candidate

        else:
            package_id = rng.choice(package_ids)
            current = state.placements[package_id]
            if(current is None and rng.random() < 0.20):
                candidate = move(problem, state, package_id, None)
                if candidate is not None:
                    return candidate
                continue
            truck = rng.choice(problem.trucks)
            position = Position(x=rng.randrange(truck.dimensions.w), y=rng.randrange(truck.dimensions.l), z=rng.randrange(truck.dimensions.h))
            candidate = move(problem, state, package_id, truck.id, position)
            if candidate is not None:
                return candidate

    return None
