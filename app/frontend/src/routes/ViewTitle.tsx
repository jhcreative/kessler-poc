import { useEffect, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import type { LiveStatus } from "../live/useLive";

const STATUS_LABEL: Record<LiveStatus, string> = { connecting: "Connecting", live: "Live", reconnecting: "Reconnecting" };

// A view puts its title and live state on the shell's pinned line, so the top of the screen is content (PQ-9).
export function ViewTitle({ title, status, children }: { title: string; status?: LiveStatus; children?: ReactNode }) {
  const [slot, setSlot] = useState<HTMLElement | null>(null);
  useEffect(() => setSlot(document.getElementById("view-title")), []);
  useEffect(() => {
    document.title = `${title} : Kessler Facility Services`;
  }, [title]);
  if (!slot) return null;
  return createPortal(
    <>
      <h1>{title}</h1>
      {status && (
        <span className="live" data-status={status} role="status">
          {STATUS_LABEL[status]}
        </span>
      )}
      {children}
    </>,
    slot,
  );
}
