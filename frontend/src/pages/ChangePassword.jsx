import { useCurrentUser } from "../api/auth";
import ChangePasswordForm from "../components/ChangePasswordForm";
import LoginForm from "../components/LoginForm";

function ChangePassword() {
  const { data: user, isLoading } = useCurrentUser();

  if (isLoading) {
    return null;
  }

  if (!user?.authenticated) {
    return <LoginForm />;
  }

  return <ChangePasswordForm />;
}

export default ChangePassword;
