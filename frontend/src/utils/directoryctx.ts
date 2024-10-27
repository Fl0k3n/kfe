import { createContext } from "react";

export const SelectedDirectoryContext = createContext<string | null>(null);

const DEFAULT_DIR_LOCAL_STORAGE_KEY = "kfe_default_dir";

export const getDefaultDir = (): string | null => {
  return window.localStorage.getItem(DEFAULT_DIR_LOCAL_STORAGE_KEY);
};

export const setDefaultDir = (name: string) => {
  window.localStorage.setItem(DEFAULT_DIR_LOCAL_STORAGE_KEY, name);
};
