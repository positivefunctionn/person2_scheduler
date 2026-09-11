import unittest, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.overload import overload_label
from src.demand_adapter import adapt
from src.models import VM
from src.fitness import repair,evaluate
from src.baseline import best_fit_decreasing
from src.gwo import gwo
from src.hho import hho
from src.hybrid import hho_gwo

CFG={'allowable_utilization':.8,'safe_utilization':.65,'risk_penalty':2,'execution_sla':1.5,'scheduling_interval':1,'weights':{'energy':.25,'makespan':.25,'sla':.25,'imbalance':.25},'normalization_references':{'energy':1000,'makespan':10,'sla':1,'imbalance':1},'hho':{'population_size':4,'iterations':3,'elite_size':2},'gwo':{'population_size':4,'iterations':3}}
ROWS=[{'predicted_cpu':'-2','p_overload':'.18','predicted_overload':'1'},{'predicted_cpu':'150','p_overload':'.1','predicted_overload':'0'}]
VMS=[VM('a','h',100,0,10,20),VM('b','h',100,0,10,20)]
class CoreTests(unittest.TestCase):
 def test_threshold(self): self.assertEqual((overload_label(.17),overload_label(.18),overload_label(.9)),(0,1,1))
 def test_demand_repairs_only_negative(self):
  log=[]; ts=adapt(ROWS,0,100,log); self.assertEqual((ts[0].demand,ts[1].demand,len(log)),(0,150,1))
 def test_discrete_repair(self): self.assertEqual(repair([-9,.6,9],2),[0,1,1])
 def test_bfd_valid_and_metric(self):
  log=[]; ts=adapt(ROWS,0,100,log); a,m=best_fit_decreasing(ts,VMS,CFG); self.assertEqual(len(a),2); self.assertGreaterEqual(m.fitness,0)
 def test_zero_work(self):
  rows=[{'predicted_cpu':'0','p_overload':'0','predicted_overload':'0'}]; t=adapt(rows,0,100,[]); self.assertEqual(evaluate(t,[0],VMS,CFG).makespan,0)
 def test_gwo_hho_and_hybrid_return_valid_schedules(self):
  tasks=adapt(ROWS,0,100,[])
  for optimizer in (gwo,hho):
   assignment,metrics,history,_=optimizer(tasks,VMS,CFG,7)
   self.assertEqual(len(assignment),len(tasks)); self.assertTrue(all(i in (0,1) for i in assignment)); self.assertEqual(len(history),3); self.assertGreaterEqual(metrics.fitness,0)
  assignment,metrics,history,details=hho_gwo(tasks,VMS,CFG,7)
  self.assertEqual(len(assignment),len(tasks)); self.assertTrue(all(i in (0,1) for i in assignment)); self.assertEqual(details['hho_elite_count'],2); self.assertEqual(details['gwo_seeded_population'],4); self.assertEqual(len(history),6); self.assertGreaterEqual(metrics.fitness,0)
if __name__=='__main__': unittest.main()
