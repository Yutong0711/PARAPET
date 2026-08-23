# parapet-record

The record every PARAPET component reads and writes.

A hardening record answers four questions about one proposed change: what
it removes, the check that proves it, what it cost, and how to reproduce
both. `parapet-triage` fills the exposure, `parapet-scope` fills the review
cost, `parapet-attrib` fills the attribution, and the budget check turns
the measured cost into an admit-or-overrun verdict.

```bash
pip install parapet-record
```

```python
from parapet_record import Budget, CostMeasure, HardeningRecord, new_provenance
from parapet_record.schema import check_budget

budget = Budget(project="acme", limits={"latency": "5%"}, binding=["latency"])
cost = CostMeasure(dimension="latency", value=104.0, unit="ms", baseline=100.0,
                   interval_low=102.0, interval_high=106.0, workload="bench/read")

record = HardeningRecord(record_id="acme-2026-001", budget=budget, costs=[cost])
record.budget_checks.append(check_budget(budget, cost))
print(record.decide())      # 'overrun': the interval reaches 6%, past the 5% limit
```

Three rules the schema enforces rather than documents:

- A limit carries its unit (`"5%"`, `"20ms"`, `"64mb"`). Comparing a
  measurement against a limit in a different unit raises instead of
  returning a wrong answer.
- A change is admitted only when the whole confidence interval fits. A
  measurement with no interval leaves the record `unscored`.
- A dimension the budget does not declare is a non-decision, not a pass.

See [docs/record-schema.md](../../docs/record-schema.md) for the field list
and the versioning policy.
