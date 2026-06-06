// 这个文件是全站外壳，放公共导航、全局样式和默认 SEO 信息。
import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Tool New Terms Radar",
  description:
    "A daily updated radar for rising AI tool terms, low-competition AI keywords, and emerging AI product concepts.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <header className="site-header">
          <Link className="brand" href="/">
            AI Tool New Terms Radar
          </Link>
          <nav className="nav-links" aria-label="Primary navigation">
            <Link href="/">Radar</Link>
            <Link href="/about">Methodology</Link>
          </nav>
        </header>
        {children}
      </body>
    </html>
  );
}
