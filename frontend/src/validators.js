/**
 * Client-side mirror of the server-side rules — see Rule 2. Every function
 * here has a matching enforcement point server-side (noted per function);
 * this file exists purely so the error shows up at the field on blur
 * instead of only after a round trip.
 */

const DUT_DOMAINS = ["dut4life.ac.za", "dut.ac.za"];

// Mirrors apps/accounts/utils.py::validate_dut_email — REGISTRATION ONLY.
// Do not use this on the login form: the DUT-domain rule governs which
// addresses may create an account, not which addresses may authenticate.
// An already-registered user must always be able to log in with the email
// they registered with, whatever it validated against at the time.
export function validateDutEmail(value) {
  if (!value) return "Email is required.";
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailPattern.test(value)) return "Enter a valid email address.";
  const domain = value.split("@")[1]?.toLowerCase();
  if (!DUT_DOMAINS.includes(domain)) {
    return `Registration requires a DUT email address (${DUT_DOMAINS.join(", ")}).`;
  }
  return "";
}

// Format-only check for the login form — no domain restriction. The
// server is the one source of truth for "does this account exist"; this
// just catches an obviously mistyped address before submitting.
export function validateEmailFormat(value) {
  if (!value) return "Email is required.";
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailPattern.test(value)) return "Enter a valid email address.";
  return "";
}

// Mirrors Django's AUTH_PASSWORD_VALIDATORS (MinimumLengthValidator=10).
export function validatePassword(value) {
  if (!value) return "Password is required.";
  if (value.length < 10) return "Password must be at least 10 characters.";
  return "";
}

// Mirrors apps/budgets/models.py CheckConstraint(allocated_amount__gte=0)
// and the DecimalField(max_digits=8, decimal_places=2) column definition.
export function validateMoneyAmount(value) {
  if (value === "" || value === null || value === undefined) return "Amount is required.";
  const n = Number(value);
  if (Number.isNaN(n)) return "Enter a number.";
  if (n < 0) return "Amount cannot be negative.";
  if (!/^\d{1,6}(\.\d{1,2})?$/.test(String(value))) {
    return "Enter an amount with at most two decimal places.";
  }
  return "";
}

export function validateRequired(label) {
  return (value) => (value?.trim?.() ? "" : `${label} is required.`);
}

// Mirrors apps/budgets/serializers.py::BudgetCreateSerializer.validate —
// the server re-checks this against the true allowance regardless of what
// the client sends; this only lets the student see the problem immediately.
export function totalAllocated(categories) {
  return categories.reduce((sum, c) => sum + (Number(c.allocated_amount) || 0), 0);
}
