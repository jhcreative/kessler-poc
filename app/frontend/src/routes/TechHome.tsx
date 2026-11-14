import { ViewTitle } from "./ViewTitle";

// The tech's phone view lands with POC-09. Until then, say so plainly rather than show an empty screen.
export function TechHome() {
  return (
    <main>
      <ViewTitle title="My schedule" />
      <p className="status-line">The schedule view isn't built yet. It comes with the field app.</p>
    </main>
  );
}
