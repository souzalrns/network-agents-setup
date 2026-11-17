import { createHash, randomBytes, scrypt as scryptCb, timingSafeEqual } from "node:crypto";
import { promisify } from "node:util";

const scrypt = promisify(scryptCb) as (pw: string, salt: Buffer, len: number, opts: object) => Promise<Buffer>;
const N = 1 << 15, R = 8, P = 1, LEN = 32;

/** scrypt com sal por palavra-passe. Formato: scrypt$N$r$p$sal$hash (base64url). */
export async function hashPassword(password: string): Promise<string> {
  if (password.length < 10) throw new Error("A palavra-passe precisa de pelo menos 10 caracteres.");
  const salt = randomBytes(16);
  const hash = await scrypt(password, salt, LEN, { N, r: R, p: P, maxmem: 64 * 1024 * 1024 });
  return `scrypt$${N}$${R}$${P}$${salt.toString("base64url")}$${hash.toString("base64url")}`;
}

export async function verifyPassword(password: string, stored: string): Promise<boolean> {
  const parts = stored.split("$");
  if (parts.length !== 6 || parts[0] !== "scrypt") return false;
  const [, n, r, p, salt, hash] = parts as [string, string, string, string, string, string];
  const expected = Buffer.from(hash, "base64url");
  try {
    const got = await scrypt(password, Buffer.from(salt, "base64url"), expected.length,
      { N: Number(n), r: Number(r), p: Number(p), maxmem: 64 * 1024 * 1024 });
    return got.length === expected.length && timingSafeEqual(got, expected);
  } catch {
    return false;
  }
}

export const newToken = (bytes = 32): string => randomBytes(bytes).toString("base64url");
export const tokenHash = (token: string): string => createHash("sha256").update(token).digest("hex");
