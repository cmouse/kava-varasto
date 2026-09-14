import { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { useCurrentUser } from "../api/auth";
import { useCreateLoan, useLoanableEquipment, useLoans } from "../api/loans";
import LoanItemCart from "../components/LoanItemCart";
import LoginForm from "../components/LoginForm";
import { clearLoanDraft, loadLoanDraft, saveLoanDraft } from "../utils/loanDraft";
import PHONE_PATTERN from "../utils/phonePattern";

// A whole non-JSON error document (an nginx 502 page, a DEBUG=False Django
// 500 page) always arrives as the top-level response body, as a string, and
// always starts with a tag -- unlike a DRF validation message, which can
// legitimately contain "<" or "<something>" as part of free-text equipment
// names (Equipment.name has no charset restriction). So this filter only
// ever applies to the outermost string, never to one found while walking
// into an object/array -- a nested string is always a real validation
// message and must never be dropped.
const MAX_PLAUSIBLE_ERROR_LENGTH = 300;

function looksLikeMarkup(value) {
  return value.trim().startsWith("<");
}

// DRF error payloads for this endpoint come in two shapes -- a flat list of
// strings from validate_items ({"items": ["Only 2 of X available..."]}) and a
// list of per-child field errors from the item serializer
// ({"items": [{"quantity": ["..."]}, {}]}) -- so walk to any depth rather
// than assuming a list of strings, or nested objects print as [object Object].
function collectErrorMessages(data, isTopLevel = true) {
  if (typeof data === "string") {
    if (isTopLevel && (looksLikeMarkup(data) || data.length > MAX_PLAUSIBLE_ERROR_LENGTH)) {
      return [];
    }
    return [data];
  }
  if (Array.isArray(data)) {
    return data.flatMap((item) => collectErrorMessages(item, false));
  }
  if (data && typeof data === "object") {
    return Object.values(data).flatMap((value) => collectErrorMessages(value, false));
  }
  return [];
}

function toDateInputValue(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function todayValue() {
  return toDateInputValue(new Date());
}

function defaultDueDateValue() {
  const d = new Date();
  d.setDate(d.getDate() + 7);
  return toDateInputValue(d);
}

// A restored due date can be stale -- the tab that wrote it may have sat
// open overnight -- and the date input's min={todayValue()} silently
// rejects anything before today rather than showing an error. Clamped
// forward to today rather than reset to the today+7 default: today is the
// smallest change that makes the stored value valid again, so it disturbs
// the user's original choice the least (a due date they picked as "a few
// days out" doesn't silently jump a whole week further away). Returns null
// for anything that isn't a plain YYYY-MM-DD string, so the caller falls
// back to the normal default.
function clampDueDateValue(value) {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    return null;
  }
  const today = todayValue();
  return value < today ? today : value;
}

// Restored items came from a session that may be hours old: equipment can
// have been deleted, gone non-loanable, or dropped in available quantity
// since. Reconciled once the live equipment list is in hand, never trusting
// the stored quantity or even the stored equipment's continued existence.
function reconcileDraftItems(items, equipment) {
  const byId = new Map(equipment.map((eq) => [eq.id, eq]));
  return items
    .map((item) => {
      const live = byId.get(item.id);
      if (!live || live.loanable_quantity <= 0) {
        return null;
      }
      if (item.short_code) {
        // short_code implies quantity 1 at the DB level -- nothing to clamp.
        return item;
      }
      const quantity = Math.min(Number(item.quantity) || 1, live.loanable_quantity);
      return quantity > 0 ? { ...item, quantity: String(quantity) } : null;
    })
    .filter((item) => item !== null);
}

const NAME_PATTERN = "\\S+(\\s+\\S+)+";

function LoanNew() {
  const { data: user, isLoading: isUserLoading } = useCurrentUser();

  if (isUserLoading) {
    return null;
  }

  if (!user?.authenticated) {
    return <LoginForm />;
  }

  // LoanNewForm carries local state (borrower name/phone, cart, ...)
  // mirrored into sessionStorage, and it renders LoginForm above in place --
  // no route change -- when unauthenticated, rather than unmounting. Keying
  // on the signed-in user's id forces a fresh LoanNewForm instance (and a
  // fresh sessionStorage read) on any authenticated-user swap, so state
  // from whoever was filling this form out before can never surface for
  // the next person on a shared browser. In this app's actual flows,
  // swapping users always passes through the LoginForm branch above first
  // -- which already discards LoanNewForm's state by unmounting it -- so
  // the key is defense-in-depth against ever relying on that as the only
  // guard.
  return <LoanNewForm key={user.user.id} />;
}

function LoanNewForm() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { data: equipment, isLoading: isEquipmentLoading, isError: isEquipmentError } = useLoanableEquipment();
  const { data: loans } = useLoans();
  const createLoan = useCreateLoan();

  const borrowerPhoneByName = useMemo(() => {
    const map = new Map();
    for (const loan of loans ?? []) {
      if (!map.has(loan.borrower_name)) {
        map.set(loan.borrower_name, loan.borrower_phone);
      }
    }
    return map;
  }, [loans]);

  // Read once, synchronously, via a lazy initializer -- not a hydrating
  // useEffect, which would render empty first and race the persist effect
  // below (which could then write that empty state over a good draft).
  const [draft] = useState(() => loadLoanDraft());

  const [borrowerName, setBorrowerName] = useState(() => draft?.borrowerName ?? "");
  const [borrowerPhone, setBorrowerPhone] = useState(() => draft?.borrowerPhone ?? "");
  const [dueDate, setDueDate] = useState(() => clampDueDateValue(draft?.dueDate) ?? defaultDueDateValue());
  const [details, setDetails] = useState(() => draft?.details ?? "");
  const [items, setItems] = useState(() => draft?.items ?? []);
  const [tripNotification, setTripNotification] = useState(() => draft?.tripNotification ?? false);

  // Restored items are shown as-is (LoanItemCart already renders an
  // unrecognised/unavailable line as unavailable) until the equipment list
  // actually resolves -- reconciling while isEquipmentLoading is still true
  // would drop every restored item on each reload, before there's any live
  // data to check them against. Runs once: this is a one-time cleanup of a
  // restored draft, not an ongoing sync that would fight the user's own
  // edits (equipment availability is otherwise deliberately advisory here --
  // see DESIGN.md).
  const didReconcileDraftItems = useRef(false);
  useEffect(() => {
    if (didReconcileDraftItems.current || isEquipmentLoading || !equipment) {
      return;
    }
    didReconcileDraftItems.current = true;
    setItems((current) => reconcileDraftItems(current, equipment));
  }, [isEquipmentLoading, equipment]);

  useEffect(() => {
    saveLoanDraft({ borrowerName, borrowerPhone, dueDate, details, items, tripNotification });
  }, [borrowerName, borrowerPhone, dueDate, details, items, tripNotification]);

  const errorMessages = useMemo(
    () => collectErrorMessages(createLoan.error?.response?.data),
    [createLoan.error],
  );

  function handleBorrowerNameChange(event) {
    const name = event.target.value;
    setBorrowerName(name);
    const knownPhone = borrowerPhoneByName.get(name);
    if (knownPhone && !borrowerPhone) {
      setBorrowerPhone(knownPhone);
    }
  }

  function handleSubmit(event) {
    event.preventDefault();
    const payload = {
      borrower_name: borrowerName,
      borrower_phone: borrowerPhone,
      due_date: dueDate,
      details,
      items: items.map((item) => ({ equipment: item.id, quantity: Number(item.quantity) })),
      trip_notification_submitted: tripNotification,
    };
    createLoan.mutate(payload, {
      onSuccess: () => {
        clearLoanDraft();
        navigate("/loans");
      },
    });
  }

  function handleCancel() {
    clearLoanDraft();
    navigate("/loans");
  }

  return (
    <form onSubmit={handleSubmit} style={{ maxWidth: "40rem" }}>
      <h1 className="h4 mb-3">{t("loanForm.title")}</h1>

      <div className="mb-3">
        <label className="form-label required" htmlFor="borrowerName">
          {t("loanForm.borrowerName")}
        </label>
        <input
          id="borrowerName"
          className="form-control"
          list="borrowerNameHistory"
          value={borrowerName}
          onChange={handleBorrowerNameChange}
          pattern={NAME_PATTERN}
          title={t("loanForm.borrowerNameHint")}
          required
        />
        <datalist id="borrowerNameHistory">
          {Array.from(borrowerPhoneByName.keys()).map((name) => (
            <option key={name} value={name} />
          ))}
        </datalist>
      </div>

      <div className="mb-3">
        <label className="form-label required" htmlFor="borrowerPhone">
          {t("loanForm.borrowerPhone")}
        </label>
        <input
          id="borrowerPhone"
          type="tel"
          className="form-control"
          value={borrowerPhone}
          onChange={(event) => setBorrowerPhone(event.target.value)}
          pattern={PHONE_PATTERN}
          title={t("loanForm.borrowerPhoneHint")}
          required
        />
      </div>

      <div className="mb-3">
        <label className="form-label required" htmlFor="dueDate">
          {t("loanForm.dueDate")}
        </label>
        <input
          id="dueDate"
          type="date"
          className="form-control"
          value={dueDate}
          min={todayValue()}
          onChange={(event) => setDueDate(event.target.value)}
          required
        />
      </div>

      <div className="mb-3">
        <label className="form-label" htmlFor="details">
          {t("loanForm.details")}
        </label>
        <textarea
          id="details"
          className="form-control"
          rows="2"
          value={details}
          onChange={(event) => setDetails(event.target.value)}
        />
      </div>

      <div className="mb-3">
        <label className="form-label required" htmlFor="loanItemSearch">
          {t("loanForm.items")}
        </label>
        <LoanItemCart
          equipment={equipment}
          isLoading={isEquipmentLoading}
          isError={isEquipmentError}
          items={items}
          onItemsChange={setItems}
        />
      </div>

      <div className="form-check mb-3">
        <input
          className="form-check-input"
          type="checkbox"
          id="loan-trip-notification"
          checked={tripNotification}
          onChange={(event) => setTripNotification(event.target.checked)}
          required
        />
        <label className="form-check-label required" htmlFor="loan-trip-notification">
          {t("loanForm.tripNotification")}
        </label>
        <div className="form-text">{t("loanForm.tripNotificationHint")}</div>
      </div>

      {createLoan.isError ? (
        <div className="alert alert-danger py-2" role="alert">
          {errorMessages.length > 0 ? (
            <ul className="mb-0 ps-3">
              {errorMessages.map((message, index) => (
                <li key={index}>{message}</li>
              ))}
            </ul>
          ) : (
            t("loanForm.error")
          )}
        </div>
      ) : null}
      {createLoan.isSuccess ? (
        <div className="alert alert-success py-2" role="alert">
          {t("loanForm.success")}
        </div>
      ) : null}

      <div className="d-flex gap-2">
        <button
          className="btn btn-primary flex-grow-1"
          type="submit"
          disabled={items.length === 0 || createLoan.isPending || isEquipmentLoading}
        >
          {t("loanForm.submit")}
        </button>
        <button className="btn btn-outline-secondary" type="button" onClick={handleCancel}>
          {t("loanForm.cancel")}
        </button>
      </div>
    </form>
  );
}

export default LoanNew;
