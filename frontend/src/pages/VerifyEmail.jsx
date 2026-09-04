import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { api } from "../api/client.js";
import AuthShell from "../components/AuthShell.jsx";
import FormField from "../components/FormField.jsx";
import { validateEmailFormat } from "../validators.js";

function ResendVerification() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [sent, setSent] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    const emailError = validateEmailFormat(email);
    if (emailError) {
      setError(emailError);
      return;
    }

    setSubmitting(true);
    setError("");
    try {
      await api.post("/auth/resend-verification/", { email });
      setSent(true);
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  if (sent) {
    return (
      <p className="mt-5 text-sm text-slate-600 dark:text-slate-400">
        If <strong>{email}</strong> is registered and not yet verified, a new link is on its way.
      </p>
    );
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="mt-5 text-left">
      <FormField
        id="email"
        label="Email address"
        type="email"
        value={email}
        onChange={setEmail}
        validate={validateEmailFormat}
        error={error}
        setError={(_, message) => setError(message)}
        autoComplete="username"
      />
      <button
        type="submit"
        disabled={submitting}
        className="w-full rounded-lg bg-brand-600 py-2.5 font-semibold text-white shadow-card transition-all hover:bg-brand-700 active:scale-[0.98] disabled:opacity-50"
      >
        {submitting ? "Sending…" : "Resend verification link"}
      </button>
    </form>
  );
}

export default function VerifyEmail() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const [status, setStatus] = useState("pending"); // pending | ok | error

  useEffect(() => {
    if (!token) {
      setStatus("error");
      return;
    }
    api
      .post("/auth/verify-email/", { token })
      .then(() => setStatus("ok"))
      .catch(() => setStatus("error"));
  }, [token]);

  return (
    <AuthShell title="Email verification">
      <div className="text-center">
        {status === "pending" && (
          <p role="status" className="text-sm text-slate-600 dark:text-slate-400">
            Verifying your email…
          </p>
        )}
        {status === "ok" && (
          <>
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100 text-2xl dark:bg-emerald-500/20">
              ✅
            </div>
            <p className="mb-5 text-sm text-slate-600 dark:text-slate-400">Your email is verified.</p>
            <Link
              to="/login"
              className="inline-block rounded-lg bg-brand-600 px-5 py-2.5 font-semibold text-white shadow-card hover:bg-brand-700"
            >
              Log in
            </Link>
          </>
        )}
        {status === "error" && (
          <>
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-red-100 text-2xl dark:bg-red-500/20">
              ⚠️
            </div>
            <p role="alert" className="mb-5 text-sm text-red-600 dark:text-red-400">
              That verification link is invalid or has expired.
            </p>
            <ResendVerification />
            <Link
              to="/login"
              className="mt-5 inline-block font-semibold text-brand-600 hover:underline dark:text-brand-400"
            >
              Back to login
            </Link>
          </>
        )}
      </div>
    </AuthShell>
  );
}
