# The Blue Red — Yapay Zekâ Destekli Teklif Asistanı

B2B satış ekipleri için Türkçe teklif asistanı. Kullanıcı mobil sohbet ekranından ürün veya politika
sorusu sorar; sistem ürünleri ve bilgi kayıtlarını bulur, cevabını **kaynaklarıyla** verir ve gerektiğinde
aynı teklif taslağı üzerinde **gerçek, kalıcı** değişiklik yapar. Web yönetim paneli aynı teklifi anlık
olarak gösterir; ürün ve bilgi kayıtları buradan yönetilir.

- Altı zorunlu araç (`search_products`, `get_knowledge_entries`, `get_quote`, `add_to_quote`,
  `update_quote_item`, `replace_with_alternative`) gerçek PostgreSQL üzerinde çalışır; sahte veya mock mutasyon yoktur.
- Sohbet SSE ile akar: mesaj başlangıcı, araç çağrısı başlangıcı/sonucu, kaynaklar, metin parçaları ve bitiş/hata.
- Dil modeli anahtarı olmadan tam çalışır: yanıtlar retrieval tabanlı ve kaynaklıdır, harici model çağrılmaz.
- Fiyat üst limiti, stok ve bekleme (backorder) kuralları hem aramada hem de değişikliğin yazıldığı anda uygulanır.

## Mimari

```text
 Expo mobil (iPhone) ─┐                      ┌─ PostgreSQL 16
                      ├─ HTTP + SSE ─ FastAPI ┤   ürün, bilgi, teklif, kalem, receipt, araç logları
 React web paneli ────┘                      └─ Alembic migration + JSON seed (ilk açılışta)
```

Tek FastAPI servisi ve tek veritabanından oluşan modüler bir monolit. Teklifin tek doğruluk kaynağı
backend'dir: fiyat, indirim ve toplamlar sunucuda hesaplanır; web ve mobil aynı `GET /api/quotes/{id}`
cevabını gösterir, kendi başlarına tutar hesaplamaz.

| Katman | Teknoloji |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2 (async), Alembic, PostgreSQL 16 |
| Web | React, TypeScript, Vite |
| Mobil | Expo SDK 57 (React Native), Expo Go ile çalışır |
| Ortak sözleşme | `packages/contracts`: SSE ayrıştırıcı, olay ve teklif tipleri (web ve mobil aynı kodu kullanır) |
| Altyapı | Docker Compose |

## Hızlı başlangıç

Gereken: Docker Desktop (Compose v2) ve Python 3. Repo kökünde:

```sh
python3 scripts/init_env.py        # .env dosyasını güçlü rastgele parolalarla üretir (git dışında)
docker compose up --build -d --wait
```

| Adres | Ne var |
|---|---|
| http://localhost:5173 | Web paneli: teklif ve sohbet, ürünler, bilgi bankası, işlem kayıtları |
| http://localhost:8001/docs | API belgesi (Swagger) |
| http://localhost:8001/health/ready | Hazır olma kontrolü (migration ve seed tamamlanınca 200) |

İlk açılışta migration ve orijinal dataset otomatik yüklenir; API bunlar bitmeden başlamaz. Veriler
Docker volume'unda kalıcıdır. Durdurmak için `docker compose stop`; veriyi korumak için `down -v` kullanmayın.

## Mobil uygulama (Expo Go)

Gereken: Node 24 ve npm 11, iPhone'da App Store'daki Expo Go. Mac ve telefon aynı Wi-Fi ağında olmalı.

1. API'yi yerel ağa açarak başlatın:

   ```sh
   npm ci
   python3 scripts/init_env.py
   API_BIND_HOST=0.0.0.0 docker compose up --build -d --wait api web
   ```

2. `apps/mobile/.env` dosyasına Mac'in yerel IP adresini yazın (dosya git dışındadır):
   `EXPO_PUBLIC_API_BASE_URL=http://<MAC_LAN_IP>:8001`
3. Expo'yu başlatın ve terminaldeki QR kodu iPhone kamerasıyla okutun:

   ```sh
   npm start --workspace @tbr/mobile
   ```

4. Uygulamada müşteri ve teklif seçin (örneğin Mavi Kırmızı Market A.Ş. / Q-1001) ve
   `BlueScan Air 1 adet daha ekle.` yazın. Yanıt parça parça akar, kaynaklar görünür, Teklif sekmesinde
   adet artar; web panelinde aynı teklif aynı adet ve sürümü gösterir.

Demo bitince API'yi yeniden yalnız bu bilgisayara kapatın:
`API_BIND_HOST=127.0.0.1 docker compose up -d --no-deps --wait api`.

Bağlanamazsa sırayla kontrol edin: aynı Wi-Fi ve Expo Go'nun yerel ağ izni; iPhone Safari'den
`http://<MAC_LAN_IP>:8001/health/ready` açılıyor mu; `.env` adresi doğru mu ve Expo yeniden başlatıldı mı.

## Testler

Backend testleri ayrı bir test veritabanında, her test için taze migrate ve seed edilmiş PostgreSQL ile çalışır:

```sh
docker compose --profile test run --build --rm test
```

Son tam koşunun sonu ([tam çıktı](reports/backend_tests.txt)):

```text
1015 passed in 211.62s (0:03:31)
```

Kapsam:

- **22 golden senaryo** (`data/source/golden_test_scenarios.json`). Her senaryo gerçek sohbet uç
  noktasına gider; beklenen araç çağrıları, kaynaklar ve veritabanı durumu doğrulanır
  ([sonuç dosyası](reports/golden_results.json)). Beklenen çağrılar "en az bu sırayla" yorumlanır;
  ek okuma çağrısına izin vardır, ek yazmaya ve yasak çağrıya yoktur ([karar kaydı 0002](docs/decisions/0002-golden-beklenti-yorumu.md)).
- Retrieval ve kaynak doğruluğu, araç seçimi, add/update/replace mutasyonları, tekrar ve idempotency,
  fiyat/stok kuralları, anahtarsız yedek mod, eşzamanlı istekler, yetki ve gövde sınırı.
- Türkçe ifade çeşitleri için bağımsız denetimlerden gelen yüzlerce regresyon örneği. Belirsiz bir
  ifadede sistemin değişiklik yapmadan netleştirme sorduğu da test edilir.

İstemci ve teslim kontrolleri (repo kökünde, `npm ci` sonrası):

```sh
npm test                                   # ortak sözleşme, web ve mobil testleri
npm run typecheck && npm run lint
npm --prefix apps/web ci && npm --prefix apps/web run build
python3 scripts/check_delivery.py          # orijinal dataset bütünlüğü, depoda gizli değer/yerel veri taraması
```

## Tasarım kararları

### 1. Kaynak bulma: SQL + normalize edilmiş anahtar sözcük eşleşmesi

Ürünler PostgreSQL'den okunur ve Türkçe karakterleri katlanmış (`ş→s`, `ı→i`) metin üzerinden ad,
Türkçe alias, etiket, ürün kodu ve SKU ile eşleştirilir. Kategori, **fiyat üst limiti**, stok ve zorunlu
özellikler (QR, 2D, 58mm…) puan değil **kesin filtredir**. Bilgi kayıtları konu ve kelime eşleşmesiyle,
yalnız yürürlükteki aktif kayıtlar arasından seçilir.

Neden: veri küçüktür (48 ürün, 22 bilgi kaydı) ve iş kuralları kesindir. Embedding veya vektör veritabanı
eklemek açıklanabilirliği azaltırdı; fiyat ve stok kuralları olasılıksal bir benzerlik skoruna
bırakılmamalıdır. Yeni eklenen ürün ve bilgi kayıtları ek indeksleme gerekmeden anında aramaya katılır.

### 2. Araç çağrısı orkestrasyonu: deterministik planlayıcı

Türkçe mesaj, kural tabanlı bir niyet/slot planlayıcısıyla araç çağrısı planına çevrilir. Plan
veritabanına yazılır ve tek bir yürütücü gerçek araçları sırayla çalıştırır. Her çağrının girdisi,
sonucu, kaynakları ve sırası `tool_call_logs` tablosuna kaydedilir; web panelindeki "İşlem kayıtları"
ekranı bunları gösterir. Planlayıcı çalışırken senaryo kimliği veya golden mesaj eşlemesi kullanmaz;
kararlarını canlı katalog verisiyle verir.

Belirsiz bir istekte (hangi ürün, kaç adet, hangi fiyat sınırı olduğu kesinleşmiyorsa) değişiklik
yapılmaz, kullanıcıya netleştirme sorusu sorulur. Bu teslimde harici dil modeli bağlantısı yoktur.
Maliyet, güvenlik ve test edilebilirlik nedeniyle bilinçli bir tercihtir.

### 3. Yedek mod: ne garanti ediliyor

`OPENAI_API_KEY` tanımlı olmasa da (varsayılan budur) sistem eksiksiz çalışır:

- Hiçbir harici model çağrılmaz; her yanıtta bu `provider_calls=0` olarak kaydedilir.
- Politika ve uyumluluk cevapları gerçek `knowledge_id` kaynaklarıyla döner; kaynak uydurulmaz.
- Yanıt, yedek mod bilgi kaydını da kaynak olarak gösterir. Politika sorusu teklifi değiştirmez;
  emin olunamayan istekte mutasyon yapılmaz.
- Akış olayları aynıdır. Metin parçaları hazırlanmış cevabın bölünmesidir; model token akışı gibi sunulmaz.

### 4. Tekrarsızlık (idempotency)

- Anahtar **sunucuda** üretilir: teklif kimliği, mesaj kimliği, plandaki adım sırası ve araç adından
  SHA-256. İstemci veya planlayıcı dışı bir kaynak anahtar veremez; değiştirilmiş anahtar reddedilir.
- Her mutasyon, sonucu ile birlikte **aynı transaction içinde** `mutation_receipts` tablosuna yazılır.
  Teklif satırı `FOR UPDATE` ile kilitlenir; eşzamanlı istekler sıraya girer.
- Aynı mesaj yeniden gelirse (ağ kopması, SSE yeniden deneme) gerçek araç yine çağrılır ama receipt
  bulunduğu için teklif değişmez: log `replayed=true`, `mutation_applied=false` gösterir. Farklı mesaj
  kimliği bilinçli yeni bir işlemdir.
- "Toplam 5 adet olsun" gibi istekler hesaplandıkları teklif sürümüne bağlıdır. Arada teklif değişirse
  eski hesap uygulanmaz (HTTP 409).

### 5. Teklif mutasyon modeli

- **Ekleme:** aynı ürün için tek aktif satır vardır (kısmi benzersiz indeks); tekrar ekleme miktarı artırır.
- **Güncelleme:** yeni miktar yazılır; `quantity=0` satırı silmez, durumunu `removed` yapar.
- **Değiştirme:** eski satır `replaced` olur ve yeni satıra bağlanır; geçmiş korunur. Hedef ürün zaten
  teklifteyse miktarlar birleştirilir, iki aktif muadil satır oluşmaz. Hedef yalnız ürünün kayıtlı
  alternatiflerinden, stokta ve kurallara uygun olanlardan seçilir.
- Satıra eklendiği andaki birim fiyat saklanır (snapshot); sonraki katalog fiyat değişikliği eski teklifi
  değiştirmez. Her başarılı mutasyon teklif sürümünü bir artırır. Taslak teklif stok rezervasyonu yapmaz.
- Kurallar değişikliğin yazıldığı anda da kontrol edilir: fiyat üst limiti (birim liste fiyatı),
  stok, bekleme için müşterinin `allow_backorder` yetkisi **ve** açık kullanıcı onayı, Plus sürümün
  açıkça seçilmesi ve istenen zorunlu özellikler.
- İndirimlerin çakışması kaynak veride belirsizdi ve kararı adaya bırakıldı. Tercihim: indirimler
  toplanmaz, en özel tek kural uygulanır (örnek: Plus ürünlerde %6 hacim indirimi partner %7 ile toplanmaz).
  Gerekçe ve seçenekler: [karar kaydı 0001](docs/decisions/0001-indirim-cakismasi.md).

### 6. Bilinen sınırlamalar

Ayrıntı: [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md). Özetle:

- Türkçe dil desteği kural tabanlıdır. Desteklenmeyen bir ifade yanlış işlem yerine netleştirme sorusu
  üretir; bazı meşru cümlelerde bu soru gereksiz olabilir.
- `max_price_try` birim fiyat sınırıdır; toplam bütçe kontrolü yoktur (toplam bütçe yazılırsa sorulur).
- Kimlik doğrulama ve rol yetkisi yoktur; müşteri seçimi demo bağlamıdır. Uygulama yerel demo içindir.
- Harici dil modeli bağlantısı yoktur.

## Güvenlik

- **Gizli değerler depoda yoktur.** `.env`, `scripts/init_env.py` ile güçlü rastgele parolalarla
  üretilir ve `.gitignore`'dadır; `.env.example` yalnız yer tutucu içerir. `check_delivery.py`
  depoya girecek dosyalarda özel anahtar, sağlayıcı anahtarı, yerel IP ve kullanıcı yolu tarar.
- **Yönetim anahtarı tarayıcıya gitmez.** Ürün ve bilgi kaydı yazma uçları `X-Admin-Key` ister; web
  paneli bu başlığı sunucu tarafındaki Vite proxy'sinde ekler. Mobil uygulama ve tarayıcı anahtarı hiç
  görmez; anahtarsız yazma `401` döner.
- **Ağ yüzeyi dardır.** PostgreSQL'in portu dışarı açılmaz; API ve web varsayılan olarak yalnız
  `127.0.0.1` adresine bağlanır. Yerel ağ açılımı yalnız mobil demo için ve açıkça istenirse yapılır.
- **Veritabanı yetkisi sınırlıdır.** Uygulama, şema değiştiremeyen ayrı bir veritabanı kullanıcısıyla
  çalışır; migration ayrı adımda sahibinin yetkisiyle yapılır. Açılışta veri silen bir adım yoktur.
- **Güvenilir çalışma bağlamı.** Fiyat sınırı, bekleme onayı ve idempotency anahtarı istemciden
  alınmaz; sunucu mesajdan ve kalıcı plandan üretir. İstemci bu kontrolleri atlatamaz.
- **Girdi sınırları.** İstek gövdesi 256 KiB ile sınırlıdır. Beklenmeyen hatalarda iç ayrıntı veya
  exception metni döndürülmez; akış kontrollü bir `error` olayıyla biter. Bilgi kayıtlarındaki metin
  yalnız kaynak olarak gösterilir, komut olarak yorumlanmaz.
- Web servisi Vite geliştirme sunucusudur; public dağıtım için tasarlanmamıştır.

## API özeti

| Uç | Açıklama |
|---|---|
| `POST /api/chat/sessions` | Müşteri, teklif ve kanal ile sohbet oturumu açar |
| `POST /api/chat/stream` | Sohbet mesajı; SSE akışı döner (`POST /api/chat` aynı işlemin akışsız hâli) |
| `GET /api/chat/sessions/{id}/messages` | Oturum mesajları |
| `GET /api/tool-calls?session_id=…` | Araç çağrısı logları |
| `GET /api/quotes/{quote_id}` | Kanonik teklif (web ve mobilin ortak okuması) |
| `POST /api/tools/search_products`, `POST /api/tools/get_knowledge_entries` | Okuma araçları |
| `GET/POST/PATCH/DELETE /api/products`, `/api/knowledge` | Ürün ve bilgi kaydı listeleme/CRUD (yazma anahtar ister, silme mantıksaldır) |
| `GET /api/customers`, `GET /api/quotes` | Müşteri ve teklif listeleri |
| `GET /health/live`, `GET /health/ready` | Süreç ve hazır olma kontrolleri |

## Proje yapısı

```text
apps/api            FastAPI uygulaması: araçlar, planlayıcı, yürütücü, SSE, migration, testler
apps/web            React + Vite web paneli
apps/mobile         Expo mobil uygulama
packages/contracts  Web ve mobilin ortak SSE ayrıştırıcısı ve tipleri
data/source         Firmanın orijinal dataset'i (değiştirilmedi)
scripts             Kurulum, doğrulama ve teslim kontrol betikleri
reports             Test ve doğrulama kanıtları (açıklama: reports/README.md)
docs                Demo akışı ve karar kayıtları
```

## Sorun giderme

- **Port dolu veya ikinci bir kurulum gerekiyor:** aynı terminalde
  `export COMPOSE_PROJECT_NAME=tbr-ikinci API_PORT=18001 WEB_PORT=15173` verip kurulum komutlarını
  tekrarlayın. Ayrı volume ve ağ oluşur; mevcut veri etkilenmez.
- **Çok sayıda test koşusundan sonra `DiskFullError`:** testler teşhis için her test veritabanını
  saklar. Yalnız test veritabanındaki geçici DB'leri silmek için:

  ```sh
  docker compose --profile test up -d --wait test-db
  docker compose --profile test exec test-db sh -c "psql -U tbr_owner -d tbr_test -tAc \"select format('DROP DATABASE %I;', datname) from pg_database where datname like 'tbr\\_test\\_%'\" | psql -U tbr_owner -d tbr_test -q"
  ```

## Belgeler

[Bilinen sınırlamalar](KNOWN_LIMITATIONS.md) · [Yapay zekâ kullanımı](AI_USAGE.md) ·
[Karar kayıtları](docs/decisions/README.md) · [Demo akışı](docs/DEMO.md) ·
[Test kanıtları](reports/README.md)
