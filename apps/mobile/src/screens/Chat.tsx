import { useEffect, useRef, useState } from "react";
import {
  KeyboardAvoidingView,
  Modal,
  Platform,
  ScrollView,
  Text,
  TextInput,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { randomUUID } from "expo-crypto";
import {
  initialStream,
  reduceChatEvent,
  type Source,
  type ToolName,
} from "@tbr/contracts";
import { api } from "../api";
import { visibleAttemptContent } from "../api/retry";
import { Button, Label, ui, usePalette } from "../shared/ui";

interface Message {
  id: string;
  user: string;
  text: string;
  sources: Source[];
  tools: string[];
  status: string;
  error?: string;
}
const toolText: Record<ToolName, string> = {
  search_products: "Ürünler aranıyor",
  get_knowledge_entries: "Bilgi kaynakları okunuyor",
  get_quote: "Teklif okunuyor",
  add_to_quote: "Ürün ekleniyor",
  update_quote_item: "Miktar güncelleniyor",
  replace_with_alternative: "Alternatif kontrol ediliyor",
};
export function Chat({
  quoteId,
  customerId,
  refresh,
  onBusy,
}: {
  quoteId: string;
  customerId: string;
  refresh: () => void;
  onBusy: (busy: boolean) => void;
}) {
  const c = usePalette();
  const [messages, setMessages] = useState<Message[]>([]),
    [draft, setDraft] = useState(""),
    [busy, setBusy] = useState(false),
    [source, setSource] = useState<Source | null>(null);
  const session = useRef(""),
    active = useRef<AbortController | null>(null),
    mounted = useRef(true),
    scroll = useRef<ScrollView>(null),
    followBottom = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      active.current?.abort();
    };
  }, []);
  function update(id: string, change: Partial<Message>) {
    if (mounted.current)
      setMessages((prev) =>
        prev.map((m) => (m.id === id ? { ...m, ...change } : m)),
      );
  }
  async function send(user: string, id: string = randomUUID()) {
    if (active.current || !user.trim()) return;
    const controller = new AbortController();
    active.current = controller;
    const timer = setTimeout(() => controller.abort(), 45000);
    setBusy(true);
    onBusy(true);
    setDraft("");
    followBottom.current = true;
    setMessages((prev) => prev.some((m) => m.id === id)
      ? prev.map((m) => m.id === id ? { ...m, status: "connecting", error: undefined, tools: [] } : m)
      : [...prev, { id, user, text: "", sources: [], tools: [], status: "connecting" }]);
    try {
      if (!session.current) {
        const created = await api.request<{ session_id: string }>(
          "/api/chat/sessions",
          { customer_id: customerId, quote_id: quoteId, channel: "mobile" },
        );
        session.current = created.session_id;
      }
      let state = initialStream(session.current, id);
      const tools: string[] = [];
      await api.stream(
        {
          session_id: session.current,
          message_id: id,
          quote_id: quoteId,
          message: user,
          channel: "mobile",
        },
        controller.signal,
        (event) => {
          state = reduceChatEvent(state, event);
          if (event.type === "tool_call_start")
            tools.push(toolText[event.payload.name]);
          if (event.type === "tool_call_result")
            tools.push(
              event.payload.replayed
                ? "Tekrar algılandı; teklif değişmedi."
                : event.payload.mutation_applied
                  ? "Teklif kaydedildi."
                  : "Kaynak okundu.",
            );
          update(id, {
            ...visibleAttemptContent(state),
            status: state.status,
            error: state.error,
            tools: [...tools],
          });
          if (
            state.needsRefetch &&
            ["tool_call_result", "done", "error"].includes(event.type)
          )
            refresh();
        },
      );
    } catch {
      update(id, {
        status: "error",
        error:
          "Bağlantı kesildi. İşlem kaydedilmiş olabilir. Teklifi kontrol edip aynı mesajla tekrar dene.",
      });
    } finally {
      clearTimeout(timer);
      active.current = null;
      if (mounted.current) {
        setBusy(false);
        onBusy(false);
        refresh();
      }
    }
  }
  return (
    <KeyboardAvoidingView
      style={ui.flex}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <ScrollView
        ref={scroll}
        contentContainerStyle={ui.content}
        keyboardShouldPersistTaps="handled"
        onScroll={(e) => {
          const { contentOffset, contentSize, layoutMeasurement } =
            e.nativeEvent;
          followBottom.current =
            contentOffset.y + layoutMeasurement.height >=
            contentSize.height - 80;
        }}
        scrollEventThrottle={100}
        onContentSizeChange={() => {
          if (followBottom.current)
            scroll.current?.scrollToEnd({ animated: false });
        }}
      >
        {!messages.length && (
          <View style={ui.section}>
            <Text
              accessibilityRole="header"
              style={[ui.heading, { color: c.ink }]}
            >
              Teklif için ne yapalım?
            </Text>
            <Label muted>
              Ürün ekleyebilir, miktarı değiştirebilir veya iade koşullarını
              sorabilirsin.
            </Label>
            <Button onPress={() => setDraft("İade süresi nedir?")}>
              İade koşullarını sor
            </Button>
          </View>
        )}
        {messages.map((m) => (
          <View
            key={m.id}
            style={[ui.separator, { borderColor: c.line, gap: 12 }]}
          >
            <View style={[ui.section, { backgroundColor: c.tint }]}>
              <Label>{m.user}</Label>
            </View>
            {m.tools.length > 0 && (
              <Text style={[ui.caption, { color: c.muted }]}>
                {m.tools.join("\n")}
              </Text>
            )}
            <Text selectable style={[ui.body, { color: c.ink }]}>
              {m.text || (m.error ? "Yanıt alınamadı." : "İstek işleniyor…")}
            </Text>
            {m.status === "done" && (
              <Text style={[ui.caption, { color: c.muted }]}>Tamamlandı</Text>
            )}
            {m.error && (
              <Text
                accessibilityRole="alert"
                style={[ui.body, { color: c.error }]}
              >
                {m.error}
              </Text>
            )}
            {m.sources.map((s) => (
              <Button
                key={s.kind + ":" + s.source_id}
                onPress={() => setSource(s)}
              >
                {
                  {
                    product: "Ürün",
                    knowledge: "Bilgi",
                    price_rule: "Fiyat kuralı",
                  }[s.kind]
                }{" "}
                · {s.title}
              </Button>
            ))}
            {!busy && (
              <Button onPress={() => void send(m.user, m.id)}>
                {m.error
                  ? "Aynı mesajla tekrar dene"
                  : "Aynı isteği tekrar gönder"}
              </Button>
            )}
          </View>
        ))}
      </ScrollView>
      <View
        style={{
          padding: 16,
          gap: 10,
          borderTopWidth: 1,
          borderColor: c.line,
          backgroundColor: c.surface,
        }}
      >
        <Text style={[ui.caption, { color: c.muted }]}>
          Mesajın · {draft.length}/2000
        </Text>
        <TextInput
          accessibilityLabel="Mesajın"
          multiline
          value={draft}
          onChangeText={setDraft}
          editable={!busy}
          maxLength={2000}
          placeholder="Ürün veya teklif hakkında yaz…"
          placeholderTextColor={c.muted}
          selectionColor={c.blue}
          style={[
            ui.body,
            {
              color: c.ink,
              minHeight: 52,
              maxHeight: 120,
              borderWidth: 1,
              borderColor: c.line,
              borderRadius: 10,
              padding: 12,
              textAlignVertical: "top",
            },
          ]}
        />
        {busy ? (
          <Button onPress={() => active.current?.abort()}>Akışı durdur</Button>
        ) : (
          <Button
            primary
            disabled={!draft.trim()}
            onPress={() => void send(draft.trim())}
          >
            Gönder
          </Button>
        )}
      </View>
      <Modal
        visible={source !== null}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setSource(null)}
      >
        <SafeAreaView style={[ui.flex, { backgroundColor: c.surface }]}>
          <ScrollView contentContainerStyle={ui.content}>
            <Button onPress={() => setSource(null)}>Kapat</Button>
            <Text
              accessibilityRole="header"
              style={[ui.heading, { color: c.ink }]}
            >
              {source?.title}
            </Text>
            <Label muted>{source?.source_id}</Label>
            <Text selectable style={[ui.body, { color: c.ink }]}>
              {source?.excerpt}
            </Text>
            <Label muted>{source?.source}</Label>
          </ScrollView>
        </SafeAreaView>
      </Modal>
    </KeyboardAvoidingView>
  );
}
