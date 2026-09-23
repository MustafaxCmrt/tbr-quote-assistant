# Web paneli (React + Vite)

Yönetim ve satış demosu paneli. İş kuralı ve para hesabı içermez; teklif her zaman backend'den okunur.

| Ekran | İçerik |
|---|---|
| Teklif & sohbet | Müşteri ve teklif seçimi, SSE sohbet, kanonik teklif: kalemler, indirimler, toplamlar ve geçmiş (kaldırılan/değiştirilen) satırlar |
| Ürünler | Ürün listeleme ve ekleme |
| Bilgi bankası | Bilgi kaydı listeleme ve ekleme |
| İşlem kayıtları | Sohbet oturumları ve araç çağrıları: girdi, sonuç, kaynaklar, deneme ve receipt tekrarları |

## Çalıştırma

Panel Docker Compose ile gelir: `docker compose up --build -d --wait` sonrası http://localhost:5173
(kurulum: [kök README](../../README.md#hızlı-başlangıç)). Vite sunucusu `/api` isteklerini API
konteynerine iletir ve ürün/bilgi yazmaları için gereken `X-Admin-Key` başlığını **sunucu tarafında**
ekler. Anahtar `VITE_` önekli olmadığı için tarayıcı paketine girmez.

```sh
npm --prefix apps/web ci
npm --prefix apps/web run build     # tip kontrolü + üretim derlemesi
npm test                            # repo kökünde; web testleri apps/web/tests altında
```

## Davranış

- Teklif her 2,5 saniyede, pencereye dönüldüğünde ve her işlem veya yeniden deneme sonunda yeniden okunur;
  eski bir sürüm yenisinin üzerine yazılmaz. Bağlantı koparsa son görünüm ve son başarılı okuma zamanı kalır.
- Yeniden deneme aynı mesaj kimliğiyle yapılır; sunucu receipt sayesinde teklifi ikinci kez değiştirmez.
- Oturum kimliği tarayıcıda saklanır; fiyat veya miktar için istemci tarafında kalıcı bir kopya tutulmaz.

## Ortak sözleşme kopyaları

`src/contracts/` ortak `packages/contracts` paketinin kopyasıdır; Docker derlemesi yalnız `apps/web`
klasörünü gördüğü için gereklidir. Elle düzenlenmez: `python3 scripts/sync_web_contracts.py` üretir,
`--check` eşitliği doğrular (`npm test` bunu da çalıştırır).

Görsel dil ve renkler: [DESIGN.md](DESIGN.md).
