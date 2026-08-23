# Quant Backtesting Project - PM Handoff Context

Bu belge yeni PM'in projeyi, geçmiş araştırmayı ve mevcut karar noktasını tek seferde anlayabilmesi için hazırlanmıştır. Amaç, stratejiyi körlemesine değiştirmek değil; mevcut kanıtı doğru yorumlayarak sistemi daha güvenilir ve mümkünse pozitif beklentili hale getirmektir.

## 1. Roller

### Kullanıcı

- Projenin sahibi ve nihai karar vericisidir.
- Araştırma hipotezlerini ve kapsamı belirler.
- Hangi değişikliklerin uygulanacağını onaylar.
- Sonuçları finansal/iş perspektifinden değerlendirir.
- Onay vermeden strateji, risk veya evren değişikliği yapılmamalıdır.

### PM

- Araştırma yönünü yönetir ve hipotezleri netleştirir.
- Sonuçları sadece toplam PnL ile değil, Avg R, expectancy, profit factor, drawdown, örneklem büyüklüğü ve konsantrasyon ile değerlendirir.
- Yeni filtre veya parametre önermeden önce bunun yeni bilgi taşıyıp taşımadığını kontrol eder.
- Araştırma, validation ve canlı/paper operasyon aşamalarını birbirine karıştırmaz.
- Parametre optimizasyonu, hindsight universe seçimi ve tek sembol sonucuna dayalı kararları engeller.

### Codder / Kodlama Asistanı

- Projeyi inceler, mevcut mimariye uygun kod yazar ve sonuçları doğrular.
- Kullanıcı veya PM açıkça istemeden strateji mantığı, parametre, risk motoru veya evren değiştirmez.
- Her deneyin veri aralığını, warmup süresini, timeframe'ini, universe'ünü ve portföy varsayımlarını kaydeder.
- Sembol bazlı backtest ile birleşik portföy backtestini ayırır.
- Kod ve sonuç çelişirse bunu saklamaz; uygulamadan önce açıkça raporlar.

## 2. Projenin amacı

Bu proje Backtrader tabanlı bir günlük US equities araştırma/backtest sistemidir. İlk hedef, doğrudan canlı para kazanmak değil; tekrarlanabilir, trade-level kayıt üreten ve gerçek portföy kısıtlarıyla değerlendirilebilen bir araştırma altyapısı kurmaktır.

Sistem bileşenleri:

- `main.py`: CLI ve strateji seçimi.
- `config/settings.py`: JSON + argparse konfigürasyonu.
- `engine/backtest_engine.py`: veri, Cerebro, broker ve çıktı akışı.
- `engine/trade_journal.py`: trade entry/exit, R multiple ve exit reason kayıtları.
- `strategies/`: stratejiler.
- `output/`: backtest ve araştırma CSV'leri.
- `scripts/`: stratejiyi değiştirmeden çalışan araştırma/validation script'leri.

## 3. Mevcut aday strateji

Üretim adayı olarak adlandırılan strateji:

`leadership_expansion_v1`

Bu strateji long-only ve günlük timeframe içindir. Temel mantığı gelecekte kazanan olacak şirketi önceden tahmin etmek değildir. Son dönemde güç göstermiş ve trendi teknik olarak sağlam olan hisselerde, yukarı yönlü genişleme/kırılım sonrası trend devamını yakalamaya çalışır.

### Giriş koşulları

Tüm koşullar sağlanmalıdır:

- Hisse kapanışı EMA200 üzerinde.
- EMA200 eğimi pozitif.
- Hisse kapanışı EMA50 üzerinde.
- Hissenin 60 günlük getirisi SPY'ın 60 günlük getirisini en az %5 aşar.
- True Range, ATR14'ün 1.5 katından büyüktür.
- Kapanış, önceki 20 barın en yüksek kapanışının üzerindedir.
- Sinyal sonrası giriş bir sonraki barın açılışında yapılır.

Stratejide ayrıca leadership quality katmanı bulunur: RS60 koşuluna ek olarak `RS20 > 0` veya `RS120 > 10%`. Bu katmanın bilgi katkısı önceki araştırmada zayıf/neredeyse nötr çıkmıştı; bu nedenle gelecekte yeniden değerlendirilirse bunun yeni bir hipotez olarak yapılması gerekir.

### Pozisyon ve çıkış

- Başlangıç stopu: giriş fiyatının `1.5 * ATR14` altı.
- Trailing stop: kapanışın `2 * ATR14` altı; yalnızca yukarı taşınır.
- Kapanış EMA50 altına inerse `EMA_EXIT`.
- Trailing/initial stop'a çarparsa `ATR_TRAIL` veya `STOP`.
- Maksimum bekleme süresi strateji parametresine bağlıdır; kod varsayılanı 60 bar, genel config varsayılanı 40 bardır. Deneylerde bunun hangisinin kullanıldığı mutlaka raporlanmalıdır.
- Risk motoru işlem başına yaklaşık %1 risk hedefler.
- Maksimum eşzamanlı pozisyon: 3.
- Pozisyon büyüklüğü ATR stop mesafesine göre hesaplanır ve nakit ile sınırlandırılır.

## 4. Araştırma geçmişi ve sonuçlar

Test edilen ve zayıf bulunan yönler:

- SMA crossover: engine/baseline testi; edge kanıtı değil.
- Basit trend/pullback: çok düşük frekans ve zayıf sonuç.
- Genişletilmiş EMA pullback: trade sayısı arttı fakat robust edge oluşmadı.
- Mean reversion: robust pozitif edge gösterilmedi.
- EMA20 touch/proximity pullback: sağlam katkı göstermedi.
- Consolidation pullback: robust edge üretmedi.
- Basit momentum candle filtresi: çoğu testte faydasız veya zararlı.
- Leadership persistence (`RS20 > 0 OR RS120 > 10`): RS60 > 5% koşuluna eklenince neredeyse hiç yeni bilgi taşımadı.

Güçlü görünen bulgular:

- Relative Strength tekrar tekrar sinyal taşıdı.
- EMA200/EMA50 trend quality katkı verdi.
- Volatility expansion/breakout, pullback ailesinden daha umut verici aday oldu.
- Asset-level performans; yıllık volatilite, ATR yüzdesi, günlük range yüzdesi ve 60 günlük momentum ile güçlü korelasyon gösterdi.

Universe araştırmasında yüksek volatilite ve momentum hisselerinden oluşan alt evren daha iyi görünse de bunun hindsight selection ve örneklem riski vardır. Universe genişletme testinde 30 adayın 18'i pozitif Avg R gösterdi; bu yaklaşık %60'tır ve tek başına güçlü genelleme kanıtı değildir.

Walk-forward sonucu:

- 2021: pozitif.
- 2022: negatif ve belirgin başarısızlık.
- 2023: pozitif.
- 2024: pozitif.
- 4 pencereden 3'ü pozitif, fakat yalnızca dört pencere vardır.
- Median Avg R pozitif olsa da ortalama PF yaklaşık 1.46'dır; bu sonuç kesin doğrulama değildir.

Monte Carlo çalışması trade sırasının tek başına sonucu açıklamadığını gösterdi; ancak bu, underlying edge'in gerçek olduğunu kanıtlamaz. Monte Carlo mevcut trade dağılımını yeniden sıralar, veri-mining ve rejim/asset concentration riskini çözmez.

Portfolio/capacity araştırması:

- Yaklaşık 586 sinyalin 239'u çalıştırılmış, 347'si max position limit nedeniyle kaçırılmıştır.
- Sistem nakit sınırlı olmaktan çok slot sınırlıdır.
- Capacity günlerin yaklaşık üçte birinde doludur.
- Kaçırılan sinyaller çalıştırılanlardan belirgin şekilde kötü değildir.
- En iyi R işlemlerinin önemli kısmı kaçırılmıştır.
- Basit tek faktör ranking'leri current selection sürecini güvenilir biçimde aşamamıştır.

Follow-through araştırması, kazanan ve kaybedenlerin girişten sonraki ilk 1-3 günde ayrıştığını gösterdi. Bu bir entry filtresi olarak kullanılmamalıdır; aksi halde look-ahead bias oluşur. Ancak paper/live monitoring ve risk management araştırması için önemlidir.

## 5. Güncel 2026 bulgusu

Kullanıcı, 2025'ten warmup verisi alıp sadece 2026 başından 2026-07-20'ye kadar olan işlemleri sayarak şu evreni test etti:

`AAPL, AMD, AMZN, GOOGL, META, MSFT, NVDA, PANW, QQQ, SPY, TSLA`

Sonuç:

- 25 kapalı işlem.
- Toplam sembol bazlı net PnL: `+544.43 USD`.
- Başlangıç sermayesi varsayımı: `10,000 USD`.
- Kaba getiri: `+5.44%`.
- PANW: `+1319.59 USD`.
- AMD: `+106.01 USD`.
- AMZN: `-56.87 USD`.
- QQQ: `-75.99 USD`.
- META: `-125.68 USD`.
- AAPL: `-163.04 USD`.
- NVDA: `-204.92 USD`.
- GOOGL: `-254.67 USD`.
- MSFT, SPY, TSLA: kapalı işlem PnL'i 0.

Bu sonuç olumlu görünse de strateji doğrulaması değildir. Toplam kârın PANW tarafından taşınması, sonucun tekil sembol ve dönem yoluna bağımlı olduğunu gösterir. 25 işlem de küçük örneklemdir. Ayrıca bu çıktı sembol bazlı toplamdır; gerçek birleşik portföyde `max_positions=3`, nakit, aynı gün sinyal çatışmaları ve açık AAPL pozisyonu sonucu değiştirir.

Önemli karşılaştırma: geniş tarihsel asset testinde PANW yaklaşık 28 işlem, Avg R yaklaşık 0.04 ve PF yaklaşık 1.04 ile zayıf görünmüştür. Bu, 2026 PANW başarısının kalıcı PANW edge'i olduğunu kanıtlamaz; dönemsel trend devamı olabilir.

## 6. Gerçek stratejik yorum

Strateji şu soruya cevap vermiyor:

“Gelecek yıl hangi şirket kesin yükselecek?”

Şu soruya cevap vermeye çalışıyor:

“Son dönemde güçlüleşmiş, trendi bozulmamış ve yukarı kırılım yapan hisselerde hareket devam etme eğiliminde mi?”

Bu yaklaşım geleceği bilme gerektirmez; fakat bilinmeyen hisselerde istikrarlı pozitif expectancy üretmesi gerekir. Mevcut kanıt bunu henüz göstermiyor. Performansın yüksek momentumlu ve yüksek volatil hisselerde yoğunlaşması, botun her piyasa ortamında çalışan genel bir motor değil, belirli koşullarda çalışan koşullu bir continuation stratejisi olduğunu düşündürüyor.

Kullanıcının “bunu zaten kendim tahmin edebilsem gider yatırım yaparım” itirazı büyük ölçüde doğrudur. Sistem geleceği önceden bilseydi stratejiye ihtiyaç kalmazdı. Sistematik trading'in avantajı tahmin kesinliği değil; çok sayıda belirsiz durumda küçük bir istatistiksel avantaj bulmaktır. Bu projede şu an sorun, bu avantajın asset/dönem bazında yeterince stabil olduğunun kanıtlanmamış olmasıdır.

## 7. Yeni PM'in ilk yapması gerekenler

Öncelik yeni filtre eklemek değil, ölçümü düzeltmek ve kanıtı sağlamlaştırmaktır:

1. 2026 evrenini gerçek birleşik portföy olarak yeniden koştur: tek hesap, `max_positions=3`, nakit, komisyon, slippage, açık pozisyon ve equity curve dahil.
2. PANW dahil/hariç sonuçları karşılaştır; PANW hariç sistemin expectancy'sini raporla.
3. Aynı dönemde tüm sembolleri ex ante sabit evren olarak kullan; sonuçtan sonra kazanan sembolleri seçme.
4. Trade count, Avg R, expectancy, PF, max drawdown, exposure ve asset concentration raporlarını birlikte üret.
5. Kod ile araştırma script'lerinin aynı entry/exit, max holding ve warmup varsayımlarını kullandığını denetle.
6. Daha uzun ileri testte parametre ve evreni dondur; her kötü dönemde parametre değiştirme.
7. Paper trading'i yalnızca operasyonel doğrulama olarak sürdür; gerçek sermaye kullanma.

## 8. Kabul kriterleri

Kârlı bot iddiası için önceden yazılı kriter gerekir. Önerilen kriterler:

- Birleşik portföy bazında pozitif expectancy.
- Sonucun tek bir sembolün PnL'ine bağlı olmaması.
- Birden fazla out-of-sample döneminde pozitif sonuç.
- Kabul edilebilir max drawdown ve kapasite kullanımı.
- Komisyon/slippage sonrası PF'nin hâlâ anlamlı olması.
- En azından makul sayıda işlem; 25 işlem karar için yeterli değildir.
- Sonuçların asset ve zaman bazında tamamen parçalanmaması.

Bu kriterler sağlanmıyorsa risk modelini artırmak, daha fazla filtre eklemek veya kârlı sembolleri seçmek çözüm değildir; yeni hipotez gerekir.

## 9. Çalışma protokolü

- PM hipotezi ve deney tasarımını yazar.
- Kullanıcı kapsamı ve değişiklik onayını verir.
- Codder mevcut kodu inceleyip yalnızca onaylanan değişikliği uygular.
- Her deney için veri dönemi, warmup, timeframe, evren, parametreler, portföy kuralları ve maliyetler kaydedilir.
- Her sonuç “in-sample”, “out-of-sample”, “paper/forward” olarak etiketlenir.
- Bir sonuç pozitif diye edge ilan edilmez; concentration, sample size ve robustness kontrol edilir.
- Bir sonuç negatif diye hemen parametre değiştirilmez; önce veri, uygulama ve portföy hesabı doğrulanır.

## 10. Mevcut teslimatlar

Harici inceleme paketi:

- `external_review_package/`
- `external_review_package.zip`

Önemli proje dosyaları:

- `strategies/leadership_expansion_v1.py`
- `engine/trade_journal.py`
- `engine/backtest_engine.py`
- `config/settings.py`
- `output/`
- `scripts/`

Bu projenin mevcut durumu “kârlı bot tamamlandı” değildir. Daha doğru durum:

“Trade-level journal, araştırma ve validation altyapısı çalışan; Relative Strength + trend quality + expansion hipotezi bazı asset ve dönemlerde umut veren, ancak genellenebilirliği ve portföy düzeyindeki edge'i henüz kanıtlanmamış araştırma sistemi.”

Yeni PM bu çerçeveyi değiştirmeden, önce ölçüm ve forward validation disiplinini sağlamlaştırmalıdır.
