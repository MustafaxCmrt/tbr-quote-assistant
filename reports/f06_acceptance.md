# F06 — gerçek yönetim ve web sohbeti

2026-09-21. Base commit `51bcd7cb0fbb6469b2b8d7543599c068eedc26bc`; bu rapor F06 commit'inin parçasıdır.

- Gerçek PostgreSQL: **144 passed**, 22 golden dahil; `f06_backend_final.txt` komut/exit0/çıktı içerir.
- İlk import hatası (`f06_admin_tests.txt`) ve inactive model regression hatası (`f06_backend_tests.txt`)
  saklandı. Şema üretimi ve retrieval düzeltildi; assertion veya source fixture gevşetilmedi.
- Backend lint, web build/typecheck/lint, ortak contract SHA eşleşmesi ve sürüm/bağlam yarış testi:
  `f06_api_lint.txt`, `f06_web_final_build.txt`, `f06_web_final_lint.txt`, `f06_contract_sync.txt`,
  `f06_state_test.txt`; exit0. `f06_delivery.txt`: 12 orijinal dosya aynı, stageable secret/LAN taraması geçti.
- `f06_compose_final.txt`: çalışan API/web yeniden build edildi, servisler healthy, exit0.

Gerçek tarayıcı akışı: Ürünler → ürün ekle → listede gör; Bilgi bankası → bilgi ekle → içeriği aç.
Eklenen ürün `PRD-30F871664B134D10`, bilgi `KNE-32FFB1FD0CFD485B`. Kullanıcının demo DB'sinde
bu kayıtlar tutuldu (49 ürün/23 bilgi); seed kaynakları değişmedi. Sohbetten “Demo Deniz Okuyucu 1 adet ekle.”
sonrası Q-1002 sürüm2, adet1, net1234.50. “Tekrar gönder (aynı istek)” aynı miktar/sürümü korudu;
ayrı attempt logunda replayed=true, mutation_applied=false görüldü. İkinci tarayıcı sekmesi aynı teklifi okudu.
`f06_demo_api.txt` gerçek API/receipt ve yeni bilginin retrieval sonucunu bağımsız doğrular, exit0.
`scripts/check_f06_demo.py` yalnız bu kaydedilmiş yerel smoke durumunu okur; temiz kurulum testi değildir.

Ekran kanıtları `images/f06/`: products-desktop, knowledge-desktop, chat-desktop, chat-narrow-web,
replay-desktop, second-client. Dar tarayıcı görüntüsü native kanıtı değildir. Viewport istekleri
1440×1000/390×844; PNG boyutları tarayıcı yakalaması nedeniyle 1425×990/375×812.
UI eylemlerinde process exit code yoktur; gözlem ve kanonik API karşılaştırması kaydedildi.

Impeccable detector exit126 (çalıştırıcı izni), otomatik görsel tarama not_run. Ayrı okuyucu incelemesi
stale görünümde sürüm/zaman ve placeholder kontrastı düzeltmelerini istedi; kod ve final görüntüleri
ayrı verdict geçişinde incelenir. Hazır reviewer türü olmadığından degraded sözleşme ile ayrı ajan kullanıldı.
Son verdict: **ship**, yalnız iki düzeltmenin resolved olduğu doğrulandı. `offline-final.png` gerçek
API kesintisinde sürüm2 ve son başarılı kontrol saatini gösterir. API stop/recovery exit0 raporları
`f06_api_offline.txt` ve `f06_api_recovered.txt`; DB ve kayıtlar korundu. Token ve bileşen belgeleri
`apps/web/DESIGN.md`, `apps/web/.impeccable/design.json` ayrı documenter tarafından mevcut koddan yazıldı.
F01 native debug gözlemi passed; **tam native chat ve web/mobile ortak state F07'de not_verified**.
