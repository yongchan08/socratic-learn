export function storedVolume(key, fallback) {
  const value = Number(window.localStorage.getItem(key));
  return Number.isFinite(value) && value >= 0 && value <= 1 ? value : fallback;
}
