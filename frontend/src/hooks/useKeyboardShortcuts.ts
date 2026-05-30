import { useEffect } from "react";

type ShortcutMap = Record<string, () => void>;

export function useKeyboardShortcuts(shortcuts: ShortcutMap) {
  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      const key = [
        event.ctrlKey ? "Ctrl" : "",
        event.metaKey ? "Meta" : "",
        event.shiftKey ? "Shift" : "",
        event.key.toUpperCase()
      ]
        .filter(Boolean)
        .join("+");
      const action = shortcuts[key];
      if (action) {
        event.preventDefault();
        action();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [shortcuts]);
}
