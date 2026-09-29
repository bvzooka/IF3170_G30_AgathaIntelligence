from .models import Problem, State, oriented_dimensions

# cek boundaries, overlap, kapasitas truck, fragile packages
# dipakai saat generate kandidat, akan di validasi dulu baru masuk ke search algorithm
# kalau invalid -> not yield
def validate_state(problem: Problem, state: State) -> dict:
    packages = {package.id: package for package in problem.packages}
    trucks = {truck.id: truck for truck in problem.trucks}

    if set(state.placements) != set(packages):
        raise ValueError("state must map every package once")

    grids = {truck_id: {} for truck_id in trucks}
    weights = {truck_id: 0.0 for truck_id in trucks}
    loaded = {truck_id: [] for truck_id in trucks}

    # cek setiap package di candidate state
    for package_id, placement in state.placements.items():
        if placement is None:
            continue
        if placement.truck_id not in trucks:
            raise ValueError(f"unknown truck: {placement.truck_id}")

        truck = trucks[placement.truck_id]
        package = packages[package_id]

        # hitung ukuran setelah rotasi dan posisi lagi mulai dari package starts
        size = oriented_dimensions(package, placement.orientation)
        position = placement.position

        # cek tidak ada koordinat negatif dan fit fi truck
        outside_bounds = (
            min(position.x, position.y, position.z) < 0
            or position.x + size.w > truck.dimensions.w
            or position.y + size.l > truck.dimensions.l
            or position.z + size.h > truck.dimensions.h
        )
        if outside_bounds:
            raise ValueError(f"package {package_id} keluar batas truck")

        weights[truck.id] += package.weight
        loaded[truck.id].append(package_id)
        grid = grids[truck.id]

        for x in range(position.x, position.x + size.w):
            for y in range(position.y, position.y + size.l):
                for z in range(position.z, position.z + size.h):
                    cell = (x, y, z)
                    if cell in grid:
                        raise ValueError(
                            f"packages {package_id} dan {grid[cell]} overlap di {truck.id}"
                        )
                    grid[cell] = package_id

    # setelah semua paket di tempatkan -> check weights and all support
    for truck_id, truck in trucks.items():
        if weights[truck_id] > truck.max_capacity:
            raise ValueError(f"truck {truck_id} melebihi kapasitas")
        
        # cek paket 1 per 1
        for package_id in loaded[truck_id]:
            placement = state.placements[package_id]
            position = placement.position
            if position.z == 0:
                continue

            size = oriented_dimensions(packages[package_id], placement.orientation)
            grid = grids[truck_id]
            supporters = {
                grid.get((x, y, position.z - 1))
                for x in range(position.x, position.x + size.w)
                for y in range(position.y, position.y + size.l)
            } - {None, package_id}

            if not supporters:
                raise ValueError(f"package {package_id} mengambang")
            if any(packages[supporter_id].is_fragile for supporter_id in supporters):
                raise ValueError(f"paket fragile di bawah paket {package_id}")

    return {
        "grids": grids,
        "loaded": loaded,
        "outside": [pid for pid, placement in state.placements.items() if placement is None],
        "weights": weights,
    }


def is_valid(problem: Problem, state: State) -> bool:
    try:
        validate_state(problem, state)
        return True
    except ValueError:
        return False
