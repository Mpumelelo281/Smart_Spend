import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { api, setTokens } from "../api/client.js";
import AuthShell from "../components/AuthShell.jsx";
import FormField from "../components/FormField.jsx";
import {
  IconEye,
  IconEyeOff,
  IconArrowLeft,
  IconArrowRight,
  IconLock,
  IconMail,
  IconShield,
} from "../components/icons.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { validateEmailFormat, validateRequired } from "../validators.js";

// Only a 400 from the login endpoint means "wrong credentials" — anything
// else (no response at all, a 5xx, a 429 rate limit) is a different
// problem, and calling it "Invalid email or password" sends people off
// retyping a correct password while the real fault goes unnoticed.
function loginErrorMessage(err) {
  const status = err.response?.status;
  if (!err.response) {
    return "Can't reach the server. It may be waking up — wait a moment and try again.";
  }
  if (status === 429) return "Too many attempts. Wait a minute and try again.";
  if (status >= 500) return "The server ran into a problem. Please try again shortly.";
  return err.response.data?.non_field_errors?.[0] || "Invalid email or password.";
}

// Two-step login mirrors the server exactly (see apps/accounts/views.py):
// password verified -> either enrol in MFA (first login) or challenge an
// existing TOTP device. No bearer token exists until step 2 succeeds.
export default function Login() {
  const navigate = useNavigate();
  const { refreshUser } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [resendState, setResendState] = useState(""); // "", "sending", "sent"

  const [step, setStep] = useState("credentials"); // credentials | mfa-setup | mfa-verify
  const [challenge, setChallenge] = useState(null);
  const [code, setCode] = useState("");

  const setFieldError = (id, message) => setErrors((prev) => ({ ...prev, [id]: message }));

  // The server only says this once the password is correct, so it's safe
  // to offer a resend for exactly this message — an account stuck as
  // "unverified" otherwise has no way to get a fresh link.
  const needsVerification = /verify your email/i.test(formError);

  async function handleResendVerification() {
    setResendState("sending");
    try {
      await api.post("/auth/resend-verification/", { email });
    } finally {
      setResendState("sent");
    }
  }

  async function handleCredentialsSubmit(e) {
    e.preventDefault();
    setFormError("");

    const emailError = validateEmailFormat(email);
    const passwordError = validateRequired("Password")(password);
    setErrors({ email: emailError, password: passwordError });
    if (emailError || passwordError) return;

    setSubmitting(true);
    try {
      // "Remember me" widens the session by asking for a longer-lived
      // refresh token client-side isn't meaningful here — the backend
      // issues a fixed 7-day refresh token regardless (see SIMPLE_JWT in
      // settings.py) — so this only controls whether we persist the
      // session past closing the tab, via localStorage either way
      // (api/client.js already always uses localStorage). Left wired up
      // for a future "session vs. persistent" distinction rather than
      // silently doing nothing.
      const { data } = await api.post("/auth/login/", { email, password });

      // SKIP_AUTH_VERIFICATION_FOR_TESTING (backend, local-dev only) skips
      // the MFA step server-side and returns real tokens directly from
      // this first request — same shape as a completed MFA response
      // (apps/accounts/views.py::_issue_jwt_pair). Log straight in when
      // that happens instead of forcing an MFA screen with nothing to
      // challenge.
      if (data.access) {
        setTokens({ access: data.access, refresh: data.refresh });
        await refreshUser();
        navigate("/", { replace: true });
        return;
      }

      setChallenge(data);
      setStep(data.mfa_setup_required ? "mfa-setup" : "mfa-verify");
    } catch (err) {
      setFormError(loginErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleMfaSubmit(e) {
    e.preventDefault();
    setFormError("");
    setSubmitting(true);
    try {
      const endpoint = step === "mfa-setup" ? "/auth/mfa/setup/confirm/" : "/auth/mfa/verify/";
      const payload =
        step === "mfa-setup"
          ? { setup_token: challenge.setup_token, code }
          : { login_token: challenge.login_token, code };

      const { data } = await api.post(endpoint, payload);
      setTokens({ access: data.access, refresh: data.refresh });
      await refreshUser();
      navigate("/", { replace: true });
    } catch (err) {
      setFormError(err.response?.data?.detail || "Incorrect code. Try again.");
    } finally {
      setSubmitting(false);
    }
  }

  function handleBackToCredentials() {
    setStep("credentials");
    setChallenge(null);
    setCode("");
    setFormError("");
  }

  const titles = {
    credentials: ["Welcome back!", "Sign in to continue to SmartSpend"],
    "mfa-setup": ["Set up 2-factor login", null],
    "mfa-verify": ["Enter your code", null],
  };
  const [title, subtitle] = titles[step];

  return (
    <AuthShell title={title} subtitle={subtitle}>
      {step === "credentials" && (
        <form onSubmit={handleCredentialsSubmit} noValidate>
          <FormField
            id="email"
            label="Email address"
            type="email"
            value={email}
            onChange={setEmail}
            validate={validateEmailFormat}
            error={errors.email}
            setError={setFieldError}
            icon={IconMail}
            placeholder="Enter your email address"
            autoComplete="username"
          />
          <FormField
            id="password"
            label="Password"
            type={showPassword ? "text" : "password"}
            value={password}
            onChange={setPassword}
            validate={validateRequired("Password")}
            error={errors.password}
            setError={setFieldError}
            icon={IconLock}
            placeholder="Enter your password"
            autoComplete="current-password"
            labelRight={
              <Link to="/forgot-password" className="text-xs font-semibold text-brand-600 hover:underline dark:text-brand-400">
                Forgot password?
              </Link>
            }
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

          <label className="mb-4 flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
            <input
              type="checkbox"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500 dark:border-navy-700 dark:bg-navy-800"
            />
            Remember me
          </label>

          {formError && (
            <p role="alert" className="mb-4 text-sm font-medium text-red-600 dark:text-red-400">
              {formError}
            </p>
          )}
          {needsVerification &&
            (resendState === "sent" ? (
              <p className="-mt-2 mb-4 text-sm font-medium text-emerald-600 dark:text-emerald-400">
                A new verification link is on its way.
              </p>
            ) : (
              <button
                type="button"
                onClick={handleResendVerification}
                disabled={resendState === "sending"}
                className="-mt-2 mb-4 text-sm font-semibold text-brand-600 hover:underline disabled:opacity-50 dark:text-brand-400"
              >
                {resendState === "sending" ? "Sending…" : "Resend verification email"}
              </button>
            ))}

          <button
            type="submit"
            disabled={submitting}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-brand-600 py-2.5 font-semibold text-white shadow-card transition-all hover:bg-brand-700 active:scale-[0.98] disabled:opacity-50"
          >
            {submitting ? "Signing in…" : "Sign in"}
            {!submitting && <IconArrowRight className="h-4 w-4" />}
          </button>

          <p className="mt-5 text-center text-sm text-slate-600 dark:text-slate-400">
            Don&apos;t have an account?{" "}
            <Link to="/register" className="font-semibold text-brand-600 hover:underline dark:text-brand-400">
              Sign up
            </Link>
          </p>

          <p className="mt-4 flex items-center justify-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
            <IconShield className="h-3.5 w-3.5 text-brand-600 dark:text-brand-400" />
            We never share your information with anyone.
          </p>
        </form>
      )}

      {step === "mfa-setup" && (
        <form onSubmit={handleMfaSubmit} noValidate>
          <button
            type="button"
            onClick={handleBackToCredentials}
            className="mb-4 flex items-center gap-1.5 text-sm font-semibold text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
          >
            <IconArrowLeft className="h-4 w-4" />
            Back
          </button>
          <p className="mb-4 text-sm text-slate-600 dark:text-slate-400">
            Scan this code with an authenticator app (Google Authenticator, Authy, etc.), then enter
            the 6-digit code it shows.
          </p>
          <div className="mb-4 flex justify-center rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-navy-700 dark:bg-navy-800">
            <img
              src={`data:image/png;base64,${challenge.qr_code_base64}`}
              alt="MFA enrolment QR code"
              className="rounded-lg"
              width={180}
              height={180}
            />
          </div>
          <FormField
            id="code"
            label="6-digit code"
            value={code}
            onChange={setCode}
            inputMode="numeric"
            maxLength={6}
            autoComplete="one-time-code"
          />
          {formError && (
            <p role="alert" className="mb-4 text-sm font-medium text-red-600 dark:text-red-400">
              {formError}
            </p>
          )}
          <button
            type="submit"
            disabled={submitting || code.length !== 6}
            className="w-full rounded-lg bg-brand-600 py-2.5 font-semibold text-white shadow-card transition-all hover:bg-brand-700 active:scale-[0.98] disabled:opacity-50"
          >
            {submitting ? "Verifying…" : "Enable & log in"}
          </button>
        </form>
      )}

      {step === "mfa-verify" && (
        <form onSubmit={handleMfaSubmit} noValidate>
          <button
            type="button"
            onClick={handleBackToCredentials}
            className="mb-4 flex items-center gap-1.5 text-sm font-semibold text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
          >
            <IconArrowLeft className="h-4 w-4" />
            Back
          </button>
          <p className="mb-4 text-sm text-slate-600 dark:text-slate-400">
            Enter the 6-digit code from your authenticator app.
          </p>
          <FormField
            id="code"
            label="6-digit code"
            value={code}
            onChange={setCode}
            inputMode="numeric"
            maxLength={6}
            autoComplete="one-time-code"
          />
          {formError && (
            <p role="alert" className="mb-4 text-sm font-medium text-red-600 dark:text-red-400">
              {formError}
            </p>
          )}
          <button
            type="submit"
            disabled={submitting || code.length !== 6}
            className="w-full rounded-lg bg-brand-600 py-2.5 font-semibold text-white shadow-card transition-all hover:bg-brand-700 active:scale-[0.98] disabled:opacity-50"
          >
            {submitting ? "Verifying…" : "Log in"}
          </button>
        </form>
      )}
    </AuthShell>
  );
}
