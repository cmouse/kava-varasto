import { useTranslation } from "react-i18next";

import { useCurrentUser } from "../api/auth";
import { useLoans } from "../api/loans";
import LoginForm from "../components/LoginForm";
import ReturnedLoansTable from "../components/ReturnedLoansTable";

function LoanArchive() {
  const { t } = useTranslation();
  const { data: user, isLoading: isUserLoading } = useCurrentUser();
  const {
    data: loans,
    isLoading,
    isError,
  } = useLoans({ enabled: user?.authenticated, archived: true });

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
    return <p className="text-danger">{t("loanArchive.error")}</p>;
  }

  return (
    <div>
      <h1 className="h4 mb-3">{t("loanArchive.title")}</h1>
      <ReturnedLoansTable loans={loans} emptyMessage={t("loanArchive.empty")} />
    </div>
  );
}

export default LoanArchive;
