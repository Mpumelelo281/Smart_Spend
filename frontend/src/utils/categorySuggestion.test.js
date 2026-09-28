import { describe, expect, it } from "vitest";

import { suggestCategoryId } from "./categorySuggestion.js";

const CATEGORIES = [
  { category_id: "food-id", name: "Food" },
  { category_id: "toiletries-id", name: "Toiletries" },
  { category_id: "transport-id", name: "Transport" },
];

describe("suggestCategoryId", () => {
  it("matches a toiletries item to the Toiletries category", () => {
    expect(suggestCategoryId("Colgate toothpaste", CATEGORIES)).toBe("toiletries-id");
  });

  it("matches a groceries item to the Food category", () => {
    expect(suggestCategoryId("Bread and milk", CATEGORIES)).toBe("food-id");
  });

  it("matches a transport item to the Transport category", () => {
    expect(suggestCategoryId("Uber to campus", CATEGORIES)).toBe("transport-id");
  });

  it("is case-insensitive", () => {
    expect(suggestCategoryId("TOOTHPASTE", CATEGORIES)).toBe("toiletries-id");
  });

  it("returns null for an empty description", () => {
    expect(suggestCategoryId("", CATEGORIES)).toBeNull();
  });

  it("returns null when no keyword matches", () => {
    expect(suggestCategoryId("xyz unrecognised item", CATEGORIES)).toBeNull();
  });

  it("returns null when the matching topic has no corresponding student category", () => {
    // Toothpaste matches the toiletries topic, but this student has no
    // category whose name overlaps with it — never force an unrelated one.
    expect(suggestCategoryId("Toothpaste", [{ category_id: "x", name: "Rent" }])).toBeNull();
  });

  it("returns null with no categories at all", () => {
    expect(suggestCategoryId("Bread", [])).toBeNull();
  });
});
