/**
 * Rule 2: format validation runs client-side on blur so the error surfaces
 * at the field, then is re-run server-side (Django form/serializer field)
 * because a client check alone can always be bypassed. `validate` here is
 * the client-side half of that pair — it must mirror, not replace, the
 * server-side rule for the same field.
 */
export default function FormField({
  id,
  label,
  type = "text",
  value,
  onChange,
  validate,
  error,
  setError,
  required = true,
  hint,
  ...rest
}) {
  const handleBlur = () => {
    if (!validate) return;
    const message = validate(value);
    setError?.(id, message || "");
  };

  return (
    <div className="mb-4">
      <label htmlFor={id} className="mb-1.5 block text-sm font-semibold text-slate-700 dark:text-slate-200">
        {label}
      </label>
      <input
        id={id}
        name={id}
        type={type}
        value={value}
        required={required}
        onChange={(e) => onChange(e.target.value)}
        onBlur={handleBlur}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? `${id}-error` : hint ? `${id}-hint` : undefined}
        className={`w-full rounded-lg border bg-slate-50 px-3.5 py-2.5 text-slate-900 transition-colors focus:border-brand-500 focus:bg-white focus:outline-none dark:bg-navy-800 dark:text-white dark:focus:bg-navy-800 ${
          error
            ? "border-red-400 bg-red-50 dark:border-red-500 dark:bg-red-950/40"
            : "border-slate-200 dark:border-navy-700"
        }`}
        {...rest}
      />
      {hint && !error && (
        <p id={`${id}-hint`} className="mt-1.5 text-xs text-slate-500 dark:text-slate-400">
          {hint}
        </p>
      )}
      {error && (
        <p id={`${id}-error`} role="alert" className="mt-1.5 text-xs font-medium text-red-600">
          {error}
        </p>
      )}
    </div>
  );
}
