# LogiTrack India - Data Engineering Capstone

## Results Summary (verified run, seed=181 / seed=190)

| Metric | Value |
|--------|-------|
| Raw rows | 538 |
| Clean rows | 530 |
| High-delay shipments | 234 (44.15%) |
| Revenue at risk | Rs 305,612.65 |
| Conformance rate | 71.32% |
| Non-conformant cases | 152 |

**Worst carrier by transit time:** Delhivery (13.13 days)
**Worst carrier by conformance:** BlueDart (61.7% conformant)

> Note: high-delay threshold is `days_in_transit > 14`, a placeholder pending
> a real client SLA. Carrier-level differences above are explained by the
> delay-linked break probability, not a carrier-specific mechanism -- see
> [docs/NRA_Capstone_Business_Case.md](docs/NRA_Capstone_Business_Case.md).

---

## Tech Stack
Python 3.11+, pandas, numpy, boto3 + moto (S3 mocking), graphviz, GitHub Actions

## How to Run
```
git clone https://github.com/deepanshu0110/Month11-DataEngineering-Portfolio.git
cd Month11-DataEngineering-Portfolio
pip install -r requirements.txt
python src/pipeline.py
python test_gate.py
```

`test_gate.py` is expected to report **GATE RESULT: FAIL**. The data-quality checks pass, but conformance (71.32%) is below the 80% threshold. That is the monitoring working as designed: it blocks a run that should not ship. Reproduced on 16 Oct 2026.

## Repository Structure
```
.
├── notebooks/            # Days 181-191: ETL, scheduling, GitHub Actions, S3 (boto3 + moto), process mining, capstone
├── src/pipeline.py       # unified pipeline: generate, clean, S3 write (mocked), conformance check
├── test_gate.py          # data-quality and conformance gate
├── logitrack_monitor.yml # GitHub Actions workflow template (move to .github/workflows/ to activate)
├── docs/
│   ├── architecture_diagram.png
│   └── NRA_Capstone_Business_Case.md
├── requirements.txt
└── README.md
```
