export function money(n) {
  if (n == null) return "—";
  return new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(n);
}

export function date(d) {
  if (!d) return "—";
  return new Date(d).toLocaleDateString("es-CO", { day: "numeric", month: "short", year: "numeric" });
}

export function relative(d) {
  if (!d) return "";
  const diff = Math.floor((new Date(d) - Date.now()) / 86400000);
  if (diff === 0) return "Hoy";
  if (diff === 1) return "Mañana";
  if (diff < 0) return `Hace ${-diff} días`;
  return `En ${diff} días`;
}

export function truncate(s, n = 100) {
  if (!s) return "";
  return s.length > n ? s.slice(0, n) + "…" : s;
}
