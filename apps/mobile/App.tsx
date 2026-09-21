import { useCallback, useEffect, useRef, useState } from "react";
import {
  AppState,
  Modal,
  ScrollView,
  StatusBar,
  Text,
  View,
  useColorScheme,
} from "react-native";
import { SafeAreaProvider, SafeAreaView } from "react-native-safe-area-context";
import type { Quote as QuoteDTO } from "@tbr/contracts";
import { api } from "./src/api";
import { acceptQuote } from "./src/api/state";
import { Chat } from "./src/screens/Chat";
import { Quote } from "./src/screens/Quote";
import { Button, Label, ui, usePalette } from "./src/shared/ui";
import DebugSmoke from "./DebugSmoke";

interface Customer {
  customer_id: string;
  name: string;
  city: string;
}
interface Summary {
  quote_id: string;
  version: number;
}
function Workspace() {
  const c = usePalette();
  const dark = useColorScheme() === "dark";
  const [customers, setCustomers] = useState<Customer[]>([]),
    [customer, setCustomer] = useState("");
  const [quotes, setQuotes] = useState<Summary[]>([]),
    [quoteId, setQuoteId] = useState(""),
    [quote, setQuote] = useState<QuoteDTO | null>(null);
  const [stale, setStale] = useState(false),
    [updated, setUpdated] = useState(""),
    [error, setError] = useState("");
  const [tab, setTab] = useState<"chat" | "quote">("chat"),
    [context, setContext] = useState(false),
    [busy, setBusy] = useState(false),
    [retry, setRetry] = useState(0);
  const selected = useRef("");
  selected.current = quoteId;
  useEffect(() => {
    let live = true;
    api
      .request<Customer[]>("/api/customers")
      .then((rows) => {
        if (live) {
          setCustomers(rows);
          setCustomer(
            (current) =>
              current ||
              rows.find((r) => r.customer_id === "CUST-IST-001")?.customer_id ||
              rows[0]?.customer_id ||
              "",
          );
          setError("");
        }
      })
      .catch((e) => live && setError(e.message));
    return () => {
      live = false;
    };
  }, [retry]);
  useEffect(() => {
    let live = true;
    setQuoteId("");
    setQuote(null);
    setQuotes([]);
    setUpdated("");
    if (customer)
      api
        .request<Summary[]>(
          "/api/quotes?customer_id=" + encodeURIComponent(customer),
        )
        .then((rows) => {
          if (live) {
            setQuotes(rows);
            setQuoteId(rows[0]?.quote_id ?? "");
            setError("");
          }
        })
        .catch((e) => live && setError(e.message));
    return () => {
      live = false;
    };
  }, [customer, retry]);
  const refresh = useCallback(() => {
    const id = selected.current;
    if (!id) return;
    void api
      .request<QuoteDTO>("/api/quotes/" + encodeURIComponent(id))
      .then((next) => {
        if (selected.current !== id) return;
        setQuote((prev) => acceptQuote(prev, next, id));
        setStale(false);
        setUpdated(new Date().toLocaleTimeString("tr-TR"));
      })
      .catch(() => {
        if (selected.current === id) setStale(true);
      });
  }, []);
  useEffect(() => {
    setQuote(null);
    setUpdated("");
    setStale(false);
    refresh();
    const timer = setInterval(() => {
      if (AppState.currentState === "active") refresh();
    }, 2500);
    const subscription = AppState.addEventListener("change", (state) => {
      if (state === "active") refresh();
    });
    return () => {
      clearInterval(timer);
      subscription.remove();
    };
  }, [quoteId, refresh]);
  return (
    <SafeAreaView style={[ui.flex, { backgroundColor: c.bg }]}>
      <StatusBar barStyle={dark ? "light-content" : "dark-content"} />
      <View
        style={{
          padding: 16,
          gap: 10,
          borderBottomWidth: 1,
          borderColor: c.line,
          backgroundColor: c.surface,
        }}
      >
        <View style={ui.row}>
          <Text
            accessibilityRole="header"
            style={[ui.heading, { color: c.ink }]}
          >
            The Blue Red
          </Text>
          <Button disabled={busy} onPress={() => setContext(true)}>
            Müşteri / teklif
          </Button>
        </View>
        <Text style={[ui.caption, { color: c.muted }]}>
          {customers.find((x) => x.customer_id === customer)?.name ??
            "Bağlanıyor…"}{" "}
          · {quoteId}
        </Text>
      </View>
      {!!error && (
        <View style={ui.content}>
          <Text accessibilityRole="alert" style={[ui.body, { color: c.error }]}>
            {error}
          </Text>
          <Button onPress={() => setRetry((v) => v + 1)}>Tekrar bağlan</Button>
        </View>
      )}
      {stale && tab === "chat" && (
        <Text
          accessibilityRole="alert"
          style={[ui.caption, { color: c.error, padding: 12 }]}
        >
          Bağlantı kesildi. Son kontrol {updated || "yapılamadı"}; teklif
          ekranından yenileyebilirsin.
        </Text>
      )}
      <View style={[ui.flex, { display: tab === "chat" ? "flex" : "none" }]}>
        {quoteId ? (
          <Chat
            key={quoteId}
            quoteId={quoteId}
            customerId={customer}
            refresh={refresh}
            onBusy={setBusy}
          />
        ) : (
          <View style={ui.content}>
            <Label>Hazır teklif bekleniyor.</Label>
          </View>
        )}
      </View>
      <View style={[ui.flex, { display: tab === "quote" ? "flex" : "none" }]}>
        <Quote
          quote={quote}
          stale={stale}
          updated={updated}
          refresh={refresh}
        />
      </View>
      <View
        accessibilityRole="tablist"
        style={{
          flexDirection: "row",
          gap: 12,
          padding: 12,
          borderTopWidth: 1,
          borderColor: c.line,
          backgroundColor: c.surface,
        }}
      >
        <View style={ui.flex}>
          <Button selected={tab === "chat"} primary={tab === "chat"} onPress={() => setTab("chat")}>
            Sohbet
          </Button>
        </View>
        <View style={ui.flex}>
          <Button
            selected={tab === "quote"}
            primary={tab === "quote"}
            onPress={() => {
              setTab("quote");
              refresh();
            }}
          >
            Teklif
          </Button>
        </View>
      </View>
      <Modal
        visible={context}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setContext(false)}
      >
        <SafeAreaView style={[ui.flex, { backgroundColor: c.bg }]}>
          <ScrollView contentContainerStyle={ui.content}>
            <Button onPress={() => setContext(false)}>Tamam</Button>
            <Text
              accessibilityRole="header"
              style={[ui.title, { color: c.ink }]}
            >
              Demo bağlamı
            </Text>
            <Label muted>
              Müşteri değişince yeni sohbet başlar. Kayıtlı teklif korunur.
            </Label>
            {customers.map((item) => (
              <Button
                key={item.customer_id}
                primary={customer === item.customer_id}
                onPress={() => setCustomer(item.customer_id)}
              >
                {item.name} · {item.city}
              </Button>
            ))}
            <Text
              accessibilityRole="header"
              style={[ui.heading, { color: c.ink }]}
            >
              Hazır teklifler
            </Text>
            {quotes.map((item) => (
              <Button
                key={item.quote_id}
                primary={quoteId === item.quote_id}
                onPress={() => {
                  setQuoteId(item.quote_id);
                  setContext(false);
                }}
              >
                {item.quote_id}
              </Button>
            ))}
          </ScrollView>
        </SafeAreaView>
      </Modal>
    </SafeAreaView>
  );
}
export default function App() {
  if (process.env.EXPO_PUBLIC_DEBUG_STREAM_SMOKE === "1") return <DebugSmoke />;
  return (
    <SafeAreaProvider>
      <Workspace />
    </SafeAreaProvider>
  );
}
