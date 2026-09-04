import { useState } from "react";

import { api } from "../api/client.js";
import FormField from "../components/FormField.jsx";
import { IconEye, IconEyeOff, IconShield } from "../components/icons.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { validatePassword, validateRequired } from "../validators.js";

function ProfileForm() {
  const { user, refreshUser } = useAuth();
  const profile = user?.profile;

  const [campus, setCampus] = useState(profile?.campus ?? "");
  const [residence, setResidence] = useState(profile?.residence ?? "");
  const [disbursementDay, setDisbursementDay] = useState(String(profile?.disbursement_day ?? 1));
  const [errors, setErrors] = useState({});
  const [status, setStatus] = useState(""); // "", "saving", "saved", "error"

  const setFieldError = (id, message) => setErrors((prev) => ({ ...prev, [id]: message }));

  async function handleSubmit(e) {
    e.preventDefault();

    const campusError = validateRequired("Campus")(campus);
    setErrors({ campus: campusError });
    if (campusError) return;

    setStatus("saving");
    try {
      await api.patch("/auth/me/", {
        campus,
        residence,
        disbursement_day: Number(disbursementDay),
      });
      await refreshUser();
      setStatus("saved");
      setTimeout(() => setStatus(""), 2500);
    } catch {
      setStatus("error");
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <label className="mb-1.5 block text-sm font-semibold text-slate-700 dark:text-slate-200">
            Email
          </label>
          <p className="rounded-lg border border-slate-100 bg-slate-50 px-3.5 py-2.5 text-slate-500 dark:border-navy-800 dark:bg-navy-800/60 dark:text-slate-400">
            {user?.email}
          </p>
        </div>

        <FormField
          id="campus"
          label="Campus"
          value={campus}
          onChange={setCampus}
          validate={validateRequired("Campus")}
          error={errors.campus}
          setError={setFieldError}
        />
        <FormField
          id="residence"
          label="Residence"
          value={residence}
          onChange={setResidence}
          required={false}
        />
        <FormField
          id="disbursement_day"
          label="NSFAS disbursement day of month"
          type="number"
          min={1}
          max={31}
          value={disbursementDay}
          onChange={setDisbursementDay}
        />
        <div>
          <label className="mb-1.5 block text-sm font-semibold text-slate-700 dark:text-slate-200">
            Monthly allowance
          </label>
          <p className="rounded-lg border border-slate-100 bg-slate-50 px-3.5 py-2.5 text-slate-500 dark:border-navy-800 dark:bg-navy-800/60 dark:text-slate-400">
            R{Number(profile?.allowance_amount ?? 0).toFixed(2)} — fixed by NSFAS
          </p>
        </div>
      </div>

      <div className="mt-5 flex items-center gap-3">
        <button
          type="submit"
          disabled={status === "saving"}
          className="rounded-lg bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white shadow-card transition-all hover:bg-brand-700 active:scale-[0.98] disabled:opacity-50"
        >
          {status === "saving" ? "Saving…" : "Save changes"}
        </button>
        {status === "saved" && (
          <span className="text-sm font-medium text-emerald-600 dark:text-emerald-400">Saved ✓</span>
        )}
        {status === "error" && (
          <span className="text-sm font-medium text-red-600 dark:text-red-400">
            Could not save. Try again.
          </span>
        )}
      </div>
    </form>
  );
}

function ChangePasswordForm() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  const setFieldError = (id, message) => setErrors((prev) => ({ ...prev, [id]: message }));

  async function handleSubmit(e) {
    e.preventDefault();
    setFormError("");
    setSuccess(false);

    const currentError = validateRequired("Current password")(currentPassword);
    const newError = validatePassword(newPassword);
    setErrors({ current_password: currentError, new_password: newError });
    if (currentError || newError) return;

    setSubmitting(true);
    try {
      await api.post("/auth/change-password/", {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setCurrentPassword("");
      setNewPassword("");
      setSuccess(true);
    } catch (err) {
      setFormError(
        err.response?.data?.current_password?.[0] ||
          err.response?.data?.new_password?.[0] ||
          "Could not change your password. Please try again."
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <FormField
          id="current_password"
          label="Current password"
          type={showCurrentPassword ? "text" : "password"}
          value={currentPassword}
          onChange={setCurrentPassword}
          validate={validateRequired("Current password")}
          error={errors.current_password}
          setError={setFieldError}
          autoComplete="current-password"
          trailing={
            <button
              type="button"
              onClick={() => setShowCurrentPassword((v) => !v)}
              aria-label={showCurrentPassword ? "Hide password" : "Show password"}
              className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
            >
              {showCurrentPassword ? <IconEyeOff className="h-4 w-4" /> : <IconEye className="h-4 w-4" />}
            </button>
          }
        />
        <FormField
          id="new_password"
          label="New password"
          type={showNewPassword ? "text" : "password"}
          value={newPassword}
          onChange={setNewPassword}
          validate={validatePassword}
          error={errors.new_password}
          setError={setFieldError}
          hint="At least 10 characters."
          autoComplete="new-password"
          trailing={
            <button
              type="button"
              onClick={() => setShowNewPassword((v) => !v)}
              aria-label={showNewPassword ? "Hide password" : "Show password"}
              className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
            >
              {showNewPassword ? <IconEyeOff className="h-4 w-4" /> : <IconEye className="h-4 w-4" />}
            </button>
          }
        />
      </div>

      {formError && (
        <p role="alert" className="mt-2 text-sm font-medium text-red-600 dark:text-red-400">
          {formError}
        </p>
      )}

      <div className="mt-5 flex items-center gap-3">
        <button
          type="submit"
          disabled={submitting}
          className="rounded-lg bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white shadow-card transition-all hover:bg-brand-700 active:scale-[0.98] disabled:opacity-50"
        >
          {submitting ? "Changing…" : "Change password"}
        </button>
        {success && (
          <span className="text-sm font-medium text-emerald-600 dark:text-emerald-400">
            Password changed ✓
          </span>
        )}
      </div>
    </form>
  );
}

function TwoFactorForm() {
  const { user, refreshUser } = useAuth();
  const mfaEnabled = Boolean(user?.mfa_enabled);

  const [confirming, setConfirming] = useState(false);
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  async function handleReset(e) {
    e.preventDefault();
    setError("");

    const passwordError = validateRequired("Current password")(password);
    if (passwordError) {
      setError(passwordError);
      return;
    }

    setSubmitting(true);
    try {
      await api.post("/auth/mfa/reset/", { current_password: password });
      setPassword("");
      setConfirming(false);
      setSuccess(true);
      await refreshUser();
    } catch (err) {
      setError(err.response?.data?.current_password?.[0] || "Could not reset two-factor authentication.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <div className="flex items-center gap-3">
        <span
          className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full ${
            mfaEnabled
              ? "bg-emerald-100 text-emerald-600 dark:bg-emerald-500/20 dark:text-emerald-400"
              : "bg-slate-100 text-slate-400 dark:bg-navy-800 dark:text-slate-500"
          }`}
        >
          <IconShield className="h-5 w-5" />
        </span>
        <div>
          <p className="font-semibold text-slate-900 dark:text-white">
            {mfaEnabled ? "Enabled" : "Not set up yet"}
          </p>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            {mfaEnabled
              ? "Codes come from your authenticator app at every login."
              : "You'll set this up the next time you log in."}
          </p>
        </div>
      </div>

      {success && (
        <p className="mt-4 text-sm font-medium text-emerald-600 dark:text-emerald-400">
          Reset. You&apos;ll set up two-factor authentication again next time you log in.
        </p>
      )}

      {mfaEnabled && !confirming && !success && (
        <button
          type="button"
          onClick={() => setConfirming(true)}
          className="mt-4 text-sm font-semibold text-red-600 hover:underline dark:text-red-400"
        >
          Lost your authenticator? Reset it
        </button>
      )}

      {confirming && (
        <form onSubmit={handleReset} className="mt-4">
          <p className="mb-3 text-sm text-slate-600 dark:text-slate-400">
            Enter your password to reset two-factor authentication. You&apos;ll be asked to set it up
            again next time you log in.
          </p>
          <FormField
            id="mfa_reset_password"
            label="Current password"
            type={showPassword ? "text" : "password"}
            value={password}
            onChange={setPassword}
            error={error}
            setError={(_, message) => setError(message)}
            autoComplete="current-password"
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
          <div className="flex items-center gap-3">
            <button
              type="submit"
              disabled={submitting}
              className="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white shadow-card transition-all hover:bg-red-700 active:scale-[0.98] disabled:opacity-50"
            >
              {submitting ? "Resetting…" : "Reset two-factor authentication"}
            </button>
            <button
              type="button"
              onClick={() => {
                setConfirming(false);
                setPassword("");
                setError("");
              }}
              className="text-sm font-semibold text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
            >
              Cancel
            </button>
          </div>
        </form>
      )}
    </div>
  );
}

export default function Profile() {
  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Profile & security</h1>
      <p className="mt-1 text-slate-500 dark:text-slate-400">
        Update your details or change your password.
      </p>

      <div className="mt-6 rounded-2xl bg-white p-6 shadow-card dark:bg-navy-900">
        <h2 className="mb-4 font-semibold text-slate-900 dark:text-white">Profile</h2>
        <ProfileForm />
      </div>

      <div className="mt-6 rounded-2xl bg-white p-6 shadow-card dark:bg-navy-900">
        <h2 className="mb-4 font-semibold text-slate-900 dark:text-white">Change password</h2>
        <ChangePasswordForm />
      </div>

      <div className="mt-6 rounded-2xl bg-white p-6 shadow-card dark:bg-navy-900">
        <h2 className="mb-4 font-semibold text-slate-900 dark:text-white">Two-factor authentication</h2>
        <TwoFactorForm />
      </div>
    </div>
  );
}
