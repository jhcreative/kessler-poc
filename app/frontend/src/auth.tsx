import { createContext, use, useCallback, useEffect, useState, type ReactNode } from "react";
import { useNavigate } from "react-router";
import { api } from "./api/client";
import type { Me, Role } from "./api/types";

interface Auth {
  me: Me | null;
  checked: boolean;
  signIn: (email: string, password: string) => Promise<Me>;
  signOut: () => Promise<void>;
  signedOut: () => void; // the server ended the session (a 401 or a socket closed with 4401)
}

const AuthContext = createContext<Auth | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [me, setMe] = useState<Me | null>(null);
  const [checked, setChecked] = useState(false);
  const navigate = useNavigate();
  useEffect(() => {
    api
      .me()
      .then(setMe)
      .catch(() => setMe(null))
      .finally(() => setChecked(true));
  }, []);
  const signIn = useCallback(async (email: string, password: string) => {
    const who = await api.login(email, password);
    setMe(who);
    return who;
  }, []);
  const signOut = useCallback(async () => {
    await api.logout().catch(() => undefined);
    setMe(null);
    navigate("/login");
  }, [navigate]);
  const signedOut = useCallback(() => {
    setMe(null);
    navigate("/login");
  }, [navigate]);
  return <AuthContext value={{ me, checked, signIn, signOut, signedOut }}>{children}</AuthContext>;
}

export function useAuth(): Auth {
  const auth = use(AuthContext);
  if (!auth) throw new Error("useAuth outside AuthProvider");
  return auth;
}

// Each role's home. A view is listed only once it's built: no screen promises what isn't there.
// A role's home is the first view listed for it.
export const VIEWS: { path: string; label: string; roles: Role[] }[] = [
  { path: "/ops/coordinator", label: "Coordinator", roles: ["coordinator"] },
  { path: "/ops", label: "Overview", roles: ["exec", "coordinator", "dispatcher", "controller"] },
];

export function homeFor(role: Role): string {
  return VIEWS.find((v) => v.roles.includes(role))?.path ?? "/ops/tech";
}
