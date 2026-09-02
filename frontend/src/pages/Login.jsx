import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { api, setTokens } from "../api/client.js";
import AuthShell from "../components/AuthShell.jsx";
import FormField from "../components/FormField.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { validateEmailFormat, validateRequired } from "../validators.js";

// Two-step login mirrors the server exactly (see apps/accounts/views.py):
// password verified -> either enrol in MFA (first login) or challenge an
// existing TOTP device. No bearer token exists until step 2 succeeds.
export default function Login() {
  const navigate = useNavigate();
  const { refreshUser } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const [step, setStep] = useState("credentials"); // credentials | mfa-setup | mfa-verify
  const [challenge, setChallenge] = useState(null);
  const [code, setCode] = useState("");

  const setFieldError = (id, message) => setErrors((prev) => ({ ...prev, [id]: message }));

  async function handleCredentialsSubmit(e) {
    e.preventDefault();
    setFormError("");

    const emailError = validateEmailFormat(email);
    const passwordError = validateRequired("Password")(password);
    setErrors({ email: emailError, password: passwordError });
    if (emailError || passwordError) return;

    setSubmitting(true);
    try {
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
      setFormError(err.response?.data?.non_field_errors?.[0] || "Invalid email or password.");
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

  const titles = {
    credentials: ["Welcome back", "Log in to manage your budget."],
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
            autoComplete="username"
          />
          <FormField
            id="password"
            label="Password"
            type="password"
            value={password}
            onChange={setPassword}
            validate={validateRequired("Password")}
            error={errors.password}
            setError={setFieldError}
            autoComplete="current-password"
          />
          <p className="-mt-2 mb-4 text-right">
            <Link to="/forgot-password" className="text-xs font-semibold text-brand-600 hover:underline">
              Forgot password?
            </Link>
          </p>
          {formError && (
            <p role="alert" className="mb-4 text-sm font-medium text-red-600">
              {formError}
            </p>
          )}
          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-lg bg-brand-600 py-2.5 font-semibold text-white shadow-card transition-all hover:bg-brand-700 active:scale-[0.98] disabled:opacity-50"
          >
            {submitting ? "Checking…" : "Continue"}
          </button>
          <p className="mt-5 text-center text-sm text-slate-500">
            New here?{" "}
            <Link to="/register" className="font-semibold text-brand-600 hover:underline">
              Create an account
            </Link>
          </p>
        </form>
      )}

      {step === "mfa-setup" && (
        <form onSubmit={handleMfaSubmit} noValidate>
          <p className="mb-4 text-sm text-slate-600">
            Scan this code with an authenticator app (Google Authenticator, Authy, etc.), then enter
            the 6-digit code it shows.
          </p>
          <div className="mb-4 flex justify-center rounded-xl border border-slate-200 bg-slate-50 p-4">
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
            <p role="alert" className="mb-4 text-sm font-medium text-red-600">
              {formError}
            </p>
          )}
          <button
            type="submit"
            disabled={submitting || code.length !== 6}
            className="w-full rounded-lg bg-emerald-600 py-2.5 font-semibold text-white shadow-card transition-all hover:bg-emerald-700 active:scale-[0.98] disabled:opacity-50"
          >
            {submitting ? "Verifying…" : "Enable & log in"}
          </button>
        </form>
      )}

      {step === "mfa-verify" && (
        <form onSubmit={handleMfaSubmit} noValidate>
          <p className="mb-4 text-sm text-slate-600">Enter the 6-digit code from your authenticator app.</p>
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
            <p role="alert" className="mb-4 text-sm font-medium text-red-600">
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
