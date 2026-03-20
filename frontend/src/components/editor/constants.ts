import { Language } from '@/types';

export interface LanguageOption {
  value: Language;
  label: string;
  version: string;
  disabled: boolean;
}

export const LANGUAGE_OPTIONS: LanguageOption[] = [
  { value: 'python', label: 'Python', version: '3.10', disabled: false },
  { value: 'javascript', label: 'JavaScript', version: '18.15.0', disabled: true },
  { value: 'java', label: 'Java', version: '15.0.2', disabled: true },
];

export const getEnabledLanguages = () => {
  return LANGUAGE_OPTIONS.filter((lang) => !lang.disabled);
};

export const getDefaultLanguage = (): Language => {
  return 'python';
};
