"""Genuine sequential HHO -> GWO: GWO receives HHO-ranked elites plus perturbations."""
import random
from .hho import hho
from .gwo import gwo
def hho_gwo(tasks,vms,cfg,seed):
    _,_,hho_history,ranked=hho(tasks,vms,cfg,seed)
    elite=ranked[:min(cfg["hho"]["elite_size"],len(ranked))]; random.seed(seed+100000); m=len(vms)
    seeds=[list(x) for x in elite]
    while len(seeds)<cfg["gwo"]["population_size"]:
        parent=elite[len(seeds)%len(elite)]; seeds.append([min(m-1,max(0,x+random.uniform(-.5,.5))) for x in parent])
    result=gwo(tasks,vms,cfg,seed+1,seeds)
    return result[0],result[1],hho_history+result[2], {"hho_elite_count":len(elite),"gwo_seeded_population":len(seeds)}
