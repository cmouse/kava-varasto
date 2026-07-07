import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { useCurrentUser } from "../api/auth";
import { useLoans } from "../api/loans";
import LoginForm from "../components/LoginForm";

function ItemsList({ items }) {
  return (
    <ul className="list-unstyled mb-0 small">
      {items.map((item, index) => (
        <li key={index}>
          {item.equipment} &times;{item.quantity}
          {item.quantity_returned > 0 ? ` (${item.quantity_returned})` : ""}
        </li>
      ))}
    </ul>
  );
}

function LoanList() {
  const { t } = useTranslation();
  const { data: user, isLoading: isUserLoading } = useCurrentUser();
  const { data: loans, isLoading, isError } = useLoans({ enabled: user?.authenticated });

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
    return <p className="text-danger">{t("loanList.error")}</p>;
  }

  const activeLoans = loans.filter((loan) => !loan.is_returned);
  const historicalLoans = loans.filter((loan) => loan.is_returned);

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h1 className="h4 mb-0">{t("loanList.title")}</h1>
        <Link to="/loans/new" className="btn btn-primary btn-sm">
          {t("loanList.newLoan")}
        </Link>
      </div>

      <h2 className="h6">{t("loanList.active")}</h2>
      {activeLoans.length === 0 ? (
        <p className="text-muted">{t("loanList.noActive")}</p>
      ) : (
        <div className="table-responsive mb-4">
          <table className="table table-striped align-middle">
            <thead>
              <tr>
                <th>{t("loanList.borrower")}</th>
                <th>{t("loanList.phone")}</th>
                <th>{t("loanList.dueDate")}</th>
                <th>{t("loanList.items")}</th>
                <th>{t("loanList.details")}</th>
                <th>{t("loanList.responsible")}</th>
              </tr>
            </thead>
            <tbody>
              {activeLoans.map((loan) => (
                <tr key={loan.id}>
                  <td>{loan.borrower_name}</td>
                  <td>{loan.borrower_phone}</td>
                  <td>{loan.due_date}</td>
                  <td>
                    <ItemsList items={loan.items} />
                  </td>
                  <td>{loan.details}</td>
                  <td>{loan.responsible}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <h2 className="h6">{t("loanList.historical")}</h2>
      {historicalLoans.length === 0 ? (
        <p className="text-muted">{t("loanList.noHistorical")}</p>
      ) : (
        <div className="table-responsive">
          <table className="table table-striped align-middle">
            <thead>
              <tr>
                <th>{t("loanList.borrower")}</th>
                <th>{t("loanList.phone")}</th>
                <th>{t("loanList.dueDate")}</th>
                <th>{t("loanList.items")}</th>
                <th>{t("loanList.returnedBy")}</th>
                <th>{t("loanList.returnedAt")}</th>
              </tr>
            </thead>
            <tbody>
              {historicalLoans.map((loan) => (
                <tr key={loan.id}>
                  <td>{loan.borrower_name}</td>
                  <td>{loan.borrower_phone}</td>
                  <td>{loan.due_date}</td>
                  <td>
                    <ItemsList items={loan.items} />
                  </td>
                  <td>{loan.returned_by}</td>
                  <td>{new Date(loan.returned_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default LoanList;
