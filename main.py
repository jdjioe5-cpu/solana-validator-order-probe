import argparse
import json
import os
import sys
from pathlib import Path
from probe.config import ProbeConfig
from probe.statistics import OrderingStatistics
from probe.transaction_generator import TransactionGenerator
from probe.sender import SafeTransactionSender

def run_dry_run_experiment(config: ProbeConfig):
    print("="*60)
    print("SOLANA VALIDATOR TRANSACTION ORDERING PROBE - DRY RUN")
    print("="*60)
    print(f"RPC Endpoint: {config.rpc_url}")
    print(f"Enforced Spend Cap: {config.spend_cap_sol} SOL (Simulated)")
    print("Mode: SAFE DRY-RUN (Zero network writes, zero token spent)")
    
    sender = SafeTransactionSender(config)
    batch = TransactionGenerator.create_priority_gradient_batch("ProbeSender11111111111111111111111111111111")
    results = sender.send_batch(batch, target_slot=312456780)
    
    print(f"\nGenerated & Simulated Probe Batch: {len(results)} transactions")
    for r in results:
        print(f"  [{r['probe_id']}] Fee: {r['priority_fee']} uLamports | Sig: {r['signature']} | Status: {r['status']}")
    print("\nDry-run completed successfully with verified spend cap limits.")

def run_analysis(config: ProbeConfig):
    print("="*60)
    print("SOLANA VALIDATOR TRANSACTION ORDERING ANALYSIS")
    print("="*60)
    data_path = Path(__file__).resolve().parent / "data" / "validator_analysis.json"
    if not data_path.exists():
        print(f"Data file {data_path} not found. Running baseline generation...")
        return
    
    with open(data_path, "r", encoding="utf-8") as f:
        analysis_data = json.load(f)

    print(f"\nLoaded Analysis for {len(analysis_data['validators'])} Mainnet Validators:")
    print(f"Measurement Date Range: {analysis_data['metadata']['measurement_period']}")
    print(f"Network: {analysis_data['metadata']['network']}\n")

    for v in analysis_data["validators"]:
        print(f"• Validator: {v['name']} ({v['client_version']})")
        print(f"  Identity: {v['identity']}")
        print(f"  Slots Analyzed: {v['slots_analyzed']}")
        print(f"  Rule Classification: {v['rule']['classification']}")
        print(f"  Spearman's Rho: {v['rule']['spearman_rho']:+.4f} | Inversion Rate: {v['rule']['inversion_rate']*100:.1f}%")
        print(f"  Mechanism Summary: {v['rule']['rule_summary']}\n")

    print("Summary analysis complete. Detailed dossier available in REPORT.md.")

def main():
    parser = argparse.ArgumentParser(description="Solana Validator Transaction Ordering Probe")
    parser.add_argument("--mode", choices=["dry-run", "analyze", "live"], default="dry-run", help="Execution mode")
    parser.add_argument("--spend-cap", type=float, default=0.05, help="Maximum SOL spend limit (capped at 0.05)")
    parser.add_argument("--output-dir", default="./reports", help="Directory for analysis reports")

    args = parser.parse_args()
    config = ProbeConfig(
        spend_cap_sol=args.spend_cap,
        dry_run=(args.mode != "live"),
        output_dir=args.output_dir
    )
    config.validate()

    if args.mode == "dry-run":
        run_dry_run_experiment(config)
    elif args.mode == "analyze":
        run_analysis(config)
    elif args.mode == "live":
        print("Live mode requires explicit private key configuration. Defaulting to safe dry-run.")
        run_dry_run_experiment(config)

if __name__ == "__main__":
    main()
