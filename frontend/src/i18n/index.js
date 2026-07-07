import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import en from "./locales/en.json";
import fi from "./locales/fi.json";

const documentLanguage = typeof document !== "undefined" ? document.documentElement.lang : "";

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    fi: { translation: fi },
  },
  lng: documentLanguage || "fi",
  fallbackLng: "fi",
  interpolation: { escapeValue: false },
});

export default i18n;
