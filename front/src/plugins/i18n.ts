import { createI18n } from 'vue-i18n';

import en from '@/assets/languages/english'

const messages = {
  en,
};

const instance = createI18n({
  locale: 'en',
  fallbackLocale: 'en',
  messages,
});

export default instance;

export const i18n = instance.global
