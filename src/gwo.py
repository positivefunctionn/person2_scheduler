"""Grey Wolf Optimizer with continuous positions and repaired discrete schedules."""
import random
from .fitness import evaluate, repair

def _fitness(x,tasks,vms,cfg): return evaluate(tasks,repair(x,len(vms)),vms,cfg).fitness
def gwo(tasks,vms,cfg,seed,initial_population=None):
    random.seed(seed); n=cfg["gwo"]["population_size"]; iters=cfg["gwo"]["iterations"]; d=len(tasks); m=len(vms)
    pop=[list(x) for x in (initial_population or [])][:n]
    while len(pop)<n: pop.append([random.uniform(0,m-1) for _ in range(d)])
    best=min(pop,key=lambda x:_fitness(x,tasks,vms,cfg)); best_score=_fitness(best,tasks,vms,cfg)
    history=[]
    for t in range(iters):
        ranked=sorted(pop,key=lambda x:_fitness(x,tasks,vms,cfg)); leaders=(ranked+[ranked[-1]]*3)[:3]; alpha,beta,delta=leaders
        a=2-2*t/max(1,iters-1); new=[]
        for wolf in pop:
            pos=[]
            for j,x in enumerate(wolf):
                vals=[]
                for leader in (alpha,beta,delta):
                    A=2*a*random.random()-a; C=2*random.random(); vals.append(leader[j]-A*abs(C*leader[j]-x))
                pos.append(sum(vals)/3)
            new.append([min(m-1,max(0,z)) for z in pos])
        pop=new
        iteration_best=min(pop,key=lambda x:_fitness(x,tasks,vms,cfg)); iteration_score=_fitness(iteration_best,tasks,vms,cfg)
        if iteration_score < best_score: best,best_score=list(iteration_best),iteration_score
        history.append(best_score)
    return repair(best,m), evaluate(tasks,repair(best,m),vms,cfg), history, pop
