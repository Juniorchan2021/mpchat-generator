import type { Metadata } from "next";
import Link from "next/link";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "MPChat v5",
  description: "MPChat Apple HIG frontend powered by Next.js + FastAPI",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <div className="app-shell">
          <header className="topbar">
            <div>
              <span className="eyebrow">MPChat</span>
              <strong className="brand-title">Content Operating System</strong>
            </div>
            <nav className="nav-pills">
              <Link href="/">工作台</Link>
              <Link href="/external">外部文章</Link>
              <Link href="/history">历史</Link>
            </nav>
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}
