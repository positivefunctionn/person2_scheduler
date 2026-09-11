"""Two-seed real-data smoke test. Does not change the Person 1 handoff."""
import csv
import statistics
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.baseline import best_fit_decreasing
from src.data_adapter import horizons, load_and_validate
from src.demand_adapter import adapt, write_repair_log
from src.gwo import gwo
from src.hho import hho
from src.hybrid import hho_gwo
from src.models import VM

SMOKE_SEEDS = (11, 23)
SMOKE_POPULATION = 4
SMOKE_ITERATIONS = 3

def write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

def task_rows(tasks, assignment, vms, cfg, algorithm, horizon_id, trial, seed):
    """Replay a finished assignment solely to expose task-level proxy outcomes."""
    loads = [vm.current_cpu_load for vm in vms]
    rows = []
    for task, vm_index in zip(tasks, assignment):
        vm = vms[vm_index]
        loads[vm_index] += task.demand
        utilization = loads[vm_index] / vm.cpu_capacity
        execution_time = task.demand / vm.cpu_capacity
        violation = utilization > cfg["allowable_utilization"] or execution_time > cfg["execution_sla"]
        rows.append({
            "task_id": task.task_id, "horizon_id": horizon_id,
            "predicted_cpu": task.predicted_cpu, "p_overload": task.p_overload,
            "predicted_overload": task.predicted_overload, "selected_vm_id": vm.vm_id,
            "host_id": vm.host_id, "resulting_utilization": utilization,
            "sla_violation": int(violation), "task_execution_time": execution_time,
            "algorithm": algorithm, "trial": trial, "seed": seed,
        })
    return rows

def main():
    cfg = yaml.safe_load((ROOT / "config/config.yaml").read_text(encoding="utf-8"))
    cfg["trials"] = len(SMOKE_SEEDS)
    cfg["seeds"] = list(SMOKE_SEEDS)
    cfg["hho"] = {**cfg["hho"], "population_size": SMOKE_POPULATION, "iterations": SMOKE_ITERATIONS}
    cfg["gwo"] = {**cfg["gwo"], "population_size": SMOKE_POPULATION, "iterations": SMOKE_ITERATIONS}
    source = ROOT / "data" / "214_final_predictions.csv"
    rows, validation = load_and_validate(source)
    if not validation["valid"]:
        raise ValueError("Handoff validation failed: " + "; ".join(validation["errors"]))
    vms = [VM(**item) for item in cfg["vms"]]
    output = ROOT / "results" / "smoke_test"
    output.mkdir(parents=True, exist_ok=True)
    repairs, horizon_results, schedule_results = [], [], []
    convergence = {"GWO": [], "HHO": [], "HHO-GWO": []}
    methods = {
        "BFD": lambda tasks, seed: (*best_fit_decreasing(tasks, vms, cfg), []),
        "GWO": lambda tasks, seed: gwo(tasks, vms, cfg, seed)[:3],
        "HHO": lambda tasks, seed: hho(tasks, vms, cfg, seed)[:3],
        "HHO-GWO": lambda tasks, seed: hho_gwo(tasks, vms, cfg, seed)[:3],
    }
    for horizon_id, batch in enumerate(horizons(rows, cfg["horizon_length"])):
        repair_count_before = len(repairs)
        tasks = adapt(batch, horizon_id, vms[0].cpu_capacity, repairs)
        horizon_repair_count = len(repairs) - repair_count_before
        for algorithm, run in methods.items():
            for trial, seed in enumerate(SMOKE_SEEDS):
                started = time.perf_counter()
                assignment, metrics, history = run(tasks, seed)
                elapsed = time.perf_counter() - started
                if len(assignment) != len(tasks) or any(not 0 <= index < len(vms) for index in assignment):
                    raise RuntimeError(f"Invalid {algorithm} schedule in horizon {horizon_id}, seed {seed}")
                result = {"horizon_id": horizon_id, "algorithm": algorithm, "trial": trial, "seed": seed,
                          **metrics.__dict__, "sla_violation_rate": metrics.sla_violation_count / len(tasks),
                          "overload_rate": metrics.overload_count / len(vms), "runtime": elapsed,
                          "prediction_repair_count": horizon_repair_count}
                horizon_results.append(result)
                schedule_results.extend(task_rows(tasks, assignment, vms, cfg, algorithm, horizon_id, trial, seed))
                if algorithm in convergence:
                    convergence[algorithm].extend({"horizon_id": horizon_id, "trial": trial, "seed": seed,
                                                    "iteration": iteration + 1, "fitness": value}
                                                   for iteration, value in enumerate(history))
    metric_fields = list(horizon_results[0])
    write_csv(output / "horizon_results.csv", horizon_results, metric_fields)
    write_csv(output / "schedule_results.csv", schedule_results, list(schedule_results[0]))
    write_repair_log(output / "repair_log.csv", repairs)
    for algorithm, records in convergence.items():
        write_csv(output / f"convergence_{algorithm.lower().replace('-', '_')}.csv", records,
                  ["horizon_id", "trial", "seed", "iteration", "fitness"])
    trials = []
    comparison = []
    for algorithm in methods:
        for trial, seed in enumerate(SMOKE_SEEDS):
            group = [row for row in horizon_results if row["algorithm"] == algorithm and row["seed"] == seed]
            trials.append({"algorithm": algorithm, "trial": trial, "seed": seed,
                           **{name: statistics.fmean(row[name] for row in group)
                              for name in ("fitness", "energy", "makespan", "sla_violation_count", "load_imbalance", "average_utilization", "overload_count", "runtime")}})
        group = [row for row in trials if row["algorithm"] == algorithm]
        comparison.append({"algorithm": algorithm, "seed_count": len(group),
                           **{f"{name}_{stat}": getattr(statistics, stat)([row[name] for row in group])
                              for name in ("fitness", "energy", "makespan", "sla_violation_count", "load_imbalance", "average_utilization", "overload_count", "runtime")
                              for stat in ("fmean", "stdev") if not (stat == "stdev" and len(group) < 2)}})
    write_csv(output / "trial_results.csv", trials, list(trials[0]))
    write_csv(output / "algorithm_comparison.csv", comparison, list(comparison[0]))
    print(f"smoke test completed: {len(horizon_results)} schedules; output={output}")

if __name__ == "__main__":
    main()
