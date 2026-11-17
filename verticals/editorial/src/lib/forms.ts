/** Leitura de campos de formulário com limites (nada vem do cliente sem passar por aqui). */
export const str = (f: FormData, k: string, max = 20_000): string => String(f.get(k) ?? "").slice(0, max).trim();
export const opt = (f: FormData, k: string, max = 2_000): string | null => str(f, k, max) || null;
export const lines = (f: FormData, k: string): string[] => str(f, k).split("\n").map((l) => l.trim()).filter(Boolean).slice(0, 50);
export const int = (f: FormData, k: string, min: number, max: number, dflt: number): number => {
  const n = Number(f.get(k));
  return Number.isInteger(n) && n >= min && n <= max ? n : dflt;
};
export const isUuid = (v: unknown): v is string => typeof v === "string" && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(v);
export const isHttpUrl = (v: string): boolean => { try { const u = new URL(v); return u.protocol === "https:" || u.protocol === "http:"; } catch { return false; } };
export const isDate = (v: string): boolean => /^\d{4}-\d{2}-\d{2}$/.test(v);
