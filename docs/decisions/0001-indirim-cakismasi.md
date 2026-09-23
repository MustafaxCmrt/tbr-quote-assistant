# 0001 — İndirim çakışması: en özel tek kural uygulanır

**Durum:** accepted (21 Eylül 2026)

## Bağlam

`data/source/price_rules.json` altı indirim kuralı tanımlar, ama iki kural aynı kaleme uyduğunda ne
olacağını söylemez: toplanma (yığma) veya öncelik kuralı yoktur.

Bu durum golden senaryo SCN-019'da ortaya çıkar. Partner müşteri (`CUST-EXT-001`) 4 adet
`PRD-BC-110-PLUS` alır. Bu satır hem kategori bazlı partner indirimine (`RUL-PARTNER-3`, %7) hem de
Plus miktar indirimine (`RUL-PLUS-QTY`, %6) uygundur. Senaryo, "Plus miktar indirimi görünmelidir"
der ve `RUL-PLUS-QTY` kaynağını bekler.

Firmaya soruldu. Cevap "kendi belirlediğiniz akışta ilerleyebilirsiniz" oldu: bir kural verilmedi,
karar adaya bırakıldı. Bu kayıt bu nedenle **firma kuralı değil, aday tercihidir**.

## Seçenekler

| Seçenek | SCN-019 sonucu (brüt 37.720,00 TL) | Değerlendirme |
|---|---|---|
| a) İndirimler toplanır (%7 + %6) | İndirim 4.903,60; net 32.816,40 | Kaynakta dayanağı yok |
| b) En özel tek kural uygulanır (Plus %6) | İndirim 2.263,20; net **35.456,80** | Seçildi |
| c) En yüksek tek kural uygulanır (partner %7) | Plus indirimi görünmez | Golden beklentisini karşılamadığı için elendi |

## Karar

Her aktif kaleme en fazla **bir** kural uygulanır. Uygun kurallar şu sırayla denenir ve ilk uyan kazanır:

1. Paket ürünler (`RUL-BUNDLE-NO-STACK`) ve acil kurulum hizmeti (`RUL-SVC-URGENT`): kural gereği %0
2. Plus ürün, aynı üründen 4 ve üzeri adet (`RUL-PLUS-QTY`, %6)
3. Yazılım kombinasyonu: teklifte PRD-SW-520 ve PRD-SW-530 birlikte (`RUL-SW-BUNDLE`, %8)
4. Aksesuar, aynı üründen 5 ve üzeri adet (`RUL-ACC-5`, %5)
5. Partner müşteri, uygun kategoride 3 ve üzeri adet (`RUL-PARTNER-3`, %7)

## Neden

Golden senaryoyu karşılayan iki seçenekten (a ve b), kaynakta dayanağı olmayan toplamayı yapmayan ve
iş açısından daha temkinli olan (daha az indirim veren) seçildi. `RUL-BUNDLE-NO-STACK` kuralının adı,
başka kategorilerde toplamanın mümkün olabileceğine zayıf bir işarettir; kural sayılmadı.

## Sonuçlar

- Kural seçimi tek fonksiyonda toplanır (`apps/api/app/services/pricing.py`, `price_lines`). Firma farklı
  bir politika isterse değişiklik bu fonksiyonla ve testleriyle sınırlı kalır.
- Tanımsız veya eksik bir kural yapılandırılırsa hesap tahmin yürütmez, hata verir. Kural koşul metinleri
  kod olarak çalıştırılmaz.
- Doğrulama: `apps/api/tests/unit/test_pricing.py` (partner oranı daha yüksek olsa da Plus'ın özel kural
  olarak kazanması dahil) ve golden SCN-019 (net 35.456,80 TL).
