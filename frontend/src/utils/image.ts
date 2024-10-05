export const getBase64ImageFromClipboard = (
  clipboardEvent: ClipboardEvent
): Promise<string | undefined> => {
  return new Promise((resolve, reject) => {
    if (!clipboardEvent.clipboardData) {
      return;
    }
    try {
      for (let i = 0; i < clipboardEvent.clipboardData.items.length; i++) {
        const item = clipboardEvent.clipboardData.items[i];
        if (item.type.includes("image")) {
          const data = item.getAsFile();
          if (data == null) {
            continue;
          }
          const reader = new FileReader();
          reader.readAsDataURL(data);
          reader.onloadend = () => {
            if (reader.result != null) {
              const base64Data = reader.result as string;
              resolve(base64Data.split(",")[1]);
              return;
            }
          };
        }
      }
    } catch (error) {
      console.error(error);
      reject(error);
    }
  });
};
