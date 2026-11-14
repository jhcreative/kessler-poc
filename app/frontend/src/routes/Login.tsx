import { useState, type FormEvent } from "react";
import { Navigate, useNavigate } from "react-router";
import { homeFor, useAuth } from "../auth";

export function Login() {
  const { me, signIn } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  if (me) return <Navigate to={homeFor(me.role)} replace />;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const who = await signIn(email, password);
      navigate(homeFor(who.role), { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign in failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="login">
      <h1>OneFamilyServices ops</h1>
      <form onSubmit={submit} noValidate>
        <div className="field">
          <label htmlFor="email">Email</label>
          <input id="email" type="email" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} aria-invalid={error ? true : undefined} />
        </div>
        <div className="field">
          <label htmlFor="password">Password</label>
          <input id="password" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} aria-invalid={error ? true : undefined} />
          <p className="form-message error-line" role="alert">{error}</p>
        </div>
        <button className="primary" type="submit" disabled={busy || !email || !password}>Sign in</button>
      </form>
    </main>
  );
}
