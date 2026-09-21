# F01a native smoke

Durum: **passed** — 2026-09-21, Mustafa fiziksel iPhone'da test edip “tamamdır dostum” diyerek ekran görüntüsü paylaştı.

- Test edilen kod commit'i: `cda7fa25dc1e803fc7d71cfa79a79db231d82450`; yalnız ignore'lu mobil .env güncel LAN adresine ayarlandı.
- İlk satır: `0.0 sn · Bağlantı çalışıyor ğüşiöç`.
- İkinci satır: `1.1 sn · İkinci parça ulaştı: ĞÜŞİÖÇ`.
- Son durum: **Tamamlandı**. Türkçe karakterler doğru; iki event'in ayrı alınma zamanları ekranda görünüyor.
- Kanıt: [iPhone ekran görüntüsü](images/f01a_iphone_stream.png), ekran saati 17:45.
- Platform: fiziksel iPhone / Expo Go. Tam cihaz modeli, iOS ve kurulu Expo Go sürümü kullanıcıdan alınmadı; **not_verified**. SDK 57 proje sürümüdür, cihaz sürümü yerine yazılmaz.
- Önceki engeller: Expo Go/CLI hesap girişi, Python için macOS gelen bağlantı izni ve mobil .env LAN adresi düzeltildi.
- Bu yalnız debug transport kanıtıdır; DB/tool mutasyonu veya web/mobil ortak teklif kanıtı değildir. F01b ve tam F01 kapısı açık.
