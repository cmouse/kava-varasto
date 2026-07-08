import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useParams } from "react-router-dom";

import { useCurrentUser } from "../api/auth";
import { useLoan, useReturnLoan } from "../api/loans";
import LoginForm from "../components/LoginForm";

function LoanReturn() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { id } = useParams();
  const { data: user, isLoading: isUserLoading } = useCurrentUser();
  const {
    data: loan,
    isLoading: isLoanLoading,
    isError,
    error,
  } = useLoan(id, { enabled: user?.authenticated });
  const returnLoan = useReturnLoan();
  const [quantities, setQuantities] = useState({});
  const [brokenQuantities, setBrokenQuantities] = useState({});

  if (isUserLoading) {
    return null;
  }

  if (!user?.authenticated) {
    return <LoginForm />;
  }

  if (isLoanLoading) {
    return null;
  }

  if (isError) {
    const notFound = error?.response?.status === 404;
    return (
      <div>
        <p className="text-danger">{t(notFound ? "loanReturn.notFound" : "loanReturn.loadError")}</p>
        <Link to="/loans">{t("loanReturn.backToList")}</Link>
      </div>
    );
  }

  if (loan.is_returned) {
    return (
      <div>
        <p className="text-muted">{t("loanReturn.alreadyReturned")}</p>
        <Link to="/loans">{t("loanReturn.backToList")}</Link>
      </div>
    );
  }

  function quantityFor(item) {
    return quantities[item.id] ?? item.quantity;
  }

  function setQuantityFor(item, value) {
    setQuantities((prev) => ({ ...prev, [item.id]: value }));
  }

  function brokenQuantityFor(item) {
    return brokenQuantities[item.id] ?? item.quantity_broken;
  }

  function setBrokenQuantityFor(item, value) {
    setBrokenQuantities((prev) => ({ ...prev, [item.id]: value }));
  }

  function handleSubmit(event) {
    event.preventDefault();
    const items = loan.items
      .filter((item) => item.quantity_returned < item.quantity)
      .map((item) => ({
        item: item.id,
        quantity_returned: Number(quantityFor(item)),
        quantity_broken: Number(brokenQuantityFor(item)),
      }));
    returnLoan.mutate({ loanId: loan.id, items }, { onSuccess: () => navigate("/loans") });
  }

  return (
    <form onSubmit={handleSubmit} style={{ maxWidth: "40rem" }}>
      <h1 className="h4 mb-3">{t("loanReturn.title")}</h1>
      <p className="mb-3">
        {loan.borrower_name} &middot; {loan.due_date}
      </p>

      <div className="mb-3">
        {loan.items.map((item) => {
          const fullyReturned = item.quantity_returned >= item.quantity;
          return (
            <div
              key={item.id}
              className="d-flex flex-column flex-md-row gap-2 align-items-md-center mb-2 pb-2 border-bottom"
            >
              <span className="flex-grow-1">{item.equipment}</span>
              {fullyReturned ? (
                <span className="badge text-bg-success align-self-start">{t("loanReturn.fullyReturned")}</span>
              ) : (
                <div className="d-flex align-items-center gap-2">
                  <label className="form-label mb-0 small" htmlFor={`return-item-${item.id}`}>
                    {t("loanReturn.returnedQuantity")}
                  </label>
                  <input
                    id={`return-item-${item.id}`}
                    type="number"
                    min={item.quantity_returned}
                    max={item.quantity}
                    className="form-control"
                    style={{ maxWidth: "8rem" }}
                    value={quantityFor(item)}
                    onChange={(event) => setQuantityFor(item, event.target.value)}
                    required
                  />
                  <span className="text-muted small">/ {item.quantity}</span>
                  <label className="form-label mb-0 small" htmlFor={`broken-item-${item.id}`}>
                    {t("loanReturn.brokenQuantity")}
                  </label>
                  <input
                    id={`broken-item-${item.id}`}
                    type="number"
                    min={item.quantity_broken}
                    max={quantityFor(item)}
                    className="form-control"
                    style={{ maxWidth: "8rem" }}
                    value={brokenQuantityFor(item)}
                    onChange={(event) => setBrokenQuantityFor(item, event.target.value)}
                    required
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {returnLoan.isError ? (
        <div className="alert alert-danger py-2" role="alert">
          {t("loanReturn.error")}
        </div>
      ) : null}
      {returnLoan.isSuccess ? (
        <div className="alert alert-success py-2" role="alert">
          {t("loanReturn.success")}
        </div>
      ) : null}

      <button className="btn btn-primary w-100 mb-3" type="submit" disabled={returnLoan.isPending}>
        {t("loanReturn.submit")}
      </button>
      <Link to="/loans">{t("loanReturn.backToList")}</Link>
    </form>
  );
}

export default LoanReturn;
