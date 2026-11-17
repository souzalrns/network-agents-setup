import type { NextConfig } from "next";

const config: NextConfig = {
  // o driver de Postgres corre no servidor tal como está
  serverExternalPackages: ["postgres"],
  poweredByHeader: false,
  // o build verifica a aplicação; os testes verificam-se com `npm run typecheck`
  typescript: { tsconfigPath: "tsconfig.build.json" },
  async headers() {
    return [{
      source: "/:path*",
      headers: [
        { key: "X-Content-Type-Options", value: "nosniff" },
        { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
        { key: "X-Frame-Options", value: "DENY" },
        { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
      ],
    }, {
      source: "/redacao/:path*",
      headers: [{ key: "X-Robots-Tag", value: "noindex, nofollow" }, { key: "Cache-Control", value: "no-store" }],
    }];
  },
};

export default config;
