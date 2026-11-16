export function localKey(): string {
  const random = globalThis.crypto;
  if (random && typeof random.randomUUID === "function") return random.randomUUID();
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

export function readImageFile(file: File): Promise<string> {
  if (!file.type.startsWith("image/")) {
    return Promise.reject(new Error("Нужен файл картинки."));
  }
  if (file.size > 10 * 1024 * 1024) {
    return Promise.reject(new Error("Файл больше 10 МБ."));
  }
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(reader.error ?? new Error("Не удалось прочитать файл"));
    reader.readAsDataURL(file);
  });
}
