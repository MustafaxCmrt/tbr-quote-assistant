---
name: The Blue Red Admin
description: Türkçe, sade ve okunur teklif çalışma alanı.
colors:
  blue: "#0a67a8"
  blue-hover: "#085b93"
  blue-deep: "#084d80"
  blue-tint: "#e4f1fb"
  red: "#c8171d"
  ink: "#172840"
  muted: "#53647b"
  line: "#d6dee8"
  line-soft: "#e6ecf2"
  surface: "#fff"
  canvas: "#f4f7fa"
  tag-surface: "#eef2f7"
  tag-ink: "#40516a"
  warning-surface: "#fff2df"
  warning-ink: "#96500b"
  error-ink: "#a01f31"
  notice-surface: "#e7f3ed"
  notice-ink: "#18553f"
  field-line: "#8797ad"
typography:
  headline:
    fontSize: "clamp(1.65rem, 2.5vw, 2.25rem)"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.025em"
  title:
    fontSize: "1.18rem"
    lineHeight: 1.35
  body:
    fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
    lineHeight: 1.5
  supporting:
    fontSize: "0.875rem"
  label:
    fontSize: "0.8rem"
    fontWeight: 600
  tag:
    fontSize: "0.72rem"
    fontWeight: 600
rounded:
  panel: "10px"
  button: "7px"
  field: "6px"
  tag: "5px"
spacing:
  compact: "8px"
  small: "12px"
  medium: "16px"
  form: "18px"
  panel: "24px"
  page: "32px"
components:
  button-primary:
    backgroundColor: "{colors.blue}"
    textColor: "{colors.surface}"
    rounded: "{rounded.button}"
    padding: "9px 16px"
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.blue}"
    rounded: "{rounded.button}"
    padding: "9px 16px"
  button-text:
    backgroundColor: "transparent"
    textColor: "{colors.blue}"
    padding: "8px 0"
  field:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.field}"
    padding: "10px 12px"
  panel:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.panel}"
    padding: "24px"
  tag:
    backgroundColor: "{colors.tag-surface}"
    textColor: "{colors.tag-ink}"
    rounded: "{rounded.tag}"
    padding: "3px 7px"
---

# Design System: The Blue Red Admin

## Overview

**Creative North Star: "Teklif çalışma alanı"**

Mevcut arayüzün kendi adını taşıyan bu sistem, açık yüzeyli ve yoğunluğu kontrollü bir B2B yönetim ekranıdır. Mavi eylemleri ve gezinmeyi, kırmızı marka vurgusunu ve alan hatalarını taşır. Türkçe metin, kayıtlı değerler ve kaynak kimlikleri görsel süsten önce gelir.

Bu belge mevcut uygulamanın kaydıdır; yeni bir görsel kimlik önermez. Kaynak: `src/style.css`, `src/main.tsx`, `src/features/QuotePanel.tsx`, `src/features/Logs.tsx`; görsel kanıt: `../../reports/images/f06/chat-desktop-final.png`.

**Key Characteristics:**

- Açık zemin, beyaz çalışma yüzeyleri.
- Türkçe, metinle açıklanan durumlar.
- Hizalı sayılar ve açılabilir ayrıntılar.

## Colors

Mavi ve kırmızı marka renkleri, serin nötr yüzeyler üzerinde kullanılır. Frontmatter mevcut CSS değerlerini kaydeder; uygulamadaki kaynak `src/style.css` dosyasıdır ve her değer orada `--token` olarak tanımlıdır.

22 Eylül 2026: firmanın gerçek logosu (`src/assets/bluered-logo.png`, sitesindeki footer markası; beyaz "the" açık yüzey için mürekkep rengine boyandı) eklendi ve palet ona hizalandı. Logo mavisi (#0a8ad0) beyaz üzerinde 3.8:1 kaldığı için işlem mavisi aynı tonun koyusudur: `blue` #0a67a8 beyaz metinle 5.97:1, `field-line` #8797ad 2.97:1 (eski #aebccb 1.93:1 idi). Kırmızı logonun sinyal kırmızısına yaklaştırıldı (#c8171d, 5.84:1). Karanlık tema web'de bilinçli olarak yok; mobil sistem temasını izler.

- **Primary — İşlem mavisi:** Birincil buton, bağlantı, odak halkası ve gezinme vurgusu. `blue-tint` etkin gezinme ve kullanıcı mesajı zemini, `blue-deep` bu zemindeki metin.
- **Secondary — Marka kırmızısı:** Yalnız logo ve geçersiz alan kenarlığı. Hata metni ayrı `error-ink` tonunu kullanır.
- **Neutral — Koyu mürekkep, ikincil metin, çizgi, beyaz yüzey ve açık tuval:** İçerik hiyerarşisi ve bölümler.
- **Status — Kehribar uyarı:** Stok dışı/beklemeli gibi durumlar; anlamı her zaman Türkçe etiket açıklar.

**The Açık Durum Rule.** Durum yalnız renkle anlatılmaz; görünür metinle adlandırılır.

## Typography

Gövde, alanlar ve butonlar mevcut sistem yazı tipi yığınını paylaşır. Sayfa başlığı için ayrı bir marka/display yazı tipi tanımlanmamıştır; bu kayıt yeni bir display fontu şartı oluşturmaz.

Başlık ve etiket ölçeği frontmatter'dadır. Bölüm alt başlıkları (1rem), tablolar (0.84rem), yardımcı küçük metin (0.77rem) kullanır. Para ve adet sütunları sağa yaslı, tabular rakamlıdır. Kaynak metni satır sonlarını korur, uzun sözcükleri kırar ve 75ch ile sınırlanır.

## Layout

Masaüstü kabuk 210px sabit gezinme sütunu ve esnek çalışma alanından oluşur. İçerik en fazla 1600px genişler. Üst bağlam çubuğunda müşteri ve teklif seçilir. Teklif/sohbet alanı 1.3fr ve en az 330px olan 1fr sütunlarını, 28px boşlukla kullanır.

1180px ve altında çalışma panelleri tek sütuna, form üç sütundan ikiye geçer; sayfa dolgusu 24px olur. 700px ve altında gezinme üstte 2×2 buton ızgarasına, form tek sütuna geçer; sayfa yatay dolgusu 16px, panel dolgusu 18px olur. Tablolar `TableScroll` kapsayıcısında yatay kayar; sağda kalan sütun varken kenar 36px solar (`.has-more`), tablo sığınca veya sona kaydırılınca solma kalkar. Sohbet alanı masaüstünde 480px, ara genişlikte 400px, dar ekranda 360px yüksekliğinde kaydırılır. Görsel kanıt: `../../reports/images/design/`.

## Elevation & Depth

Mevcut sistemde kutu gölgesi yoktur. Beyaz yüzey, açık tuval ve ince ayırıcılar bölümleri tanımlar. Etkileşim odağı mavi dış çizgiyle belirtilir; dekoratif yükselme veya dönüşüm yoktur.

## Shapes

Köşeler hafif yuvarlatılmıştır: panel, buton, alan ve etiket yarıçapları frontmatter'da ayrı tutulur. Alanlar ve ikincil butonlar ince kenarlık kullanır. Kullanıcı mesajının yumuşak köşeli açık mavi yüzeyi sohbet içindeki konuşmacıyı ayırır.

## Components

- **Butonlar:** Mavi ana eylem; çizgili ikincil yenileme; metin biçiminde tekrar gönderme. Standart buton en az 42px, metin butonu 36px yüksekliğindedir. Hover renk değişimi 150ms ease-out; disabled durum opaklığı 0.55 ve not-allowed imlecidir.
- **Odak:** Buton, bağlantı, alan, seçim, metin alanı ve açılır ayrıntıda 3px mavi outline ve 3px offset. Azaltılmış hareket tercihinde geçişler kapanır.
- **Alanlar:** Üstte görünür etiket, beyaz yüzey, ince kenarlık, en az 43px yükseklik. Geçersiz giriş kırmızı kenarlık ve ilgili hata metniyle gösterilir.
- **Marka:** Sol üstte logo görseli (en fazla 150px, dar ekranda 124px), altında "Teklif asistanı" alt yazısı. Sekme ikonu iki renkli SVG data URI; ayrı ikon sistemi yoktur.
- **Gezinme:** Sol menüde etkin sayfa açık mavi yüzey, koyu mavi yazı ve `aria-current` ile belirtilir. Dar ekranda 2×2 ızgara, çerçeveli butonlar.
- **Etiketler:** Kompakt, metin içeren nötr veya kehribar durum işaretleri. Uzun metinler etiket içine zorlanmaz.
- **Teklif:** Tablo ve sağa hizalı toplam grubu kayıtlı tutarları gösterir; net toplam kalın ve daha büyüktür. Sürüm, son kontrol ve eski veri uyarısı görünürdür. Geçmiş ve fiyat kuralları açılabilir ayrıntılardır.
- **Kaynaklar ve kayıtlar:** Açılabilir metin blokları ayrıntıyı erişilebilir tutar. Kayıt girdisi/sonucu sarılan, kendi içinde kayan kod bloğunda gösterilir; kaynak kimliği metinde korunur.

## Do's and Don'ts

- **Do** Türkçe etiketleri ve görünür durum açıklamalarını koru.
- **Do** Yeni ekranlarda mevcut alan, buton, tablo ve panel biçimlerini kullan.
- **Do** Para ve miktarları sunucunun kayıtlı cevabından göster.
- **Don't** İstemcide fiyat veya iyimser miktar hesaplayarak görünümü değiştir.
- **Don't** Görsel süs için yoğun animasyon, ikinci UI kütüphanesi veya özgün ikon sistemi ekle.
