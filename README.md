# The Blue Red — Teklif Asistanı

Hedef: kaynaklı Türkçe chat, altı gerçek tool ve web/mobil ortak kalıcı teklif durumu.
**23 Eylül 2026: dördüncü yeniden denetimin (90/100) W01–W03 P1 grupları, W04/UX11–UX13 bulguları ve 91 denemesi HTTP/DB regresyonlarıyla kapatıldı. B10 ve U10 belgeli sınır olarak açık; F09 fiziksel prova/video/teslim açık.**
Altı gerçek araç, transaction/receipt, kaynaklı deterministik sohbet, SSE, web admin ve Expo
uygulaması çalışıyor. Son tam backend koşusu **1015 passed** (22 golden dahil):
[komut/çıktı](reports/reaudit4_fix_final_backend.txt), [golden sonuçları](reports/reaudit4_fix_final_golden.json).
Dördüncü yeniden denetim düzeltmeleri: [çözüm kaydı](reports/reaudit4_fix_resolution.md); üçüncü:
[çözüm kaydı](reports/reaudit3_fix_resolution.md); ikinci:
[çözüm kaydı](reports/reaudit2_fix_resolution.md); ilk yeniden denetim:
[çözüm kaydı](reports/reaudit_fix_resolution.md); ilk tam denetim: [çözüm kaydı](reports/audit_fix_resolution.md);
önceki fiyat/onay düzeltmeleri: [çözüm kaydı](reports/safety_review_resolution.md).
Doğrulanan uygulama commit'i: `77ccd81b87403bf397b93dfd558f1e83818bcf53`.
Teslim adayı: `demo-candidate-20260923-v13`; etiketin uygulama kodu test edilen commit ile aynıdır.
Önceki v3 temiz clone'da 229 test geçmişti: [tarihsel temiz kurulum kanıtı](reports/hardening_resolution.md#v3-temiz-clone-provası).
Bu düzeltmede yeni temiz clone açılmadı. Testler izole test PostgreSQL'inde gerçek FastAPI route'larını ASGI üzerinden çalıştırdı; demo API/web süreci başlatılmadı, canlı proxy/SSE zamanlaması bu tur doğrulanmadı.
Mustafa fiziksel iPhone'da stream, ürün ekleme, web ile ortak teklif, aynı isteğin tekrarı,
klavye ve kaynak aç/kapat akışlarını doğruladı. Kullanıcı bildirimi: iPhone 16e / iOS 26.6.2; Expo Go Client Version 57.0.9, Supported SDK 57.0.0.
[Kabul kanıtları](reports/acceptance.md) kapsamı ve kalan teslim kapılarını ayırır.

## Docker ile yerel altyapı

Docker Desktop çalışırken repo kökünde:

```sh
python3 scripts/init_env.py
docker compose up --build -d --wait
```

İlk komut güçlü parolalar ve yönetim anahtarıyla ignored `.env` oluşturur; mevcut dosyada yalnız eksik
`ADMIN_API_KEY` değerini ekler, diğer değerleri değiştirmez. API
`http://localhost:8001/health/ready`, web yönetimi `http://localhost:5173` adresindedir.
PostgreSQL host portu açılmaz. API ve web varsayılan olarak yalnız Mac loopback'e bağlanır.
Migration ve JSON seed başarılı olmadan API başlamaz. Runtime DB rolü şema değiştiremez.
Web Compose servisi Vite geliştirme sunucusudur; public dağıtım için kullanılmaz.
Ürün/bilgi ekleme, düzenleme ve silme `X-Admin-Key` ister. Web paneli bu başlığı Vite proxy'si üzerinden
sunucu tarafında ekler; tarayıcıya veya mobil uygulamaya anahtar verilmez. Anahtarsız yazma 401 döner.
Okuma, sohbet ve teklif uçları anahtarsızdır. İstek gövdesi 256 KiB ile sınırlıdır.

```sh
docker compose --profile test run --build --rm test
docker compose run --rm --no-deps migrate-seed alembic check
```

Testler ayrı test-db servisinde her test için yeni veritabanı oluşturur; teşhis için tutar.
Belleği sınırlamak için mevcut test image/DB hazırken aşağıdaki ek Compose dosyası kullanılabilir.
Bu dosya test sürecini 512 MB / 1 CPU ile sınırlar, konteyner swap'ını kapatır ve güncel kaynak/testleri
salt okunur bağlar. PostgreSQL ayrı servistir; bu sınır bütün makinenin bellek sınırı değildir.

```sh
docker compose --profile test up -d --wait test-db
docker compose -f compose.yaml -f reports/safety_review_resources.compose.yaml run --rm --no-deps test pytest -v
docker compose --profile test stop test-db
```

Çok sayıda tam koşudan sonra testler `DiskFullError` verirse eski test veritabanlarını yalnız test-db'de sil
(demo veritabanına ve volume'lara dokunmaz):

```sh
docker compose --profile test up -d --wait test-db
docker compose --profile test exec test-db sh -c "psql -U tbr_owner -d tbr_test -tAc \"select format('DROP DATABASE %I;', datname) from pg_database where datname like 'tbr\\_test\\_%'\" | psql -U tbr_owner -d tbr_test -q"
```

Son onaylı temizliklerde geçici test DB’leri silindi (her seferinde sonuç 0); [önce/sonra kanıtı](reports/reaudit4_fix_testdb_cleanup.txt). Sonraki test koşuları yeniden geçici DB oluşturur. Çok sayıda geçici DB test-db’nin 64 MB `/dev/shm` alanını doldurabilir; bu durumda önce bu temizlik yapılır, limit büyütülmez.

Seed yalnız eksik ID'leri ekler, mevcut kullanıcı düzenlemelerini değiştirmez; startup'ta DROP/reset yoktur.
Tüm seed ve başarı işareti tek transaction içindedir. Named volume veriyi restart'ta korur.
Kaynak `seed.sql` otomatik çalıştırılmaz. Kanıt: [F01b kabul raporu](reports/f01b_acceptance.md).

## Mevcut demoyu koruyarak ikinci kurulum

Yeni clone klasöründe aşağıdaki değişkenleri aynı terminalde ayarla; sonra yukarıdaki
kurulum ve test komutlarını çalıştır. Compose proje adı ayrı volume/network oluşturur.
Portların boş olması gerekir. Mevcut `.env` veya veritabanını kopyalama/sıfırlama.

```sh
export COMPOSE_PROJECT_NAME=tbr-f09-clean
export API_BIND_HOST=127.0.0.1
export API_PORT=18001
export WEB_PORT=15173
python3 scripts/init_env.py
docker compose up --build -d --wait
```

Bu ortam API `http://localhost:18001`, web `http://localhost:15173` kullanır.
Aynı terminalde `docker compose stop` servisleri durdurur ve volume'ları korur.
`down -v` kullanma. Fiziksel telefon demosu için ana kurulumun aşağıdaki LAN adımlarını izle.
[F09 temiz kurulum kanıtı](reports/f09_acceptance.md) ve [3:30 demo akışı](docs/DEMO.md).

## Kurulum ve iPhone testi

Gerekenler: uv 0.12.17, Python 3.12.14, Node 24.21.0, npm 11.19.0.
Python sürümü `apps/api/.python-version`, Node `.node-version`; bağımlılıklar `uv.lock` ve kök `package-lock.json` ile kilitli.
Expo SDK 57, FastAPI 0.141.1 ve uvicorn 0.53.0 kurulup doğrulandı.

1. Repo kökünde kur ve kalıcı API'yi yerel ağ demosu için başlat:

   ```sh
   npm ci
   python3 scripts/init_env.py
   API_BIND_HOST=0.0.0.0 docker compose up --build -d --wait api web
   ```

   Bu adım API'yi aynı Wi-Fi'daki cihazlara açar. Ürün/bilgi yazma anahtar ister; okuma ve sohbet açıktır.
   Yalnız güvenilen ağda ve demo süresince kullan. Bitince `API_BIND_HOST=127.0.0.1 docker compose up -d --no-deps --wait api` ile API'yi
   açıkça loopback adresine döndür. Demo sırasında başka bir servisi yeniden build ederken
   (örn. `docker compose up -d --build web`) aynı `API_BIND_HOST=0.0.0.0` önekini tekrar ver; yoksa
   Compose API'yi loopback ayarıyla yeniden oluşturur ve telefon "sunucuya ulaşılamadı" der.

2. `apps/mobile/.env` dosyasına `EXPO_PUBLIC_API_BASE_URL=http://<MAC_LAN_IP>:8001` yaz.
   `<MAC_LAN_IP>` yerine Mac'in Wi-Fi ayarlarındaki IP adresini kullan. Dosya git dışındadır; yeni kurulumda oluştur,
   ağ değişirse güncelle. IP'yi rapora/örnek dosyaya/ekran görüntüsüne koyma. Telefonda localhost Mac'e gitmez.
3. İkinci terminali repo kökünde açıp Expo'yu başlat:

   ```sh
   npm start --workspace @tbr/mobile
   ```

4. Expo Go ve Mac CLI’da aynı Expo hesabıyla giriş yap (`npx expo login`); ardından Expo’yu yeniden başlat. Mac ve iPhone aynı Wi-Fi'dayken App Store'daki güncel Expo Go'yu kullan. iPhone Kamerasıyla
   terminaldeki QR'ı okut, Expo Go'da aç; yerel ağ izni sorulursa izin ver.
5. Mavi Kırmızı Market A.Ş. / Q-1001 seç; mevcut adedi not et. **“BlueScan Air 1 adet daha ekle.”**
   gönder. Parça parça yanıt ve kaynaklar görünmeli; Teklif tabında adet bir artmalı. Web'de aynı
   Q-1001 aynı adet/sürümü göstermeli. **Aynı isteği tekrar gönder** adedi yeniden artırmamalı.
6. macOS güvenlik duvarı sorarsa bu yerel test için Docker/API ve Node'un gelen bağlantılarına izin ver;
   güvenlik duvarını tamamen kapatman gerekmez.
7. Çalışmazsa ilk üç kontrol: **(a)** aynı Wi-Fi, VPN/misafir ağı izolasyonu ve Expo Go yerel ağ izni;
   **(b)** iPhone Safari'den `http://<MAC_LAN_IP>:8001/health/ready` açılıyor mu, API çalışıyor mu;
   **(c)** `.env` adresi doğru mu, Expo yeniden başlatıldı mı, Expo Go SDK 57 ile uyumlu mu?

Metro QR bağlantısı ile API bağlantısı ayrıdır. Expo'nun açılması API erişimini tek başına kanıtlamaz.
F01 debug sonucu **passed**: Mustafa 0.0/1.1 sn ve Tamamlandı görüntüsünü paylaştı.
Bu tam sohbet testi değildir. Güncel fiziksel kabul durumu `reports/native_smoke.md` içindedir.
Eski debug ekranı için mobil `.env` içinde `EXPO_PUBLIC_DEBUG_STREAM_SMOKE=1`, API'de
`DEBUG_STREAM_SMOKE=1` gerekir. DB'siz debug API komutu:
`DEBUG_STREAM_SMOKE=1 uv run --directory apps/api --locked uvicorn app.main:app --host 0.0.0.0 --port 8000 --no-access-log`.
Bu ayrı debug testi için mobil API portu 8000 seçilir; gerçek uygulama için 8001'e dönülür.

## Doğrulama

Repo kökünde:

```sh
npm test
npm run typecheck
npm run lint
npm exec --workspace @tbr/mobile -- expo install --check
PYTHONPATH=apps/api uv run --project apps/api --locked python scripts/check_debug_flag.py
# Ayrı debug API 8000 portunda açıkken:
python3 scripts/smoke_api.py
```

`scripts/smoke_api.py` gerçek `curl -N` çalıştırır, olayların geliş zamanlarını ve Türkçe içeriklerini doğrular.
`reports/` içinde gerçek komutlar, exit code'lar ve çıktılar bulunur; başarısız ilk denemeler de saklanır.
iOS bundle üretimi native cihaz gözlemi yerine geçmez. Kanıt haritası: [F01a kabul raporu](reports/f01a_acceptance.md).

## Kapsam ve düzen

- `apps/api`: altı domain tool, kaynaklı sohbet/SSE, ürün/bilgi CRUD, `/health/live` ve `/health/ready`; env ile açılan `/api/debug/stream-smoke`. `DEBUG_STREAM_SMOKE` yoksa/0 ise debug yolu yoktur;
  değişiklik API yeniden başlatılınca geçerli olur. Kök `.env` otomatik yüklenmez.
- `apps/mobile`: Türkçe sohbet, kaynaklar, retry ve kanonik teklif; `expo/fetch`, ortak parser. Compose dışında çalışır.
- `packages/contracts`: testli SSE parser/reducer, Quote DTO ve version1 event sözleşmeleri.
- `apps/web`: React/TypeScript/Vite admin/chat/quote/log. Ayrı `apps/web/package-lock.json` ile kilitli; `npm --prefix apps/web ci` ve `npm --prefix apps/web run build`.
- `apps/api/app/persistence`: SQLAlchemy async Core şema, Alembic, JSON seed ve readiness.
- `data/source`: orijinal şirket dataset'i, değiştirilmez. Seed/kalıcılık, iş kuralları ve golden testleri gerçek PostgreSQL üzerinde çalışır.

ADR-005 (indirimler toplanmaz, özel kural önceliği) ve ADR-007 (beklenen çağrı/kaynaklar minimum)
firma tarafından karar adaya bırakıldıktan sonra **kabul edilmiş aday tercihleridir** (21 Eylül 2026).
Şirketin belirlediği kesin kurallar olarak sunulmaz; saf fiyatlama ve mutasyon yürütücüsü gerçek DB'de test edildi.

[AI kullanımı](AI_USAGE.md) · [Bilinen sınırlamalar](KNOWN_LIMITATIONS.md)

## Kaynaklı okuma (F02)

`POST /api/tools/search_products`, `POST /api/tools/get_knowledge_entries`,
`GET /api/quotes/{quote_id}` gerçek PostgreSQL verisini okur. Para cevaplarda iki ondalıklı string,
hesapta Decimal'dir. Teklif mevcut snapshot birim fiyatını kullanır; katalog fiyat güncellemesi eski teklifi değiştirmez.
Aktif ve geçmiş satırlar ayrı döner. Read işlemleri teklif version'ını artırmaz.

```sh
python3 scripts/smoke_reads.py
```

Fiyat çakışmasında en özel tek kural uygulanır (bundle/acil hizmet hariç tutma → Plus →
yazılım kombinasyonu → aksesuar → partner). Örneğin 4 × 9430 için Plus %6: net 35456.80;
toplamsal %13 seçilseydi net 32816.40 olurdu. Firma kararı adaya bıraktı; bu belgelenmiş
aday tercihidir. Kaynak condition metinleri eval edilmez.
Kanıt: [F02 kabul raporu](reports/f02_acceptance.md).

## Transaction ve tekrar davranışı (F03)

Üç mutation tool'u tek executor'dan, kaydedilmiş plan ve güvenilir mesaj bağlamıyla çalışır.
Sunucu anahtarı quote/message/action-index/tool üzerinden üretir; client veya LLM'nin değiştirdiği
anahtar reddedilir. Teklif satırı `FOR UPDATE` kilidiyle receipt kontrolü ve güncelleme sıraya girer.
Ürün satırları sabit ID sırasında `FOR SHARE` ile okunur; fiyat/stok admin güncellemesi commit öncesinde
kontrolü geçersiz kılamaz. Grup içindeki ikinci hata, kalem/version/receipt/başarı loglarını birlikte geri alır.

Aynı mesajın yeniden gönderimi gerçek wrapper'ı receipt yolundan geçirir; yeni deneme loglanır,
teklif tekrar değiştirilmez. Farklı message_id kasıtlı yeni işlemdir. Eski quantity-set tekrarları,
arada yapılan yeni güncellemeyi geri almaz. Başarı cevabı yalnız transaction commit'inden sonra döner.
Bu belirli anahtarda tekrar etmeyen DB etkisidir; genel bir “exactly once delivery” iddiası değildir.

`quantity=0` kalemi removed yapar; pasif/stok dışı kaynak ürünü kaldırmayı engellemez.
Replace eski satırı replaced yapar ve hedefe bağlar; hedef zaten aktifse miktarı birleştirir.
Yeni stok dışı add için hem müşteri uygunluğu hem açık bekleme onayı gerekir; replace hedefi stoklu olmalıdır.
Taslak stok rezervasyonu yapmaz ve stok miktarını düşürmez. Araçlar gerçek web sohbetine bağlıdır.

F04 sohbet: `POST /api/chat/sessions` ile `customer_id`, `quote_id`, `channel` gönder;
dönen `session_id` ile `POST /api/chat` gövdesinde `message_id`, `quote_id`, `message` gönder.
Aynı gönderimin tekrarında aynı `message_id`, yeni mesajda yeni kimlik kullanılır. Plan sunucuda
kalıcıdır; istemci guard veya idempotency anahtarı veremez. Anahtarsız Türkçe fallback gerçek
araçları çalıştırır; şu anda ücretli/harici model adaptörü yoktur. 22 golden senaryo HTTP sohbet
kapısından geçti; kanıt `reports/f04_acceptance.md`. SSE ve web chat entegrasyonu F05/F06'da tamamlandı.

F05: `POST /api/chat/stream` aynı chat gövdesiyle gerçek SSE döndürür. `message_start`, gerçek
`tool_call_start/result`, `sources`, `text_delta`, `done/error` olayları version 1 envelope kullanır.
Başarılı araç sonuçları transaction commit'inden sonra yayınlanır. Bağlantıyı kesmek kabul edilmiş
işlemi geri almaz; aynı mesaj kimliğiyle tekrar dene ve `GET /api/quotes/{id}` ile yenile.
`GET /api/chat/sessions/{id}/messages` toparlanma, `GET /api/tool-calls?session_id=...` denetim içindir.
Kalıcı token/Last-Event-ID replay yoktur; işlem tekrarsızlığı receipt ile sağlanır. Fallback metni
parçalar halinde gönderilir; LLM token akışı diye sunulmaz. Kanıt `reports/f05_acceptance.md`.

## Web yönetimi (F06)

Compose açıkken `http://localhost:5173/`: müşteri/teklif seç, sohbetten işlem yap ve aynı kanonik
teklifi izle. Ürünler ve Bilgi bankası ekranlarından listeleme/ekleme yapılır; yeni kayıtlar
anında DB retrieval'ına katılır. İşlem kayıtları ekranı gerçek araç girdisi/sonucu, kaynaklar,
deneme ve receipt tekrarını gösterir. API `/api/products` ve `/api/knowledge` için GET/list,
POST, PATCH ve mantıksal DELETE sağlar. ID verilmezse sunucu üretir; silme geçmişi bozmaz.

Web her 2,5 saniyede, pencereye dönünce ve mutation/retry sonunda teklifi yeniden okur;
eski sürüm yeni sürümü ezmez. Bağlantı kesilince son görünüm ve başarılı kontrol zamanı korunur.
Oturum kimliği tarayıcıda saklanır; fiyat ve miktar için ikinci bir kalıcı istemci deposu yoktur.

`npm run build --prefix apps/web` production build/typecheck; `python3 scripts/sync_web_contracts.py --check`
ortak parser/DTO kopyalarının eşleşmesini doğrular. Compose web build context'i `apps/web` olduğundan
`python3 scripts/sync_web_contracts.py` ile üretilmiş, SHA256 işaretli kopyalar kullanılır; elle düzenlenmez.
Yerel demo authentication/RBAC içermez; müşteri seçimi kimlik doğrulama değildir.
Kanıt: [F06 kabul raporu](reports/f06_acceptance.md).

Görsel dil: firmanın logosu ve ona hizalanmış mavi/kırmızı token seti (`apps/web/DESIGN.md`),
sistem yazı tipi, animasyonsuz. Dar ekranda gezinme 2×2 ızgaraya geçer, tablolar sağda sütun
kaldıkça solan kenarla kayar. Web'de karanlık tema yok; mobil sistem temasını izler.
Kanıt ve öncesi/sonrası görüntüler: [tasarım düzenleme raporu](reports/design_polish.md).


## Son sağlamlaştırma (F08)

Tanınmayan fiyat sınırı, olumsuzlanan Plus/özellik, belirsiz kalem ve kısmi çıkarma komutlarında
netleştirme istenir; rastgele mutasyon yapılmaz. Wi-Fi/USB C/çevrimdışı yazımları aynı kesin
özellik filtrelerine dönüşür. Canlı ürünler kategori sözcüğü olmadan model adıyla bulunabilir.
Eşit güçlü adaylar fiyat sırasına göre otomatik eklenmez; ürün kodu sorulur.

“Toplam N olsun” planı, delta hesaplanan teklif sürümüne bağlıdır. Araya değişiklik girerse yeni
etki 409 ile reddedilir ve güncel hedef yeni mesajla istenir. Taslak olmayan teklif değiştirilemez.
Önceden tamamlanmış receipt replay bu kontrollerden önce doğrulanır; geçmiş işlem ikinci etki yaratmaz.
[Bağımsız review](reports/f08_claude_review.md) ve [düzeltme/test eşlemesi](reports/f08_review_resolution.md)
ayrıdır; test başarısı bütün olası doğal dil ifadelerinin desteklendiği iddiası değildir.
