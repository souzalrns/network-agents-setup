const TZ = "Europe/Lisbon";

export function fmtDate(d: Date | string | null | undefined, opts: Intl.DateTimeFormatOptions = { day: "numeric", month: "short", year: "numeric" }): string {
  if (!d) return "";
  const date = typeof d === "string" ? new Date(d.length === 10 ? `${d}T12:00:00Z` : d) : d;
  return new Intl.DateTimeFormat("pt-PT", { timeZone: TZ, ...opts }).format(date);
}
export const fmtDateTime = (d: Date | string | null | undefined) =>
  fmtDate(d, { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
export const fmtShort = (d: Date | string | null | undefined) => fmtDate(d, { day: "numeric", month: "short" });

export function relTime(d: Date | string | null | undefined): string {
  if (!d) return "";
  const date = typeof d === "string" ? new Date(d) : d;
  const s = Math.round((Date.now() - date.getTime()) / 1000);
  const rtf = new Intl.RelativeTimeFormat("pt-PT", { numeric: "auto" });
  const abs = Math.abs(s);
  if (abs < 60) return rtf.format(-s, "second");
  if (abs < 3600) return rtf.format(-Math.round(s / 60), "minute");
  if (abs < 86400) return rtf.format(-Math.round(s / 3600), "hour");
  if (abs < 30 * 86400) return rtf.format(-Math.round(s / 86400), "day");
  return fmtDate(date);
}

/** Data/hora local de Lisboa para um <input type="datetime-local"> e de volta. */
export function toLocalInput(d: Date | null | undefined): string {
  if (!d) return "";
  const parts = new Intl.DateTimeFormat("sv-SE", { timeZone: TZ, year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" }).format(d);
  return parts.replace(" ", "T");
}
export function fromLocalInput(v: string): Date | null {
  if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(v)) return null;
  // descobre o desfasamento de Lisboa nessa data
  const guess = new Date(`${v}:00Z`);
  const lisbon = new Date(guess.toLocaleString("en-US", { timeZone: TZ }));
  const utc = new Date(guess.toLocaleString("en-US", { timeZone: "UTC" }));
  return new Date(guess.getTime() - (lisbon.getTime() - utc.getTime()));
}
