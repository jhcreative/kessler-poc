import { useEffect, useState } from "react";

// True only once `waiting` has lasted `ms`: a load under 150 ms never shows a skeleton (PQ-33).
export function useDelayed(waiting: boolean, ms = 150): boolean {
  const [shown, setShown] = useState(false);
  useEffect(() => {
    if (!waiting) return setShown(false);
    const t = window.setTimeout(() => setShown(true), ms);
    return () => window.clearTimeout(t);
  }, [waiting, ms]);
  return waiting && shown;
}
