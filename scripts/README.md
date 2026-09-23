# scripts/

Repo kökünden çalıştırılır. Veri değiştiren tek betik `init_env.py`'dir (yalnız eksik `.env` değerlerini ekler).

| Betik | Görev |
|---|---|
| `init_env.py` | Compose için `.env` dosyasını güçlü rastgele parolalarla üretir; mevcut değerleri değiştirmez, parolaları yazdırmaz |
| `check_delivery.py` | Teslim kontrolü: orijinal dataset baytları değişmedi mi; depoya girecek dosyalarda özel anahtar, sağlayıcı anahtarı, yerel IP veya kullanıcı yolu var mı |
| `check_git_history.py` | Git geçmişinde gizli değer taraması (eşleşen değeri yazdırmaz) |
| `check_admin_runtime.py` | Çalışan stack'te yazma uçlarının anahtar istediğini, web proxy'sinin anahtarı sunucuda eklediğini ve anahtarın tarayıcıya sızmadığını doğrular |
| `smoke_compose.py` | API ve web proxy'si üzerinden sağlık kontrolü |
| `smoke_reads.py` | Okuma araçlarına gerçek HTTP istekleri |
| `smoke_chat.py` | Teklifi değiştirmeyen gerçek sohbet isteği |
| `smoke_stream.py` | `curl -N` ile SSE olaylarının gerçek zamanlı gelişini ölçer (web proxy'si dahil) |
| `smoke_api.py`, `smoke_metro.py`, `check_debug_flag.py` | Veritabanısız akış testi ucu, Metro açılışı ve debug bayrağının kapalıyken ucun kaydedilmediği kontrolleri |
| `check_f06_demo.py`, `check_f07_native_retry.py` | Web ve iPhone demolarında oluşan kayıtların salt okunur doğrulaması |
| `sync_web_contracts.py` | Ortak sözleşmelerin web kopyalarını üretir; `--check` eşitliği doğrular |
| `export_stream_schemas.py`, `export_tool_schemas.py` | Backend şemalarından `packages/contracts/*.schema.json` dosyalarını üretir (`PYTHONPATH=apps/api` ile) |
| `record_command.py` | Bir komutu çalıştırıp gerçek çıktısını ve çıkış kodunu `reports/` altına kaydeder |
| `postgres/` | Uygulamanın şema değiştiremeyen çalışma zamanı veritabanı rolünü oluşturan PostgreSQL imajı |
