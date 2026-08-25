# Python Backtesting ve Paper Trading Sistemi

PAPER-002 Aşama A Düzeltmesi (STAGE A REMEDIATION — TIMING + BBBY DATA BLOCKER) gereksinimleri ve kısıtlamalarına uygun olarak gerçek `engine/paper_trading_controller.py` mantığını ve dondurulmuş 250'li evreni sentetik veri olmaksızın kullanan modüler yapı.

## Yapı

- `config/`: Merkezi yapılandırma ve varsayılanlar
- `data/`: Piyasa veri sağlayıcıları
- `engine/`: Backtest orkestrasyonu, metrikler, çizimler ve paper trading kontrolcüsü
- `strategies/`: Strateji sınıfları ve uygulamaları
- `run.py`: PAPER-002 dry-run ve çalıştırma giriş noktası

## Kurulum

```powershell
py -m pip install -r requirements.txt
```

## Çalıştırma

PAPER-002 kontrollü çalıştırma dry-run kontrolcüsünü çalıştırmak için:

```powershell
py run.py
```
