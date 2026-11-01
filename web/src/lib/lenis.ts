import type Lenis from "lenis";

// Instância única do smooth scroll, para pausar em modais/menus.
let instance: Lenis | null = null;

export const setLenis = (lenis: Lenis | null) => {
  instance = lenis;
};

export const lockScroll = (locked: boolean) => {
  if (instance) {
    if (locked) instance.stop();
    else instance.start();
  }
  document.documentElement.style.overflow = locked ? "hidden" : "";
};

export const scrollToId = (id: string) => {
  const el = document.getElementById(id);
  if (!el) return;
  if (instance) instance.scrollTo(el, { offset: -72 });
  else el.scrollIntoView({ behavior: "smooth" });
};
