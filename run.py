from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

from engine.paper_trading_controller import PaperTradingController, PaperControllerConfig, result_to_dict

def main() -> int:
    print("PAPER-002 Aşaması: Gerçek Alpaca Paper Altyapısı ve Dondurulmuş 250'li Evren ile Kontrollü Çalıştırma Başlatılıyor...")
    
    config = PaperControllerConfig()
    controller = PaperTradingController(config=config)
    
    result = controller.run_dry_run()
    
    print(f"Oturum Kimliği (Session ID): {result.paper_session_id}")
    print(f"Rebalance Kimliği: {result.rebalance_id}")
    print(f"Ortam: {result.environment}")
    print(f"Hazırlık Durumu (Readiness State): {result.readiness_state}")
    print(f"Sağlık Durumu (Health State): {result.health_state}")
    print(f"Gönderim Yetkilendirildi mi?: {result.submission_authorized}")
    print(f"Blok Sebebi: {result.block_reason}")
    print(f"Uyarılar/Olaylar (Incidents): {result.incidents}")
    
    if result.submission_authorized:
        print("Sistem kontrollü canlı kâğıt ticareti (paper trading) için tamamen hazır.")
        return 0
    else:
        print("Sistem güvenlik korumaları veya zamanlama kuralları gereği bloklandı veya dry-run modunda.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
