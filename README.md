# Person 2: BiLSTM-triggered HHO → GWO scheduler

This standalone Python research prototype turns Person 1's *predicted* VM-214 CPU observations into synthetic scheduling workloads, grouped into configurable sequential horizons. A row is **not** claimed to be a real independent Bitbrain task. The core has no CloudSim/Java dependency.

```
Person 1 CSV -> validation -> demand adapter -> horizons -> BFD | GWO | HHO | HHO→GWO
                                                             -> task-to-VM mapping -> Person 3 CloudSim Plus
```

Copy the unmodified `214_final_predictions.csv` to `data/214_final_predictions.csv`, then run `python -m unittest discover tests`, `python experiments/toy_benchmarks.py`, and `python experiments/run_experiments.py`. Requires Python 3.10+, `pip install -r requirements.txt`.

The proxy uses `demand = predicted_cpu / 100 × reference_cpu_capacity`; negative values are logged and repaired to zero while values above 100 are retained. Energy, SLA, makespan, and utilization are experimental proxies only. CloudSim Plus is authoritative for final simulation measurements.

See `docs/` for methodology, algorithm choices, CloudSim mapping, limitations, and viva material.
