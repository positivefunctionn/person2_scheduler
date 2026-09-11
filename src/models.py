from dataclasses import dataclass

@dataclass(frozen=True)
class Task:
    task_id: int; horizon_id: int; predicted_cpu: float; p_overload: float; predicted_overload: int; demand: float

@dataclass(frozen=True)
class VM:
    vm_id: str; host_id: str; cpu_capacity: float; current_cpu_load: float; idle_power: float; max_power: float

@dataclass
class ScheduleMetrics:
    fitness: float; energy: float; makespan: float; sla_violation_count: int; load_imbalance: float; average_utilization: float; overload_count: int
