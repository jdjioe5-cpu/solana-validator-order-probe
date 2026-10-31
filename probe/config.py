import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class ProbeConfig:
    rpc_url: str = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
    spend_cap_sol: float = float(os.getenv("SPEND_CAP_SOL", "0.05"))
    private_key: Optional[str] = os.getenv("SOLANA_PRIVATE_KEY", None)
    dry_run: bool = True
    output_dir: str = "./reports"
    sample_size_per_validator: int = 50

    def validate(self):
        if not self.dry_run:
            if not self.private_key:
                raise ValueError("SOLANA_PRIVATE_KEY must be supplied when dry_run=False.")
            if self.spend_cap_sol <= 0 or self.spend_cap_sol > 0.05:
                raise ValueError("Enforced Bounty Constraint: SPEND_CAP_SOL must be <= 0.05 SOL.")
