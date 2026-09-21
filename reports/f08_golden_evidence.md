# Golden kanıt raporu — F07 cihaz kapısı beklenirken hazırlık

`golden_results.json` gerçek pytest koşusundan üretildi: 22 passed, 0 failed/error/skipped/not_run.
22 ayrı taze PostgreSQL veritabanı; demo DB değişmedi, test DB'leri silinmedi.
Her senaryo HTTP chat route'undan geçti. ASGITransport kullanıldı; bu koşu canlı soket/SSE zamanlaması iddiası değildir.
Beklenen tool ve kaynaklar, gerçek loglar, response'lar, canonical before/after, tüm quote satırları ve stok snapshot'ları vardır.
Setup/call/teardown birlikte passed olmadıkça başarılı yazılmaz. Eksik çalışmış senaryo not_run kalır.

- Gerçek komut ve exit0: `f08_golden_evidence_run.txt`.
- Runtime commit: `26f939dd302cf9067fe0ff2b0580f62677a55cb8`. Yalnız test raporlama değişikliği koşuda working tree'deydi; bu belgeyle commit edilir. Runtime kodu değişmedi.
- Reporter hata denemesi: `f08_reporter_failure_probe.txt`; geçici izole pytest içinde bilerek assertion/setup/teardown hatası ve skip oluşturuldu. Alt pytest exit1, denetim scripti exit0: pass1/fail1/error2/skip1 doğru raporlandı. Bu yapay örnekler ürün kabul testi değildir.
- Golden assertion'ları ve kaynak fixture'ları değiştirilmedi. Ruff ilk import/UTC uyarıları otomatik düzeltildi; son lint exit0 (`f08_golden_lint.txt`).
- Fiziksel native kaynak/klavye/stream ve bağımsız Claude review henüz not_verified/not_run. F08 kapısı geçildi denmiyor.
