import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

function ReturnedLoansTable({ loans, emptyMessage }) {
  const { t } = useTranslation();

  if (loans.length === 0) {
    return <p className="text-muted">{emptyMessage}</p>;
  }

  return (
    <div className="table-responsive">
      <table className="table table-striped align-middle">
        <thead>
          <tr>
            <th>#</th>
            <th>{t("loanList.borrower")}</th>
            <th>{t("loanList.phone")}</th>
            <th>{t("loanList.dueDate")}</th>
            <th>{t("loanList.items")}</th>
            <th>{t("loanList.returnedBy")}</th>
            <th>{t("loanList.returnedAt")}</th>
          </tr>
        </thead>
        <tbody>
          {loans.map((loan) => (
            <tr key={loan.id}>
              <td>
                <Link to={`/loans/${loan.id}`}>#{loan.id}</Link>
              </td>
              <td>{loan.borrower_name}</td>
              <td>{loan.borrower_phone}</td>
              <td>{loan.due_date}</td>
              <td>{loan.items.length}</td>
              <td>{loan.returned_by}</td>
              <td>{new Date(loan.returned_at).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default ReturnedLoansTable;
