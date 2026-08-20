import { useEffect, useMemo, useRef, useState } from "react";
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
  const [status, setStatus] = useState("");
  const searchInputRef = useRef(null);

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
  // sitting there looking current. Skipped while the box is empty so this
  // doesn't stomp on the itemAdded/itemBumped/maxReached message add() just
  // set (add() clears search back to "" as its last step).
  useEffect(() => {
    if (!search.trim()) {
      return;
    }
    setStatus(
      suggestions.length > 0
        ? t("loanForm.suggestionCount", { count: suggestions.length })
        : t("loanForm.noSuggestions"),
    );
  }, [search, suggestions.length, t]);

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
      setStatus(t("loanForm.itemAdded", { name: equipmentLabel(item) }));
    } else if (items[index].short_code) {
      // short_code implies quantity 1 at the DB level -- a line already in
      // the cart has nothing further to add, so this is the max case too.
      setStatus(t("loanForm.maxReached"));
    } else {
      const current = Number(items[index].quantity) || 0;
      if (current >= item.loanable_quantity) {
        setStatus(t("loanForm.maxReached"));
      } else {
        const quantity = current + 1;
        onItemsChange(items.map((line, i) => (i === index ? { ...line, quantity: String(quantity) } : line)));
        // Distinct wording from itemAdded: two identical consecutive
        // aria-live strings get deduped by most screen readers, and a bump
        // needs its own announcement or the quantity change goes unheard.
        setStatus(t("loanForm.itemBumped", { name: equipmentLabel(item), quantity }));
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
      setStatus(t("loanForm.topUnavailable", { name: equipmentLabel(topSuggestion) }));
      return;
    }
    add(topSuggestion);
  }

  function remove(line) {
    onItemsChange(items.filter((item) => item.id !== line.id));
    setStatus(t("loanForm.itemRemoved", { name: equipmentLabel(line) }));
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
          onChange={(event) => setSearch(event.target.value)}
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

      <div aria-live="polite" className="form-text mb-0">
        {status}
      </div>
    </div>
  );
}

export default LoanItemCart;
