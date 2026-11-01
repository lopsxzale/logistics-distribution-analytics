import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { notFound } from "next/navigation";
import Script from "next/script";
import { getDictionary } from "@/i18n";
import { hasLocale, locales } from "@/i18n/config";
import { site } from "@/site.config";
import "../globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const dynamicParams = false;

export function generateStaticParams() {
  return locales.map((lang) => ({ lang }));
}

export async function generateMetadata({ params }: LayoutProps<"/[lang]">): Promise<Metadata> {
  const { lang } = await params;
  if (!hasLocale(lang)) return {};
  const t = getDictionary(lang);
  return {
    ...(site.url ? { metadataBase: new URL(site.url) } : {}),
    // Aba do navegador: curto e objetivo. A manchete completa fica no compartilhamento (OG).
    title: t.meta.tabTitle,
    description: t.meta.description,
    authors: [{ name: site.author }],
    // URLs canônicas exigem domínio absoluto: só entram quando site.url estiver definido.
    ...(site.url
      ? { alternates: { canonical: `/${lang}/`, languages: { "pt-BR": "/pt/", en: "/en/" } } }
      : {}),
    openGraph: {
      type: "website",
      title: t.meta.title,
      description: t.meta.description,
      locale: lang === "pt" ? "pt_BR" : "en_US",
    },
    twitter: { card: "summary_large_image", title: t.meta.title, description: t.meta.description },
  };
}

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f5f6f3" },
    { media: "(prefers-color-scheme: dark)", color: "#0a0c0b" },
  ],
};

// Define o tema antes da primeira pintura (evita o flash de tema errado).
const themeScript = `(function(){try{var t=localStorage.getItem("theme");if(t!=="light"&&t!=="dark"){t=matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light"}document.documentElement.dataset.theme=t}catch(e){document.documentElement.dataset.theme="dark"}})()`;

export default async function LangLayout({ children, params }: LayoutProps<"/[lang]">) {
  const { lang } = await params;
  if (!hasLocale(lang)) notFound();

  return (
    <html
      lang={lang === "pt" ? "pt-BR" : "en"}
      data-theme="dark"
      suppressHydrationWarning
      className={`${geistSans.variable} ${geistMono.variable} antialiased`}
    >
      <body>
        <Script id="theme" strategy="beforeInteractive">
          {themeScript}
        </Script>
        {children}
      </body>
    </html>
  );
}
