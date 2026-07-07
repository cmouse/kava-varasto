import { useTranslation } from "react-i18next";

import { useCurrentUser } from "../api/auth";
import { useLoanableEquipment } from "../api/loans";
import LoginForm from "../components/LoginForm";

function Storage() {
  const { t } = useTranslation();
  const { data: user, isLoading: isUserLoading } = useCurrentUser();
  const { data, isLoading, isError } = useLoanableEquipment({ enabled: user?.authenticated });

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
    return <p className="text-danger">{t("storage.error")}</p>;
  }

  return (
    <div>
      <h1 className="h4 mb-3">{t("storage.title")}</h1>
      <div className="table-responsive">
        <table className="table table-striped align-middle">
          <thead>
            <tr>
              <th>{t("storage.shortCode")}</th>
              <th>{t("storage.name")}</th>
              <th>{t("storage.category")}</th>
              <th className="text-end">{t("storage.quantity")}</th>
              <th className="text-end">{t("storage.broken")}</th>
              <th className="text-end">{t("storage.available")}</th>
              <th>{t("storage.status")}</th>
              <th>{t("storage.externalLoanable")}</th>
            </tr>
          </thead>
          <tbody>
            {data.map((item) => (
              <tr key={item.id}>
                <td>{item.short_code || "–"}</td>
                <td>{item.name}</td>
                <td>{item.category}</td>
                <td className="text-end">{item.quantity}</td>
                <td className="text-end">{item.broken_quantity}</td>
                <td className="text-end">{item.loanable_quantity}</td>
                <td>
                  {item.loanable_quantity > 0 ? (
                    <span className="badge text-bg-success">{t("storage.availableBadge")}</span>
                  ) : (
                    <span className="badge text-bg-secondary">{t("storage.unavailableBadge")}</span>
                  )}
                </td>
                <td>
                  {item.is_external_loanable ? (
                    <span className="badge text-bg-success">{t("storage.yes")}</span>
                  ) : (
                    <span className="badge text-bg-secondary">{t("storage.no")}</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default Storage;
