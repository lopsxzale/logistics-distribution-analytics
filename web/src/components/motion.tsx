"use client";

import { animate, motion, useInView, useReducedMotion } from "motion/react";
import { useEffect, useRef, type ReactNode } from "react";

/** Revela o conteúdo ao entrar na viewport (uma vez). */
export function Reveal({
  children,
  delay = 0,
  y = 28,
  className,
}: {
  children: ReactNode;
  delay?: number;
  y?: number;
  className?: string;
}) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y, filter: "blur(6px)" }}
      whileInView={{ opacity: 1, y: 0, filter: "blur(0px)" }}
      viewport={{ once: true, margin: "0px 0px -12% 0px" }}
      transition={{ duration: 0.9, delay }}
    >
      {children}
    </motion.div>
  );
}

/** Título que sobe palavra por palavra. */
export function SplitText({
  text,
  className,
  delay = 0,
  as: Tag = "h2",
}: {
  text: string;
  className?: string;
  delay?: number;
  as?: "h1" | "h2";
}) {
  const words = text.split(" ");
  return (
    <Tag className={className} aria-label={text}>
      {words.map((word, i) => (
        <span key={i} aria-hidden className="inline-block overflow-hidden pb-[0.12em] align-top">
          <motion.span
            className="inline-block"
            initial={{ y: "105%" }}
            whileInView={{ y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.85, delay: delay + i * 0.045 }}
          >
            {word}
            {i < words.length - 1 ? " " : ""}
          </motion.span>
        </span>
      ))}
    </Tag>
  );
}

/** Número que conta até o valor final ao aparecer. */
export function CountUp({
  value,
  format,
  duration = 1.8,
  className,
}: {
  value: number;
  format: (v: number) => string;
  duration?: number;
  className?: string;
}) {
  const ref = useRef<HTMLSpanElement>(null);
  const textRef = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: "0px 0px -10% 0px" });
  const reduce = useReducedMotion();
  // `format` costuma ser uma função inline; o ref evita reiniciar a animação a cada render.
  const formatRef = useRef(format);
  useEffect(() => {
    formatRef.current = format;
  });

  useEffect(() => {
    if (!inView) return;
    // Escreve direto no DOM: 60 atualizações por segundo sem re-render do React.
    const controls = animate(0, value, {
      duration: reduce ? 0 : duration,
      ease: [0.16, 1, 0.3, 1],
      onUpdate: (v) => {
        if (textRef.current) textRef.current.textContent = formatRef.current(v);
      },
    });
    return () => controls.stop();
  }, [inView, reduce, value, duration]);

  // O texto animado é decorativo; o valor final fica disponível para leitores de tela e SEO.
  return (
    <span ref={ref} className={className}>
      <span className="sr-only">{format(value)}</span>
      <span ref={textRef} aria-hidden>
        {format(0)}
      </span>
    </span>
  );
}

/** Hook: dispara animações dos gráficos quando entram na tela. */
export function useChartInView<T extends Element>() {
  const ref = useRef<T>(null);
  const inView = useInView(ref, { once: true, margin: "0px 0px -15% 0px" });
  return [ref, inView] as const;
}
