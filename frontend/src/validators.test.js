import { describe, expect, it } from "vitest";

import {
  totalAllocated,
  validateDutEmail,
  validateEmailFormat,
  validateMoneyAmount,
  validatePassword,
  validateRequired,
} from "./validators.js";

describe("validateDutEmail", () => {
  it("requires a value", () => {
    expect(validateDutEmail("")).toBe("Email is required.");
  });

  it("rejects a malformed address", () => {
    expect(validateDutEmail("not-an-email")).toBe("Enter a valid email address.");
  });

  it("rejects a non-DUT domain", () => {
    expect(validateDutEmail("student@gmail.com")).toMatch(/DUT email address/);
  });

  it("accepts a dut4life.ac.za address", () => {
    expect(validateDutEmail("thabo@dut4life.ac.za")).toBe("");
  });

  it("accepts a dut.ac.za address", () => {
    expect(validateDutEmail("staff@dut.ac.za")).toBe("");
  });

  it("is case-insensitive on the domain", () => {
    expect(validateDutEmail("thabo@DUT4LIFE.AC.ZA")).toBe("");
  });
});

describe("validateEmailFormat", () => {
  it("accepts any well-formed address, not just DUT domains", () => {
    expect(validateEmailFormat("someone@gmail.com")).toBe("");
  });

  it("rejects a malformed address", () => {
    expect(validateEmailFormat("nope")).toBe("Enter a valid email address.");
  });
});

describe("validatePassword", () => {
  it("requires at least 10 characters", () => {
    expect(validatePassword("short1!")).toMatch(/at least 10 characters/);
  });

  it("accepts a 10+ character password", () => {
    expect(validatePassword("Correct-Horse-9!")).toBe("");
  });
});

describe("validateMoneyAmount", () => {
  it("requires a value", () => {
    expect(validateMoneyAmount("")).toBe("Amount is required.");
  });

  it("rejects a negative amount", () => {
    expect(validateMoneyAmount("-5")).toBe("Amount cannot be negative.");
  });

  it("rejects more than two decimal places", () => {
    expect(validateMoneyAmount("10.999")).toMatch(/at most two decimal places/);
  });

  it("accepts a valid amount", () => {
    expect(validateMoneyAmount("199.99")).toBe("");
  });

  it("accepts a whole-number amount", () => {
    expect(validateMoneyAmount("200")).toBe("");
  });
});

describe("validateRequired", () => {
  it("flags a blank value with the given label", () => {
    expect(validateRequired("Category")("   ")).toBe("Category is required.");
  });

  it("passes a non-blank value", () => {
    expect(validateRequired("Category")("Groceries")).toBe("");
  });
});

describe("totalAllocated", () => {
  it("sums allocated_amount across categories", () => {
    const categories = [{ allocated_amount: "100.50" }, { allocated_amount: "49.50" }];
    expect(totalAllocated(categories)).toBe(150);
  });

  it("treats a missing/invalid amount as zero", () => {
    expect(totalAllocated([{ allocated_amount: "" }, { allocated_amount: "20" }])).toBe(20);
  });

  it("returns 0 for an empty list", () => {
    expect(totalAllocated([])).toBe(0);
  });
});
