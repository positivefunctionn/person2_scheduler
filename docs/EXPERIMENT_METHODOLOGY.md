# Experimental methodology

The required Person 1 handoff is validated for expected columns, 1,084 rows, probability range, and binary labels without modification. It is partitioned sequentially into non-overlapping H=10 horizons; the final partial horizon is processed. Each row is a synthetic workload abstraction, not a Bitbrain cloud task.

BFD, independent GWO, independent HHO, and sequential HHO→GWO receive the same horizons, VM configuration, constraint rules, objective and seeds. Ten configured seeds are recorded; report mean, standard deviation, min, and max without seed cherry-picking. The VM cluster, capacities beyond any supplied VM-214 reference, execution rule, power model, and SLA are experimental simulation parameters. No result should be reported until the actual handoff is present and the runner completes.
