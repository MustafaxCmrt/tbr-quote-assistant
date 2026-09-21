# Claude Opus 5 / xhigh follow-up

Base commit: 313a486. Tools disabled, source review only.
Reported model IDs: claude-opus-5

# F08 odaklı takip incelemesi: 313a486

**Model:** claude-opus-5. Salt okunur kaynak izlemesi yapıldı. Hiçbir araç, komut veya test çalıştırılmadı. Çözüm kaydındaki test sonuçları yeniden doğrulanmadı. Seed değerleri verilen `products.json`, `quotes.json` ve `quote_items.json` dosyalarından alındı. `QuoteDTO`, `ReplaceInput`, admin ve tool endpoint'leri verilmediği için kapsam dışında kaldı.

## Orijinal bulguların durumu

| Madde | Durum | Gerekçe |
|---|---|---|
| P1-1 fiyat tavanı | **Kısmen çözüldü** | Listelenen dört cümle kapandı. "lira" ve "en fazla" sınıfı hâlâ açık (aşağıda). |
| P1-2 olumsuzlanan Plus/özellik | **Kısmen çözüldü** | Olumsuzlama tespiti sabit bir kelime listesine dayanıyor. Listede olmayan yaygın biçimler hâlâ Plus ekliyor. |
| P1-3 kanıtsız referans | **Kısmen çözüldü** | Kanıtsız dört cümle kapandı. Ancak cümlede kategori sözcüğü geçmesi tek başına "kanıt" sayılıyor. |
| P1-4 kısmi çıkarma | **Çözüldü** | `planner.py:244-252`: "N adet/tane" + çıkar/sil ya da miktarlı kaldır netleştirme istiyor. "adede" `(adet\|tane)\b` ile eşleşmediği için hedef miktar güncellemesi korunuyor. |
| Toplam hedef TOCTOU | **Çözüldü** | Plan, quote kilidi altında okunuyor (`chat.py:59-63,92`). Sürüm plana yazılıyor (`planner.py:338`). Her wrapper sürümü artırıyor (`mutations.py:232-237`). Kontrol, receipt replay'den sonra ve kilit altında yapılıyor (`mutations.py:216-230`). |
| Draft dışı teklif | **Çözüldü** | Üç mutasyon wrapper'ı da `receipt_operation` üzerinden geçiyor. Durum kontrolü (`mutations.py:223-224`) replay'den sonra geliyor. |

## Kalan doğrulanmış P1'ler

### P1-1 (devam): "lira" ya da "en fazla" ile yazılan tavan sessizce düşüyor

- **Konum**
  - `normalization.py:30`: tutar yalnızca `tl` sonekiyle yakalanıyor.
  - `normalization.py:41-44`: "en fazla" ve "ustune cikmadan" tavan belirteci sayılıyor.
  - Ancak `planner.py:202-205` içindeki `money_intent` listesinde bu belirteçler ve "lira" yok. İki liste birbiriyle tutarsız.
- **Tetikleyici** (Q-1002 / CUST-ANK-002):
  - `5.000 liraya kadar QR ve kablosuz okuyucu ekle.`
  - `En fazla 5.000 lira olan QR ve kablosuz okuyucu ekle.`
- **Gerçek:**
  - `amounts=[]` olduğu için `max_price_try=None`, `money_intent=False`.
  - Bu yüzden `planner.py:206` kontrolü atlanıyor.
  - Segmentasyon QR'ı okuyucuya bağlıyor. Tek aday PRD-BC-110 (7.990) seçiliyor ve guard tavansız geçiyor.
- **Beklenen:** Netleştirme istenmeli, receipt oluşmamalı.
- Çözüm kaydındaki "Desteklenmeyen para ifadesi açık TL sınırı sorar" ifadesi bu durumda doğru değil.

### P1-2 (devam): Listede olmayan olumsuzlamalar Plus'ı "açık seçim" yapıyor

- **Konum**
  - `planner.py:211`: yalnızca `olmasin|olmayan|degil|plus[ -]?siz` yakalanıyor.
  - `planner.py:219`: `"plus"` token'ı `explicit_plus=True` yapıyor.
  - `retrieval.py:77,93`: Plus olmayan satırlar eleniyor.
  - `mutations.py:29`: guard bu nedenle geçiliyor.
- **Tetikleyici** (Q-1001):
  - `BlueScan Air ekle, Plus olmadan.`
  - `Plus istemiyorum, BlueScan Air ekle.`
  - `Plus'suz BlueScan Air ekle.` Normalize sonrası "plus suz" oluyor, regex yalnızca "siz" arıyor.
- **Gerçek:** Model eşleşmesi {BC-110, BC-110-PLUS} içinden `plus_requested` ile yalnızca PLUS kalıyor. PRD-BC-110-PLUS (9.430) yeni satır olarak commit ediliyor.

### P1-3 (devam): Kategori sözcüğü, fiilin nesnesi ürün olmasa da referans sayılıyor

- **Konum**
  - `planner.py:75`: yalnızca `cat` bulunması aday tutmaya yetiyor.
  - `planner.py:35`: kategori alt dize olarak aranıyor ("okuyucunun" içinde "okuyucu" bulunuyor).
  - `planner.py:182-183`: fiil cümlenin herhangi bir yerinde aranıyor.
  - `planner.py:278-289`: hedef yoksa ilk stoklu alternatif seçiliyor.
- **Tetikleyici** (Q-1001):
  - `Okuyucunun teslim tarihini değiştir.`
    - Gerçek: BC-110, PRD-BC-120 ile değiştiriliyor (12.950 TL; kaybedilen özellikler: bluetooth, kablosuz, qr).
  - `Okuyucu indirimini kaldır.`
    - Gerçek: BC-110 `removed` oluyor ve yanıt "kalıcı olarak kaydedildi" diyor.
  - Daha zayıf örnek: `Endüstriyel okuyucuyu kaldır.` BC-110 endüstriyel olmadığı hâlde siliniyor.
- Çözüm kaydındaki "brand/model ile pozitif referans gerekir" ifadesi kodla uyuşmuyor. Kategori ya da FEATURE eşleşmesi tek başına yetiyor.

### Önerilen regresyonlar

- Yukarıdaki cümleleri mevcut `test_review_price_expression_never_silently_drops_ceiling` ve `test_review_unsupported_or_unmatched_intent_clarifies_without_mutation` testlerine parametre olarak ekleyin. Beklenen: receipt 0, teklif aynı.

### Düzeltme yönü

- **Para:** Tek bir para belirteci kümesi kullanın: `tl|₺|lira|try` + `kadar|en fazla|ustune cikmadan|…`. `numeric_slots` belirteçleri, `money_intent` kümesinin alt kümesi olmalı.
- **Plus:** Olumsuzlama kümesini genişletin (`olmadan|haric|istemiyorum|disinda|plus[ -]?s[iu]z`). Daha sağlamı: mutasyon mesajında "plus" yalnızca açık PLUS ID/SKU'su ya da "<model> plus" kalıbıyla birlikte geçiyorsa kabul edin.
- **Referans:** Çözüm yalnızca kategoriye dayanıyorsa ve cümlede eşleşmeyen bir içerik nesnesi kalıyorsa (indirim, teslim, tarih, fiyat …) netleştirme isteyin.

## Düzeltmelerin getirdiği regresyon

Düzeltmelerin getirdiği bir P0/P1 bulunmadı.

- Yeni planner kontrolleri (para, olumsuzlama, "daha ucuz", eşitlik durumunda `unique_choice`, marka/model filtresi) yalnızca netleştirme yönünde çalışıyor.
- Eşanlam normalizasyonu yalnızca sert filtre ekliyor.
- `expected_quote_version`, receipt hash'ine ve public input'a girmiyor.
- `render` içinde iddialar ile kaynaklar aynı tool çıktısından türetiliyor. Başarılı bir akışta SOURCE_NOT_GROUNDED'a düşülmüyor.

## Doğrulanmamış hipotezler

1. **Miktarlı replace (P1-4'ün kardeşi).**
   - `mutations.py:140-142,171-175`: kaynak satır tamamen `replaced` işaretleniyor, hedefe `args.quantity` yazılıyor.
   - Senaryo: `5 adede çıkar` ardından `Kablosuz okuyucuyu 1 adet değiştir.` Sonuç: 5 adet → 1 adet BC-120.
   - Bunun bulgu olup olmadığı `ReplaceInput.quantity` sözleşmesine bağlı; sözleşme verilmedi.
2. **Sürüm artışının kapsamı.** TOCTOU guard'ı, `quote_items`'a yapılan her yazmanın `receipt_operation`'dan geçtiğini varsayıyor. Admin/tool endpoint'leri ve `QuoteDTO.status/version` alanları verilmediği için doğrulanamadı.
3. **"Süresi geçmiş" teklif.** `quotes.json`'da geçerlilik alanı yok. Yalnızca `status != draft` kontrolü doğrulanabildi.

## Karar

- **F08 bu hâliyle kabul edilmemeli.**
- Kalan 3 doğrulanmış P1, orijinal P1-1, P1-2 ve P1-3'ün kısmen kapatılmış sınıflarıdır. Düzeltmeler test edilen cümleleri kapatıyor ama sabit listeye dayalı bu fail-open sınıfını kapatmıyor.
- P1-4, toplam hedef TOCTOU'su ve draft hipotezi kaynak izlemesiyle kapanmış görünüyor.
- Hiçbiri çalıştırılarak doğrulanmadı.