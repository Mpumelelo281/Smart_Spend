// Best-effort "which of the student's own budget categories does this item
// probably belong to" hint for the log-expense form. Deliberately never
// authoritative: it only pre-selects a dropdown option the student can
// still change (or has already changed — see `categoryTouched` in
// Dashboard.jsx) before saving. The category actually recorded is always
// whatever ends up selected at submit time, exactly as before this file
// existed; nothing here talks to the server or changes what gets sent.
//
// Categories are freeform names the student typed themselves (there's no
// fixed global taxonomy — see BudgetCategory in apps/budgets/models.py), so
// this can't just map a keyword straight to a category. Instead: match the
// item description against a topic's keywords, then see if any of the
// student's own category names overlaps with that topic's common synonyms.
const TOPIC_HINTS = [
  {
    synonyms: ["toiletries", "toiletry", "personal care", "hygiene", "bathroom"],
    keywords: [
      "toothpaste", "toothbrush", "soap", "shampoo", "conditioner", "deodorant",
      "lotion", "sanitary", "tampon", "pad", "razor", "toilet paper", "tissue", "roll-on",
    ],
  },
  {
    synonyms: ["food", "groceries", "grocery", "meals"],
    keywords: [
      "bread", "milk", "rice", "eggs", "chicken", "beef", "mince", "vegetable", "fruit",
      "apple", "banana", "cereal", "pasta", "maize", "meal", "snack", "chips", "chocolate",
      "cooldrink", "juice", "yoghurt", "cheese", "coffee", "tea", "sugar",
    ],
  },
  {
    synonyms: ["textbooks", "stationery", "school", "education", "books"],
    keywords: [
      "textbook", "notebook", "pen", "pencil", "printing", "photocopy", "calculator",
      "file", "folder", "highlighter", "ring binder",
    ],
  },
  {
    synonyms: ["transport", "travel", "taxi"],
    keywords: ["taxi", "uber", "bolt", "bus", "train", "petrol", "fuel", "fare", "parking"],
  },
  {
    synonyms: ["clothes", "clothing", "shoes"],
    keywords: [
      "shirt", "jeans", "trousers", "dress", "shoes", "sneakers", "jacket", "socks", "underwear",
    ],
  },
  {
    synonyms: ["airtime", "data", "phone", "communication"],
    keywords: ["airtime", "data bundle", "wifi", "recharge", "prepaid"],
  },
  {
    synonyms: ["rent", "residence", "accommodation"],
    keywords: ["rent", "residence", "accommodation", "lease", "deposit"],
  },
  {
    synonyms: ["entertainment", "leisure"],
    keywords: ["movie", "cinema", "netflix", "spotify", "outing", "party", "concert"],
  },
];

/** Returns a matching category's id, or null if nothing matched confidently
 * enough to suggest. `categories` is the current budget's own category list
 * (each `{ category_id, name, ... }`). */
export function suggestCategoryId(description, categories) {
  const text = description.trim().toLowerCase();
  if (!text || !categories?.length) return null;

  for (const { synonyms, keywords } of TOPIC_HINTS) {
    if (!keywords.some((keyword) => text.includes(keyword))) continue;

    const match = categories.find((c) => {
      const name = c.name.trim().toLowerCase();
      return synonyms.some((s) => name.includes(s) || s.includes(name));
    });
    if (match) return match.category_id;
  }
  return null;
}
