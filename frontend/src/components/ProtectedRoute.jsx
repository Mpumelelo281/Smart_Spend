import { Navigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";
import Layout from "./Layout.jsx";

// Rule 9: this hides navigation/routes for the wrong role as a UX nicety
// only — every request the resulting screens make is re-checked
// server-side by DRF permission_classes, which is the actual boundary.
export default function ProtectedRoute({ children, role }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-100 text-slate-500">
        Loading…
      </div>
    );
  }
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  if (role && user.role !== role) {
    return <Navigate to="/" replace />;
  }
  return <Layout>{children}</Layout>;
}
