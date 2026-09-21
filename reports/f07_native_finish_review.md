# F07 native finish review

Bağımsız Codex native reviewer; fiziksel cihazı kontrol etmedi. Üç Mustafa iPhone ekran görüntüsü ve mobil kaynak incelendi.
İlk disposition: fix. Retry bağlantı başarısızlığında eski yanıtı siliyordu; sekmelerin selected/tab erişilebilirlik bilgisi eksikti.
Düzeltme sonrası kaynak review disposition: ship (yalnız bu iki bulgu için). Fiziksel kaynak/klavye/stream, hata ve VoiceOver gözlemi not_verified.

| Gereksinim | Kanıt |
|---|---|
| Retry hatasında kısmi metin ve kaynak korunur | `retry preserves previous text and citations through reconnect and early error` |
| Yeni yanıt eski metne eklenmez; yeni metin ve başarılı boş sonuç doğru değiştirilir | `retry replaces rather than duplicates text and uses new citations; successful empty answer clears old content` |
| Doğrulama | `npm test` 19 passed, `npm run typecheck`, `npm run lint`, iOS export exit0; f07_retry_fix_* raporları |

Dark native başlangıç ve teklif görüntülerinde kesilme bulgusu yok. Kaydırma görüntüsü viewport sınırıdır.
Yüzen dişli bu kaynakta yok; uygulama bileşeni olarak sınıflandırılmadı. Redesign gerekmiyor.
