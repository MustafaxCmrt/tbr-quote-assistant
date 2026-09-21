# API — F01a

Python 3.12.14, FastAPI 0.141.1, uvicorn 0.53.0; bağımlılıklar `uv.lock` ile kilitli.
Repo kökünden:

```sh
uv sync --directory apps/api --locked
DEBUG_STREAM_SMOKE=1 uv run --directory apps/api --locked uvicorn app.main:app --host 0.0.0.0 --port 8000 --no-access-log
```

`GET /health/live` → `{"status":"ok"}`. Bu yalnız süreç sağlığıdır, DB hazır kontrolü değildir.
`POST /api/debug/stream-smoke` geçici ve DB'sizdir: iki `text_delta`, sonra `done`, aralarında bir saniye.
Her payload `debug: true` taşır. Gerçek chat/tool/teklif mutasyonu değildir; F05 sözleşmesini sabitlemez.
`StreamingResponse` ve `text/event-stream` kullanılır.

Debug varsayılan kapalıdır. Kapatmak için `DEBUG_STREAM_SMOKE=0` ile API'yi yeniden başlat;
endpoint ve OpenAPI kaydı bulunmaz. `.env` kendiliğinden yüklenmez; komuttaki env bayrağı kullanılır.

Çalışan API için repo kökünde `python3 scripts/smoke_api.py`; bayrak kontrolü için
`PYTHONPATH=apps/api uv run --project apps/api --locked python scripts/check_debug_flag.py`.
Gerçek çıktı: `reports/f01a_curl_stream.txt`, `reports/f01a_debug_flag.txt`.
Docker/PostgreSQL, migration, seed, `/health/ready` ve altı tool henüz uygulanmadı.
