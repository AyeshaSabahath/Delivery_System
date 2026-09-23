"""
Runs the simulator against every provided test case (both input
schemas) and checks the one hard invariant the assignment calls out:
"Make sure total packages delivered matches total packages."

Usage (from the delivery_system/ directory):
    python -m tests.run_tests
"""

import glob
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from delivery_system import load_data, generate_report  # noqa: E402


def run_case(path):
    warehouses, agents, packages = load_data(path)
    report, _ = generate_report(agents, warehouses, packages)
    delivered = sum(v["packages_delivered"] for k, v in report.items() if k != "best_agent")
    ok = delivered == len(packages)
    return ok, delivered, len(packages), report


def main():
    here = os.path.dirname(__file__)
    paths = [os.path.join(here, "base_case.json")]
    paths += sorted(glob.glob(os.path.join(here, "test_cases", "*.json")))

    all_passed = True
    for path in paths:
        ok, delivered, total, report = run_case(path)
        status = "PASS" if ok else "FAIL"
        if not ok:
            all_passed = False
        print(f"[{status}] {os.path.basename(path):20s} delivered={delivered}/{total}  best_agent={report.get('best_agent')}")

    print()
    print("ALL TESTS PASSED" if all_passed else "SOME TESTS FAILED")
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
