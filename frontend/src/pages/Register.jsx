import { useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../api/client.js";
import AuthShell from "../components/AuthShell.jsx";
import FormField from "../components/FormField.jsx";
import { IconEye, IconEyeOff } from "../components/icons.jsx";
import { validateDutEmail, validatePassword, validateRequired } from "../validators.js";

export default function Register() {
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    password: "",
    campus: "",
    residence: "",
    disbursement_day: "1",
  });
  const [popiaConsent, setPopiaConsent] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [resent, setResent] = useState(false);
  const [resending, setResending] = useState(false);

  const set = (field) => (value) => setForm((prev) => ({ ...prev, [field]: value }));
  const setFieldError = (id, message) => setErrors((prev) => ({ ...prev, [id]: message }));

  async function handleSubmit(e) {
    e.preventDefault();
    setFormError("");

    const nextErrors = {
      full_name: validateRequired("Full name")(form.full_name),
      email: validateDutEmail(form.email),
      password: validatePassword(form.password),
      campus: validateRequired("Campus")(form.campus),
      popia_consent: popiaConsent ? "" : "You must agree to the Privacy Policy to create an account.",
    };
    setErrors(nextErrors);
    if (Object.values(nextErrors).some(Boolean)) return;

    setSubmitting(true);
    try {
      await api.post("/auth/register/", {
        ...form,
        disbursement_day: Number(form.disbursement_day),
        popia_consent: popiaConsent,
      });
      setSubmitted(true);
    } catch (err) {
      const data = err.response?.data;
      if (data && typeof data === "object") {
        const fieldErrors = Object.fromEntries(
          Object.entries(data).map(([field, message]) => [
            field,
            Array.isArray(message) ? message[0] : message,
          ])
        );
        setErrors((prev) => ({ ...prev, ...fieldErrors }));
      } else {
        setFormError("Registration failed. Please try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  async function handleResend() {
    setResending(true);
    try {
      await api.post("/auth/resend-verification/", { email: form.email });
    } finally {
      setResent(true);
      setResending(false);
    }
  }

  if (submitted) {
    return (
      <AuthShell title="Check your email">
        <div className="text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100 text-2xl dark:bg-emerald-500/20">
            📩
          </div>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            We&apos;ve sent a verification link to <strong>{form.email}</strong>. Verify your account,
            then{" "}
            <Link to="/login" className="font-semibold text-brand-600 hover:underline dark:text-brand-400">
              log in
            </Link>
            .
          </p>
          {resent ? (
            <p className="mt-4 text-sm font-medium text-emerald-600 dark:text-emerald-400">
              New link sent.
            </p>
          ) : (
            <button
              type="button"
              onClick={handleResend}
              disabled={resending}
              className="mt-4 text-sm font-semibold text-brand-600 hover:underline disabled:opacity-50 dark:text-brand-400"
            >
              {resending ? "Sending…" : "Didn't get it? Resend"}
            </button>
          )}
        </div>
      </AuthShell>
    );
  }

  return (
    <AuthShell
      title="Create your account"
      subtitle="Track your NSFAS allowance and find the best prices."
    >
      <form onSubmit={handleSubmit} noValidate>
        <FormField
          id="full_name"
          label="Full name"
          value={form.full_name}
          onChange={set("full_name")}
          validate={validateRequired("Full name")}
          error={errors.full_name}
          setError={setFieldError}
          autoComplete="name"
        />
        <FormField
          id="email"
          label="DUT email address"
          type="email"
          value={form.email}
          onChange={set("email")}
          validate={validateDutEmail}
          error={errors.email}
          setError={setFieldError}
          hint="Must be a dut4life.ac.za or dut.ac.za address."
          autoComplete="username"
        />
        <FormField
          id="password"
          label="Password"
          type={showPassword ? "text" : "password"}
          value={form.password}
          onChange={set("password")}
          validate={validatePassword}
          error={errors.password}
          setError={setFieldError}
          hint="At least 10 characters."
          autoComplete="new-password"
          trailing={
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              aria-label={showPassword ? "Hide password" : "Show password"}
              className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
            >
              {showPassword ? <IconEyeOff className="h-4 w-4" /> : <IconEye className="h-4 w-4" />}
            </button>
          }
        />
        <FormField
          id="campus"
          label="Campus"
          value={form.campus}
          onChange={set("campus")}
          validate={validateRequired("Campus")}
          error={errors.campus}
          setError={setFieldError}
        />
        <FormField
          id="residence"
          label="Residence (optional)"
          value={form.residence}
          onChange={set("residence")}
          required={false}
          error={errors.residence}
          setError={setFieldError}
        />
        <FormField
          id="disbursement_day"
          label="NSFAS disbursement day of month"
          type="number"
          min={1}
          max={31}
          value={form.disbursement_day}
          onChange={set("disbursement_day")}
          error={errors.disbursement_day}
          setError={setFieldError}
        />
        <label className="mb-4 flex items-start gap-2 text-sm text-slate-600 dark:text-slate-400">
          <input
            type="checkbox"
            checked={popiaConsent}
            onChange={(e) => {
              setPopiaConsent(e.target.checked);
              setFieldError("popia_consent", "");
            }}
            className="mt-0.5 h-4 w-4 shrink-0 rounded border-slate-300 text-brand-600 focus:ring-brand-500 dark:border-navy-700 dark:bg-navy-800"
          />
          <span>
            I agree to the{" "}
            <Link
              to="/privacy"
              target="_blank"
              rel="noopener noreferrer"
              className="font-semibold text-brand-600 hover:underline dark:text-brand-400"
            >
              Privacy Policy
            </Link>{" "}
            and consent to SmartSpend processing my personal information under POPIA.
          </span>
        </label>
        {errors.popia_consent && (
          <p role="alert" className="-mt-2 mb-4 text-xs font-medium text-red-600 dark:text-red-400">
            {errors.popia_consent}
          </p>
        )}

        {formError && (
          <p role="alert" className="mb-4 text-sm font-medium text-red-600 dark:text-red-400">
            {formError}
          </p>
        )}
        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-lg bg-brand-600 py-2.5 font-semibold text-white shadow-card transition-colors hover:bg-brand-700 disabled:opacity-50"
        >
          {submitting ? "Creating account…" : "Register"}
        </button>

        <p className="mt-5 text-center text-sm text-slate-600 dark:text-slate-400">
          Already have an account?{" "}
          <Link to="/login" className="font-semibold text-brand-600 hover:underline dark:text-brand-400">
            Log in
          </Link>
        </p>
      </form>
    </AuthShell>
  );
}
