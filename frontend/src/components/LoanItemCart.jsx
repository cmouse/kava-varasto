import { useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { useEquipmentFilter } from "../hooks/useEquipmentFilter";
import { equipmentLabel } from "../utils/equipmentLabel";

const MAX_SUGGESTIONS = 10;

// Exact short_code match first, then prefix match, then everything else --
// unranked substring matching would let "X75" rank X750 ahead of X75 itself,
// so Enter could commit the wrong item. Array.prototype.sort is stable, so
// within a rank the server's category/name ordering survives untouched.
function rankSuggestions(list, term) {
  const needle = term.trim().toLowerCase();
  if (!needle) {
    return list;
  }
  const rank = (item) => {
    const code = (item.short_code ?? "").toLowerCase();
    if (code === needle) {
      return 0;
    }
    if (code.startsWith(needle)) {
      return 1;
    }
    return 2;
  };
  return [...list].sort((a, b) => rank(a) - rank(b));
}

// One search box + suggestion list feeding a shopping-cart-style list of
// added items, replacing what used to be one full equipment <select> per
// loan row (issue #39). Picking an item already in the cart bumps its
// quantity in place instead of adding a second line, which is also what
// makes the serializer's duplicate-equipment 400 unreachable from here.
function LoanItemCart({ equipment, isLoading, isError, items, onItemsChange }) {
  const { t } = useTranslation();
  const { search, setSearch, filteredEquipment } = useEquipmentFilter(equipment);
  const [isFocused, setIsFocused] = useState(false);
  // Event-driven messages only (itemAdded/itemBumped/maxReached/itemRemoved/
  // topUnavailable), set from add()/attemptAddTop()/remove() below and
  // cleared by the search input's onChange -- a real DOM event that fires
  // whenever the user types, meaning "the user moved on from that message".
  // add() clears the search programmatically via setSearch(""), which does
  // NOT fire onChange, so its message survives that clear; but backspacing
  // the box by hand does fire onChange, so a stale message can't resurface
  // just because the box happens to return to a value (e.g. "") an old
  // message was set at. The suggestion-count announcement is still derived
  // during render, since it's a pure function of `search` and `suggestions`
  // and doesn't need an effect to compute it.
  // Carries a slot counter alongside the message: two identical consecutive
  // announcements (Enter twice on an out-of-stock suggestion, re-picking a
  // short-code item already in the cart) are the case to defend against, and
  // a bare string loses them twice over -- setState bails out on Object.is
  // equality, and even when re-rendered React skips writing an unchanged text
  // node, so the live region never fires. Bumping the counter on every event
  // both forces the render and moves the text to the other of the two live
  // regions below, making each announcement a genuine ""->text change.
  // Clearing keeps the counter: typing must not shuffle the slots, or the
  // derived suggestion-count string would be re-announced on every keystroke.
  const [eventStatus, setEventStatus] = useState({ message: "", slot: 0 });
  const searchInputRef = useRef(null);

  function announce(message) {
    setEventStatus((prev) => ({ message, slot: prev.slot + 1 }));
  }

  function clearAnnouncement() {
    setEventStatus((prev) => (prev.message ? { message: "", slot: prev.slot } : prev));
  }

  const suggestions = useMemo(
    () => rankSuggestions(filteredEquipment, search).slice(0, MAX_SUGGESTIONS),
    [filteredEquipment, search],
  );
  const topSuggestion = suggestions.length > 0 ? suggestions[0] : null;
  // An empty box still shows the top-N list for browsing, but Enter/Add must
  // not commit an arbitrary "first in the catalog" item from it -- especially
  // since add() refocuses the search box, so Enter pressed right after adding
  // one item (aiming to submit the loan) would otherwise silently add another.
  const hasTypedTerm = Boolean(search.trim());
  const addButtonDisabled = isLoading || !hasTypedTerm || !topSuggestion;

  // Announce what the search box just found, so someone driving this by
  // screen reader gets a signal even when nothing on screen changes -- a
  // search with zero matches otherwise leaves the last add/remove message
  // sitting there looking current. An event message, once set, wins until
  // the input's onChange clears it (see eventStatus above), so this doesn't
  // stomp on the itemAdded/itemBumped/maxReached/itemRemoved/topUnavailable
  // message an event just set.
  const status = eventStatus.message
    ? eventStatus.message
    : hasTypedTerm
      ? suggestions.length > 0
        ? t("loanForm.suggestionCount", { count: suggestions.length })
        : t("loanForm.noSuggestions")
      : "";

  function focusSearch() {
    searchInputRef.current?.focus();
  }

  function add(item) {
    if (!item || item.loanable_quantity <= 0) {
      return;
    }
    const index = items.findIndex((line) => line.id === item.id);
    if (index === -1) {
      onItemsChange([...items, { id: item.id, name: item.name, short_code: item.short_code, quantity: "1" }]);
      announce(t("loanForm.itemAdded", { name: equipmentLabel(item) }));
    } else if (items[index].short_code) {
      // short_code implies quantity 1 at the DB level -- a line already in
      // the cart has nothing further to add, so this is the max case too.
      announce(t("loanForm.maxReached"));
    } else {
      const current = Number(items[index].quantity) || 0;
      if (current >= item.loanable_quantity) {
        announce(t("loanForm.maxReached"));
      } else {
        const quantity = current + 1;
        onItemsChange(items.map((line, i) => (i === index ? { ...line, quantity: String(quantity) } : line)));
        // Distinct wording from itemAdded: "added" for something that was
        // already in the cart would misdescribe what happened, and the new
        // quantity is the whole point of the event.
        announce(t("loanForm.itemBumped", { name: equipmentLabel(item), quantity }));
      }
    }
    setSearch("");
    focusSearch();
  }

  function attemptAddTop() {
    if (!hasTypedTerm || !topSuggestion) {
      return;
    }
    if (topSuggestion.loanable_quantity <= 0) {
      // Otherwise an exact match that's out of stock leaves Enter/Add
      // looking dead -- the button is enabled (there is a top suggestion),
      // it just can't be added, and that needs saying. Named, not the bare
      // badge fragment: with several suggestions on screen, "not available"
      // alone doesn't say which one.
      announce(t("loanForm.topUnavailable", { name: equipmentLabel(topSuggestion) }));
      return;
    }
    add(topSuggestion);
  }

  function remove(line) {
    onItemsChange(items.filter((item) => item.id !== line.id));
    announce(t("loanForm.itemRemoved", { name: equipmentLabel(line) }));
    focusSearch();
  }

  function setQuantity(id, value) {
    onItemsChange(items.map((item) => (item.id === id ? { ...item, quantity: value } : item)));
  }

  const equipmentById = useMemo(() => new Map((equipment ?? []).map((eq) => [eq.id, eq])), [equipment]);

  return (
    <div>
      {items.length === 0 ? (
        <p className="text-muted mb-2">{t("loanForm.emptyCart")}</p>
      ) : (
        <ul className="list-group mb-2">
          {items.map((line) => {
            const live = equipmentById.get(line.id);
            const available = live?.loanable_quantity ?? 0;
            const unavailable = available < 1;
            return (
              <li
                key={line.id}
                className="list-group-item d-flex flex-column flex-md-row gap-2 align-items-md-center"
              >
                <span className="flex-grow-1">{equipmentLabel(line)}</span>
                {line.short_code ? (
                  <div className="d-flex align-items-center gap-2">
                    <span className="fw-semibold">1</span>
                    {unavailable ? <span className="text-danger small">{t("loanForm.unavailable")}</span> : null}
                  </div>
                ) : (
                  <div className="d-flex align-items-center gap-2">
                    <label className="form-label mb-0 small required" htmlFor={`loan-item-quantity-${line.id}`}>
                      {t("loanForm.quantity")}
                    </label>
                    <input
                      id={`loan-item-quantity-${line.id}`}
                      type="number"
                      min="1"
                      max={unavailable ? undefined : available}
                      className="form-control"
                      style={{ maxWidth: "8rem" }}
                      value={line.quantity}
                      onChange={(event) => setQuantity(line.id, event.target.value)}
                      required={!unavailable}
                    />
                    {unavailable ? <span className="text-danger small">{t("loanForm.unavailable")}</span> : null}
                  </div>
                )}
                <button
                  type="button"
                  className="btn btn-outline-danger btn-sm"
                  onClick={() => remove(line)}
                  aria-label={t("loanForm.removeItem", { name: equipmentLabel(line) })}
                >
                  &times;
                </button>
              </li>
            );
          })}
        </ul>
      )}

      {isError ? <p className="text-danger small">{t("storage.error")}</p> : null}

      <div className="d-flex gap-2">
        <input
          ref={searchInputRef}
          id="loanItemSearch"
          type="search"
          className="form-control"
          placeholder={t("equipmentFilter.searchPlaceholder")}
          value={search}
          onChange={(event) => {
            // A real DOM event, not a state-derived effect: the user typing
            // (including backspacing to "") means "moved on", so any event
            // message on screen -- however it was set -- is no longer
            // current and must not resurface just because `search` later
            // returns to a value it was set at (see eventStatus above).
            setSearch(event.target.value);
            clearAnnouncement();
          }}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          onKeyDown={(event) => {
            // This box sits inside the loan form, so Enter would otherwise
            // submit the loan -- with whatever's already in the cart --
            // instead of adding the item the user is aiming at.
            if (event.key === "Enter") {
              event.preventDefault();
              attemptAddTop();
            }
          }}
          disabled={isLoading}
        />
        <button
          type="button"
          className="btn btn-outline-secondary text-nowrap"
          onClick={attemptAddTop}
          disabled={addButtonDisabled}
        >
          {t("loanForm.addItem")}
        </button>
      </div>

      {isFocused && suggestions.length > 0 ? (
        <div className="list-group mt-1">
          {suggestions.map((eq) => {
            const eqUnavailable = eq.loanable_quantity <= 0;
            return (
              <button
                key={eq.id}
                type="button"
                className="list-group-item list-group-item-action py-1"
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => add(eq)}
                disabled={eqUnavailable}
              >
                <div className="d-flex justify-content-between">
                  <span>{equipmentLabel(eq)}</span>
                  <span className="text-muted small">
                    {eqUnavailable ? t("loanForm.unavailable") : `${eq.loanable_quantity} ${t("loanForm.available")}`}
                  </span>
                </div>
                <div className="text-muted small">{eq.category}</div>
              </button>
            );
          })}
        </div>
      ) : null}

      {/* Two regions, both present from first mount -- a live region added to
          the DOM in the same commit as its content is announced unreliably,
          and one that merely keeps its text is not announced at all. The
          message alternates between them so every announcement is an
          ""->text change in a region that was already there. */}
      <div className="form-text mb-0">
        <div aria-live="polite">{eventStatus.slot % 2 === 0 ? status : ""}</div>
        <div aria-live="polite">{eventStatus.slot % 2 === 0 ? "" : status}</div>
      </div>
    </div>
  );
}

export default LoanItemCart;
