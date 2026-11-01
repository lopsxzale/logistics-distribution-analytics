"use client";

import { useEffect, useRef, useState } from "react";

/** Largura do container, atualizada no resize (gráficos SVG responsivos). */
export function useWidth<T extends HTMLElement>(initial = 640) {
  const ref = useRef<T>(null);
  const [width, setWidth] = useState(initial);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    // Ignora largura 0 (elemento escondido durante a troca gráfico/tabela).
    const ro = new ResizeObserver(([entry]) => {
      const w = Math.round(entry.contentRect.width);
      if (w > 0) setWidth(w);
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  return [ref, width] as const;
}
