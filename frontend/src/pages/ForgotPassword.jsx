import { useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../api/client.js";
import AuthShell from "../components/AuthShell.jsx";
import FormField from "../components/FormField.jsx";
import { validateEmailFormat } from "../validators.js";

export default function ForgotPassword() {
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
      // The backend always returns the same generic response whether or
      // not the email is registered — mirrored here by always showing
      // the "sent" state, so this screen can't be used to check which
      // addresses have accounts.
      await api.post("/auth/password-reset/request/", { email });
      setSent(true);
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  if (sent) {
    return (
      <AuthShell title="Check your email">
        <div className="text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-brand-50 text-2xl dark:bg-brand-600/20">
            📩
          </div>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            If <strong>{email}</strong> is registered, a reset link is on its way. It expires after a
            while, so use it soon.
          </p>
          <Link
            to="/login"
            className="mt-5 inline-block font-semibold text-brand-600 hover:underline dark:text-brand-400"
          >
            Back to login
          </Link>
        </div>
      </AuthShell>
    );
  }

  return (
    <AuthShell title="Forgot your password?" subtitle="We'll email you a link to reset it.">
      <form onSubmit={handleSubmit} noValidate>
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
          {submitting ? "Sending…" : "Send reset link"}
        </button>
        <p className="mt-5 text-center text-sm text-slate-500">
          <Link to="/login" className="font-semibold text-brand-600 hover:underline">
            Back to login
          </Link>
        </p>
      </form>
    </AuthShell>
  );
}
