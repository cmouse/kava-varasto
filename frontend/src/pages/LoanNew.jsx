import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { useCurrentUser } from "../api/auth";
import { useCreateLoan, useLoanableEquipment, useLoans } from "../api/loans";
import LoanItemCart from "../components/LoanItemCart";
import LoginForm from "../components/LoginForm";

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

const PHONE_PATTERN = "\\+358\\d{6,12}|0\\d{6,12}";
const NAME_PATTERN = "\\S+(\\s+\\S+)+";

function LoanNew() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { data: user, isLoading: isUserLoading } = useCurrentUser();
  const {
    data: equipment,
    isLoading: isEquipmentLoading,
    isError: isEquipmentError,
  } = useLoanableEquipment({
    enabled: user?.authenticated,
  });
  const { data: loans } = useLoans({ enabled: user?.authenticated });
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

  const [borrowerName, setBorrowerName] = useState("");
  const [borrowerPhone, setBorrowerPhone] = useState("");
  const [dueDate, setDueDate] = useState(() => defaultDueDateValue());
  const [details, setDetails] = useState("");
  const [items, setItems] = useState([]);

  const errorMessages = useMemo(
    () => collectErrorMessages(createLoan.error?.response?.data),
    [createLoan.error],
  );

  if (isUserLoading) {
    return null;
  }

  if (!user?.authenticated) {
    return <LoginForm />;
  }

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
    };
    createLoan.mutate(payload, {
      onSuccess: () => {
        navigate("/loans");
      },
    });
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
        <button
          className="btn btn-outline-secondary"
          type="button"
          onClick={() => navigate("/loans")}
        >
          {t("loanForm.cancel")}
        </button>
      </div>
    </form>
  );
}

export default LoanNew;
