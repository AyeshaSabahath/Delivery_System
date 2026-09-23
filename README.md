# FastBox Mystery Delivery System

A one-day delivery simulation for a fictional logistics company:
packages are assigned to the nearest agent, each agent's route is
simulated, and a performance report is produced.

## Requirements

Python 3.8+, standard library only (`json`, `math`, `csv`, `random`,
`argparse`, `os`). No third-party packages required.

## Usage

```bash
python delivery_system.py <input.json> [--outdir OUT] [--seed N] [--visualize]
```

- `--outdir` — where to write `report.json` / `top_performer.csv` / `route_map.txt` (default: current directory)
- `--seed` — an integer seed. If provided, simulates a random per-delivery delay (bonus feature) and adds `total_delay_minutes` to each agent's report entry. Omit for a deterministic, delay-free run.
- `--visualize` — prints and saves a simple ASCII scatter map of warehouses / agent start positions / package destinations (bonus feature)

Example:

```bash
python delivery_system.py sample_data.json --outdir out --seed 42 --visualize
```

`sample_data.json` is the exact example from the assignment PDF.

## Running the test suite

The zip that came with the assignment included 10 test cases plus a
`base_case.json`, using two *different* JSON shapes (see "Assumptions"
below). `tests/run_tests.py` runs the simulator against all of them and
checks the one invariant explicitly called out in the assignment:
**total packages delivered must equal total packages**.

```bash
cd delivery_system
python -m tests.run_tests
```

All 11 provided cases pass.

## Design overview

1. **`load_data` / `normalize_input`** — reads the JSON file with the
   standard `json` module and converts it into one internal shape:
   `warehouses: {id: (x, y)}`, `agents: {id: (x, y)}`,
   `packages: [{"id", "warehouse", "destination": (x, y)}]`.
2. **`assign_packages`** — assigns each package to the agent whose
   current location is closest (Euclidean distance) to the package's
   warehouse, exactly as specified in the brief.
3. **`simulate_agent_route`** — for each agent, greedily visits the
   nearest remaining assigned package's warehouse, picks it up,
   delivers it, and repeats from the new position. Returns total
   distance traveled and (optionally) simulated delay.
4. **`generate_report`** — builds the `packages_delivered` /
   `total_distance` / `efficiency` report per agent, verifies the
   delivered-packages invariant, and determines `best_agent`.
5. Bonus features: random delivery delays (`--seed`), ASCII route/layout
   visualization (`--visualize`), a new-agent-joining-mid-day code path
   (`assign_packages(..., new_agents=...)`), and CSV export of the top
   performer (`top_performer.csv`, always written).

## Assumptions made (per the brief's instruction to document rather than ask)

The email/brief that came with this assignment said: *"If you
encounter any ambiguous logic or undefined scenarios... assume the
best possible scenario and proceed... document these assumptions."*
Here's everything that was actually ambiguous or underspecified, and
the call I made on each:

1. **Two incompatible input schemas were provided.** The assignment
   PDF's own worked example, and all 10 files in
   `tests/test_cases/`, use `"warehouses": {"W1": [x, y]}` and
   packages with a `"warehouse"` key. But `base_case.json` (also in
   the zip) uses `"warehouses": [{"id": "W1", "location": [x, y]}]`
   and packages with `"warehouse_id"` instead. Rather than picking one
   and failing on the other, `normalize_input()` detects and accepts
   **both** shapes.
2. **Route order for an agent with multiple assigned packages is not
   specified.** The brief just says "picks up packages from warehouse
   and delivers to destination." I used a greedy nearest-next-pickup
   heuristic: from wherever the agent currently is, go to whichever
   remaining assigned package's warehouse is closest, deliver it, and
   repeat. This is a reasonable, cheap approximation of an efficient
   route without implementing a full TSP-style optimizer, which would
   be overkill here.
3. **`efficiency` is not defined in the brief.** From the worked
   example (`85.32` distance / `2` delivered = `42.66` efficiency,
   which matches exactly), efficiency is `total_distance /
   packages_delivered` — i.e. **lower is better**. `best_agent` is
   therefore the agent with the *lowest* efficiency among agents who
   delivered at least one package, which is also consistent with the
   worked example (A1 has the lowest efficiency and is the
   `best_agent`).
4. **Agents with zero deliveries** would otherwise cause a
   divide-by-zero on efficiency. They're reported with
   `efficiency: 0.0` and excluded from the `best_agent` calculation,
   so the report schema stays consistent across every agent.
5. **The worked example's specific numbers (`85.32`, `120.12`, etc.)
   don't reproduce from the actual sample coordinates**, no matter
   which reasonable routing rule you use (I checked). I treated that
   sample report purely as a **schema template** to match — not
   as ground truth to reproduce — since the assignment counts
   (2, 2, 1 packages delivered per agent) *do* reproduce exactly under
   the described nearest-agent rule, which was the part explicitly
   specified.
6. **"New agent joining mid-day" (bonus)** has no notion of "time" in
   the input data. I modeled package list order as chronological
   order, so a new agent (passed via `new_agents=[{"id", "location",
   "after_package"}]`) becomes available for assignment starting from
   the package after the one named in `after_package`.

## Files

```
delivery_system.py       # main script (parsing, assignment, simulation, report, bonuses)
sample_data.json         # the exact example input from the assignment PDF
tests/
  run_tests.py            # validates all provided test cases
  base_case.json          # provided sample (alternate schema)
  test_cases/*.json       # 10 provided test cases (dict schema)
```
