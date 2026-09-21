# Independent Claude source review

Requested model: claude-opus-5; effort: xhigh. Tools disabled; no reviewer test execution. Base commit b367c61.
Reported model IDs: claude-opus-5

# F08 bağımsız inceleme: b367c61

## Kapsam

- Yalnızca verilen satır numaralı kaynaklar incelendi. Hiçbir komut veya test çalıştırılmadı.
- Aşağıdaki "doğrulanmış" bulgular kod yolu satır satır izlenerek elde edildi.
- Seed değerleri için yalnızca testlerde görünen bilgiler kullanıldı:
  - Q-1001'de tek aktif kalem var: PRD-BC-110 (BlueScan Air, 7.990 TL, stok 18, `kablosuz` etiketli).
  - PRD-BC-110-PLUS (BlueScan Air Plus) aktif ve stoklu.
- Migration, `database.py`, `readiness`, istemciler ve price_rules dışındaki seed JSON'ları verilmedi.

## Doğrulanmış bulgular (öncelik sırasıyla)

### P1-1: Açık fiyat tavanı tanınmayan biçimde yazılırsa sessizce düşüyor

- **Konum**
  - `apps/api/app/services/normalization.py:23`: tutar yalnızca "TL" sonekiyle yakalanıyor.
  - `apps/api/app/services/normalization.py:34-37,40`: belirteç listesinde "kadar", "aşmayan/geçmeyen", "₺" yok.
  - `apps/api/app/orchestration/planner.py:162-172`: tutar veya belirteç görülüp tavan kurulamazsa netleştirme istenmiyor.
  - `apps/api/app/services/mutations.py:31-35`: tavan `None` olunca kontrol yapılmıyor.
- **Tetikleyici** (Q-1002 / CUST-ANK-002): `5.000 TL'ye kadar QR ve kablosuz okuyucu ekle.`
- **Beklenen:** Tavan 5.000 uygulanır, PRD-BC-110 (7.990) elenir. Değişiklik olmaz ya da netleştirme istenir.
- **Gerçek:**
  - `amounts=["5.000"]` bulunuyor ama `ceiling=False`, dolayısıyla `max_price_try=None`.
  - Aynı özellik seti `apps/api/tests/test_chat.py:239-245`'te PRD-BC-110'u seçiyor.
  - Sonuçta `add_to_quote` PRD-BC-110 fiyat kontrolü olmadan commit ediliyor.
- **Aynı sınıf:** `5 bin TL altında …` (belirteç var, tutar ayrıştırılamıyor), `5.000 ₺ altında …`, `5.000 TL'yi aşmayan …`.
- **Regresyon:** Bu cümleleri parametrize et. Beklenen: ya `trusted_constraints.max_price_try == "5000"` ile guard reddi, ya da receipt sayısı 0 ve teklif değişmemiş. Kural: tutar ya da karşılaştırma belirteci varsa ve tavan kurulamadıysa mutasyon adımı üretilmemeli.

### P1-2: Olumsuzlanan Plus veya özellik "açık seçim" sayılıyor

- **Konum**
  - `apps/api/app/orchestration/planner.py:164`: `"plus" in tokens` doğrudan `explicit_plus=True` yapıyor.
  - `apps/api/app/services/retrieval.py:77,92-94`: `plus_requested` yalnızca Plus satırlarını bırakıyor.
  - `apps/api/app/services/mutations.py:29`: guard bu nedenle geçiliyor.
  - "olmasın/değil/-sız" negasyon listesinde yok: `apps/api/app/orchestration/planner.py:137-141`.
- **Tetikleyici** (Q-1001): `BlueScan Air ekle, Plus olmasın.`
- **Beklenen:** BC-110 +1 ya da netleştirme. Plus eklenmez.
- **Gerçek:**
  - BC-110, `is_plus != plus_requested` koşuluyla eleniyor.
  - Yerine PRD-BC-110-PLUS öneriliyor ve yeni satır olarak ekleniyor (min. sipariş karşılandığı varsayımıyla).
- **Aynı sınıf:** `Plus'sız BlueScan Air ekle`. `kablosuz olmayan okuyucu ekle` cümlesinde `kablosuz` zorunlu etikete dönüşüyor (`planner.py:327`, `retrieval.py:65`).
- **Regresyon:** Bu cümlelerde Plus veya olumsuzlanan etikete sahip ürün için receipt oluşmamalı.

### P1-3: Kanıtsız kalem çözümü, tek kalemli teklifte ilgisiz komutları mutasyona çeviriyor

- **Konum**
  - `apps/api/app/orchestration/planner.py:64-67`: tek aday skor 0 olsa bile döndürülüyor.
  - `:241`: herhangi bir "daha" token'ı referans niyeti sayılıyor.
  - `:242`: "ayni" alt dize olarak aranıyor.
  - `:252-273`: bu çözümden update/add üretiliyor. `:194-236`'daki replace de aynı çözücüyü kullanıyor.
- **Tetikleyiciler** (Q-1001):
  - `İndirimi kaldır.` Kategori `None`, tek aday var. `update_quote_item qty=0` çalışıyor, BC-110 `removed` oluyor. Yanıt "kalıcı olarak kaydedildi" diyor (`apps/api/app/orchestration/templates.py:42`).
  - `Daha ucuz bir okuyucu ekle.` BC-110 miktarı 1'den 2'ye çıkıyor.
  - `RedScan'den 1 tane daha ekle.` Teklifte RedScan yok, ama BlueScan Air +1 ekleniyor.
  - `Teslim tarihini değiştir.` BC-110'un stoklu kayıtlı alternatifi varsa replace çalışıyor (veriye bağlı).
- **Test boşluğu:** `apps/api/tests/test_chat.py:47` yalnızca `Bunu çıkar.` cümlesini deniyor. Bu cümle de miktar eksik olduğu için `planner.py:187`'de duruyor ve çözücüye hiç ulaşmıyor.
- **Regresyon:** Dört cümle için Q-1001'de receipt 0 ve teklif değişmemiş olmalı.
- **Düzeltme yönü:** ID/SKU, model adı, kategori veya özellik eşleşmesinden pozitif kanıt şartı koy. "daha" yalnızca "N tane/adet daha" kalıbında kabul edilsin.

### P1-4: "-dan N adet çıkar/sil" eksiltme yerine hedef miktar ya da tam silme oluyor

- **Konum**
  - `apps/api/app/services/normalization.py:24-26`: "adet" ile "adede" aynı ele alınıyor.
  - `apps/api/app/orchestration/planner.py:143-145,256`: sonuç ya hedef miktar ya da tam silme.
- **Tetikleyici** (Q-1001): Önce `Kablosuz okuyucuyu 5 adede çıkar.`
  - Sonra `Kablosuz okuyucudan 2 adet çıkar.` Beklenen 3 ya da netleştirme. Gerçek: miktar 2 oluyor.
  - Sonra `Kablosuz okuyucudan 2 adet sil.` Beklenen 3. Gerçek: kalem tamamen `removed` oluyor.
- **Regresyon:** Bu iki cümlede miktar 2'ye düşmemeli ve kalem `removed` olmamalı.

## Doğrulama gerektiren belirsiz konular

1. **Teklif durumu (olası P1).**
   - `apps/api/app/services/executor.py:62-74` ve `apps/api/app/services/mutations.py:187-252` `quotes.status` alanını hiç kontrol etmiyor.
   - Sözleşme ise "taslak teklife ekler" diyor.
   - Seed'de draft dışı ya da süresi geçmiş bir teklif varsa, o teklife mutasyon kabul edilir. Seed'deki `quotes.status` değerleri kontrol edilmeli.
2. **"toplam … olsun" TOCTOU (olası P1).**
   - Delta planlama transaction'ında hesaplanıyor (`planner.py:261`, `chat.py:46-106`). Uygulama ise sonraki transaction'da göreli bir `add` olarak yapılıyor.
   - Test: Aynı teklife paralel iki farklı message_id ile `Kablosuz okuyucu toplam 5 adet olsun` gönder. Sonuç 5 yerine 9 olursa bulgu doğrulanır.
   - Araya değişiklik giren failed→retry akışı da hedefi aşabilir.
3. **Ekleme yolunda eşitlik kontrolü yok.**
   - `planner.py:326-327` doğrudan `recommendations[0]` seçiyor. `planner.py:65`'teki eşitlik reddi burada uygulanmıyor.
   - `Barkod okuyucu ekle` eşit skorlu adaylardan en ucuzunu seçebilir (`retrieval.py:124`). Sonuç alias ve etiket verisine bağlı.
4. **FEATURES dışı özellik yazımları.**
   - `Wi-Fi` "wi-fi" olarak normalize ediliyor ve "wifi" ile eşleşmiyor. `USB C` ve `çevrimdışı` da zorunlu etikete dönüşmüyor (`retrieval.py:19-32,65`).
   - P1-1 ile aynı fail-open sınıfı. Etikete bağlı olarak yanlış ürün eklenebilir.
5. **Migration verilmedi.**
   - `apps/api/app/persistence/models.py:138-144`'teki kısmi unique index ve CHECK kısıtlarının runtime DB'de gerçekten var olduğu doğrulanmalı.

## Kalan sınırlamalar (P2 / belgeli)

- **Kaynak doğrulaması boş:** `templates.py:61-62`'deki `bundle.require(list(sources))` totolojik, SOURCE_NOT_GROUNDED hatasına hiç ulaşılamıyor. Kaynak garantisi yalnızca yapıdan geliyor (`chat.py:112-126`, attempt log'ları). Garanti doğru ama kontrol hiçbir şey sınamıyor.
- **Karar aramaları loglanmıyor:** Kararı veren planlama aramaları kaydedilmiyor (`planner.py:128`), log'daki arama yeniden çalıştırmadır. Persist edilen notice retry'da tekrar yayınlanıyor (`chat.py:85`) ve güncel log'la çelişebilir.
- **Yeni canlı ürünler sohbetten bulunamayabilir:** `planner.py:31` seed marka adlarını sabit kodluyor. Okuma yolu da kategori ya da ID şartı koşuyor (`planner.py:179-182`). Yeni markalı canlı ürün, kategori kelimesi olmadan yazılırsa sohbetten bulunamaz. Tool endpoint'i ise bulur.
- **Runtime'da senaryo eşleşmesi yok:** Senaryo ID'si veya tam mesaj eşleşmesi görülmedi. `pricing.py:37` kural koşulundaki ID'leri sabit kodluyor; DB'deki condition değişirse bunun etkisi olmaz.
- **Bekleme onayı mesaj geneli:** Onay (`planner.py:165-170`) gruptaki her stoksuz ürüne uygulanıyor.
- **action_key session_id içermiyor** (`execution_context.py:31-34`): Aynı message_id farklı oturumlardan gelirse IDEMPOTENCY_CONFLICT oluşuyor. Bu fail-closed bir sonuç.
- **Auth yok** (`KNOWN_LIMITATIONS.md:7-8`): `admin.py:280-295`, `/api/customers` ve `/api/quotes` ile herhangi bir teklif bulunup mutasyon yapılabilir. Oturum/teklif eşleşmesi tutarlılık kontrolüdür, yetkilendirme değildir. Belgeli ve kabul edilmiş.
- **Testler çıkarımı sınamıyor:** Guard testleri (`test_mutations.py:190-206,390-405,489-509`) kısıtları doğrudan enjekte ediyor. Bu, enforcement'ı kanıtlar ama çıkarımı kanıtlamaz; dört P1'in hepsi çıkarım katmanında. Golden22 sabit ifadeler kullandığı için bunları yakalayamaz.

## Karar

- Kaynak izlemesiyle 4 P1 doğrulandı. Hiçbiri çalıştırılarak doğrulanmadı.
- Hepsi planner'ın belirsiz, olumsuzlanmış ya da tanınmayan girdide fail-open davranmasından kaynaklanıyor.
- Executor, receipt replay, kilit sırası, atomiklik ve bağlam eşleşmesi katmanlarında P0/P1 bulunmadı. Bu, tüm kusurların yokluğu anlamına gelmiyor.
- **F08 bu hâliyle kabul edilmemeli.** Kabul için:
  1. Dört P1 fail-closed hâle getirilmeli: tanınmayan fiyat, olumsuzlama veya kanıtsız referans durumunda netleştirme istenmeli, mutasyon adımı üretilmemeli.
  2. Yukarıdaki odaklı regresyonlar gerçek PostgreSQL'de koşulmalı.
  3. Belirsiz 1 ve 2 veri kontrolü ve eşzamanlılık testiyle kapatılmalı.
