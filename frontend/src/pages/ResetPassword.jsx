import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { api } from "../api/client.js";
import AuthShell from "../components/AuthShell.jsx";
import FormField from "../components/FormField.jsx";
import { validatePassword } from "../validators.js";

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const uid = searchParams.get("uid");
  const token = searchParams.get("token");

  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    const passwordError = validatePassword(password);
    if (passwordError) {
      setError(passwordError);
      return;
    }

    setSubmitting(true);
    setError("");
    try {
      await api.post("/auth/password-reset/confirm/", { uid, token, new_password: password });
      setDone(true);
    } catch (err) {
      setError(err.response?.data?.detail || "That reset link is invalid or has expired.");
    } finally {
      setSubmitting(false);
    }
  }

  if (!uid || !token) {
    return (
      <AuthShell title="Invalid link">
        <p className="text-sm text-red-600 dark:text-red-400">
          This password reset link is missing information. Request a new one from the login page.
        </p>
        <Link
          to="/forgot-password"
          className="mt-5 inline-block font-semibold text-brand-600 hover:underline dark:text-brand-400"
        >
          Request a new link
        </Link>
      </AuthShell>
    );
  }

  if (done) {
    return (
      <AuthShell title="Password reset">
        <div className="text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100 text-2xl dark:bg-emerald-500/20">
            ✅
          </div>
          <p className="mb-5 text-sm text-slate-600 dark:text-slate-400">
            Your password has been reset. You can log in with it now.
          </p>
          <Link
            to="/login"
            className="inline-block rounded-lg bg-brand-600 px-5 py-2.5 font-semibold text-white shadow-card hover:bg-brand-700"
          >
            Log in
          </Link>
        </div>
      </AuthShell>
    );
  }

  return (
    <AuthShell title="Choose a new password">
      <form onSubmit={handleSubmit} noValidate>
        <FormField
          id="password"
          label="New password"
          type="password"
          value={password}
          onChange={setPassword}
          validate={validatePassword}
          error={error}
          setError={(_, message) => setError(message)}
          hint="At least 10 characters."
          autoComplete="new-password"
        />
        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-lg bg-brand-600 py-2.5 font-semibold text-white shadow-card transition-all hover:bg-brand-700 active:scale-[0.98] disabled:opacity-50"
        >
          {submitting ? "Resetting…" : "Reset password"}
        </button>
      </form>
    </AuthShell>
  );
}
