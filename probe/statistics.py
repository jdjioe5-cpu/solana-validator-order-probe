import math
from typing import List, Dict, Any, Tuple

class OrderingStatistics:
    """Computes rigorous ordering metrics across extracted block transactions."""

    @staticmethod
    def calculate_inversion_rate(extracted: List[Dict[str, Any]]) -> Tuple[float, int, int]:
        """Calculates percentage of transaction pairs where a lower fee tx preceded a higher fee tx."""
        n = len(extracted)
        if n < 2:
            return 0.0, 0, 0
        
        inversions = 0
        total_pairs = 0
        
        # Sample up to first 500 transactions to maintain O(N^2) tractable
        sample = extracted[:min(500, n)]
        sample_len = len(sample)
        
        for i in range(sample_len):
            for j in range(i + 1, sample_len):
                total_pairs += 1
                fee_i = sample[i]["estimated_cu_price"]
                fee_j = sample[j]["estimated_cu_price"]
                # Inversion: Earlier transaction i had lower priority fee than later transaction j
                if fee_i < fee_j and fee_j > 1000:
                    inversions += 1
                    
        rate = (inversions / total_pairs) if total_pairs > 0 else 0.0
        return rate, inversions, total_pairs

    @staticmethod
    def calculate_spearman_rank_correlation(extracted: List[Dict[str, Any]]) -> float:
        """Computes Spearman's rho between block index and priority fee."""
        n = len(extracted)
        if n < 5:
            return 0.0

        sample = extracted[:min(500, n)]
        m = len(sample)

        # Rank by block index (1..m)
        index_ranks = list(range(1, m + 1))
        
        # Rank by priority fee
        sorted_by_fee = sorted(range(m), key=lambda k: sample[k]["estimated_cu_price"], reverse=True)
        fee_ranks = [0] * m
        for rank, orig_idx in enumerate(sorted_by_fee):
            fee_ranks[orig_idx] = rank + 1

        d_sq_sum = sum((index_ranks[i] - fee_ranks[i]) ** 2 for i in range(m))
        rho = 1.0 - (6.0 * d_sq_sum) / (m * (m ** 2 - 1))
        return rho

    @classmethod
    def classify_ordering_rule(cls, extracted: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Categorizes the validator block scheduler behavior based on empirical metrics."""
        inversion_rate, inv_count, pairs = cls.calculate_inversion_rate(extracted)
        rho = cls.calculate_spearman_rank_correlation(extracted)

        # Classification heuristics
        if rho > 0.65 and inversion_rate < 0.15:
            classification = "Strict Global Priority Fee Scheduler"
            confidence = "High"
            rule_summary = "Transactions strictly sorted descending by Priority Fee."
        elif rho > 0.25 and inversion_rate < 0.40:
            classification = "Multi-threaded BankingStage with Partial Priority Sorting"
            confidence = "High"
            rule_summary = "Local priority sorting per Banking thread; interleaving between threads creates moderate inversions."
        else:
            classification = "First-Come-First-Served (FCFS) Packet-Arrival Stream"
            confidence = "High"
            rule_summary = "No global priority ordering detected; sequence driven by network packet arrival and lock contention."

        return {
            "classification": classification,
            "rule_summary": rule_summary,
            "spearman_rho": round(rho, 4),
            "inversion_rate": round(inversion_rate, 4),
            "inversion_count": inv_count,
            "total_pairs_evaluated": pairs,
            "sample_size": len(extracted)
        }
