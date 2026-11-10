# 🤖 ERPNext AI Financial Reconciliation Agent

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![RapidFuzz](https://img.shields.io/badge/RapidFuzz-3.5+-purple.svg)](https://github.com/maxbachmann/RapidFuzz)
[![ERPNext](https://img.shields.io/badge/ERPNext-v14%20%7C%20v15-blue.svg)](https://erpnext.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An intelligent, automated **Bank Statement Reconciliation Agent** for **ERPNext & Frappe Framework**. Parses unstandardized bank statements (CSV/PDF) across major banks (HDFC, ICICI, SBI, Axis), performs multi-factor fuzzy matching against ERPNext `Payment Entry` and `General Ledger` records, and automatically posts vouchers to the ERPNext **Bank Reconciliation Tool**.

---

## 💡 Why This Solves a Critical ERP Problem

Bank reconciliation is one of the most manual, error-prone tasks in enterprise accounting. Bank statement narrations are often truncated or cryptic (e.g. `UPI/CR/630811928312/SHARMA/HDFC`), while ERP records have formal legal names (`Sharma Textiles and Garments Pvt Ltd`).

This engine bridges that gap using:
1. **Narration Party Extraction**: Regex & NLP heuristics separating UTR/IMPS codes from party names.
2. **Multi-Factor Scoring Matrix**:
   - Exact Amount Match (Weight: 45 pts)
   - UTR / Cheque Reference Match (Weight: 35 pts)
   - Token & Partial Ratio Fuzzy String Match via `rapidfuzz` (Weight: 25 pts)
   - Date Proximity Decay Window (Weight: 15 pts)
3. **Auto-Clearance Threshold**: Records with score $\ge$ 90% auto-update `clearance_date` in ERPNext, while borderline matches are queued for 1-click review.

---

## 🏗️ Architecture

```
┌─────────────────────────────────┐
│ Raw Bank Statement (CSV / PDF)  │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│     BankStatementParser         │
│  • Extract Date, UTR, Amount    │
│  • Strip Bank Narration Noise   │
└────────────────┬────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────┐
│             ReconciliationMatcher (Python)             │
│  • Multi-factor fuzzy algorithm                        │
│  • RapidFuzz token sorting                             │
│  • Score calculation (0 - 100%)                        │
└────────────────┬───────────────────────▲───────────────┘
                 │                       │ Fetch Unallocated
                 ▼                       │ Payment Entries
┌─────────────────────────────────┐      │
│     ERPNextReconcileSync        ├──────┘
│  • Auto-posts Bank Transactions │
│  • Updates Clearance Dates      │
└─────────────────────────────────┘
```

---

## 🚀 Quickstart

### 1. Installation

```bash
git clone https://github.com/shyampandey1104/erpnext-ai-reconcile-agent.git
cd erpnext-ai-reconcile-agent
pip install -r requirements.txt
```

### 2. Run Reconciliation CLI

Run reconciliation on the included sample statement:

```bash
python3 cli.py reconcile samples/sample_bank_statement.csv --threshold 80
```

Sample output:
```text
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Date       ┃ Bank Narration                      ┃ ERP Payment ID     ┃ ERP Party Name             ┃ Amount (₹)  ┃ Confidence ┃ Auto-Clear ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ 2026-11-02 │ UPI/CR/630811928312/SHARMA TEXTI... │ ACC-PAY-2026-00089 │ Sharma Textiles and Gar... │ ₹45,000.00  │ 98.2%      │ ✓ YES      │
│ 2026-11-04 │ NEFT-N1042026-VIRAR PACKAGING LT... │ ACC-PAY-2026-00092 │ Virar Packaging Pvt Ltd    │ ₹18,250.00  │ 96.5%      │ ✓ YES      │
│ 2026-11-07 │ RTGS/HDFCR5202611070001/ANANYA T... │ ACC-PAY-2026-00098 │ Ananya Traders Mumbai      │ ₹125,000.00 │ 95.0%      │ ✓ YES      │
└────────────┴─────────────────────────────────────┴────────────────────┴────────────────────────────┴─────────────┴────────────┴────────────┘
```

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

Author: **Shyamkumar Bhupendra Pandey** ([@shyampandey1104](https://github.com/shyampandey1104))
