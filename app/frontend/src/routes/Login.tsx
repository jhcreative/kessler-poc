import { useState, type FormEvent } from "react";
import { Navigate, useNavigate } from "react-router";
import { homeFor, useAuth } from "../auth";

// A password pasted from the PDF can carry what a masked field hides: a trailing space, a typographic dash for a
// hyphen, an invisible soft hyphen. Every demo password is plain letters, digits and hyphens, so these are cleaned.
export function cleanPassword(raw: string): string {
  return raw.replace(/[\u00ad\u200b-\u200d\u2060\ufeff]/g, "").replace(/[\u2010-\u2015\u2212]/g, "-").trim();
}

export function Login() {
  const { me, signIn } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [shown, setShown] = useState(false);
  if (me) return <Navigate to={homeFor(me.role)} replace />;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const who = await signIn(email.trim(), cleanPassword(password));
      navigate(homeFor(who.role), { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign in failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="login">
      <h1>Kessler Facility Services</h1>
      <form onSubmit={submit} noValidate>
        <div className="field">
          <label htmlFor="email">Email</label>
          <input id="email" type="email" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} aria-invalid={error ? true : undefined} />
        </div>
        <div className="field">
          <label htmlFor="password">Password</label>
          <input id="password" type={shown ? "text" : "password"} autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} aria-invalid={error ? true : undefined} />
          <label className="show-password">
            <input type="checkbox" checked={shown} onChange={(e) => setShown(e.target.checked)} /> Show password
          </label>
          <p className="form-message error-line" role="alert">{error}</p>
        </div>
        <button className="primary" type="submit" disabled={busy || !email || !password}>Sign in</button>
      </form>
    </main>
  );
}
