# API (FastAPI)

Teklif asistanının backend'i: altı araç, Türkçe planlayıcı, SSE sohbet, teklif hesaplama, ürün ve bilgi
kaydı yönetimi. Python 3.12, FastAPI, SQLAlchemy 2 (async) ve PostgreSQL 16; bağımlılıklar `uv.lock`
ile kilitli.

## Çalıştırma ve test

API, Docker Compose ile çalışır (kurulum: [kök README](../../README.md#hızlı-başlangıç)). Repo kökünde:

```sh
docker compose --profile test run --build --rm test                              # tüm testler
docker compose --profile test run --rm test pytest -q tests/golden               # yalnız 22 golden senaryo
docker compose --profile test run --rm --no-deps test ruff check app tests       # lint
```

Testler ayrı `test-db` servisinde, her test için taze migrate ve seed edilmiş bir veritabanı kullanır.
Editör ve yerel araçlar için bağımlılıklar: `uv sync --directory apps/api --locked`.

## Kod haritası

| Yol | Görev |
|---|---|
| `app/main.py` | Uygulama kurulumu, istek gövdesi sınırı (256 KiB), hata cevapları, `/health/live` ve `/health/ready` |
| `app/api/chat.py` | Sohbet oturumu, `POST /api/chat` ve `POST /api/chat/stream` (SSE), mesajlar, araç logları |
| `app/api/reads.py` | Okuma araçları ve kanonik teklif (`GET /api/quotes/{id}`) |
| `app/api/admin.py` | Ürün ve bilgi kaydı listeleme/CRUD (yazma `X-Admin-Key` ister), müşteri ve teklif listeleri |
| `app/orchestration/planner.py` | Türkçe mesajı niyet ve slotlara ayırıp araç çağrısı planına çevirir; belirsizlikte netleştirme sorar |
| `app/orchestration/chat.py` | Planı kaydeder ve yürütür; yedek mod ve yanıt kaydı |
| `app/orchestration/streaming.py` | SSE olayları: `message_start`, `tool_call_start`, `tool_call_result`, `sources`, `text_delta`, `done`/`error` |
| `app/orchestration/templates.py` | Araç sonuçlarından kaynaklı Türkçe yanıt metni |
| `app/services/retrieval.py` | Ürün ve bilgi kaydı arama; fiyat, stok, kategori ve özellik filtreleri |
| `app/services/normalization.py` | Türkçe metin normalizasyonu; fiyat sınırı, miktar ve onay ifadelerinin tanınması |
| `app/services/executor.py` | Kalıcı planı sırayla çalıştırır, her çağrıyı loglar |
| `app/services/mutations.py` | `add_to_quote`, `update_quote_item`, `replace_with_alternative`; receipt ve yazma anındaki kurallar |
| `app/services/pricing.py` | İndirim kuralları ve teklif toplamları |
| `app/services/quotes.py` | Kanonik teklif görünümü (aktif ve geçmiş satırlar) |
| `app/services/execution_context.py` | Güvenilir çalışma bağlamı ve sunucu tarafında üretilen idempotency anahtarı |
| `app/services/evidence.py` | Yanıttaki her ürün, bilgi ve fiyat iddiasının bir kaynağa dayandığını doğrular |
| `app/persistence/` | Şema, bağlantı, JSON seed ve hazır olma kontrolü |
| `app/schemas/` | Araç girdi/çıktıları, SSE olayları ve yönetim uçları için Pydantic şemaları |
| `migrations/` | Alembic: şema, aktif satır için kısmi benzersiz indeks, çalışma zamanı rolünün yetkileri |
| `tests/` | `golden/` (22 senaryo), HTTP/DB entegrasyon testleri, `unit/` |

## Ortam değişkenleri

`.env` dosyasını `python3 scripts/init_env.py` üretir; örnek: [`.env.example`](../../.env.example).

| Değişken | Anlamı |
|---|---|
| `POSTGRES_PASSWORD`, `APP_DB_PASSWORD` | Veritabanı sahibi ve çalışma zamanı rolünün parolaları |
| `ADMIN_API_KEY` | Ürün/bilgi yazma anahtarı; yalnız sunucuda ve web proxy'sinde kullanılır |
| `API_BIND_HOST`, `API_PORT` | API'nin dinlediği adres (varsayılan `127.0.0.1`) ve port (`8001`) |
| `OPENAI_API_KEY`, `LLM_MODE` | Varsayılan (`LLM_MODE=off`, anahtar boş) yedek moddur ve yanıt bunu belirtir. Ayarlansalar da bu sürümde hiçbir model çağrılmaz |
| `DEBUG_STREAM_SMOKE` | `1` ise veritabanı kullanmayan `POST /api/debug/stream-smoke` test ucu açılır; varsayılan kapalı, uç kaydedilmez |
