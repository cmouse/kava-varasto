import { useState } from "react";
import { useTranslation } from "react-i18next";

import { useChangePassword } from "../api/auth";

function ChangePasswordForm({ forced = false }) {
  const { t } = useTranslation();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [mismatch, setMismatch] = useState(false);
  const changePassword = useChangePassword();

  function handleSubmit(event) {
    event.preventDefault();
    if (newPassword !== confirmPassword) {
      setMismatch(true);
      return;
    }
    setMismatch(false);
    changePassword.mutate(
      { current_password: currentPassword, new_password: newPassword },
      {
        onSuccess: () => {
          setCurrentPassword("");
          setNewPassword("");
          setConfirmPassword("");
        },
      }
    );
  }

  return (
    <form className="mx-auto" style={{ maxWidth: "24rem" }} onSubmit={handleSubmit}>
      <h1 className="h4 mb-3">{t(forced ? "changePassword.forcedTitle" : "changePassword.title")}</h1>

      <div className="mb-3">
        <label className="form-label" htmlFor="currentPassword">
          {t("changePassword.currentPassword")}
        </label>
        <input
          id="currentPassword"
          type="password"
          className="form-control"
          value={currentPassword}
          onChange={(event) => setCurrentPassword(event.target.value)}
          autoComplete="current-password"
          required
        />
      </div>

      <div className="mb-3">
        <label className="form-label" htmlFor="newPassword">
          {t("changePassword.newPassword")}
        </label>
        <input
          id="newPassword"
          type="password"
          className="form-control"
          value={newPassword}
          onChange={(event) => setNewPassword(event.target.value)}
          autoComplete="new-password"
          required
        />
      </div>

      <div className="mb-3">
        <label className="form-label" htmlFor="confirmPassword">
          {t("changePassword.confirmNewPassword")}
        </label>
        <input
          id="confirmPassword"
          type="password"
          className="form-control"
          value={confirmPassword}
          onChange={(event) => setConfirmPassword(event.target.value)}
          autoComplete="new-password"
          required
        />
      </div>

      {mismatch ? (
        <div className="alert alert-danger py-2" role="alert">
          {t("changePassword.mismatchError")}
        </div>
      ) : null}
      {changePassword.isError ? (
        <div className="alert alert-danger py-2" role="alert">
          {t("changePassword.error")}
        </div>
      ) : null}
      {changePassword.isSuccess ? (
        <div className="alert alert-success py-2" role="alert">
          {t("changePassword.success")}
        </div>
      ) : null}

      <button className="btn btn-primary w-100" type="submit" disabled={changePassword.isPending}>
        {t("changePassword.submit")}
      </button>
    </form>
  );
}

export default ChangePasswordForm;
