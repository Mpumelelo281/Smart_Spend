import { afterEach, describe, expect, it } from "vitest";

import { api, clearTokens, getTokens, setTokens } from "./client.js";

afterEach(() => {
  localStorage.clear();
});

describe("token storage", () => {
  it("returns null when nothing is stored", () => {
    expect(getTokens()).toBeNull();
  });

  it("round-trips tokens through localStorage", () => {
    setTokens({ access: "a", refresh: "r" });
    expect(getTokens()).toEqual({ access: "a", refresh: "r" });
  });

  it("clearTokens removes the stored value", () => {
    setTokens({ access: "a", refresh: "r" });
    clearTokens();
    expect(getTokens()).toBeNull();
  });

  it("survives corrupted localStorage content instead of throwing", () => {
    localStorage.setItem("smartspend.tokens", "{not json");
    expect(getTokens()).toBeNull();
  });
});

describe("request interceptor", () => {
  it("attaches the Authorization header when a token is stored", async () => {
    setTokens({ access: "test-access-token", refresh: "r" });
    const config = await api.interceptors.request.handlers[0].fulfilled({ headers: {} });
    expect(config.headers.Authorization).toBe("Bearer test-access-token");
  });

  it("leaves the Authorization header unset with no stored token", async () => {
    const config = await api.interceptors.request.handlers[0].fulfilled({ headers: {} });
    expect(config.headers.Authorization).toBeUndefined();
  });
});
