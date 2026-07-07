import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router-dom";

import { useCurrentUser } from "../api/auth";
import { useLoans, useReturnLoan } from "../api/loans";
import LoginForm from "../components/LoginForm";

function LoanReturn() {
  const { t } = useTranslation();
  const { id } = useParams();
  const { data: user, isLoading: isUserLoading } = useCurrentUser();
  const { data: loans, isLoading: isLoansLoading } = useLoans({ enabled: user?.authenticated });
  const returnLoan = useReturnLoan();
  const [quantities, setQuantities] = useState({});

  if (isUserLoading) {
    return null;
  }

  if (!user?.authenticated) {
    return <LoginForm />;
  }

  if (isLoansLoading) {
    return null;
  }

  const loan = loans?.find((entry) => entry.id === Number(id));

  if (!loan) {
    return (
      <div>
        <p className="text-danger">{t("loanReturn.notFound")}</p>
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

  function handleSubmit(event) {
    event.preventDefault();
    const items = loan.items
      .filter((item) => item.quantity_returned < item.quantity)
      .map((item) => ({ item: item.id, quantity_returned: Number(quantityFor(item)) }));
    returnLoan.mutate({ loanId: loan.id, items });
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
