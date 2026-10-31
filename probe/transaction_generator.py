import time
from typing import List, Dict, Any

class TransactionGenerator:
    """Generates structured micro-probe transaction batches with controlled variations."""

    @staticmethod
    def create_priority_gradient_batch(
        sender_pubkey: str,
        priority_fee_micro_lamports: List[int] = [0, 1000, 5000, 25000, 100000]
    ) -> List[Dict[str, Any]]:
        """Generates a batch of test transactions with stepped priority fees."""
        batch = []
        for idx, fee in enumerate(priority_fee_micro_lamports):
            tx_meta = {
                "probe_id": f"probe_fee_{idx}",
                "sender": sender_pubkey,
                "priority_fee_micro_lamports": fee,
                "compute_unit_limit": 200,  # Minimal dummy transfer/memo
                "target_account": f"ProbeAccountLock{idx:02d}",
                "scheduled_timestamp_ms": int(time.time() * 1000) + (idx * 50),
                "memo": f"probe_gradient_fee_{fee}"
            }
            batch.append(tx_meta)
        return batch

    @staticmethod
    def create_contention_pair(
        sender_pubkey: str,
        shared_lock_account: str
    ) -> List[Dict[str, Any]]:
        """Generates a pair of conflicting transactions competing for the exact same write-lock."""
        now = int(time.time() * 1000)
        tx_a = {
            "probe_id": "contention_tx_a",
            "sender": sender_pubkey,
            "priority_fee_micro_lamports": 5000,
            "target_account": shared_lock_account,
            "is_writable": True,
            "scheduled_timestamp_ms": now,
            "memo": "contention_lock_contender_A"
        }
        tx_b = {
            "probe_id": "contention_tx_b",
            "sender": sender_pubkey,
            "priority_fee_micro_lamports": 10000,
            "target_account": shared_lock_account,
            "is_writable": True,
            "scheduled_timestamp_ms": now + 10,
            "memo": "contention_lock_contender_B"
        }
        return [tx_a, tx_b]
