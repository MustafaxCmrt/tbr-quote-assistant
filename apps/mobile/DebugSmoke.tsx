import { useEffect, useRef, useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StatusBar, StyleSheet, Text, View } from "react-native";
import { SafeAreaProvider, SafeAreaView } from "react-native-safe-area-context";
import { fetch } from "expo/fetch";
import { createSseParser, type SseEvent } from "@tbr/contracts";

export default function App() {
  const [lines, setLines] = useState<string[]>([]);
  const [status, setStatus] = useState("Teste hazır");
  const [error, setError] = useState(false);
  const [busy, setBusy] = useState(false);
  const active = useRef<AbortController | null>(null);
  useEffect(() => () => active.current?.abort(), []);

  async function startTest() {
    if (active.current) return;
    const baseUrl = process.env.EXPO_PUBLIC_API_BASE_URL?.trim().replace(/\/+$/, "");
    if (!baseUrl || !/^https?:\/\//.test(baseUrl)) {
      setError(true);
      setStatus("API adresi eksik. .env dosyasına EXPO_PUBLIC_API_BASE_URL yazıp Expo’yu yeniden başlat.");
      return;
    }
    const controller = new AbortController();
    active.current = controller;
    const timeout = setTimeout(() => controller.abort(), 15000);
    setBusy(true);
    setError(false);
    setLines([]);
    setStatus("Bağlanıyor…");
    let reader: ReadableStreamDefaultReader<Uint8Array> | undefined;
    try {
      const response = await fetch(`${baseUrl}/api/debug/stream-smoke`, {
        method: "POST",
        headers: { Accept: "text/event-stream", "Content-Type": "application/json" },
        body: JSON.stringify({}),
        signal: controller.signal,
      });
      if (!response.ok) {
        throw new Error(response.status === 404
          ? "Test endpoint’i kapalı. API’yi DEBUG_STREAM_SMOKE=1 ile başlat."
          : "API isteği başarısız. Sunucuyu kontrol edip tekrar dene.");
      }
      if (!response.body || !response.headers.get("content-type")?.includes("text/event-stream")) {
        throw new Error("API beklenen olay akışını göndermedi.");
      }
      reader = response.body.getReader();
      const parser = createSseParser();
      const started = Date.now();
      let completed = false;
      function showEvent(event: SseEvent) {
        const payload: unknown = JSON.parse(event.data);
        if (typeof payload !== "object" || payload === null || !("debug" in payload) || payload.debug !== true) {
          throw new Error("Beklenmeyen test yanıtı alındı.");
        }
        if (event.event === "text_delta" && "text" in payload && typeof payload.text === "string") {
          const text = payload.text;
          const elapsed = ((Date.now() - started) / 1000).toFixed(1);
          setLines((previous) => [...previous, `${elapsed} sn · ${text}`]);
          setStatus("Akış sürüyor…");
        } else if (event.event === "done") {
          completed = true;
          setStatus("Tamamlandı");
        } else {
          throw new Error("Beklenmeyen test olayı alındı.");
        }
      }
      while (!completed) {
        const chunk = await reader.read();
        if (chunk.done) {
          parser.finish().forEach(showEvent);
          break;
        }
        for (const event of parser.push(chunk.value)) {
          showEvent(event);
          if (completed) break;
        }
      }
      if (!completed) throw new Error("Bağlantı tamamlanmadan kesildi. Tekrar dene.");
    } catch (cause) {
      setError(true);
      // Fetch exceptions can contain hostnames; only our controlled messages are shown.
      const controlled = cause instanceof Error && [
        "Test endpoint’i kapalı.", "API isteği başarısız.", "API beklenen", "Beklenmeyen test", "Bağlantı tamamlanmadan",
      ].some((prefix) => cause.message.startsWith(prefix));
      setStatus(controlled && cause instanceof Error ? cause.message :
        "Bağlantı kurulamadı veya zaman aşımına uğradı. Aynı Wi-Fi ağını ve API’nin açık olduğunu kontrol edip tekrar dene.");
    } finally {
      clearTimeout(timeout);
      await reader?.cancel().catch(() => undefined);
      reader?.releaseLock();
      active.current = null;
      setBusy(false);
    }
  }

  return (
    <SafeAreaProvider>
      <SafeAreaView style={styles.safe}>
        <StatusBar barStyle="dark-content" />
        <ScrollView contentContainerStyle={styles.content}>
          <Text accessibilityRole="header" style={styles.title}>Stream testi</Text>
          <Text style={styles.description}>Geçici debug ekranı. API’den gelen iki metin parçasını sırayla gösterir; teklif verisini değiştirmez.</Text>
          <Pressable accessibilityRole="button" accessibilityState={{ disabled: busy, busy }} disabled={busy}
            onPress={() => void startTest()} style={({ pressed }) => [styles.button, (pressed || busy) && styles.buttonDim]}>
            {busy && <ActivityIndicator color="#fff" />}
            <Text style={styles.buttonText}>{busy ? "Test sürüyor…" : "Stream testi"}</Text>
          </Pressable>
          <Text accessibilityRole={error ? "alert" : "text"} accessibilityLiveRegion="polite"
            style={[styles.status, error && styles.error]}>{status}</Text>
          <View style={styles.events}>
            {lines.length === 0 ? <Text style={styles.description}>Gelen parçalar burada görünecek.</Text> :
              lines.map((line, index) => <Text key={index} style={styles.line}>{line}</Text>)}
          </View>
        </ScrollView>
      </SafeAreaView>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: "#F5F7FA" },
  content: { padding: 24, gap: 20, width: "100%", maxWidth: 640, alignSelf: "center" },
  title: { fontSize: 30, fontWeight: "700", color: "#14233B" },
  description: { fontSize: 17, lineHeight: 25, color: "#46566D" },
  button: { minHeight: 52, padding: 16, backgroundColor: "#1649A2", borderRadius: 12, flexDirection: "row", gap: 12, justifyContent: "center", alignItems: "center" },
  buttonDim: { opacity: 0.7 },
  buttonText: { color: "#fff", fontSize: 18, fontWeight: "600" },
  status: { fontSize: 18, fontWeight: "600", color: "#14233B" },
  error: { color: "#A3212C" },
  events: { gap: 16, borderTopWidth: 1, borderTopColor: "#CCD4E0", paddingTop: 20 },
  line: { fontSize: 17, lineHeight: 26, color: "#14233B" },
});
