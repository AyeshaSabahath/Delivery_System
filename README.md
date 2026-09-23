# FastBox Mystery Delivery System

## Overview

A one-day delivery simulation for a fictional logistics company:
packages are assigned to the nearest agent, each agent's route is
simulated, and a performance report is produced.


## Key Features

* **Nearest-Agent Assignment** – Assigns each package to the delivery agent closest to its warehouse.
* **Route Simulation** – Simulates each agent's delivery route using a nearest-next-pickup strategy.
* **Distance Calculation** – Calculates total travel distance for each delivery agent.
* **Performance Metrics** – Generates delivery count, total distance, and efficiency metrics.
* **Multiple Input Schemas** – Supports and normalizes two different JSON input formats.
* **Delivery Delay Simulation** – Optional deterministic/random delivery delays using a configurable seed.
* **Route Visualization** – Provides a simple ASCII representation of warehouses, agents, and package destinations.
* **CSV Export** – Generates a CSV report containing the top-performing agent.
* **Mid-Day Agent Support** – Supports adding new agents during the simulation.
* **Automated Testing** – Includes test cases covering the required delivery invariant and multiple input scenarios.


## Tech Stack

* **Language:** Python 3.8+
* **Standard Library:** `json`, `math`, `csv`, `random`, `argparse`, `os`
* **Testing:** Python test runner / custom test suite
* **Input/Output:** JSON and CSV
* **Visualization:** ASCII-based route visualization

## Files

```
delivery_system.py       # main script (parsing, assignment, simulation, report, bonuses)
sample_data.json         # the exact example input from the assignment PDF
tests/
  run_tests.py            # validates all provided test cases
  base_case.json          # provided sample (alternate schema)
  test_cases/*.json       # 10 provided test cases (dict schema)
```


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


## Output

```
Depending on the command-line options, the system can generate:

| Output              | Description                                                 |
| ------------------- | ----------------------------------------------------------- |
| `report.json`       | Delivery statistics for each agent                          |
| `top_performer.csv` | CSV summary of the top-performing agent                     |
| `route_map.txt`     | ASCII visualization of warehouses, agents, and destinations |

Example report metrics include:

* `packages_delivered`
* `total_distance`
* `efficiency`
* `total_delay_minutes` when delay simulation is enabled
```


## Author
Ayesha Sabahath