export type FileListVariant = "small" | "medium" | "large";

export const lowerFileListVariant = (cur: FileListVariant): FileListVariant => {
  return cur === "small" ? "small" : cur === "medium" ? "small" : "medium";
};

export const higherFileListVariant = (
  cur: FileListVariant
): FileListVariant => {
  return cur === "large" ? "large" : cur === "medium" ? "large" : "medium";
};

const FILE_LIST_VARIANT_KEY = "kfe_file_list_variant";

export const getFileListVariant = (
  defaultVariant: FileListVariant
): FileListVariant => {
  const storageItem = window.localStorage.getItem(FILE_LIST_VARIANT_KEY);
  if (
    storageItem == null ||
    (storageItem !== "small" &&
      storageItem !== "medium" &&
      storageItem !== "large")
  ) {
    return defaultVariant;
  }
  return storageItem;
};

export const updateFileListVariant = (newVariant: FileListVariant) => {
  window.localStorage.setItem(FILE_LIST_VARIANT_KEY, newVariant);
};
