import { NavLink, Navigate, Outlet, useLocation } from "react-router";
import { VIEWS, useAuth } from "../auth";

// The pinned top line: the view's title and live state come from the view (via the portal slot), the nav and the
// signed-in role from here. Five items at most (PQ-27); only views that exist are listed.
export function Shell() {
  const { me, checked, signOut } = useAuth();
  const location = useLocation();
  if (!checked) return null;
  if (!me) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  const views = VIEWS.filter((v) => v.roles.includes(me.role));
  return (
    <>
      <header className="top">
        <div id="view-title" style={{ display: "contents" }} />
        {views.length > 1 && (
          <nav aria-label="Views">
            {views.map((v) => (
              <NavLink key={v.path} to={v.path} end>
                {v.label}
              </NavLink>
            ))}
          </nav>
        )}
        <div className="who">
          <span>{me.label}</span>
          <button className="link-button" type="button" onClick={() => void signOut()}>
            Sign Out
          </button>
        </div>
      </header>
      <Outlet />
    </>
  );
}
