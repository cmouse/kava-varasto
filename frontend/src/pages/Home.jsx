import { useTranslation } from "react-i18next";

import { useCurrentUser } from "../api/auth";
import LoginForm from "../components/LoginForm";

function Home() {
  const { t } = useTranslation();
  const { data, isLoading } = useCurrentUser();

  if (isLoading) {
    return null;
  }

  if (!data?.authenticated) {
    return <LoginForm />;
  }

  return (
    <div>
      <h1 className="h4">{t("home.welcome", { username: data.user.username })}</h1>
      <p className="text-muted">{t("home.placeholder")}</p>
    </div>
  );
}

export default Home;
