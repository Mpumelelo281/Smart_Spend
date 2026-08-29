import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { api } from "../api/client.js";
import AuthShell from "../components/AuthShell.jsx";

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
        {status === "pending" && <p className="text-sm text-slate-600">Verifying your email…</p>}
        {status === "ok" && (
          <>
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100 text-2xl">
              ✅
            </div>
            <p className="mb-5 text-sm text-slate-600">Your email is verified.</p>
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
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-red-100 text-2xl">
              ⚠️
            </div>
            <p className="text-sm text-red-600">
              That verification link is invalid or has expired. Contact Student Services if this
              persists.
            </p>
          </>
        )}
      </div>
    </AuthShell>
  );
}
