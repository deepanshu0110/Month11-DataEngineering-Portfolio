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
> NRA_Capstone_Business_Case.md.

---

## Tech Stack
Python 3.11+, pandas, numpy, boto3 + moto (S3 mocking), graphviz, GitHub Actions

## How to Run
```
git clone https://github.com/deepanshu0110/Month11-DataEngineering-Portfolio.git
cd Month11-DataEngineering-Portfolio
pip install -r requirements.txt
python pipeline.py
python test_gate.py
```

## Repository Structure
```
.
├── notebooks/Day189...ipynb, Day190...ipynb, Day191...ipynb
├── pipeline.py
├── test_gate.py
├── .github/workflows/logitrack_monitor.yml
├── architecture_diagram.png
├── NRA_Capstone_Business_Case.md
└── README.md
```
