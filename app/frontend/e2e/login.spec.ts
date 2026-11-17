// Sign-in as a person does it: a password pasted from the PDF, and a way to see what was pasted (John, 2026-11-17).
import { expect, test } from "@playwright/test";
import { logins } from "./helpers";

test("the password can be shown, and a paste with a trailing space, a soft hyphen and a typographic dash still signs in", async ({
  page,
}) => {
  const real = logins["coord@kfs.com"] ?? "";
  const mid = Math.floor(real.length / 2);
  await page.goto("/login");
  await page.getByLabel("Email").fill("coord@kfs.com ");
  const field = page.getByLabel("Password", { exact: true });
  await field.fill(
    `${real.slice(0, mid).replace("-", "\u2010")}\u00ad${real.slice(mid)} `,
  ); // a dash, a soft hyphen, a space
  await expect(field).toHaveAttribute("type", "password");
  await page.getByLabel("Show password").check();
  await expect(field).toHaveAttribute("type", "text");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/ops\/coordinator/);
});
