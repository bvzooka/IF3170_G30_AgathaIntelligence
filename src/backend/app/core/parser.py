import json
from pathlib import Path
from .models import Dimensions, Orientation, Package, Placement, Position, Problem, State, Truck

# convert package, trucks into objects 
# return Problem 
def parse_problem(data: dict) -> Problem:
    try:
        if ("truck" in data) == ("trucks" in data): 
            raise ValueError("provide exactly one of truck or trucks")
        
        raw_trucks = [data["truck"]] if "truck" in data else data["trucks"]
        trucks = tuple(Truck(item.get("id", "truck-1") if len(raw_trucks) == 1 else item["id"], Dimensions(**item["dimensions"]), item["max_capacity"]) for item in raw_trucks)
        packages = tuple(Package(item["id"], Dimensions(**item["dimensions"]), item["value"], item["weight"], item["is_fragile"], item["eta"]) for item in data["packages"])
        
        return Problem(trucks, packages)
    except (KeyError, TypeError) as exc: raise ValueError(f"invalid problem JSON: {exc}") from exc

# read the JSON and call parse_problem so it could be converted into objects
def read_problem(path: str | Path) -> Problem: 
    return parse_problem(json.loads(Path(path).read_text(encoding="utf-8")))

# parsing the State
def parse_state(data: dict, problem: Problem) -> State:
    try:
        raw = data["placements"]
        if set(raw) != {package.id for package in problem.packages}: raise ValueError("state must map every package once")
        return State({pid: None if item is None else Placement(item["truck_id"], Position(**item["position"]), Orientation(**item["orientation"])) for pid, item in raw.items()})
    except (KeyError, TypeError) as exc: raise ValueError(f"invalid state JSON: {exc}") from exc
