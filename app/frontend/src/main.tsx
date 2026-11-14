import { StrictMode, Suspense, lazy } from "react";
import { createRoot } from "react-dom/client";
import { Navigate, Outlet, RouterProvider, createBrowserRouter } from "react-router";
import { AuthProvider, homeFor, useAuth } from "./auth";
import { Login } from "./routes/Login";
import { Shell } from "./routes/Shell";
import { ToastProvider } from "./Toast";
import "./styles/app.css";

// The grid (AG Grid) loads only with the views that use it, so signing in stays light.
const Overview = lazy(() => import("./routes/Overview").then((m) => ({ default: m.Overview })));
const Controller = lazy(() => import("./routes/Controller").then((m) => ({ default: m.Controller })));
const Tech = lazy(() => import("./routes/Tech").then((m) => ({ default: m.Tech })));
const Dispatch = lazy(() => import("./routes/Dispatch").then((m) => ({ default: m.Dispatch })));
const Coordinator = lazy(() => import("./routes/Coordinator").then((m) => ({ default: m.Coordinator })));

function Root() {
  return (
    <AuthProvider>
      <ToastProvider>
        <Outlet />
      </ToastProvider>
    </AuthProvider>
  );
}

function Home() {
  const { me, checked } = useAuth();
  if (!checked) return null;
  return <Navigate to={me ? homeFor(me.role) : "/login"} replace />;
}

const router = createBrowserRouter([
  {
    element: <Root />,
    children: [
      { path: "/", element: <Home /> },
      { path: "/login", element: <Login /> },
      {
        element: <Shell />,
        children: [
          { path: "/ops", element: <Suspense fallback={null}><Overview /></Suspense> },
          { path: "/ops/coordinator", element: <Suspense fallback={null}><Coordinator /></Suspense> },
          { path: "/ops/dispatch", element: <Suspense fallback={null}><Dispatch /></Suspense> },
          { path: "/ops/controller", element: <Suspense fallback={null}><Controller /></Suspense> },
          { path: "/ops/tech", element: <Suspense fallback={null}><Tech /></Suspense> },
          { path: "/ops/tech/:jobId", element: <Suspense fallback={null}><Tech /></Suspense> },
        ],
      },
      { path: "*", element: <Home /> },
    ],
  },
]);

const root = document.getElementById("root");
if (root)
  createRoot(root).render(
    <StrictMode>
      <RouterProvider router={router} />
    </StrictMode>,
  );
