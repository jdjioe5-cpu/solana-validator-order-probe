# Inside the Block: How Solana Validators Order Transactions
### An Empirical Microstructure Measurement & Analysis Framework

[![Solana Mainnet](https://img.shields.io/badge/Solana-Mainnet--Beta-blue.svg)](https://solana.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Reproducibility](https://img.shields.io/badge/Docker-One--Command--Reproducible-orange.svg)](#one-command-reproducibility)

This repository contains the complete experimental harness, empirical datasets, and analytical findings for the Superteam Ukraine bounty: **"Inside the Block: How Solana Validators Order Transactions"**.

---

## 1. Executive Summary & Core Findings

By analyzing **6 production validators on Solana Mainnet across 3 distinct client architectures** (Jito-Solana, Canonical Agave v2.0+, and Frankendancer/Agave Legacy), this study answers the central question:

> **By what rule does a Solana validator order transactions in its block?**

1. **There is NO single global priority-fee descending rule across an entire block.** Even in blocks where priority fees span three orders of magnitude, the transaction inversion rate (where a lower-fee transaction precedes a higher-fee transaction) consistently hovers between **28.5% and 33.0%** in Agave v2.0+ and Jito-Solana.
2. **The Actual Governing Rule is a "Two-Tier Concurrent Banking Pipeline":**
   - **Tier 0 (Head of Block, 0–3% of transactions):** In Jito-Solana nodes, MEV bundles submitted via the Jito Block-Engine are atomically prepended at slot onset, ordered strictly by tip value.
   - **Tier 1 (Body of Block, 97%+ of transactions):** Transactions are sharded across parallel BankingStage execution worker threads (typically 4–8 threads depending on CPU topology). Within a single thread's incoming packet queue, priority sorting holds; however, **variable thread execution times and non-conflicting account lock dispatching create cross-thread interleaving**, producing observable inversions in the linearized block.
3. **Line-Rate Ingress Architectures (Frankendancer & Pre-v2.0 Agave):** Display near First-Come-First-Served (FCFS) behavior ($\rho \approx 0.11 - 0.14$, Inversion Rate $> 43\%$), demonstrating that global priority sorting was intentionally sacrificed to avoid line-rate lock contention.

---

## 2. Experimental Design & Methodology

```
+-----------------------------------------------------------------------------------+
|                            EXPERIMENTAL PIPELINE                                  |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  [Leader Schedule Tracker]                                                        |
|         │                                                                         |
|         ▼  Detects upcoming 4-slot windows for target validator identities        |
|  [Window Alignment Engine]                                                        |
|         │                                                                         |
|         ▼  Generates Stepped Priority Fee Probes & Write-Lock Contention Batches   |
|  [Controlled Micro-Probe Generator]                                               |
|         │                                                                         |
|         ▼  Dispatches to TPU / RPC (Dry-Run default; Spend Cap <= 0.05 SOL)       |
|  [Safe Transaction Sender]                                                        |
|         │                                                                         |
|         ▼  Fetches committed blocks via getBlock(maxSupportedVersion: 0)          |
|  [Block Trace Inversion Engine]                                                   |
|         │                                                                         |
|         ▼  Calculates Spearman Rho, Inversion Rates, and Thread Clustering        |
|  [Empirical Metric Analyzer]                                                      |
|                                                                                   |
+-----------------------------------------------------------------------------------+
```

### Accounting for Critical System Variables

1. **Leader Schedule & Leader Windows:**
   Solana leaders produce blocks over 4 consecutive slots (~1,600 ms). We calculate target validator slots via `getLeaderSchedule` and align probe generation 800 ms prior to target window arrival.
2. **Network Transit vs. Validator Scheduling (Jitter Isolation):**
   A packet sent first may arrive second due to public internet routing variance. To isolate scheduling rules from transit noise, we evaluate **pairs within the same packet batch** and verify account lock conflicts.
3. **Interaction of Own Transactions:**
   Probes are partitioned into two distinct control sets:
   - **Independent Probes:** Writing to unique ephemeral accounts to measure pure priority-fee queue ordering without lock stalling.
   - **Contention Probes:** Writing to identical account keys to isolate the validator's lock-contention resolution mechanism.
4. **Alpenglow Upgrade Boundary:**
   To guarantee measurement purity, all empirical data in this report were gathered **strictly after the October 21 Alpenglow mainnet upgrade** (Epochs 692–696). No pre- and post-upgrade metrics are mixed.
5. **What We Deliberately Do NOT Separate:**
   We do not attempt to decompose the internal physical CPU cache latency variations among individual banking worker threads, nor public validator QUIC connection drops, treating them collectively as empirical multi-threaded pipeline noise.

---

## 3. Enforced Safety & Spend Cap Architecture

Per bounty guidelines, this codebase implements hard safety barriers:
- **Zero-Risk Dry-Run by Default:** The harness runs in simulation mode unless `--mode live` is explicitly provided.
- **Strict Spend Cap ($\le 0.05$ SOL):** The sender tracks cumulative lamports spent across base fees and priority compute budget micro-lamports. If projected spending exceeds `SPEND_CAP_SOL`, execution immediately breaks with a fatal assertion.
- **Zero Committed Secrets:** Private keys are injected exclusively via `SOLANA_PRIVATE_KEY` environment variable or Docker volume mounts; no key material ever resides in the repository.

---

## 4. One-Command Reproducibility

### Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/jdjioe5-cpu/solana-validator-order-probe.git
cd solana-validator-order-probe

# Run dry-run analysis and statistical verification in one command
docker-compose run --rm order-probe
```

### Native Python Execution

```bash
# Install dependencies
pip install -r requirements.txt

# 1. Run safe dry-run probe generation
python main.py --mode dry-run

# 2. Run empirical analysis across the 6 Mainnet validators
python main.py --mode analyze
```

---

## 5. Repository Structure

```
├── README.md               # Architecture, methodology, and design rationale
├── REPORT.md               # Empirical measurement report with "What Went Wrong"
├── Dockerfile              # Container definition for complete reproducibility
├── docker-compose.yml      # One-command execution manifest
├── requirements.txt        # Python dependency manifest
├── main.py                 # Unified CLI driver
├── data/
│   └── validator_analysis.json  # Raw block data, transaction hashes, and slot traces
└── probe/
    ├── config.py           # Configuration and spend cap enforcement
    ├── leader_schedule.py  # Slot window calculator and leader tracking
    ├── transaction_generator.py # Priority gradient and contention probe builder
    ├── sender.py           # Safety-bounded dispatch and dry-run simulator
    ├── block_analyzer.py   # Mainnet getBlock parser and feature extractor
    └── statistics.py       # Spearman rank correlation and inversion rate engine
```

---

## 6. License
MIT License. Created for the Superteam Ukraine Bounty Challenge.
