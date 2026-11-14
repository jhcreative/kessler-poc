// Display helpers. No dashes in UI text (PQ-34); $ at half size.
import type { JobState } from "./api/types";

export const STATE_LABEL: Record<JobState, string> = {
  intake_draft: "Intake draft",
  qualified: "Qualified",
  needs_client_approval: "Needs client approval",
  ready_for_dispatch: "Ready for dispatch",
  assigned: "Assigned",
  onsite: "Onsite",
  needs_review: "Needs review",
  closed: "Closed",
  billing_review: "Billing review",
  invoiced: "Invoiced",
  paid: "Paid",
};

export const QUEUE_LABEL: Record<string, string> = {
  coordinator: "Coordinator",
  dispatch: "Dispatch",
  field: "Field",
  billing: "Billing",
  collections: "Collections",
  done: "Done",
};

export function dollars(cents: number | null | undefined): string {
  if (cents == null) return "";
  return (cents / 100).toLocaleString("en-US", { maximumFractionDigits: 0 });
}

export function hours(h: number | null | undefined): string {
  if (h == null) return "";
  if (h < 1) return `${Math.round(h * 60)} min`;
  if (h < 48) return `${h.toFixed(1)} h`;
  return `${(h / 24).toFixed(1)} days`;
}

export function when(iso: string): string {
  return new Date(iso).toLocaleString("en-US", { weekday: "short", hour: "numeric", minute: "2-digit" });
}

export const ISSUE_LABEL: Record<string, string> = {
  hvac: "HVAC",
  refrigeration: "Refrigeration",
  electrical: "Electrical",
  plumbing: "Plumbing",
  doors_locks: "Doors and locks",
  lighting: "Lighting",
  roofing: "Roofing",
  general: "General",
};
