import type { ReactNode } from "react";
import {
  Image,
  Pressable,
  StyleSheet,
  Text,
  useColorScheme,
  View,
} from "react-native";
import logoLight from "../../assets/bluered-logo-light.png";
import logoDark from "../../assets/bluered-logo-dark.png";

// Same brand hue as the web admin: the firm's cyan-blue darkened for contrast
// on light surfaces, lightened on dark ones (both ≥ 4.5:1 against their bg).
const light = {
  bg: "#F5F7FA",
  surface: "#FFFFFF",
  ink: "#172840",
  muted: "#53647B",
  line: "#D6DEE8",
  blue: "#0A67A8",
  error: "#A3212C",
  tint: "#E4F1FB",
};
const dark = {
  bg: "#11151D",
  surface: "#1D2430",
  ink: "#F1F4FA",
  muted: "#B7C3D5",
  line: "#404C5D",
  blue: "#6FC0FF",
  error: "#FFADB7",
  tint: "#22344D",
};
export function usePalette() {
  return useColorScheme() === "dark" ? dark : light;
}
/** The firm's word mark; the light variant inks the white "the" for light surfaces. */
export function Logo({ height = 26 }: { height?: number }) {
  const isDark = useColorScheme() === "dark";
  return (
    <Image
      accessibilityRole="image"
      accessibilityLabel="The Blue Red"
      source={isDark ? logoDark : logoLight}
      resizeMode="contain"
      style={{ height, width: Math.round(height * (1192 / 215)) }}
    />
  );
}
export function Button({
  children,
  onPress,
  disabled = false,
  primary = false,
  selected,
}: {
  children: ReactNode;
  onPress: () => void;
  disabled?: boolean;
  primary?: boolean;
  selected?: boolean;
}) {
  const c = usePalette();
  return (
    <Pressable
      accessibilityRole={selected === undefined ? "button" : "tab"}
      accessibilityState={{ disabled, ...(selected === undefined ? {} : { selected }) }}
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [
        ui.button,
        {
          backgroundColor: primary ? c.blue : c.tint,
          opacity: disabled ? 0.5 : pressed ? 0.75 : 1,
        },
      ]}
    >
      <Text
        style={[
          ui.buttonText,
          { color: primary ? (c === dark ? "#14233B" : "#FFFFFF") : c.blue },
        ]}
      >
        {children}
      </Text>
    </Pressable>
  );
}
export function Label({
  children,
  muted = false,
}: {
  children: ReactNode;
  muted?: boolean;
}) {
  const c = usePalette();
  return (
    <Text style={[ui.body, { color: muted ? c.muted : c.ink }]}>
      {children}
    </Text>
  );
}
export function Row({ label, value }: { label: string; value: string }) {
  return (
    <View style={ui.row}>
      <Label muted>{label}</Label>
      <Label>{value}</Label>
    </View>
  );
}
export const money = (value: string) =>
  new Intl.NumberFormat("tr-TR", { style: "currency", currency: "TRY" }).format(
    Number(value),
  );
export const ui = StyleSheet.create({
  flex: { flex: 1 },
  content: { padding: 20, gap: 16 },
  body: { fontSize: 17, lineHeight: 25 },
  caption: { fontSize: 13, lineHeight: 19 },
  title: { fontSize: 28, fontWeight: "700", letterSpacing: -0.4 },
  heading: { fontSize: 20, fontWeight: "700" },
  subheading: { fontSize: 17, lineHeight: 23, fontWeight: "600" },
  row: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 12,
    flexWrap: "wrap",
  },
  button: {
    minHeight: 48,
    minWidth: 48,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 10,
    justifyContent: "center",
    alignItems: "center",
  },
  buttonText: { fontSize: 16, fontWeight: "600" },
  section: { padding: 16, borderRadius: 12, gap: 12 },
  separator: { borderBottomWidth: 1, paddingBottom: 16, marginBottom: 16 },
});
