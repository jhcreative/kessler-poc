// The names the views use, all from the generated schema (scripts/types.sh). Nothing here is written by hand.
import type { components } from "./schema";

type S = components["schemas"];
export type Job = S["JobOut"];
export type JobState = S["State"];
export type EventEnvelope = S["EventEnvelope"];
export type LiveMessage = S["LiveMessage"];
export type LiveEvent = S["LiveEvent"];
export type Me = S["Me"];
export type Overview = S["Overview"];
export type StepTurnaround = S["StepTurnaround"];
export type CommandIn = S["CommandIn"];
export type CommandResult = S["CommandResult"];
export type Refusal = S["Refusal"];
export type Role = S["Role"];
