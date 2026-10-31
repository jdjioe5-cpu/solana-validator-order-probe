import requests
from typing import Dict, List, Optional, Tuple

class LeaderScheduleTracker:
    def __init__(self, rpc_url: str):
        self.rpc_url = rpc_url
        self.cached_schedule: Optional[Dict[str, List[int]]] = None
        self.epoch_info: Optional[dict] = None

    def refresh_epoch_info(self) -> dict:
        payload = {"jsonrpc": "2.0", "id": 1, "method": "getEpochInfo"}
        resp = requests.post(self.rpc_url, json=payload, timeout=15)
        resp.raise_for_status()
        self.epoch_info = resp.json().get("result", {})
        return self.epoch_info

    def get_leader_schedule(self) -> Dict[str, List[int]]:
        if self.cached_schedule is not None:
            return self.cached_schedule
        payload = {"jsonrpc": "2.0", "id": 2, "method": "getLeaderSchedule"}
        resp = requests.post(self.rpc_url, json=payload, timeout=25)
        resp.raise_for_status()
        self.cached_schedule = resp.json().get("result", {})
        return self.cached_schedule

    def find_upcoming_windows(self, target_identity: str, count: int = 5) -> List[Tuple[int, int]]:
        """Return upcoming (start_slot, end_slot) 4-slot windows for target validator."""
        info = self.refresh_epoch_info()
        current_slot = info.get("absoluteSlot", 0)
        schedule = self.get_leader_schedule()
        
        slots = schedule.get(target_identity, [])
        upcoming = [s for s in slots if s > current_slot]
        upcoming.sort()
        
        windows = []
        for s in upcoming:
            # Group into 4-slot windows
            base_slot = s - (s % 4)
            win = (base_slot, base_slot + 3)
            if win not in windows:
                windows.append(win)
            if len(windows) >= count:
                break
        return windows
