import { useEffect, useState } from "react";
import { Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { Login } from "./pages/Login";
import { Dashboard } from "./pages/Dashboard";
import { KeyForm } from "./pages/KeyForm";
import { api } from "./lib/api";

function RequireAuth({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<"loading" | "ok" | "no">("loading");
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    api
      .me()
      .then(() => setState("ok"))
      .catch(() => {
        setState("no");
        navigate("/login", { replace: true, state: { from: location } });
      });
  }, [navigate, location]);

  if (state === "loading") return <div className="p-10 text-muted">Loading…</div>;
  if (state === "no") return null;
  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <RequireAuth>
            <Dashboard />
          </RequireAuth>
        }
      />
      <Route
        path="/new"
        element={
          <RequireAuth>
            <KeyForm mode="create" />
          </RequireAuth>
        }
      />
      <Route
        path="/keys/:id"
        element={
          <RequireAuth>
            <KeyForm mode="edit" />
          </RequireAuth>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
