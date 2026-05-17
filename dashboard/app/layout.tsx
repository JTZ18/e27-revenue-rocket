import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Boldr Intel Engine",
  description: "Read-only state viewer for the self-improving customer-intelligence system.",
};

const nav = [
  { href: "/", label: "Status" },
  { href: "/kb", label: "KB" },
  { href: "/gaps", label: "Gaps" },
  { href: "/themes", label: "Themes" },
  { href: "/personas", label: "Personas" },
  { href: "/briefs", label: "Briefs" },
  { href: "/sentiment", label: "Sentiment" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="min-h-screen flex">
          <aside className="w-56 border-r border-[var(--color-border)] p-6 flex flex-col gap-1">
            <div className="text-xl font-semibold mb-6">Boldr Intel</div>
            <nav className="flex flex-col gap-1 text-sm">
              {nav.map((item) => (
                <Link key={item.href} href={item.href} className="px-2 py-1 rounded hover:bg-[var(--color-card)]">
                  {item.label}
                </Link>
              ))}
            </nav>
            <div className="mt-auto text-xs text-[var(--color-muted)]">Read-only view.</div>
          </aside>
          <main className="flex-1 p-8 max-w-5xl">{children}</main>
        </div>
      </body>
    </html>
  );
}
