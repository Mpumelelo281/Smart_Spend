import { Suspense, lazy } from "react";
import { Route, Routes } from "react-router-dom";

import ProtectedRoute from "./components/ProtectedRoute.jsx";
import BudgetSetup from "./pages/BudgetSetup.jsx";
import Cart from "./pages/Cart.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import ForgotPassword from "./pages/ForgotPassword.jsx";
import Login from "./pages/Login.jsx";
import Profile from "./pages/Profile.jsx";
import Register from "./pages/Register.jsx";
import ResetPassword from "./pages/ResetPassword.jsx";
import Search from "./pages/Search.jsx";
import VerifyEmail from "./pages/VerifyEmail.jsx";

// Chart.js is the single heaviest dependency in the bundle and only this
// one page needs it — code-split so a student who never opens History
// never pays for it. Mobile data is expensive for this user base; that's
// a first-class constraint, not an optimisation to do "later".
const History = lazy(() => import("./pages/History.jsx"));

function RouteFallback() {
  return <p className="text-slate-500 dark:text-slate-400">Loading…</p>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/verify-email" element={<VerifyEmail />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/profile"
        element={
          <ProtectedRoute>
            <Profile />
          </ProtectedRoute>
        }
      />
      <Route
        path="/budgets/new"
        element={
          <ProtectedRoute role="STUDENT">
            <BudgetSetup />
          </ProtectedRoute>
        }
      />
      <Route
        path="/search"
        element={
          <ProtectedRoute>
            <Search />
          </ProtectedRoute>
        }
      />
      <Route
        path="/cart"
        element={
          <ProtectedRoute role="STUDENT">
            <Cart />
          </ProtectedRoute>
        }
      />
      <Route
        path="/history"
        element={
          <ProtectedRoute role="STUDENT">
            <Suspense fallback={<RouteFallback />}>
              <History />
            </Suspense>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}
