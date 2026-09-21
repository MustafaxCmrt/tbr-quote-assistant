# Türkçe demo — yaklaşık 3 dakika 30 saniye

Bu metin kayıt planıdır; video çekildi veya gönderildi anlamına gelmez.
Doğrulanan kod: `demo-candidate-20260921-v2` (runtime `53b9948`).
Test kanıtı: `reports/f09_clean_backend.txt` — 225 passed, 22 golden dahil.

## Hazırlık

Ana demo: web `http://localhost:5173`, mevcut Expo Go uygulaması. Veritabanını sıfırlama.
Q-1001'in mevcut adet ve sürümünü ilk karede göster; her yeni ekleme miktarı bir artırır.
Yeni clone provası ayrı18001/15173 portlarında; telefon ana8001 ortamını kullanır.
Kayıtta `.env`, QR/LAN adresi, kişisel sekmeler veya parolalar görünmesin.
15 saniyelik ses/görüntü denemesi yap. Gerçek telefon kaydını kullan; web'i native diye sunma.

| Zaman | Ekranda yap | Kısa anlatım |
|---|---|---|
| 0:00–0:25 | README mimari ve uygulama | “Tek FastAPI, PostgreSQL ve iki istemci. Teklifin tek doğruluk kaynağı backend.” |
| 0:25–1:10 | Telefonda Mavi Kırmızı Market/Q1001; `BlueScan Air 1 adet daha ekle.`; Teklif tabı, web aynı Q1001 | “Doğal dil komutu gerçek araç çağrısına ve transaction'a dönüşüyor. İki ekran aynı miktar ve sürümü okuyor.” |
| 1:10–1:35 | Aynı isteği tekrar gönder; web İşlem kayıtları | “Aynı mesaj kimliği receipt üzerinden tekrarlandı; yeni deneme var ama ikinci miktar artışı yok.” |
| 1:35–2:05 | Q1004 mevcut kalemini göster; ilk durum uygunsa `Pahalı okuyucuyu 9.000 TL altında bir alternatifle değiştir.` | “Fiyat tavanı sunucuda tekrar kontrol ediliyor. Eski satır geçmişte, yeni satır aktif.” |
| 2:05–2:35 | `İade süresi nedir?`; bilgi kaynağı aç/kapat | “Harici model adaptörü yok. Kaynaklı deterministik mod gerçek knowledge kimliğiyle cevap veriyor; bu soru teklifi değiştirmiyor.” |
| 2:35–3:00 | f09_clean_backend.txt ve golden_results.json | “225 backend testi ve 22 golden senaryo. Gerçek PostgreSQL; tool girdileri, yasak etkiler, kaynaklar ve DB sonucu birlikte kontrol edildi.” |
| 3:00–3:30 | README trade-off, KNOWN_LIMITATIONS, AI_USAGE | “Firma indirim çakışmasını adaya bıraktı; özel tek kural önceliğini belgeledim. Yerel demo auth/RBAC içermiyor. AI katkısı ve insan cihaz doğrulaması ayrı kaydedildi.” |

Replace adımını mevcut Q1004'ü okuyarak prova et; daha önce değiştirilmişse reset yapma.
Akış yetişmezse replace bölümünü kısalt; ortak teklif ve retry kanıtını koru.
SSE, hazırlanmış fallback cevabının parçalanmasıdır; LLM token akışı değildir.

## Teslim öncesi insan adımları

1. Telefon modeli, iOS ve Expo Go sürümünü not et; final kayıtta klavye, kaynak ve ortak teklif akışını doğrula.
2. Türkçe2–4 dakikalık videoyu oluştur ve paylaşım bağlantısını belirle.
3. Repo/video erişimini değerlendiricinin hesabı/oturumu üzerinden kontrol et; kendi oturumunda açılması yeterli değildir.
4. Alıcı ve somut teslim metnini kontrol edip gönderimi onayla veya kendin gönder. Görünürlük otomatik değiştirilmez.

Replace cümlesi ayrı temiz kurulumda gerçek API üzerinden doğrulandı: Q1004 BC120/12.950 TL → BC110/7.990 TL, eski satır replaced, adet1/sürüm2. Kanıt: reports/f09_demo_replace.txt. Ana demo Q1004 prova sırasında değiştirilmedi.
