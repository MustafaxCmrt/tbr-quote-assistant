# The Blue Red — Teklif Asistanı

Hedef: kaynaklı Türkçe chat, altı gerçek tool ve web/mobil ortak kalıcı teklif durumu.
**21 Eylül 2026: F01–F02 tamamlandı.** PostgreSQL/Compose, Alembic, idempotent seed ve readiness doğrulandı.
iPhone debug streaming Mustafa tarafından doğrulandı. Üç okuma aracı ve kaynaklı retrieval hazır; mutasyon/chat/admin akışları sonraki fazlardır.

## Docker ile yerel altyapı

Docker Desktop çalışırken repo kökünde:

```sh
python3 scripts/init_env.py
docker compose up --build -d --wait
```

İlk komut güçlü parolalarla ignored `.env` oluşturur; mevcut dosyayı değiştirmez. API
`http://localhost:8001/health/ready`, web iskeleti `http://localhost:5173` adresindedir.
PostgreSQL host portu açılmaz. API ve web varsayılan olarak yalnız Mac loopback'e bağlanır.
Migration ve JSON seed başarılı olmadan API başlamaz. Runtime DB rolü şema değiştiremez.
Web F01'de Vite geliştirme sunucusudur; public dağıtım için kullanılmaz.

```sh
docker compose --profile test run --build --rm test
docker compose run --rm --no-deps migrate-seed alembic check
```

Testler ayrı test-db servisinde her test için yeni veritabanı oluşturur; teşhis için tutar.
Seed yalnız eksik ID'leri ekler, mevcut kullanıcı düzenlemelerini değiştirmez; startup'ta DROP/reset yoktur.
Tüm seed ve başarı işareti tek transaction içindedir. Named volume veriyi restart'ta korur.
Kaynak `seed.sql` otomatik çalıştırılmaz. Kanıt: [F01b kabul raporu](reports/f01b_acceptance.md).

## Kurulum ve iPhone testi

Gerekenler: uv 0.12.17, Python 3.12.14, Node 24.21.0, npm 11.19.0.
Python sürümü `apps/api/.python-version`, Node `.node-version`; bağımlılıklar `uv.lock` ve kök `package-lock.json` ile kilitli.
Expo SDK 57, FastAPI 0.141.1 ve uvicorn 0.53.0 kurulup doğrulandı.

1. Repo kökünde kur ve API'yi başlat:

   ```sh
   cd /Users/comert/Desktop/tbr-quote-assistant
   uv sync --directory apps/api --locked
   npm ci
   DEBUG_STREAM_SMOKE=1 uv run --directory apps/api --locked uvicorn app.main:app --host 0.0.0.0 --port 8000 --no-access-log
   ```

2. `apps/mobile/.env` dosyasına `EXPO_PUBLIC_API_BASE_URL=http://<MAC_LAN_IP>:8000` yaz.
   `<MAC_LAN_IP>` yerine Mac'in Wi-Fi ayarlarındaki IP adresini kullan. Bu oturumda yerel dosya hazırlandı;
   ağ değişirse güncelle. IP'yi rapora/örnek dosyaya/ekran görüntüsüne koyma. Telefonda localhost Mac'e gitmez.
3. İkinci terminalde Expo'yu başlat:

   ```sh
   cd /Users/comert/Desktop/tbr-quote-assistant/apps/mobile
   npm start
   ```

4. Expo Go ve Mac CLI’da aynı Expo hesabıyla giriş yap (`npx expo login`); ardından Expo’yu yeniden başlat. Mac ve iPhone aynı Wi-Fi'dayken App Store'daki güncel Expo Go'yu kullan. iPhone Kamerasıyla
   terminaldeki QR'ı okut, Expo Go'da aç; yerel ağ izni sorulursa izin ver.
5. **Stream testi** butonuna bas. Önce “Bağlantı çalışıyor ğüşiöç”, yaklaşık bir saniye sonra
   “İkinci parça ulaştı: ĞÜŞİÖÇ”, yaklaşık bir saniye sonra **Tamamlandı** görmelisin.
   Satırlar topluca değil, geldikçe görünmeli; başlarında geçen süre yer alır. İkinci denemede eski satırlar temizlenir.
6. macOS güvenlik duvarı sorarsa bu yerel test için Python/uvicorn ve Node'un gelen bağlantılarına izin ver;
   güvenlik duvarını tamamen kapatman gerekmez.
7. Çalışmazsa ilk üç kontrol: **(a)** aynı Wi-Fi, VPN/misafir ağı izolasyonu ve Expo Go yerel ağ izni;
   **(b)** iPhone Safari'den `http://<MAC_LAN_IP>:8000/health/live` açılıyor mu, API terminali çalışıyor mu;
   **(c)** `.env` adresi doğru mu, Expo yeniden başlatıldı mı, Expo Go SDK 57 ile uyumlu mu?

Metro QR bağlantısı ile API bağlantısı ayrıdır. Expo'nun açılması API erişimini tek başına kanıtlamaz.
Native sonuç **passed**: Mustafa iPhone ekranında 0.0/1.1 sn zamanları ve Tamamlandı durumunu paylaştı.
Kanıt `reports/native_smoke.md` içinde; tam cihaz/iOS/Expo Go sürüm bilgisi henüz bildirilmedi.

## Doğrulama

Repo kökünde:

```sh
npm test
npm run typecheck
npm run lint
npm exec --workspace @tbr/mobile -- expo install --check
PYTHONPATH=apps/api uv run --project apps/api --locked python scripts/check_debug_flag.py
# API yukarıdaki komutla açıkken:
python3 scripts/smoke_api.py
```

`scripts/smoke_api.py` gerçek `curl -N` çalıştırır, olayların geliş zamanlarını ve Türkçe içeriklerini doğrular.
`reports/` içinde gerçek komutlar, exit code'lar ve çıktılar bulunur; başarısız ilk denemeler de saklanır.
iOS bundle üretimi native cihaz gözlemi yerine geçmez. Kanıt haritası: [F01a kabul raporu](reports/f01a_acceptance.md).

## Kapsam ve düzen

- `apps/api`: `/health/live`, env ile açılan `/api/debug/stream-smoke`. `DEBUG_STREAM_SMOKE` yoksa/0 ise debug yolu yoktur;
  değişiklik API yeniden başlatılınca geçerli olur. Kök `.env` otomatik yüklenmez.
- `apps/mobile`: geçici Türkçe bağlantı ekranı, `expo/fetch`, ortak saf parser. Compose dışında çalışır.
- `packages/contracts`: testli SSE parser; gerçek DTO/event sözleşmeleri F05'te sabitlenecek.
- `apps/web`: React/TypeScript/Vite bağlantı iskeleti. Ayrı `apps/web/package-lock.json` ile kilitli; `npm --prefix apps/web ci` ve `npm --prefix apps/web run build`.
- `apps/api/app/persistence`: SQLAlchemy async Core şema, Alembic, JSON seed ve readiness.
- `data/source`: orijinal, değiştirilmedi. Kalıcılık ve 7 gerçek PostgreSQL testi passed.

ADR-005 (indirimler toplanmaz, özel kural önceliği) ve ADR-007 (beklenen çağrı/kaynaklar minimum)
firma tarafından karar adaya bırakıldıktan sonra **kabul edilmiş aday tercihleridir** (21 Eylül 2026).
Şirketin belirlediği kesin kurallar olarak sunulmaz; saf fiyatlama uygulanıp test edildi; mutasyon yürütücüsü sıradadır.

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
