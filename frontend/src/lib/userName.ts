const KEY = "eco.name";
let fallback = ""; // when localStorage is blocked, the name lasts for the session

export function getUserName(): string {
  try {
    return localStorage.getItem(KEY) ?? fallback;
  } catch {
    return fallback;
  }
}

export function setUserName(name: string) {
  fallback = name.trim();
  try {
    localStorage.setItem(KEY, fallback);
  } catch {
    // blocked storage: the session fallback is enough
  }
}
