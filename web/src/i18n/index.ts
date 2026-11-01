import type { Locale } from "./config";
import { en } from "./en";
import { pt, type Dictionary } from "./pt";

const dictionaries: Record<Locale, Dictionary> = { pt, en };

export const getDictionary = (locale: Locale) => dictionaries[locale];
export type { Dictionary };
