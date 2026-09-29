from dataclasses import dataclass, field
from typing import Any

# widht, lenght, dan height 
@dataclass(frozen=True)
class Dimensions:
    w: int
    l: int
    h: int
    # validasi
    def __post_init__(self):
        if any(type(v) is not int or v <= 0 for v in (self.w, self.l, self.h)): raise ValueError("nilai dimensi harus positif")

@dataclass(frozen=True)
class Package:
    id: str
    dimensions: Dimensions
    value: float
    weight: float
    is_fragile: bool
    eta: int
    # validasi
    def __post_init__(self):
        if type(self.id) is not str or not self.id: raise ValueError("id package tidak boleh kosong")
        if type(self.value) not in (int, float) or not 0 <= self.value < float("inf"): raise ValueError("value harus positif dan finite")
        if type(self.weight) not in (int, float) or not 0 <= self.weight < float("inf"): raise ValueError("weight harus positif dan finite")
        if type(self.is_fragile) is not bool: raise ValueError("is_fragile harus boolean")
        if type(self.eta) is not int or self.eta < 0: raise ValueError("eta tidak boleh negatif")

@dataclass(frozen=True)
class Truck:
    id: str
    dimensions: Dimensions
    max_capacity: float
    # validasi
    def __post_init__(self):
        if type(self.id) is not str or not self.id: raise ValueError("id truck tidak boleh kosong")
        if type(self.max_capacity) not in (int, float) or not 0 <= self.max_capacity < float("inf"): raise ValueError("max_capacity harus positif dan finite")

# group dari trucks dan packages (1 problem)
@dataclass(frozen=True)
class Problem:
    trucks: tuple[Truck, ...]
    packages: tuple[Package, ...]
    # validasi
    def __post_init__(self):
        if not self.trucks: raise ValueError("minimal 1 truck")
        if len({t.id for t in self.trucks}) != len(self.trucks): raise ValueError("id truck harus unik")
        if len({p.id for p in self.packages}) != len(self.packages): raise ValueError("id package harus unik")

# koordinat paket
@dataclass(frozen=True)
class Position:
    x: int
    y: int
    z: int
    # validasi
    def __post_init__(self):
        if any(type(v) is not int for v in (self.x, self.y, self.z)): raise ValueError("koordinat harus integer")

# record original package axis points dari each dimensi truck
@dataclass(frozen=True)
class Orientation:
    w: str = "x"
    l: str = "y"
    h: str = "z"
    # validasi
    def __post_init__(self):
        if set((self.w, self.l, self.h)) != {"x", "y", "z"}: raise ValueError("orientasi hanya x, y, z")

# simpan dari 1 paket : which truck (id), posisi dan orientasi
@dataclass(frozen=True)
class Placement:
    truck_id: str
    position: Position
    orientation: Orientation = field(default_factory=Orientation)

# solusi placement package di truck
@dataclass
class State:
    placements: dict[str, Placement | None]

    def copy(self) -> "State": return State(self.placements.copy())

# result untuk ditampilin
@dataclass
class SearchResult:
    final_state: State
    score_history: list[float]
    iterations: int
    metrics: dict[str, Any] = field(default_factory=dict)
    average_history: list[float] | None = None


def oriented_dimensions(package: Package, orientation: Orientation) -> Dimensions:
    axes = {"x": package.dimensions.w, "y": package.dimensions.l, "z": package.dimensions.h}
    return Dimensions(axes[orientation.w], axes[orientation.l], axes[orientation.h])
