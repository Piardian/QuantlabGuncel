from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

from engine.paper_trading_controller import PaperTradingController, PaperControllerConfig, result_to_dict

def main() -> int:
    print("=" * 80)
    print("PAPER-002 STAGE A REMEDIATION REVIEW — TIMING + BBBY DATA BLOCKER")
    print("Gerçek Motor ve Dondurulmuş Evren ile Kontrollü Dry-Run Başlatılıyor...")
    print("=" * 80)
    
    config = PaperControllerConfig()
    controller = PaperTradingController(config=config)
    
    result = controller.run_dry_run()
    
    print(f"\n[RAPOR] Oturum Kimliği (Session ID): {result.paper_session_id}")
    print(f"[RAPOR] Rebalance Kimliği: {result.rebalance_id}")
    print(f"[RAPOR] Ortam: {result.environment}")
    print(f"[RAPOR] Takvim Durumu (Calendar State): {result.calendar_state}")
    print(f"[RAPOR] Zamanlama Durumu (Schedule State): {result.schedule_state}")
    print(f"[RAPOR] Veri Güncelliği (Freshness State): {result.freshness_state}")
    print(f"[RAPOR] Uygunluk Durumu (Eligibility State): {result.eligibility_state}")
    print(f"[RAPOR] Uygun Sembol Sayısı (Eligible Count): {result.eligible_count} (BBBY Engellenmiştir)")
    print(f"[RAPOR] Hedef Varlık Sayısı: {result.target_holding_count}")
    print(f"[RAPOR] Hazırlık Durumu (Readiness State): {result.readiness_state}")
    print(f"[RAPOR] Sağlık Durumu (Health State): {result.health_state}")
    print(f"[RAPOR] Gönderim Yetkilendirildi mi?: {result.submission_authorized}")
    print(f"[RAPOR] Blok Sebebi: {result.block_reason}")
    print(f"[RAPOR] Uyarılar/Olaylar (Incidents): {result.incidents}")
    
    print("\n" + "=" * 80)
    if result.submission_authorized:
        print("Sistem kontrollü canlı kağıt ticareti (paper trading) için tamamen hazır.")
    else:
        print("PAPER-002 Stage A Güvenlik Korumaları, T+1 Zamanlama Kuralları ve BBBY Veri Engelleyicileri gereği işlem güvenli bir şekilde durduruldu (İşlem Yapılmadı).")
    print("=" * 80)
    return 0

if __name__ == "__main__":
    sys.exit(main())
