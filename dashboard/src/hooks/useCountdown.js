import { useState, useEffect } from "react";

/**
 * Hook to format time remaining until a date
 * @param {string} isoDate - ISO date string
 * @returns {string} Formatted countdown (e.g. "5h 30m")
 */
export function useCountdown(isoDate) {
  const [remaining, setRemaining] = useState("");

  useEffect(() => {
    if (!isoDate) return;

    const tick = () => {
      const diff = new Date(isoDate) - new Date();
      if (diff <= 0) {
        setRemaining("Expirado");
        return;
      }
      const h = Math.floor(diff / 3600000);
      const m = Math.floor((diff % 3600000) / 60000);
      setRemaining(`${h}h ${m}m`);
    };

    tick();
    const id = setInterval(tick, 60000);
    return () => clearInterval(id);
  }, [isoDate]);

  return remaining;
}
