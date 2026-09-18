import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { useAuth } from "../context/AuthContext.jsx";
import ProtectedRoute from "./ProtectedRoute.jsx";

vi.mock("../context/AuthContext.jsx", () => ({ useAuth: vi.fn() }));
// Layout pulls in CartContext/ThemeContext/NotificationBell (which makes a
// live API call) — none of that is what this test is about, so it's
// swapped for a passthrough to keep the test focused on ProtectedRoute's
// own loading/redirect/role logic (Rule 9: a UX nicety, not the real
// access-control boundary, which is enforced server-side regardless).
vi.mock("./Layout.jsx", () => ({ default: ({ children }) => <div>{children}</div> }));

afterEach(() => {
  vi.clearAllMocks();
});

function renderProtected({ role } = {}) {
  return render(
    <MemoryRouter initialEntries={["/secret"]}>
      <Routes>
        <Route path="/login" element={<p>Login page</p>} />
        <Route path="/" element={<p>Dashboard page</p>} />
        <Route
          path="/secret"
          element={
            <ProtectedRoute role={role}>
              <p>Secret content</p>
            </ProtectedRoute>
          }
        />
      </Routes>
    </MemoryRouter>
  );
}

describe("ProtectedRoute", () => {
  it("shows a loading state while auth is resolving", () => {
    useAuth.mockReturnValue({ user: null, loading: true });
    renderProtected();
    expect(screen.getByText("Loading…")).toBeInTheDocument();
  });

  it("redirects to /login when there is no authenticated user", () => {
    useAuth.mockReturnValue({ user: null, loading: false });
    renderProtected();
    expect(screen.getByText("Login page")).toBeInTheDocument();
  });

  it("redirects to / when the user's role doesn't match", () => {
    useAuth.mockReturnValue({ user: { role: "STUDENT" }, loading: false });
    renderProtected({ role: "ADMINISTRATOR" });
    expect(screen.getByText("Dashboard page")).toBeInTheDocument();
  });

  it("renders the protected content for a matching role", () => {
    useAuth.mockReturnValue({ user: { role: "STUDENT" }, loading: false });
    renderProtected({ role: "STUDENT" });
    expect(screen.getByText("Secret content")).toBeInTheDocument();
  });

  it("renders the protected content when no role is required", () => {
    useAuth.mockReturnValue({ user: { role: "STUDENT" }, loading: false });
    renderProtected();
    expect(screen.getByText("Secret content")).toBeInTheDocument();
  });
});
