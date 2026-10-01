import { createContext, useContext, useEffect, useMemo, useState } from "react";

const STORAGE_KEY = "makai-language";
const LanguageContext = createContext(null);

function initialLanguage() {
  const saved = window.localStorage.getItem(STORAGE_KEY);
  return saved === "en" ? "en" : "it";
}

export function LanguageProvider({ children }) {
  const [language, setLanguage] = useState(initialLanguage);

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, language);
    document.documentElement.lang = language;
    document.title = language === "en" ? "Makai Grand Line Rome" : "Makai Grand Line Roma";
  }, [language]);

  const value = useMemo(() => ({ language, setLanguage }), [language]);
  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) throw new Error("useLanguage must be used inside LanguageProvider");
  return context;
}
