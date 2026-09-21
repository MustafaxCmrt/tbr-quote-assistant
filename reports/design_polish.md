# Teslim öncesi görsel düzenleme — logo, palet, tutarlılık, responsive

22 Eylül 2026. Mustafa'nın isteğiyle, PDF'in istemediği ama demo kalitesine giren dar bir görsel
düzenleme yapıldı. Kapsam bilinçli olarak sınırlı: yeni kütüphane, animasyon, ekran yapısı veya akış
değişikliği yok; web'e karanlık tema eklenmedi (mobil zaten sistem temasını izliyordu). API,
sözleşme (`packages/contracts`) ve backend dokunulmadı.

## Değişiklikler

| Alan | Değişiklik |
|---|---|
| Logo | Firmanın sitesindeki footer logosu (`logoFooter-*.png`, 11982×2218) kırpılıp 1192×215'e ölçeklendi. Logodaki beyaz "the" açık yüzeyde görünmediği için açık yüzey varyantında mürekkep rengine (#172840) boyandı; koyu yüzey varyantı orijinal. Web: `apps/web/src/assets/bluered-logo.png` (Vite bundle'a girer, Dockerfile değişmedi). Mobil: `apps/mobile/assets/bluered-logo-{light,dark}.png`, `Logo` bileşeni sistem temasına göre seçer |
| Palet | İşlem mavisi logonun tonuna hizalandı: web `--blue` #184ca3 → #0a67a8 (beyaz metinle 5.97:1; logonun kendi #0a8ad0'ı 3.8:1 kaldığı için koyultuldu), `--red` #a92438 → #c8171d, alan kenarlığı #aebccb (1.93:1) → #8797ad (2.97:1). Mobil açık tema mavi #0A67A8, koyu tema #6FC0FF (koyu tint üzerinde 6.4:1). `style.css`'teki tüm sabit renkler `:root` token'ına taşındı |
| Tutarlılık | Web: `.text-button` hover alt çizgi; işlem kayıtları listesi köşeli panel; favicon (iki renkli SVG data URI) ve `theme-color`/`description` meta. Mobil: teklif kalemleri toplam kartıyla aynı yüzey kartı, ürün adı `subheading` (17/600), SKU ve durum tek satır; başlık ölçeği 30 → 28 |
| Responsive (web) | ≤700px'te gezinme yatay kaydırma yerine 2×2 ızgara (önceden 4. sekme ekran dışına taşıyordu). Tablolar yeni `TableScroll` bileşeninde: sağda görünmeyen sütun varken kenar solar, sığınca veya sona kaydırılınca solma kalkar (ResizeObserver + scroll). Sidebar alt yazısı iki satıra sarmayacak şekilde kısaltıldı |

Denenip geri alınan: saf CSS "scroll shadow" (`background-attachment: local`) tekniği. 1024px ve
üstünde tablo taşmadığı halde Chrome'da gri şerit bıraktı; ölçüm `scrollWidth == clientWidth` gösterdi.
Bunun yerine JS ile ölçen bileşen kullanıldı.

## Doğrulama

| Kontrol | Sonuç |
|---|---|
| [Web build (tsc + vite)](design_web_build.txt) | exit0 |
| [Typecheck (mobil + contracts)](design_typecheck.txt) | exit0 |
| [Lint (mobil, contracts, web)](design_lint.txt) | exit0 |
| [İstemci testleri](design_clients.txt) | 22/22 passed, exit0 |
| [Expo iOS export](design_expo_export.txt) | exit0; `dist/assets` altında iki logo PNG (1192×215 RGBA) bundle'a girdi |
| [Teslim taraması](design_delivery.txt) | exit0 |
| Web container yeniden build (`docker compose up -d --build --wait web`) | Healthy; ana demo API/DB dokunulmadı |
| Tarayıcı ölçümü (Playwright + yerel Chrome, 1440/1024/768/375, dört sayfa) | Yatay sayfa taşması yok, konsol hatası yok (önceki tek hata favicon 404 idi) |

Ekran görüntüleri `images/design/`: `before-*` ve `after-*` aynı sayfa/genişlik; `after-quote-375-scrolled`
tablonun sona kaydırılmış hali (solma kalkıyor); `after-quote-chat-1440` sohbet paneli.

**Kontrast (WCAG, hesaplanan):** işlem mavisi/beyaz 5.97; mavi/tint 5.19; kırmızı/beyaz 5.84;
alan kenarlığı/beyaz 2.97; koyu tema mavi/tint 6.40; koyu tema ikincil metin/yüzey 8.74.

## Fiziksel iPhone gözlemi

**passed (kullanıcı gözlemi).** 22 Eylül 01:45 civarı (TR): Mustafa Expo Go'da yeni bundle'ı açtı;
logo üst çubukta ve teklif kalemleri kart görünümünde geldi. İlk denemede "sunucuya ulaşılamadı"
aldı: web container'ı `API_BIND_HOST` öneki olmadan yeniden build edilince Compose API'yi loopback
ile yeniden oluşturmuştu (`127.0.0.1:8001`). `API_BIND_HOST=0.0.0.0 docker compose up -d --wait api`
ile LAN'a döndürüldü; Q-1001 sürüm 3 / 23.970 TL değişmedi. README LAN adımına uyarı eklendi.
Karanlık/açık tema karşılaştırması ve simülatör görüntüsü alınmadı.

## Doğrulanmayan

Export yalnız bundle'ın derlendiğini ve logoların pakete girdiğini gösterir; cihaz gözlemi
yukarıdaki kadardır, ekran görüntüsü yoktur. Web'de otomatik erişilebilirlik taraması yapılmadı;
kontrast değerleri hesapla doğrulandı, ekran okuyucu ile denenmedi.
