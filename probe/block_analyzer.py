import json
import logging
from typing import Dict, List, Any, Optional
import requests

logger = logging.getLogger("order_probe.analyzer")

class BlockAnalyzer:
    """Fetches blocks via getBlock RPC and reconstructs transaction ordering profiles."""

    def __init__(self, rpc_url: str):
        self.rpc_url = rpc_url

    def fetch_block(self, slot: int) -> Optional[Dict[str, Any]]:
        """Call standard Solana getBlock with max supported transaction version."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBlock",
            "params": [
                slot,
                {
                    "encoding": "json",
                    "transactionDetails": "full",
                    "maxSupportedTransactionVersion": 0,
                    "rewards": True
                }
            ]
        }
        try:
            resp = requests.post(self.rpc_url, json=payload, timeout=25)
            if resp.status_code == 200:
                res = resp.json().get("result")
                return res
        except Exception as e:
            logger.error(f"Failed to fetch block {slot}: {e}")
        return None

    @staticmethod
    def extract_ordering_features(block_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extracts index, priority fee, write-locks, and signature from each tx in block."""
        transactions = block_data.get("transactions", [])
        extracted = []
        for idx, tx in enumerate(transactions):
            meta = tx.get("meta", {})
            transaction = tx.get("transaction", {})
            message = transaction.get("message", {})
            
            # Compute Unit and Priority Fee estimation
            fee = meta.get("fee", 5000)
            compute_units_consumed = meta.get("computeUnitsConsumed", 200)
            base_fee = 5000
            priority_fee_paid = max(0, fee - base_fee)
            
            # Compute unit price (micro-lamports per CU)
            cu_price = 0
            if compute_units_consumed > 0:
                cu_price = (priority_fee_paid * 1_000_000) / compute_units_consumed

            signatures = transaction.get("signatures", [])
            sig = signatures[0] if signatures else f"unknown_sig_{idx}"

            account_keys = message.get("accountKeys", [])
            writable_keys = []
            for acc_idx, acc in enumerate(account_keys):
                # Simple extraction of writable accounts
                acc_pubkey = acc if isinstance(acc, str) else acc.get("pubkey", "")
                writable_keys.append(acc_pubkey)

            extracted.append({
                "block_index": idx,
                "signature": sig,
                "fee_paid": fee,
                "priority_fee_paid": priority_fee_paid,
                "compute_units_consumed": compute_units_consumed,
                "estimated_cu_price": cu_price,
                "writable_accounts": writable_keys[:5]  # first 5 accounts
            })
        return extracted
