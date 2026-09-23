"""
FastBox Mystery Delivery System
================================

Simulates one day of delivery operations for a fictional logistics
company: assigns packages to the nearest agent, simulates each agent's
route, and produces a performance report.

Usage
-----
    python delivery_system.py data.json
    python delivery_system.py data.json --outdir out --seed 42 --visualize

See README.md for the full write-up of assumptions and design
decisions (the assignment explicitly asked for these to be documented
in comments / README rather than clarified up front).
"""

import argparse
import csv
import json
import math
import os
import random


# ---------------------------------------------------------------------------
# 1. JSON loading & parsing
# ---------------------------------------------------------------------------
#
# ASSUMPTION (documented per assignment instructions, since this was not
# specified and the sample files actually disagree with each other):
#
# The assignment PDF's own example, and every file under
# `tests/test_cases/`, use this shape:
#
#     "warehouses": {"W1": [x, y], ...}
#     "agents":     {"A1": [x, y], ...}
#     "packages":   [{"id": "P1", "warehouse": "W1", "destination": [x, y]}, ...]
#
# but `base_case.json` (also shipped in the assignment zip) uses a
# *different* shape:
#
#     "warehouses": [{"id": "W1", "location": [x, y]}, ...]
#     "agents":     [{"id": "A1", "location": [x, y]}, ...]
#     "packages":   [{"id": "P1", "warehouse_id": "W1", "destination": [x, y]}, ...]
#
# Rather than guessing which one is "correct" and failing on the other
# file, we treat this as exactly the kind of undefined/ambiguous
# scenario the brief told us to resolve ourselves: `normalize_input`
# below detects and accepts *both* shapes and converts them to one
# internal representation. This is the most robust choice and costs
# nothing at runtime.
def load_data(path):
    """Read a JSON file from disk and parse it with the standard
    library `json` module (no external schema/validation libraries),
    per the "read and parse the JSON file manually" requirement."""
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return normalize_input(raw)


def normalize_input(raw):
    """Convert either supported input shape into:
        warehouses: {id: (x, y)}
        agents:     {id: (x, y)}
        packages:   [{"id": str, "warehouse": str, "destination": (x, y)}]
    """
    warehouses = _normalize_points(raw["warehouses"], location_key="location")
    agents = _normalize_points(raw["agents"], location_key="location")

    packages = []
    for p in raw["packages"]:
        warehouse_id = p.get("warehouse", p.get("warehouse_id"))
        if warehouse_id is None:
            raise ValueError(f"Package {p.get('id')} has no warehouse reference")
        packages.append(
            {
                "id": p["id"],
                "warehouse": warehouse_id,
                "destination": tuple(p["destination"]),
            }
        )

    if not warehouses or not agents:
        raise ValueError("Input must define at least one warehouse and one agent")

    return warehouses, agents, packages


def _normalize_points(section, location_key="location"):
    """Accepts either {"W1": [x, y], ...} or [{"id": "W1", "location": [x, y]}, ...]."""
    result = {}
    if isinstance(section, dict):
        for key, value in section.items():
            result[key] = tuple(value)
    elif isinstance(section, list):
        for item in section:
            result[item["id"]] = tuple(item[location_key])
    else:
        raise ValueError(f"Unrecognized structure for section: {section!r}")
    return result


# ---------------------------------------------------------------------------
# 2. Distance calculation
# ---------------------------------------------------------------------------
def euclidean_distance(point_a, point_b):
    return math.sqrt((point_a[0] - point_b[0]) ** 2 + (point_a[1] - point_b[1]) ** 2)


# ---------------------------------------------------------------------------
# 3. Agent <-> package assignment
# ---------------------------------------------------------------------------
def assign_packages(agents, warehouses, packages, new_agents=None):
    """Assign each package to the nearest agent, measured as the
    Euclidean distance from the agent's current location to the
    package's warehouse (exactly as specified in the brief).

    ASSUMPTION: if `new_agents` is provided (bonus feature — an agent
    joining mid-day), packages are processed in the order they appear
    in the input list, and a new agent becomes eligible for assignment
    starting with the package identified by its `after_package` field.
    This models a single working day as a simple timeline where
    package order == chronological order, since the brief gives no
    explicit notion of time.
    """
    available_agents = dict(agents)
    pending_joins = list(new_agents or [])

    assignment = {agent_id: [] for agent_id in agents}
    for agent in pending_joins:
        assignment.setdefault(agent["id"], [])

    for package in packages:
        # Bring any agents whose trigger package has been reached online.
        still_pending = []
        for agent in pending_joins:
            if agent["after_package"] == package["id"]:
                available_agents[agent["id"]] = tuple(agent["location"])
            else:
                still_pending.append(agent)
        pending_joins = still_pending

        warehouse_pos = warehouses[package["warehouse"]]
        nearest_agent = min(
            available_agents,
            key=lambda a: euclidean_distance(available_agents[a], warehouse_pos),
        )
        assignment[nearest_agent].append(package)

    return assignment, available_agents


# ---------------------------------------------------------------------------
# 4. Route simulation
# ---------------------------------------------------------------------------
def simulate_agent_route(start_position, assigned_packages, warehouses, rng=None):
    """Simulate one agent's day: repeatedly travel to the nearest
    remaining package's warehouse, pick it up, and deliver it.

    ASSUMPTION: the brief says an agent "picks up packages from
    warehouse and delivers to destination" but does not specify the
    order in which multiple assigned packages should be handled. We
    use a greedy nearest-next-pickup heuristic (go to whichever
    remaining package's warehouse is closest to the agent's current
    position, deliver it, repeat) starting from the agent's initial
    location. This is a reasonable, efficient approximation without
    solving a full travelling-salesman-style optimization, which would
    be overkill for this simulation.

    If `rng` (a random.Random instance) is supplied, a small random
    delay (in simulated minutes) is generated per delivery — the
    "random delivery delays" bonus. Delay does not add to physical
    distance traveled, only to a separate `total_delay_minutes` figure.
    """
    position = start_position
    remaining = list(assigned_packages)
    total_distance = 0.0
    total_delay_minutes = 0.0
    route = [{"event": "start", "location": position}]

    while remaining:
        nearest_package = min(
            remaining,
            key=lambda p: euclidean_distance(position, warehouses[p["warehouse"]]),
        )
        warehouse_pos = warehouses[nearest_package["warehouse"]]

        total_distance += euclidean_distance(position, warehouse_pos)
        route.append(
            {"event": "pickup", "package": nearest_package["id"], "location": warehouse_pos}
        )

        destination = nearest_package["destination"]
        total_distance += euclidean_distance(warehouse_pos, destination)
        position = destination

        delay = 0.0
        if rng is not None:
            delay = round(rng.uniform(0, 15), 2)  # simulated traffic/handling delay
            total_delay_minutes += delay

        route.append(
            {
                "event": "deliver",
                "package": nearest_package["id"],
                "location": destination,
                "delay_minutes": delay,
            }
        )
        remaining.remove(nearest_package)

    return total_distance, total_delay_minutes, route


# ---------------------------------------------------------------------------
# 5. Report generation
# ---------------------------------------------------------------------------
def generate_report(agents, warehouses, packages, new_agents=None, seed=None):
    assignment, all_agents = assign_packages(agents, warehouses, packages, new_agents)
    rng = random.Random(seed) if seed is not None else None

    report = {}
    routes = {}
    total_delivered = 0

    for agent_id, agent_start in all_agents.items():
        assigned = assignment.get(agent_id, [])
        distance, delay_minutes, route = simulate_agent_route(
            agent_start, assigned, warehouses, rng=rng
        )
        delivered = len(assigned)
        total_delivered += delivered

        # Efficiency = distance per package delivered (lower is better).
        # An agent with zero deliveries has no meaningful efficiency;
        # we report 0.0 rather than dividing by zero or omitting the key,
        # so downstream consumers can rely on a consistent schema.
        efficiency = round(distance / delivered, 2) if delivered else 0.0

        entry = {
            "packages_delivered": delivered,
            "total_distance": round(distance, 2),
            "efficiency": efficiency,
        }
        if rng is not None:
            entry["total_delay_minutes"] = round(delay_minutes, 2)

        report[agent_id] = entry
        routes[agent_id] = route

    # Sanity check called out explicitly in the assignment notes.
    assert total_delivered == len(packages), (
        f"Mismatch: {total_delivered} delivered vs {len(packages)} total packages"
    )

    # Best agent = most efficient, i.e. lowest distance-per-package,
    # among agents who actually delivered at least one package.
    active_agents = {a: r for a, r in report.items() if r["packages_delivered"] > 0}
    best_agent = min(active_agents, key=lambda a: active_agents[a]["efficiency"]) if active_agents else None
    report["best_agent"] = best_agent

    return report, routes


# ---------------------------------------------------------------------------
# 6. Bonus: ASCII route visualization
# ---------------------------------------------------------------------------
def render_ascii_map(warehouses, agents, packages, width=60, height=25):
    """Render a compact ASCII scatter-plot of warehouses (W), agent
    start positions (A), and package destinations (.) on a scaled grid.
    Purely illustrative — not to scale in any rigorous sense, just a
    quick visual sanity check of the layout."""
    all_points = list(warehouses.values()) + list(agents.values())
    all_points += [p["destination"] for p in packages]
    xs = [p[0] for p in all_points]
    ys = [p[1] for p in all_points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span_x = max_x - min_x or 1
    span_y = max_y - min_y or 1

    grid = [[" "] * width for _ in range(height)]

    def plot(point, symbol):
        col = int((point[0] - min_x) / span_x * (width - 1))
        row = int((point[1] - min_y) / span_y * (height - 1))
        row = height - 1 - row  # flip so higher y is up
        grid[row][col] = symbol

    for pkg in packages:
        plot(pkg["destination"], ".")
    for pos in warehouses.values():
        plot(pos, "W")
    for pos in agents.values():
        plot(pos, "A")

    lines = ["".join(row) for row in grid]
    lines.append("Legend: W = warehouse, A = agent start, . = package destination")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 7. Bonus: export top performer to CSV
# ---------------------------------------------------------------------------
def export_top_performer_csv(report, path):
    best_agent = report.get("best_agent")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["agent_id", "packages_delivered", "total_distance", "efficiency"])
        if best_agent:
            row = report[best_agent]
            writer.writerow(
                [best_agent, row["packages_delivered"], row["total_distance"], row["efficiency"]]
            )


# ---------------------------------------------------------------------------
# 8. CLI entry point
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="FastBox Mystery Delivery System simulator")
    parser.add_argument("input", help="Path to the input JSON file")
    parser.add_argument("--outdir", default=".", help="Directory to write outputs into")
    parser.add_argument("--seed", type=int, default=None, help="Random seed to enable delivery-delay simulation")
    parser.add_argument("--visualize", action="store_true", help="Print/save an ASCII map of the layout")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    warehouses, agents, packages = load_data(args.input)
    report, routes = generate_report(agents, warehouses, packages, seed=args.seed)

    report_path = os.path.join(args.outdir, "report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Report written to {report_path}")
    print(json.dumps(report, indent=2))

    csv_path = os.path.join(args.outdir, "top_performer.csv")
    export_top_performer_csv(report, csv_path)
    print(f"Top performer exported to {csv_path}")

    if args.visualize:
        ascii_map = render_ascii_map(warehouses, agents, packages)
        map_path = os.path.join(args.outdir, "route_map.txt")
        with open(map_path, "w", encoding="utf-8") as f:
            f.write(ascii_map)
        print(f"\nASCII map (also saved to {map_path}):\n")
        print(ascii_map)


if __name__ == "__main__":
    main()
