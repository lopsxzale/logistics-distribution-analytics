"use client";

import Link from "next/link";
import { useEffect } from "react";

// Export estático não tem servidor para negociar idioma: decide no navegador.
export default function RootRedirect() {
  useEffect(() => {
    const lang = navigator.language?.toLowerCase().startsWith("pt") ? "pt" : "en";
    window.location.replace(`/${lang}/`);
  }, []);

  return (
    <main className="grid min-h-screen place-items-center text-sm text-muted">
      <noscript>
        <meta httpEquiv="refresh" content="0; url=/pt/" />
      </noscript>
      <Link href="/pt/">Combustível & Logística →</Link>
    </main>
  );
}
