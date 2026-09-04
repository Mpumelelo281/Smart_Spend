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
  icon: Icon,
  trailing,
  labelRight,
  ...rest
}) {
  const handleBlur = () => {
    if (!validate) return;
    const message = validate(value);
    setError?.(id, message || "");
  };

  return (
    <div className="mb-4">
      <div className="mb-1.5 flex items-baseline justify-between">
        <label htmlFor={id} className="text-sm font-semibold text-slate-700 dark:text-slate-200">
          {label}
        </label>
        {labelRight}
      </div>
      <div className="relative">
        {Icon && (
          <Icon className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        )}
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
          className={`w-full rounded-lg border bg-slate-50 py-2.5 text-slate-900 transition-colors focus:border-brand-500 focus:bg-white focus:outline-none dark:bg-navy-800 dark:text-white dark:focus:bg-navy-800 ${
            Icon ? "pl-10" : "pl-3.5"
          } ${trailing ? "pr-10" : "pr-3.5"} ${
            error
              ? "border-red-400 bg-red-50 dark:border-red-500 dark:bg-red-950/40"
              : "border-slate-200 dark:border-navy-700"
          }`}
          {...rest}
        />
        {trailing && <div className="absolute right-2.5 top-1/2 -translate-y-1/2">{trailing}</div>}
      </div>
      {hint && !error && (
        <p id={`${id}-hint`} className="mt-1.5 text-xs text-slate-500 dark:text-slate-400">
          {hint}
        </p>
      )}
      {error && (
        <p id={`${id}-error`} role="alert" className="mt-1.5 text-xs font-medium text-red-600 dark:text-red-400">
          {error}
        </p>
      )}
    </div>
  );
}
