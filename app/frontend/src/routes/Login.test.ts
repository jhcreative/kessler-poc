import { describe, expect, it } from "vitest";
import { cleanPassword } from "./Login";

describe("cleanPassword: what a paste from the PDF can carry", () => {
  it("trims spaces and line ends", () =>
    expect(cleanPassword("  ab-cd \n")).toBe("ab-cd"));
  it("turns typographic dashes into hyphens", () =>
    expect(cleanPassword("ab‐cd–ef−gh")).toBe("ab-cd-ef-gh"));
  it("drops invisible characters", () =>
    expect(cleanPassword("ab­cd​-ef﻿")).toBe("abcd-ef"));
  it("leaves a clean password alone", () =>
    expect(cleanPassword("plain-words-42")).toBe("plain-words-42"));
});
