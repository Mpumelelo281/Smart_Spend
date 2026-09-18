import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { api } from "../api/client.js";
import PushNotificationSettings from "./PushNotificationSettings.jsx";

vi.mock("../api/client.js", () => ({ api: { get: vi.fn(), post: vi.fn() } }));

afterEach(() => {
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

describe("PushNotificationSettings", () => {
  it("shows an unsupported message when the browser lacks Push/ServiceWorker APIs", async () => {
    render(<PushNotificationSettings />);
    expect(
      await screen.findByText("Push notifications aren't supported in this browser.")
    ).toBeInTheDocument();
    // Never calls the backend when the browser can't do push at all.
    expect(api.get).not.toHaveBeenCalled();
  });
});
