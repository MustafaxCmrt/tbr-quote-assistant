# The Blue Red — Yapay Zeka Destekli Teklif Asistanı

B2B satış kataloğunda ürün veya politika sorusunu **Türkçe** yanıtlayan, cevabını gerçek ürün / bilgi kaydı /
fiyat kuralı kaynaklarıyla destekleyen ve gerektiğinde **aynı kalıcı teklif taslağı** üzerinde gerçek mutasyon
yapan asistan. Web admin ve mobil uygulama aynı `quote_id` için aynı durumu gösterir.

**Teknoloji:** FastAPI · PostgreSQL · React + TypeScript · React Native / Expo · Docker Compose

> **Durum (2026-09-21):** Repo iskeleti ve orijinal veri seti hazır. Uygulama kodu, migration, Compose ve testler
> henüz yazılmadı. Aşağıdaki bölümler ilgili fazlar gerçekten tamamlanınca doldurulacaktır; çalışmamış komut
> "çalışıyor" diye yazılmaz.

## Repo düzeni
```
apps/api/            FastAPI backend, SQLAlchemy 2 async, Alembic, altı tool, orkestrasyon, SSE, testler
apps/web/            React + Vite admin: ürün/bilgi listele-ekle, teklif, oturum/tool logları, küçük test chat
apps/mobile/         Expo: chat, streaming, kaynak kartları, ortak teklif/draft ekranı (Compose dışında çalışır)
packages/contracts/  Ortak DTO, SSE event zarfı ve saf SSE parser (tek sahipli)
data/source/         Şirketin orijinal dataset'i — DEĞİŞTİRİLMEZ (seed ve golden testler salt okunur kullanır)
scripts/             bootstrap, seed import, dataset doğrulama, smoke
reports/             Gerçek test kanıtları (golden sonuçları, test çıktısı, native smoke)
docs/decisions/      Mimari karar kayıtları (ADR)
compose.yaml         db + migrate-seed + api + web   (F01'de eklenecek)
.env.example         Yalnız placeholder; private değer içermez
```

## Hızlı başlangıç
_F01 tamamlanınca: `cp .env.example .env` → `docker compose up --build` → health URL'leri → web/API adresleri → seed davranışı._

## Mobil
_F01/F07 tamamlanınca: Expo kurulum/başlatma, uyumlu Expo Go sürümü, telefon için API adresi ayarı, test edilen cihaz._

## Testler
_Gerçek tek komut, DB izolasyonu, 22 golden + negatif test kapsamı, gerçek kısa çıktı, tarih ve commit._

## Mimari, tool orkestrasyonu, idempotency, fiyat kuralları
_Uygulama ilerledikçe: retrieval yaklaşımı ve nedeni; deterministik/LLM/hibrit mod; anahtarsız garanti;
idempotency anahtarı ve retry; quote lifecycle (replace / removed / snapshot fiyat); indirim çakışma tercihi ve statüsü._

## AI kullanımı ve sınırlamalar
`AI_USAGE.md` ve `KNOWN_LIMITATIONS.md` F09'da gerçek kullanım ve gerçek sınırlamalarla yazılacaktır.
