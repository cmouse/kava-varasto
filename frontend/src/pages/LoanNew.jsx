import { useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { useCurrentUser } from "../api/auth";
import { useCreateLoan, useLoanableEquipment } from "../api/loans";
import LoginForm from "../components/LoginForm";

function emptyItem(key) {
  return { key, equipmentId: "", quantity: 1 };
}

function equipmentLabel(item) {
  return item.short_code ? `${item.short_code} ${item.name}` : item.name;
}

function LoanNew() {
  const { t } = useTranslation();
  const { data: user, isLoading: isUserLoading } = useCurrentUser();
  const { data: equipment, isLoading: isEquipmentLoading } = useLoanableEquipment({
    enabled: user?.authenticated,
  });
  const createLoan = useCreateLoan();
  const nextKey = useRef(1);

  const [borrowerName, setBorrowerName] = useState("");
  const [borrowerPhone, setBorrowerPhone] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [details, setDetails] = useState("");
  const [items, setItems] = useState([emptyItem(0)]);

  if (isUserLoading) {
    return null;
  }

  if (!user?.authenticated) {
    return <LoginForm />;
  }

  function addItem() {
    nextKey.current += 1;
    setItems((prev) => [...prev, emptyItem(nextKey.current)]);
  }

  function removeItem(key) {
    setItems((prev) => (prev.length > 1 ? prev.filter((item) => item.key !== key) : prev));
  }

  function updateItem(key, changes) {
    setItems((prev) => prev.map((item) => (item.key === key ? { ...item, ...changes } : item)));
  }

  function handleSubmit(event) {
    event.preventDefault();
    const payload = {
      borrower_name: borrowerName,
      borrower_phone: borrowerPhone,
      due_date: dueDate,
      details,
      items: items
        .filter((item) => item.equipmentId)
        .map((item) => ({ equipment: Number(item.equipmentId), quantity: Number(item.quantity) })),
    };
    createLoan.mutate(payload, {
      onSuccess: () => {
        setBorrowerName("");
        setBorrowerPhone("");
        setDueDate("");
        setDetails("");
        nextKey.current += 1;
        setItems([emptyItem(nextKey.current)]);
      },
    });
  }

  return (
    <form onSubmit={handleSubmit} style={{ maxWidth: "40rem" }}>
      <h1 className="h4 mb-3">{t("loanForm.title")}</h1>

      <div className="mb-3">
        <label className="form-label" htmlFor="borrowerName">
          {t("loanForm.borrowerName")}
        </label>
        <input
          id="borrowerName"
          className="form-control"
          value={borrowerName}
          onChange={(event) => setBorrowerName(event.target.value)}
          required
        />
      </div>

      <div className="mb-3">
        <label className="form-label" htmlFor="borrowerPhone">
          {t("loanForm.borrowerPhone")}
        </label>
        <input
          id="borrowerPhone"
          type="tel"
          className="form-control"
          value={borrowerPhone}
          onChange={(event) => setBorrowerPhone(event.target.value)}
          required
        />
      </div>

      <div className="mb-3">
        <label className="form-label" htmlFor="dueDate">
          {t("loanForm.dueDate")}
        </label>
        <input
          id="dueDate"
          type="date"
          className="form-control"
          value={dueDate}
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
        <label className="form-label">{t("loanForm.items")}</label>
        {items.map((item) => {
          const selected = equipment?.find((eq) => String(eq.id) === item.equipmentId);
          return (
            <div key={item.key} className="d-flex flex-column flex-md-row gap-2 mb-2 pb-2 border-bottom">
              <select
                className="form-select"
                value={item.equipmentId}
                onChange={(event) => updateItem(item.key, { equipmentId: event.target.value })}
                required
              >
                <option value="">{t("loanForm.selectEquipment")}</option>
                {(equipment ?? []).map((eq) => (
                  <option key={eq.id} value={eq.id} disabled={eq.loanable_quantity <= 0}>
                    {equipmentLabel(eq)} ({eq.loanable_quantity} {t("loanForm.available")})
                  </option>
                ))}
              </select>
              <input
                type="number"
                min="1"
                max={selected?.loanable_quantity}
                className="form-control"
                style={{ maxWidth: "8rem" }}
                value={item.quantity}
                onChange={(event) => updateItem(item.key, { quantity: event.target.value })}
                required
              />
              <button
                type="button"
                className="btn btn-outline-danger"
                onClick={() => removeItem(item.key)}
                disabled={items.length === 1}
                aria-label={t("loanForm.removeItem")}
              >
                &times;
              </button>
            </div>
          );
        })}
        <button type="button" className="btn btn-outline-secondary btn-sm" onClick={addItem}>
          {t("loanForm.addItem")}
        </button>
      </div>

      {createLoan.isError ? (
        <div className="alert alert-danger py-2" role="alert">
          {t("loanForm.error")}
        </div>
      ) : null}
      {createLoan.isSuccess ? (
        <div className="alert alert-success py-2" role="alert">
          {t("loanForm.success")}
        </div>
      ) : null}

      <button className="btn btn-primary w-100" type="submit" disabled={createLoan.isPending || isEquipmentLoading}>
        {t("loanForm.submit")}
      </button>
    </form>
  );
}

export default LoanNew;
