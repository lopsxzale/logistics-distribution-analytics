"use client";

import { AnimatePresence, motion } from "motion/react";
import { useEffect, useRef, useState } from "react";
import type { SqlId } from "@/lib/data";
import { lockScroll } from "@/lib/lenis";
import { site } from "@/site.config";
import { useI18n, type HighlightedSql } from "./providers";

export function SqlModal({
  id,
  sql,
  onClose,
}: {
  id: SqlId | null;
  sql: HighlightedSql;
  onClose: () => void;
}) {
  const { t } = useI18n();
  const [copied, setCopied] = useState(false);
  const closeRef = useRef<HTMLButtonElement>(null);
  const entry = id ? sql[id] : null;

  useEffect(() => {
    if (!id) return;
    const previous = document.activeElement as HTMLElement | null;
    closeRef.current?.focus();
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    document.addEventListener("keydown", onKey);
    lockScroll(true);
    return () => {
      document.removeEventListener("keydown", onKey);
      lockScroll(false);
      previous?.focus();
    };
  }, [id, onClose]);

  const copy = async () => {
    if (!entry) return;
    await navigator.clipboard.writeText(entry.raw);
    setCopied(true);
    setTimeout(() => setCopied(false), 1600);
  };

  return (
    <AnimatePresence>
      {id && entry && (
        <motion.div
          className="fixed inset-0 z-[60] flex items-end justify-center p-0 sm:items-center sm:p-6"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <button
            aria-label={t.nav.close}
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={onClose}
            tabIndex={-1}
          />
          <motion.div
            role="dialog"
            aria-modal="true"
            aria-labelledby="sql-title"
            className="card relative flex max-h-[85vh] w-full max-w-3xl flex-col overflow-hidden rounded-b-none shadow-2xl sm:rounded-b-[1.25rem]"
            initial={{ y: 40, scale: 0.98, opacity: 0 }}
            animate={{ y: 0, scale: 1, opacity: 1 }}
            exit={{ y: 24, scale: 0.98, opacity: 0 }}
            transition={{ duration: 0.45 }}
          >
            <div className="flex items-center gap-3 border-b border-line px-5 py-4">
              <div className="min-w-0 flex-1">
                <p className="text-xs font-medium uppercase tracking-widest text-muted">
                  {t.method.sqlTitle}
                </p>
                <h2 id="sql-title" className="truncate font-mono text-sm text-ink">
                  sql/analysis/{id}.sql
                </h2>
              </div>
              <button
                onClick={copy}
                className="rounded-full border border-line px-3 py-1.5 text-sm text-ink-2 transition hover:bg-surface-2 hover:text-ink"
              >
                {copied ? t.method.copied : t.method.copy}
              </button>
              {site.repo && (
                <a
                  href={`${site.repo}/blob/main/sql/analysis/${id}.sql`}
                  target="_blank"
                  rel="noreferrer"
                  className="hidden rounded-full border border-line px-3 py-1.5 text-sm text-ink-2 transition hover:bg-surface-2 hover:text-ink sm:block"
                >
                  {t.method.openRepo}
                </a>
              )}
              <button
                ref={closeRef}
                onClick={onClose}
                aria-label={t.nav.close}
                className="grid size-9 place-items-center rounded-full text-ink-2 transition hover:bg-surface-2 hover:text-ink"
              >
                <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden>
                  <path d="M3 3l10 10M13 3L3 13" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
                </svg>
              </button>
            </div>
            <div
              data-lenis-prevent
              className="overflow-auto px-5 py-4 text-[13px] leading-relaxed [&_pre]:font-mono"
              dangerouslySetInnerHTML={{ __html: entry.html }}
            />
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
