import { useState } from "react";
import { useTranslation } from "react-i18next";

import { useLogin } from "../api/auth";

function LoginForm() {
  const { t } = useTranslation();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const login = useLogin();

  function handleSubmit(event) {
    event.preventDefault();
    login.mutate({ username, password });
  }

  return (
    <form className="mx-auto" style={{ maxWidth: "24rem" }} onSubmit={handleSubmit}>
      <h1 className="h4 mb-3">{t("login.title")}</h1>
      <div className="mb-3">
        <label className="form-label" htmlFor="username">
          {t("login.username")}
        </label>
        <input
          id="username"
          className="form-control"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          autoComplete="username"
          required
        />
      </div>
      <div className="mb-3">
        <label className="form-label" htmlFor="password">
          {t("login.password")}
        </label>
        <input
          id="password"
          type="password"
          className="form-control"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          autoComplete="current-password"
          required
        />
      </div>
      {login.isError ? (
        <div className="alert alert-danger py-2" role="alert">
          {t("login.error")}
        </div>
      ) : null}
      <button className="btn btn-primary w-100" type="submit" disabled={login.isPending}>
        {t("login.submit")}
      </button>
    </form>
  );
}

export default LoginForm;
