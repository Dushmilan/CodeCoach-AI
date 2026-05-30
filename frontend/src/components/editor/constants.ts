import { Language } from '@/types';

export interface LanguageOption {
  value: Language;
  label: string;
  version: string;
  disabled: boolean;
}

export const LANGUAGE_OPTIONS: LanguageOption[] = [
  { value: 'python', label: 'Python', version: '3.10', disabled: false },
  { value: 'javascript', label: 'JavaScript', version: '18.15.0', disabled: false },
  { value: 'java', label: 'Java', version: '15.0.2', disabled: false },
  { value: 'cpp', label: 'C++', version: '10.2.0', disabled: false },
  { value: 'c', label: 'C', version: '10.2.0', disabled: false },
  { value: 'go', label: 'Go', version: '1.16.2', disabled: false },
  { value: 'rust', label: 'Rust', version: '1.68.2', disabled: false },
  { value: 'typescript', label: 'TypeScript', version: '5.0.2', disabled: false },
];

export const getEnabledLanguages = () => {
  return LANGUAGE_OPTIONS.filter((lang) => !lang.disabled);
};

export const getDefaultLanguage = (): Language => {
  return 'python';
};
