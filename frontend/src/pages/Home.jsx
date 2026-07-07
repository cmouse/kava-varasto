import { useCurrentUser } from "../api/auth";
import LoginForm from "../components/LoginForm";

function Home() {
  const { data, isLoading } = useCurrentUser();

  if (isLoading) {
    return null;
  }

  if (!data?.authenticated) {
    return <LoginForm />;
  }

  return (
    <div>
      <h1 className="h4">Tervetuloa, {data.user.username}</h1>
      <p className="text-muted">Varasto- ja lainauslistat tulevat tähän.</p>
    </div>
  );
}

export default Home;
