"""Full configured experiment runner; it is not invoked by the smoke test."""
import csv, statistics, sys, time
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from src.baseline import best_fit_decreasing
from src.data_adapter import horizons,load_and_validate
from src.demand_adapter import adapt,write_repair_log
from src.gwo import gwo
from src.hho import hho
from src.hybrid import hho_gwo
from src.models import VM

def write_csv(path,rows,fields):
    with open(path,"w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=fields); writer.writeheader(); writer.writerows(rows)

def task_rows(tasks,assignment,vms,cfg,algorithm,horizon_id,trial,seed):
    loads=[vm.current_cpu_load for vm in vms]; output=[]
    for task,index in zip(tasks,assignment):
        vm=vms[index]; loads[index]+=task.demand; utilization=loads[index]/vm.cpu_capacity; execution=task.demand/vm.cpu_capacity
        output.append({"task_id":task.task_id,"horizon_id":horizon_id,"predicted_cpu":task.predicted_cpu,"p_overload":task.p_overload,"predicted_overload":task.predicted_overload,"selected_vm_id":vm.vm_id,"host_id":vm.host_id,"resulting_utilization":utilization,"sla_violation":int(utilization>cfg["allowable_utilization"] or execution>cfg["execution_sla"]),"task_execution_time":execution,"algorithm":algorithm,"trial":trial,"seed":seed})
    return output

def main():
    cfg=yaml.safe_load((ROOT/"config/config.yaml").read_text(encoding="utf-8")); seeds=cfg["seeds"][:cfg["trials"]]
    if len(seeds)!=cfg["trials"]: raise ValueError("configuration has fewer seeds than trials")
    rows,report=load_and_validate(ROOT/"data/214_final_predictions.csv")
    if not report["valid"]: raise ValueError("Handoff validation failed: "+"; ".join(report["errors"]))
    vms=[VM(**item) for item in cfg["vms"]]; out=ROOT/"results"; out.mkdir(exist_ok=True)
    repairs=[]; horizon_results=[]; schedules=[]; convergence={"GWO":[],"HHO":[],"HHO-GWO":[]}
    methods={"BFD":lambda tasks,seed:(*best_fit_decreasing(tasks,vms,cfg),[]),"GWO":lambda tasks,seed:gwo(tasks,vms,cfg,seed)[:3],"HHO":lambda tasks,seed:hho(tasks,vms,cfg,seed)[:3],"HHO-GWO":lambda tasks,seed:hho_gwo(tasks,vms,cfg,seed)[:3]}
    for hid,batch in enumerate(horizons(rows,cfg["horizon_length"])):
        before=len(repairs); tasks=adapt(batch,hid,vms[0].cpu_capacity,repairs)
        for algorithm,run in methods.items():
            for trial,seed in enumerate(seeds):
                started=time.perf_counter(); assignment,metric,history=run(tasks,seed); runtime=time.perf_counter()-started
                if len(assignment)!=len(tasks) or any(not 0<=i<len(vms) for i in assignment): raise RuntimeError(f"Invalid {algorithm} schedule in horizon {hid}, seed {seed}")
                horizon_results.append({"horizon_id":hid,"algorithm":algorithm,"trial":trial,"seed":seed,**metric.__dict__,"sla_violation_rate":metric.sla_violation_count/len(tasks),"overload_rate":metric.overload_count/len(vms),"runtime":runtime,"prediction_repair_count":len(repairs)-before})
                schedules.extend(task_rows(tasks,assignment,vms,cfg,algorithm,hid,trial,seed))
                if algorithm in convergence: convergence[algorithm].extend({"horizon_id":hid,"trial":trial,"seed":seed,"iteration":i+1,"fitness":value} for i,value in enumerate(history))
    write_csv(out/"horizon_results.csv",horizon_results,list(horizon_results[0])); write_csv(out/"schedule_results.csv",schedules,list(schedules[0])); write_repair_log(out/"repair_log.csv",repairs)
    for algorithm,records in convergence.items(): write_csv(out/f"convergence_{algorithm.lower().replace('-', '_')}.csv",records,["horizon_id","trial","seed","iteration","fitness"])
    fields=("fitness","energy","makespan","sla_violation_count","load_imbalance","average_utilization","overload_count","runtime"); trials=[]
    for algorithm in methods:
        for trial,seed in enumerate(seeds):
            group=[x for x in horizon_results if x["algorithm"]==algorithm and x["seed"]==seed]
            trials.append({"algorithm":algorithm,"trial":trial,"seed":seed,**{name:statistics.fmean(x[name] for x in group) for name in fields}})
    comparison=[]
    for algorithm in methods:
        group=[x for x in trials if x["algorithm"]==algorithm]; record={"algorithm":algorithm,"seed_count":len(group)}
        for name in fields: record[f"{name}_fmean"]=statistics.fmean(x[name] for x in group); record[f"{name}_stdev"]=statistics.stdev(x[name] for x in group) if len(group)>1 else 0.0
        comparison.append(record)
    write_csv(out/"trial_results.csv",trials,list(trials[0])); write_csv(out/"algorithm_comparison.csv",comparison,list(comparison[0]))
    print(f"completed {len(horizon_results)} schedules using {len(seeds)} seeds")
if __name__=="__main__": main()
