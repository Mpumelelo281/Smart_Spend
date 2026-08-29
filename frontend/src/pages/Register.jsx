import { useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../api/client.js";
import AuthShell from "../components/AuthShell.jsx";
import FormField from "../components/FormField.jsx";
import { validateDutEmail, validatePassword, validateRequired } from "../validators.js";

export default function Register() {
  const [form, setForm] = useState({
    email: "",
    password: "",
    campus: "",
    residence: "",
    disbursement_day: "1",
  });
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const set = (field) => (value) => setForm((prev) => ({ ...prev, [field]: value }));
  const setFieldError = (id, message) => setErrors((prev) => ({ ...prev, [id]: message }));

  async function handleSubmit(e) {
    e.preventDefault();
    setFormError("");

    const nextErrors = {
      email: validateDutEmail(form.email),
      password: validatePassword(form.password),
      campus: validateRequired("Campus")(form.campus),
    };
    setErrors(nextErrors);
    if (Object.values(nextErrors).some(Boolean)) return;

    setSubmitting(true);
    try {
      await api.post("/auth/register/", {
        ...form,
        disbursement_day: Number(form.disbursement_day),
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

  if (submitted) {
    return (
      <AuthShell title="Check your email">
        <div className="text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100 text-2xl">
            📩
          </div>
          <p className="text-sm text-slate-600">
            We&apos;ve sent a verification link to <strong>{form.email}</strong>. Verify your account,
            then{" "}
            <Link to="/login" className="font-semibold text-brand-600 hover:underline">
              log in
            </Link>
            .
          </p>
        </div>
      </AuthShell>
    );
  }

  return (
    <AuthShell title="Create your account" subtitle="Track your NSFAS allowance and find the best prices.">
      <form onSubmit={handleSubmit} noValidate>
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
          type="password"
          value={form.password}
          onChange={set("password")}
          validate={validatePassword}
          error={errors.password}
          setError={setFieldError}
          hint="At least 10 characters."
          autoComplete="new-password"
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
        {formError && (
          <p role="alert" className="mb-4 text-sm font-medium text-red-600">
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
      </form>
      <p className="mt-5 text-center text-sm text-slate-500">
        Already have an account?{" "}
        <Link to="/login" className="font-semibold text-brand-600 hover:underline">
          Log in
        </Link>
      </p>
    </AuthShell>
  );
}
