import json
from dataclasses import asdict
from pathlib import Path
from .models import Problem, State
from .validation import validate_state

# object -> dictionary yang bisa di tulis JSON
def state_dict(state: State) -> dict:
    placements = {}
    for package_id, placement in state.placements.items():
        placements[package_id] = (
            asdict(placement) if placement is not None else None
        )
    return {"placements": placements}

# buat pemetaan paket di truk
def occupancy_dict(problem: Problem, state: State) -> dict:
    grids = validate_state(problem, state)["grids"]
    occupancy = {}

    for truck in problem.trucks:
        grid = grids[truck.id]
        layers = {}
        for z in range(truck.dimensions.h):
            rows = []
            for y in range(truck.dimensions.l):
                row = [
                    grid.get((x, y, z))
                    for x in range(truck.dimensions.w)
                ]
                rows.append(row)
            layers[str(z)] = rows
        occupancy[truck.id] = layers
    return occupancy

# menyimpan sebagai JSON
def write_json(path: str | Path, data: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    content = json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False,)
    path.write_text(content + "\n", encoding="utf-8")