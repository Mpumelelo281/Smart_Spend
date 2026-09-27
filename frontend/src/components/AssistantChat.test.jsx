import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { api } from "../api/client.js";
import AssistantChat from "./AssistantChat.jsx";

vi.mock("../api/client.js", () => ({ api: { post: vi.fn() } }));

afterEach(() => {
  vi.clearAllMocks();
});

describe("AssistantChat", () => {
  it("greets the student on open and shows quick replies", async () => {
    api.post.mockResolvedValue({
      data: {
        reply: "Hi! I'm SpendWise, your SmartSpend assistant.",
        intent: "greeting",
        quick_replies: [{ label: "📊 My spending", message: "How much have I spent this month?" }],
      },
    });
    const user = userEvent.setup();
    render(<AssistantChat />);

    await user.click(screen.getByLabelText("Open SpendWise assistant"));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith("/assistant/ask/", { message: "Hi" }));
    expect(await screen.findByText("Hi! I'm SpendWise, your SmartSpend assistant.")).toBeInTheDocument();
    expect(screen.getByText("📊 My spending")).toBeInTheDocument();
  });

  it("sends a typed message and shows the reply", async () => {
    api.post
      .mockResolvedValueOnce({ data: { reply: "Hi there!", intent: "greeting", quick_replies: [] } })
      .mockResolvedValueOnce({
        data: { reply: "You've spent R345.00 this month.", intent: "spend_by_category", quick_replies: [] },
      });
    const user = userEvent.setup();
    render(<AssistantChat />);

    await user.click(screen.getByLabelText("Open SpendWise assistant"));
    await screen.findByText("Hi there!");

    await user.type(screen.getByPlaceholderText("Ask about your spending…"), "How much did I spend?");
    await user.click(screen.getByLabelText("Send"));

    expect(await screen.findByText("You've spent R345.00 this month.")).toBeInTheDocument();
    expect(api.post).toHaveBeenLastCalledWith("/assistant/ask/", { message: "How much did I spend?" });
  });

  it("shows a friendly message when the request fails", async () => {
    api.post.mockRejectedValue(new Error("network down"));
    const user = userEvent.setup();
    render(<AssistantChat />);

    await user.click(screen.getByLabelText("Open SpendWise assistant"));

    expect(await screen.findByText(/couldn't reach the server/i)).toBeInTheDocument();
  });

  it("closes the panel", async () => {
    api.post.mockResolvedValue({ data: { reply: "Hi there!", intent: "greeting", quick_replies: [] } });
    const user = userEvent.setup();
    render(<AssistantChat />);

    await user.click(screen.getByLabelText("Open SpendWise assistant"));
    await screen.findByText("Hi there!");

    await user.click(screen.getByLabelText("Close chat"));
    expect(screen.queryByPlaceholderText("Ask about your spending…")).not.toBeInTheDocument();
  });
});
