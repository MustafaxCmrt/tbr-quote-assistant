# 0002 — Golden senaryolarda beklenen çağrı ve kaynak listelerinin yorumu

**Durum:** accepted (21 Eylül 2026)

## Bağlam

`data/source/golden_test_scenarios.json` her senaryo için `expected_tool_calls` ve `expected_sources`
listeleri verir. Bazı senaryolar bir bilgi kaydını kaynak olarak bekler, ama o kaydı getirecek
`get_knowledge_entries` çağrısı beklenen çağrılar arasında yoktur:

| Beklenen kaynak | Senaryolar |
|---|---|
| `KNE-PRICE-001` | SCN-001, SCN-005, SCN-020 |
| `KNE-IDEMP-001` | SCN-003, SCN-010, SCN-013 |
| `KNE-STOCK-001` | SCN-006, SCN-014, SCN-022 |

Çağrı listesi "tam olarak bu" diye okunursa bu kaynaklar ya hiç gösterilemez ya da gerçek bir araç
sonucu olmadan etikete eklenmesi gerekir. İkincisi kaynaksız cevap üretmek demektir; PDF'te
diskalifiye sebebidir.

Firmaya soruldu; tam eşitlik şartı konmadı ve karar adaya bırakıldı. Bu kayıt bu nedenle aday
tercihidir.

## Karar

- `expected_tool_calls` **en az bu sırayla** yorumlanır: beklenen çağrılar gerçek loglarda aynı sırayla
  bulunmalıdır. Aralarda ek **okuma** çağrılarına (örneğin kaynak için bilgi kaydı okuma) izin verilir.
- Mutasyon çağrıları **tam** eşleşmelidir: beklenmeyen hiçbir `add_to_quote`, `update_quote_item` veya
  `replace_with_alternative` kabul edilmez.
- `must_not_call` ve `must_not_recommend` **mutlaktır**.
- `expected_sources` **en az bu küme** olarak yorumlanır: ek ilgili kaynak gösterilebilir, ama yanıttaki
  her kaynak aynı denemenin gerçek araç sonuçlarından gelmek zorundadır.

## Neden

Kaynak gösterme zorunluluğu ancak gerçek okuma çağrılarıyla kanıta dayanabilir. Ek okumalara izin
vermek teklifi değiştirmez; ek yazmalara izin vermemek ise yan etkisiz davranışı korur.

## Sonuçlar

- Golden koşucusu (`apps/api/tests/golden/test_chat_golden.py`) her senaryoyu taze seed'li veritabanında
  gerçek sohbet uç noktasından geçirir ve şunları doğrular: çağrıların sırası, mutasyon listesinin
  tam eşitliği, yasak çağrılar, kaynakların gerçek araç sonucundan gelmesi, teklifin son durumu, stok
  miktarlarının ve diğer tekliflerin değişmemesi, yedek mod ve `provider_calls=0`.
- Sonuç dosyası her senaryo için gerçek araç listesini gösterir; ek okuma çağrıları orada açıkça görünür
  ([son sonuç](../../reports/reaudit4_fix_final_golden.json)).
- Firma tam eşitlik bekliyorsa ek okumalar fark olarak görünür; bu risk bilinerek kabul edildi.
