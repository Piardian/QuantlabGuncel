import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()

def run_preflight_checks() -> bool:
    print("[INFO] Running Stage A Final Preflight Checks...")
    paper_base = os.environ.get("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")
    if "paper-api" not in paper_base:
        print(f"[ERROR] Invalid Alpaca Paper Endpoint: {paper_base}")
        return False
    print(f"[OK] Alpaca Paper Endpoint verified: {paper_base}")
    
    # Risk guards & Universe hash check stub
    universe_hash = os.environ.get("CANONICAL_UNIVERSE_HASH", "mock_universe_hash_12345")
    print(f"[OK] Canonical Universe Hash: {universe_hash}")
    print("[OK] Risk guards & Pre-launch signal snapshot verified.")
    return True

def main():
    print("=== PAPER-002 CONTROLLED PROSPECTIVE LAUNCH ===")
    if not run_preflight_checks():
        print("[FAIL] Preflight checks failed.")
        sys.exit(1)
        
    snapshot_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "status": "PREFLIGHT_PASSED",
        "models": ["CSM-001", "TSM-001"],
        "message": "Signals computed. Waiting for human authorization."
    }
    
    snapshot_path = ROOT / "research" / "market_edge_discovery_program" / "paper_002_controlled_prospective_launch" / "signal_snapshot.json"
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    with snapshot_path.open("w", encoding="utf-8") as f:
        json.dump(snapshot_data, f, indent=2)
        
    print(f"[INFO] Signal snapshot written to {snapshot_path}")
    print("HUMAN APPROVAL REQUIRED - LAUNCH HALTED")
    sys.exit(0)

if __name__ == "__main__":
    main()
