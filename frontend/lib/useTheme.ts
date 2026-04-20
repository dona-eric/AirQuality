"use client";
import { useState, useEffect, useCallback } from "react";

export type Theme = "dark" | "light";

/**
 * useTheme — gestion du thème clair/sombre.
 * Lit la préférence OS au premier chargement,
 * puis persiste le choix de l'utilisateur dans localStorage.
 */
export function useTheme() {
  const [theme, setTheme] = useState<Theme>("dark"); // SSR-safe default

  // Hydratation côté client
  useEffect(() => {
    const saved = localStorage.getItem("aqi-theme") as Theme | null;
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const initial: Theme = saved ?? (prefersDark ? "dark" : "light");
    setTheme(initial);
    document.documentElement.setAttribute("data-theme", initial);
  }, []);

  const toggle = useCallback(() => {
    setTheme((prev) => {
      const next: Theme = prev === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      localStorage.setItem("aqi-theme", next);
      return next;
    });
  }, []);

  const set = useCallback((t: Theme) => {
    setTheme(t);
    document.documentElement.setAttribute("data-theme", t);
    localStorage.setItem("aqi-theme", t);
  }, []);

  return { theme, toggle, set, isDark: theme === "dark" };
}