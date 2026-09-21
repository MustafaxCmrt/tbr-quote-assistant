# Native keyboard fix


## F07 kaynak ve klavye cihaz gözlemi — 2026-09-21 19:38–19:39
Mustafa: “klavye açıkken göndere ulaşamıyorum klavye butonun üstünde kalıyor” — **failed**.
Önceki durum: reports/images/f07/native-keyboard-overlap-before.png.
Mustafa Bilgi kaynağına basıp Kapat ile kapanmasını doğruladı — **passed (insan gözlemi)**.
Yanıt/kaydırma/kaynak düğmeleri: native-policy-response.png, native-policy-sources.png. Statik görüntüler zamanlama kanıtı değildir; streaming timing not_verified.
Salt okunur API kontrolünde yeni mobile mesaj ea204128-43f4-456c-a509-6f66a3495678 yalnız get_knowledge_entries ×2/get_quote çağırmış, mutation_applied sayısı0.

Düzeltme: nested Chat KeyboardAvoidingView kaldırıldı; tek KAV ekran kökünde SafeAreaView'ı sarar (iOS padding, Android height).
Kurulu RN hesaplaması yerel frame ile keyboard screenY'yi karşılaştırıyordu; root yerleşimi koordinat farkını kaldırır. Sabit cihaz/header yüksekliği tahmin edilmedi.
Kaynak: https://reactnative.dev/docs/keyboardavoidingview ; kurulu node_modules/react-native/Libraries/Components/Keyboard/KeyboardAvoidingView.js.
Bağımsız Codex native reviewer kaynak diff'inde yeni koordinat/flex hatası bulmadı; fiziksel tekrar kontrolü **not_verified**.
`npm run typecheck`, `npm run lint`, iOS export exit0: reports/f07_keyboard_typecheck.txt, f07_keyboard_lint.txt, f07_keyboard_ios.txt.
Mustafa'dan Reload ardından klavye açıkken input/Gönder ve akışın kademeli olup olmadığını tekrar gözlemesi istendi. F07 açık.
