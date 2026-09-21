import { useState } from "react";
import { RefreshControl, ScrollView, Text, View } from "react-native";
import type { Quote as QuoteDTO, QuoteLine } from "@tbr/contracts";
import { Button, Label, money, Row, ui, usePalette } from "../shared/ui";
export function Quote({
  quote,
  stale,
  updated,
  refresh,
}: {
  quote: QuoteDTO | null;
  stale: boolean;
  updated: string;
  refresh: () => void;
}) {
  const c = usePalette();
  const [history, setHistory] = useState(false);
  function line(p: QuoteLine) {
    return (
      <View
        key={p.quote_item_id}
        style={[ui.separator, { borderColor: c.line, gap: 8 }]}
      >
        <Text style={[ui.heading, { color: c.ink }]}>{p.name_tr}</Text>
        <Label muted>{p.sku}</Label>
        <Label muted>
          {p.status === "replaced"
            ? "Değiştirildi"
            : p.status === "removed"
              ? "Kaldırıldı"
              : p.fulfillment_status === "backorder"
                ? "Beklemeli"
                : p.fulfillment_status === "out_of_stock"
                  ? "Stok dışı"
                  : "Stoklu"}
        </Label>
        <Row label="Adet" value={String(p.quantity)} />
        <Row label="Birim" value={money(p.unit_price_try)} />
        <Row label="Brüt" value={money(p.gross_total_try)} />
        <Row label="İndirim" value={money(p.discount_total_try)} />
        <Row label="Net" value={money(p.net_total_try)} />
        {p.rule_ids.length > 0 && (
          <Label muted>Kurallar: {p.rule_ids.join(", ")}</Label>
        )}
      </View>
    );
  }
  return (
    <ScrollView
      contentContainerStyle={ui.content}
      refreshControl={
        <RefreshControl
          refreshing={false}
          onRefresh={refresh}
          tintColor={c.blue}
        />
      }
    >
      <Text accessibilityRole="header" style={[ui.title, { color: c.ink }]}>
        Teklif taslağı
      </Text>
      {stale && (
        <Text accessibilityRole="alert" style={[ui.body, { color: c.error }]}>
          Bağlantı kesildi; son kayıtlı görünüm gösteriliyor.
        </Text>
      )}
      <Label muted>
        {quote
          ? `${quote.quote_id} · Sürüm ${quote.version}`
          : "Teklif yükleniyor…"}
      </Label>
      {!!updated && <Label muted>Son başarılı kontrol: {updated}</Label>}
      <Button onPress={refresh}>Teklifi yenile</Button>
      {quote && (
        <>
          <View style={[ui.section, { backgroundColor: c.surface }]}>
            <Label>{quote.customer_name}</Label>
            <Row label="Brüt toplam" value={money(quote.gross_total_try)} />
            <Row label="İndirim" value={money(quote.discount_total_try)} />
            <Row label="Net teklif" value={money(quote.net_total_try)} />
          </View>
          <Label muted>Taslak stok rezervasyonu yapmaz.</Label>
          {quote.items.length ? (
            quote.items.map(line)
          ) : (
            <Label>Bu teklif henüz boş. Sohbetten ürün ekleyebilirsin.</Label>
          )}
          {quote.rule_ids.length > 0 && (
            <Label muted>Uygulanan kurallar: {quote.rule_ids.join(", ")}</Label>
          )}
          {quote.history.length > 0 && (
            <>
              <Button onPress={() => setHistory((v) => !v)}>
                {history
                  ? "Geçmişi gizle"
                  : `Kalem geçmişi (${quote.history.length})`}
              </Button>
              {history && quote.history.map(line)}
            </>
          )}
        </>
      )}
    </ScrollView>
  );
}
