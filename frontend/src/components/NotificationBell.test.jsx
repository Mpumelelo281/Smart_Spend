import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { api } from "../api/client.js";
import NotificationBell from "./NotificationBell.jsx";

vi.mock("../api/client.js", () => ({ api: { get: vi.fn(), post: vi.fn() } }));

afterEach(() => {
  vi.clearAllMocks();
});

const NOTIFICATIONS = [
  {
    notification_id: "1",
    message: "You've used 80% of your Food budget.",
    is_read: false,
    created_at: new Date().toISOString(),
  },
  {
    notification_id: "2",
    message: "Welcome to SmartSpend.",
    is_read: true,
    created_at: new Date().toISOString(),
  },
];

describe("NotificationBell", () => {
  it("shows the unread count badge", async () => {
    api.get.mockResolvedValue({ data: NOTIFICATIONS });
    render(<NotificationBell />);

    await waitFor(() => expect(api.get).toHaveBeenCalledWith("/notifications/"));
    expect(await screen.findByLabelText("Notifications (1 unread)")).toBeInTheDocument();
  });

  it("shows no badge when nothing is unread", async () => {
    api.get.mockResolvedValue({ data: [] });
    render(<NotificationBell />);

    expect(await screen.findByLabelText("Notifications")).toBeInTheDocument();
  });

  it("lists notifications and marks one read on click", async () => {
    api.get.mockResolvedValue({ data: NOTIFICATIONS });
    api.post.mockResolvedValue({});
    const user = userEvent.setup();
    render(<NotificationBell />);

    await user.click(await screen.findByLabelText("Notifications (1 unread)"));
    expect(screen.getByText("You've used 80% of your Food budget.")).toBeInTheDocument();

    await user.click(screen.getByText("You've used 80% of your Food budget."));
    expect(api.post).toHaveBeenCalledWith("/notifications/1/read/");
  });

  it("degrades to an empty bell when the fetch fails", async () => {
    api.get.mockRejectedValue(new Error("network down"));
    render(<NotificationBell />);

    await waitFor(() => expect(api.get).toHaveBeenCalled());
    expect(await screen.findByLabelText("Notifications")).toBeInTheDocument();
  });
});
