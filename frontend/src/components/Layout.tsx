import { Link, useNavigate } from "react-router-dom";
import { api } from "../lib/api";

export function Layout({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();

  const handleLogout = async () => {
    await api.logout();
    navigate("/login");
  };

  return (
    <div className="min-h-full">
      <header className="border-b border-line bg-card">
        <div className="mx-auto max-w-5xl px-6 py-5 flex items-center justify-between">
          <Link to="/" className="font-serif text-2xl text-royal tracking-tight">
            KeyRotate
          </Link>
          <button onClick={handleLogout} className="text-sm text-muted hover:text-ink transition">
            Log out
          </button>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-6 py-10">{children}</main>
    </div>
  );
}
