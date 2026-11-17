import type { MetadataRoute } from "next";
import { site } from "@/lib/public";

export default async function robots(): Promise<MetadataRoute.Robots> {
  const { pub, baseUrl } = await site();
  if (!pub.public_launch) return { rules: [{ userAgent: "*", disallow: "/" }] };
  return { rules: [{ userAgent: "*", allow: "/", disallow: ["/redacao", "/api", "/pesquisa"] }], sitemap: `${baseUrl}/sitemap.xml` };
}
