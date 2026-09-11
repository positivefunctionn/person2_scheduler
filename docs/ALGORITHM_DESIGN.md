# Algorithm design

Facts from Person 1: the handoff has 1,084 aligned observations; `predicted_cpu`, `p_overload`, and `predicted_overload` are the only scheduler inputs; τ=0.18 is preserved. Actual columns are excluded from scheduler modules.

Experimental choices: a horizon row becomes task `t`; its demand is `d_t=predicted_cpu/100 × C_ref`. VM utilization is `u_i=(current_load_i + Σd_t)/C_i`. A task is infeasible when resultant utilization exceeds the configured threshold or its `d_t/C_i` execution time exceeds `execution_sla`. Makespan is `max_i Σ(d_t/C_i)`. Energy proxy is `Σ[P_idle+(P_max-P_idle)u_i]Δt`. Load imbalance is population standard deviation of VM utilizations.

The minimized objective is `wE E/Eref + wM M/Mref + wSLA SLA/SLAref + wL L/Lref`. SLA is violation rate plus configured high-risk placement penalty `p_overload×max(0,u-safe)×penalty`; it remains part of SLA rather than a fifth objective. Reference normalizers are fixed config constants, so algorithm comparisons remain comparable.

Position components are continuous during search, then rounded to a VM index, clipped to `[0,n-1]`, and evaluated as a valid schedule. HHO uses population search, escaping energy, exploration, soft/hard besiege and a rapid-dive candidate. GWO independently initializes its own wolves and updates from alpha/beta/delta. The hybrid runs HHO, ranks its population, passes its configurable elites to GWO, and fills remaining wolves by bounded elite perturbations—not unrelated random schedules.
