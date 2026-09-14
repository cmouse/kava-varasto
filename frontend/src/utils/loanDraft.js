import scriptName from "./scriptName";

// Namespaced per mount point: sessionStorage is per-origin, and two
// deployments sharing a host (e.g. a root-mounted install next to one under
// "/varasto") must not see each other's in-progress draft.
const STORAGE_KEY = `${scriptName}/loanDraft`;

function isPlainObject(value) {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

// A stored line is {id, name, short_code, quantity} (see LoanItemCart.add).
// sessionStorage content is attacker-controllable in a shared-browser
// scenario, so every field is re-typed defensively rather than trusted.
function sanitizeItems(rawItems) {
  if (!Array.isArray(rawItems)) {
    return [];
  }
  return rawItems
    .filter((item) => isPlainObject(item) && (typeof item.id === "number" || typeof item.id === "string"))
    .map((item) => ({
      id: item.id,
      name: typeof item.name === "string" ? item.name : "",
      short_code: typeof item.short_code === "string" ? item.short_code : "",
      quantity:
        typeof item.quantity === "string" || typeof item.quantity === "number" ? String(item.quantity) : "1",
    }));
}

// Reads and defensively validates the draft. Returns null when there is
// nothing usable to restore -- storage empty, unavailable (private window /
// site data blocked), or holding something that isn't the shape we wrote.
export function loadLoanDraft() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return null;
    }
    const parsed = JSON.parse(raw);
    if (!isPlainObject(parsed)) {
      return null;
    }
    return {
      borrowerName: typeof parsed.borrowerName === "string" ? parsed.borrowerName : "",
      borrowerPhone: typeof parsed.borrowerPhone === "string" ? parsed.borrowerPhone : "",
      dueDate: typeof parsed.dueDate === "string" ? parsed.dueDate : "",
      details: typeof parsed.details === "string" ? parsed.details : "",
      items: sanitizeItems(parsed.items),
      tripNotification: parsed.tripNotification === true,
      // Explicit "was this ever edited" flag, not derived from field values
      // (a restored value can coincide with what a fresh default happens to
      // be, which is not the same thing as "untouched" -- see LoanNew.jsx).
      // A draft written before this field existed has no way to say, so it
      // defaults to true: treating an old-format draft as touched risks
      // keeping it around a little longer, treating it as untouched risks
      // silently deleting content the user actually entered.
      touched: typeof parsed.touched === "boolean" ? parsed.touched : true,
    };
  } catch {
    return null;
  }
}

export function saveLoanDraft(draft) {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(draft));
  } catch {
    // Private window / site data blocked -- the draft just doesn't persist.
  }
}

// Called on submit success, Cancel, login and logout -- see LoanNew.jsx and
// api/auth.js. Login is included even though a fresh login has no draft of
// its own: borrower_name/borrower_phone is third-party personal data, and a
// shared browser must not show the next signed-in user a draft the previous
// one left behind.
export function clearLoanDraft() {
  try {
    sessionStorage.removeItem(STORAGE_KEY);
  } catch {
    // Same as above -- nothing to clean up if storage isn't available.
  }
}
