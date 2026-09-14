import { useCurrentUser } from "../api/auth";
import ProfileForm from "../components/ProfileForm";
import LoginForm from "../components/LoginForm";

function Profile() {
  const { data: user, isLoading } = useCurrentUser();

  if (isLoading) {
    return null;
  }

  if (!user?.authenticated) {
    return <LoginForm />;
  }

  return <ProfileForm user={user.user} />;
}

export default Profile;
