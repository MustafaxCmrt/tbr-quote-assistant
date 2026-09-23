# Demo akışı

Demo videosu yaklaşık 4 dakikadır ve aşağıdaki adımları sırayla izler. Adımlardaki cümleler temiz bir
kurulumda (seed verisi), tek veritabanında bu sırayla gerçek API üzerinden çalıştırılarak doğrulandı; beklenen sonuçlar tablodadır.
Aynı adımları kendi kurulumunuzda deneyebilirsiniz.

## Başlangıç

- Kurulum: [README → Hızlı başlangıç](../README.md#hızlı-başlangıç). Mobil için
  [README → Mobil uygulama](../README.md#mobil-uygulama-expo-go) (API yerel ağa açılır, telefon Expo Go ile bağlanır).
- Veritabanı ilk kurulumdaki seed durumunda olmalıdır; önceki denemeler miktarları değiştirmiş olabilir.
- Web: `http://localhost:5173` → **Teklif & sohbet**. Web, seçili teklifi 2,5 saniyede bir yeniler.
- Mobilde müşteri ve teklif, üstteki **Müşteri / teklif** düğmesiyle seçilir.

## Adımlar

| Süre | Nerede | Ne yapılır | Beklenen sonuç |
|---|---|---|---|
| 0:00–0:20 | README | Mimari şema | Tek FastAPI ve PostgreSQL; web ve mobil aynı teklifi okur. Dil modeli gerekmez: deterministik planlayıcı altı aracı çağırır. |
| 0:20–0:55 | Mobil: Ankara Toptan Depo Ltd. / Q-1002 (boş) | `9.000 TL altında, stokta olan kablosuz QR barkod okuyucu ekler misin?` | Cevap akarak gelir; kaynaklar `KNE-PRICE-001` ve `PRD-BC-110`. **Teklif** sekmesinde BlueScan Air 1 adet, 7.990 TL. Web'de aynı teklif aynı satırı gösterir. |
| 0:55–1:30 | Mobil: Mavi Kırmızı Market A.Ş. / Q-1001 (BlueScan Air 1 adet) | `Kablosuz barkod okuyucudan 1 tane daha ekle.`, ardından mesajın altındaki **Aynı isteği tekrar gönder** | İlk istek adedi 2 yapar. Tekrar gönderim "Tekrar algılandı; teklif değişmedi." der; adet ve sürüm aynı kalır. Web **İşlem kayıtları**nda ikinci `add_to_quote` için "Tekrar · değişiklik yok". |
| 1:30–1:45 | Mobil: aynı teklif | `Cep tipi RedScan Mini 2D okuyucu ekle.` | "İstenen ürün stokta yok… teklif değişmedi." Kaynak `KNE-STOCK-001`; stoklu aday olarak BlueScan Air gösterilir, eklenmez. |
| 1:45–2:10 | Mobil: Mavi Kırmızı Market A.Ş. / Q-1004 (BlueScan Pro Rugged, 12.950 TL) | `Rugged okuyucu çok pahalı; 9.000 TL altında stoklu alternatifle değiştir.` | BlueScan Air 7.990 TL aktif kalem olur; eski satır **Kalem geçmişi**nde "Değiştirildi". |
| 2:10–2:30 | Mobil: Q-1001 | `Aktive edilmiş yazılım lisansını iade edebilir miyiz?` | Kaynak `KNE-RET-001`: aktive edilmiş lisans iade kapsamında değil. Kaynak düğmesiyle kayıt açılıp kapanır; teklif değişmez. |
| 2:30–2:55 | Web: Ankara Toptan Depo Ltd. / Q-1002 | `Depo için 3 adet BlueScan Air ekle; partner indirimini de göster.` | 4 adet; partner indirimi `RUL-PARTNER-3` (%7) uygulanır, net 29.722,80 TL. İndirimler toplanmaz, en özel tek kural uygulanır ([karar kaydı 0001](decisions/0001-indirim-cakismasi.md)). |
| 2:55–3:45 | Web: **Ürünler** → **Ürün ekle**, sonra **Teklif & sohbet** | Yeni ürün: DemoScan Mini QR Kablosuz Okuyucu, SKU `TBR-DEMO-01`, marka The Blue Red, kategori Barkod okuyucu, 5500.00 TL, stok 10, özellikler `2d, qr, kablosuz`, arama adı `demoscan`. Ardından sohbete `6.000 TL altında stokta olan kablosuz QR barkod okuyucu öner.` Son olarak **Bilgi bankası** | Eklemeden önce bu fiyatın altında uygun ürün yoktur; kayıttan hemen sonra DemoScan önerilir. Ek indeksleme gerekmez; teklif değişmez. |
| 3:45–4:15 | Test kanıtları | [reports/README.md](../reports/README.md) | 1015 backend testi ve 22/22 golden senaryo; golden özet tablosu. |

## Anlatırken

- Metin SSE ile parça parça akar. Dil modeli yoktur; akan metin, araç sonuçlarından hazırlanan kaynaklı
  cevabın parçalarıdır ([bilinen sınırlamalar](../KNOWN_LIMITATIONS.md#akış-tekrar-ve-istemciler)).
- Her teklif değişikliği sunucuda tek bir transaction ve tekrarsızlık kaydıyla yapılır. Web ve mobil aynı
  kaydı sunucudan okur.
- Çalışma biçimi ve yapay zekâ kullanımı: [AI_USAGE.md](../AI_USAGE.md).

## Ek adımlar (süre kalırsa)

| Nerede | Ne yapılır | Beklenen sonuç |
|---|---|---|
| Mobil: Q-1001 | `BlueScan Air'den iki adet ekle.` | "Miktarı kesinleştiremedim. Adedi rakamla yazar mısın?… Teklifi değiştirmedim." Belirsiz ifadede sistem sorar, tahmin etmez. |
| Web: Mavi Kırmızı Market A.Ş. Pilot Şube / Q-2001 | `BlueScan Air Plus toplam 4 adet olsun, varsa hacim indirimini göster.` | Partner müşteride Plus hacim indirimi `RUL-PLUS-QTY` (%6) partner indiriminin önüne geçer; net 35.456,80 TL. |
| Web: Mavi Kırmızı Market A.Ş. / Q-1003 | `Ethernet fiş yazıcısını 4 adede çıkar.` | `update_quote_item`: BluePrint 80 Ethernet Fiş Yazıcı 2 → 4 adet. |
| Mobil: Q-1001 | `8K TL'ye kadar endüstriyel barkod okuyucu öner.` | "Fiyat sınırını kesinleştiremedim…"; arama ve öneri yapılmaz. |
