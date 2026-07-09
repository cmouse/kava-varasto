import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router-dom";

import { useCurrentUser } from "../api/auth";
import { useLoan } from "../api/loans";
import LoginForm from "../components/LoginForm";

function LoanDetail() {
  const { t } = useTranslation();
  const { id } = useParams();
  const { data: user, isLoading: isUserLoading } = useCurrentUser();
  const {
    data: loan,
    isLoading,
    isError,
    error,
  } = useLoan(id, { enabled: user?.authenticated });

  if (isUserLoading) {
    return null;
  }

  if (!user?.authenticated) {
    return <LoginForm />;
  }

  if (isLoading) {
    return null;
  }

  if (isError) {
    const notFound = error?.response?.status === 404;
    return (
      <div>
        <p className="text-danger">{t(notFound ? "loanDetail.notFound" : "loanDetail.error")}</p>
        <Link to="/loans">{t("loanDetail.backToList")}</Link>
      </div>
    );
  }

  const itemsByCategory = {};
  for (const item of loan.items) {
    (itemsByCategory[item.category] ??= []).push(item);
  }
  const categories = Object.keys(itemsByCategory).sort((a, b) => a.localeCompare(b));

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h1 className="h4 mb-0">{t("loanDetail.title", { id: loan.id })}</h1>
        {!loan.is_returned ? (
          <Link to={`/loans/${loan.id}/return`} className="btn btn-primary btn-sm">
            {t("loanDetail.returnAction")}
          </Link>
        ) : null}
      </div>

      <dl className="row mb-4">
        <dt className="col-sm-3">{t("loanDetail.borrower")}</dt>
        <dd className="col-sm-9">{loan.borrower_name}</dd>

        <dt className="col-sm-3">{t("loanDetail.phone")}</dt>
        <dd className="col-sm-9">{loan.borrower_phone}</dd>

        <dt className="col-sm-3">{t("loanDetail.dueDate")}</dt>
        <dd className="col-sm-9">{loan.due_date}</dd>

        <dt className="col-sm-3">{t("loanDetail.responsible")}</dt>
        <dd className="col-sm-9">{loan.responsible}</dd>

        <dt className="col-sm-3">{t("loanDetail.details")}</dt>
        <dd className="col-sm-9">{loan.details || "—"}</dd>

        <dt className="col-sm-3">{t("loanDetail.createdAt")}</dt>
        <dd className="col-sm-9">{new Date(loan.created_at).toLocaleString()}</dd>

        <dt className="col-sm-3">{t("loanDetail.status")}</dt>
        <dd className="col-sm-9">
          {loan.is_returned ? (
            <span className="badge text-bg-success">{t("loanDetail.returned")}</span>
          ) : (
            <span className="badge text-bg-primary">{t("loanDetail.active")}</span>
          )}
        </dd>

        {loan.is_returned ? (
          <>
            <dt className="col-sm-3">{t("loanDetail.returnedBy")}</dt>
            <dd className="col-sm-9">{loan.returned_by}</dd>

            <dt className="col-sm-3">{t("loanDetail.returnedAt")}</dt>
            <dd className="col-sm-9">{new Date(loan.returned_at).toLocaleString()}</dd>
          </>
        ) : null}
      </dl>

      <h2 className="h6">{t("loanDetail.items")}</h2>
      <div className="table-responsive mb-4">
        <table className="table table-striped align-middle">
          <thead>
            <tr>
              <th>{t("loanDetail.equipment")}</th>
              <th>{t("loanDetail.quantity")}</th>
              <th>{t("loanDetail.returnedQuantity")}</th>
              <th>{t("loanDetail.brokenQuantity")}</th>
            </tr>
          </thead>
          {categories.map((category) => (
            <tbody key={category} className="table-group-divider">
              <tr className="table-light">
                <th colSpan={4}>{category}</th>
              </tr>
              {itemsByCategory[category].map((item) => (
                <tr key={item.id}>
                  <td>{item.equipment}</td>
                  <td>{item.quantity}</td>
                  <td>{item.quantity_returned}</td>
                  <td>{item.quantity_broken}</td>
                </tr>
              ))}
            </tbody>
          ))}
        </table>
      </div>

      <Link to="/loans">{t("loanDetail.backToList")}</Link>
    </div>
  );
}

export default LoanDetail;
