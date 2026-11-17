"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

export function NewsroomNav({ items }: { items: { href: string; label: string }[] }) {
  const path = usePathname();
  return (
    <nav className="nr-nav" aria-label="Redação">
      {items.map((i) => {
        const active = i.href === "/redacao" ? path === "/redacao" : path.startsWith(i.href);
        return <Link key={i.href} href={i.href} aria-current={active ? "page" : undefined}>{i.label}</Link>;
      })}
    </nav>
  );
}
