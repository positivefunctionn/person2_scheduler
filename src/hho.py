"""Harris Hawks Optimizer. Standard exploration/besiege/rapid-dive transitions."""
import random, math
from .fitness import evaluate, repair
def _fit(x,tasks,vms,cfg): return evaluate(tasks,repair(x,len(vms)),vms,cfg).fitness
def hho(tasks,vms,cfg,seed):
    random.seed(seed); n=cfg["hho"]["population_size"]; iters=cfg["hho"]["iterations"]; d=len(tasks); m=len(vms)
    pop=[[random.uniform(0,m-1) for _ in range(d)] for _ in range(n)]
    best=min(pop,key=lambda x:_fit(x,tasks,vms,cfg)); best_score=_fit(best,tasks,vms,cfg); history=[]
    for t in range(iters):
        prey=min(pop,key=lambda x:_fit(x,tasks,vms,cfg)); mean=[sum(x[j] for x in pop)/n for j in range(d)]; nxt=[]
        for x in pop:
            E=2*(1-t/max(1,iters))* (2*random.random()-1); q=random.random(); r=random.random()
            if abs(E)>=1: # exploration
                peer=random.choice(pop); y=[peer[j]-random.random()*abs(peer[j]-2*random.random()*x[j]) if q<.5 else (prey[j]-mean[j])-random.random()*(0+(m-1)*random.random()) for j in range(d)]
            else: # soft/hard besiege, with a simple rapid-dive candidate
                J=2*(1-random.random()); base=[prey[j]-E*abs(J*prey[j]-x[j]) if r>=.5 else prey[j]-E*abs(prey[j]-x[j]) for j in range(d)]
                dive=[base[j]+0.01*math.tan(math.pi*(random.random()-.5)) for j in range(d)]
                y=dive if _fit(dive,tasks,vms,cfg)<_fit(base,tasks,vms,cfg) else base
            nxt.append([min(m-1,max(0,z)) for z in y])
        pop=nxt
        iteration_best=min(pop,key=lambda x:_fit(x,tasks,vms,cfg)); iteration_score=_fit(iteration_best,tasks,vms,cfg)
        if iteration_score < best_score: best,best_score=list(iteration_best),iteration_score
        history.append(best_score)
    ranked=sorted(pop + [best],key=lambda x:_fit(x,tasks,vms,cfg))
    return repair(best,m),evaluate(tasks,repair(best,m),vms,cfg),history,ranked
