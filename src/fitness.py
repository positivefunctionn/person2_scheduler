"""Common normalized four-term objective. Risk penalty is included in SLA term."""
import math
from .models import ScheduleMetrics
from .overload import risk_cost

def decode(position, vm_count): return min(vm_count-1, max(0, int(round(position))))
def repair(position, vm_count): return [decode(x, vm_count) for x in position]

def evaluate(tasks, assignment, vms, cfg):
    if len(tasks)!=len(assignment): raise ValueError("assignment length differs from task count")
    loads=[v.current_cpu_load for v in vms]; completion=[0.0]*len(vms); violations=0; risk=0.0
    for task, idx in zip(tasks, repair(assignment,len(vms))):
        vm=vms[idx]; loads[idx]+=task.demand; util=loads[idx]/vm.cpu_capacity
        completion[idx]+=task.demand/vm.cpu_capacity
        bad=util>cfg["allowable_utilization"] or task.demand/vm.cpu_capacity>cfg["execution_sla"]
        violations += int(bad)
        risk += risk_cost(task,util,cfg["safe_utilization"],cfg["risk_penalty"])
    utils=[load/v.cpu_capacity for load,v in zip(loads,vms)]
    energy=sum((v.idle_power+(v.max_power-v.idle_power)*u)*cfg["scheduling_interval"] for v,u in zip(vms,utils))
    makespan=max(completion,default=0.0); imbalance=math.sqrt(sum((u-sum(utils)/len(utils))**2 for u in utils)/len(utils)) if utils else 0
    sla=(violations/len(tasks) if tasks else 0.0)+risk
    refs=cfg["normalization_references"]; w=cfg["weights"]
    score=w["energy"]*energy/refs["energy"]+w["makespan"]*makespan/refs["makespan"]+w["sla"]*sla/refs["sla"]+w["imbalance"]*imbalance/refs["imbalance"]
    return ScheduleMetrics(score,energy,makespan,violations,imbalance,sum(utils)/len(utils),sum(u>cfg["allowable_utilization"] for u in utils))
