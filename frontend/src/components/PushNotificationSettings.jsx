import { useEffect, useState } from "react";

import { api } from "../api/client.js";

// Web Push subscribe/unsubscribe — pairs with apps/notifications/push.py
// server-side. Per-device, not per-account: a student who logs in on a
// second phone sees "not enabled" there until they opt in on it too.
function base64UrlToUint8Array(base64Url) {
  const padding = "=".repeat((4 - (base64Url.length % 4)) % 4);
  const base64 = (base64Url + padding).replace(/-/g, "+").replace(/_/g, "/");
  const raw = window.atob(base64);
  return Uint8Array.from([...raw].map((char) => char.charCodeAt(0)));
}

const SUPPORTED =
  typeof navigator !== "undefined" && "serviceWorker" in navigator && "PushManager" in window;

export default function PushNotificationSettings() {
  const [subscribed, setSubscribed] = useState(null); // null = still checking
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!SUPPORTED) {
      setSubscribed(false);
      return;
    }
    navigator.serviceWorker.ready
      .then((registration) => registration.pushManager.getSubscription())
      .then((subscription) => setSubscribed(Boolean(subscription)))
      .catch(() => setSubscribed(false));
  }, []);

  async function enable() {
    setError("");
    setBusy(true);
    try {
      const permission = await Notification.requestPermission();
      if (permission !== "granted") {
        setError(
          "Notifications were blocked — enable them in your browser's site settings to turn this on."
        );
        return;
      }

      const { data } = await api.get("/notifications/vapid-public-key/");
      if (!data.vapid_public_key) {
        setError("Push notifications aren't configured on the server yet.");
        return;
      }

      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: base64UrlToUint8Array(data.vapid_public_key),
      });
      const json = subscription.toJSON();
      await api.post("/notifications/push-subscriptions/", {
        endpoint: json.endpoint,
        p256dh: json.keys.p256dh,
        auth: json.keys.auth,
      });
      setSubscribed(true);
    } catch {
      setError("Could not enable push notifications on this device.");
    } finally {
      setBusy(false);
    }
  }

  async function disable() {
    setError("");
    setBusy(true);
    try {
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();
      if (subscription) {
        await api.post("/notifications/push-subscriptions/unsubscribe/", {
          endpoint: subscription.endpoint,
        });
        await subscription.unsubscribe();
      }
      setSubscribed(false);
    } catch {
      setError("Could not disable push notifications on this device.");
    } finally {
      setBusy(false);
    }
  }

  if (!SUPPORTED) {
    return (
      <p className="text-sm text-slate-500 dark:text-slate-400">
        Push notifications aren&apos;t supported in this browser.
      </p>
    );
  }

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="font-semibold text-slate-900 dark:text-white">
            {subscribed ? "Enabled on this device" : "Not enabled on this device"}
          </p>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Get budget alerts and price-drop notifications even when SmartSpend isn&apos;t open.
          </p>
        </div>
        <button
          onClick={subscribed ? disable : enable}
          disabled={busy || subscribed === null}
          className={`shrink-0 rounded-lg px-4 py-2 text-sm font-semibold shadow-card transition-colors disabled:opacity-50 ${
            subscribed
              ? "border border-slate-200 text-slate-700 hover:bg-slate-50 dark:border-navy-700 dark:text-slate-200 dark:hover:bg-navy-800"
              : "bg-brand-600 text-white hover:bg-brand-700"
          }`}
        >
          {busy ? "Working…" : subscribed ? "Disable" : "Enable"}
        </button>
      </div>
      {error && (
        <p role="alert" className="mt-3 text-xs font-medium text-red-600 dark:text-red-400">
          {error}
        </p>
      )}
    </div>
  );
}
