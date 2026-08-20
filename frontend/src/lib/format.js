export function formatPrice(value, digits = 0) {
  return value.toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

export function formatSigned(value, digits = 1) {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(digits)}`;
}

export function formatLabel(id) {
  return id.replace(/_/g, " ");
}

const SUFFIX_LABELS = [
  { suffix: "_lag1", tag: "1mo lag" },
  { suffix: "_lag3", tag: "3mo lag" },
  { suffix: "_lag6", tag: "6mo lag" },
  { suffix: "_roll3", tag: "3mo avg" },
];

// e.g. "crude_oil_price_roll3" -> "Crude Oil Price (3mo avg)"
export function formatFeatureLabel(feature) {
  const match = SUFFIX_LABELS.find((s) => feature.endsWith(s.suffix));
  if (!match) return formatLabel(feature);
  const base = feature.slice(0, -match.suffix.length);
  return `${formatLabel(base)} (${match.tag})`;
}

export function monthLabel(month) {
  const [year, m] = month.split("-");
  const date = new Date(Number(year), Number(m) - 1, 1);
  return date.toLocaleDateString("en-US", { month: "short", year: "2-digit" });
}
