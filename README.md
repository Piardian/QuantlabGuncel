# QuantLab

**Quantitative Backtesting & Paper Trading Research Infrastructure**

![Status](https://img.shields.io/badge/status-active%20development-blue)
![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![Strategy](https://img.shields.io/badge/Strategy-CSM--001%20x%20TSM--001-green)
![Universe](https://img.shields.io/badge/Universe-FUF001--250-purple)
![Environment](https://img.shields.io/badge/Environment-Alpaca%20PAPER-orange)

QuantLab is a modular Python research and paper-trading platform for systematic market-data ingestion, strategy execution, portfolio simulation, performance analysis, and reproducible quantitative experiments.

---

## 🏛️ System Architecture

```text
[ Market Data & Calendar Layer (Alpaca / Yahoo) ]
                      ↓
[ Security Identity & Corporate Action Resolver (SecurityIdentityResolver) ]
                      ↓
[ Frozen Universe Membership & Alpha Pipeline (CSM-001 x TSM-001) ]
                      ↓
[ Risk Guards & Safety Manager (PaperRiskGuards / Read-Only Invariants) ]
                      ↓
[ Production Paper Trading Controller (PaperTradingController) ]
                      ↓
[ Scheduled Telegram Operational Reporting (TelegramNotifier) ]
```

---

## 🚀 Key Modules & Capabilities

- **Frozen Universe & Alpha (FUF001 & CSM x TSM):** Cross-Sectional Momentum ($12-1$ return decile ranking) and Time-Series Momentum trend filters on a 250-security frozen exploratory universe.
- **Security Identity & Corporate Actions (PAPER-001R):** Authoritative SEC CIK / exchange listing transition mapper and historical price series stitcher with boundary, gap, and finite price checks.
- **Paper Trading Controller (ALP-003 / PAPER-002):** Production-grade preflight checks, T+1 schedule enforcement, multi-session timing guards, and portfolio reconciliation.
- **Operational Safety Layer:** Hard fail-closed guards (`TRADING_ENABLED=FALSE`, `PAPER_EXECUTION_ENABLED=FALSE`, `Broker mutations=0`).
- **Telegram Status Reporter:** Automated daily status alerts, monthly signal notifications, and incident alerts without trading mutation risks.

---

## 📂 Repository Structure

```text
config/       Configuration files, frozen universe mappings, and telegram configs
data/         Market data ingestors and normalization adapters
engine/       PaperTradingController, AlpacaBrokerAdapter, SecurityIdentityResolver, risk guards
research/     Audit trails, scientific frozen manifests, and identity remediation reports
scripts/      Controlled launch, identity verification, operational tests, telegram status
strategies/   Strategy implementations and abstractions
automation/   Windows scheduler scripts and batch launchers
```

---

## 🧪 Test Suites & Verification

The platform maintains a 100% pass rate across all automated regression suites (122+ tests):

```powershell
# 1. Identity & Corporate Action Resolution Tests
py scripts/paper_identity_tests.py

# 2. Paper Launch Safety Tests
py scripts/paper_launch_tests.py

# 3. Paper Risk Guard Tests
py scripts/paper_safety_tests.py

# 4. Telegram Reporting Tests
py scripts/paper_telegram_tests.py

# 5. Operational Scheduler & DST Tests
py scripts/paper_scheduler_operational_tests.py
```

---

## 🛡️ License & Disclaimer

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

QuantLab is a research and engineering platform. Performance metrics and simulation outputs are treated strictly as research artifacts and do not constitute financial advice or guarantees of future market performance.
