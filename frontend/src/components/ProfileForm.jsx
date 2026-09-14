import { useState } from "react";
import { useTranslation } from "react-i18next";

import { useUpdateProfile } from "../api/auth";
import PHONE_PATTERN from "../utils/phonePattern";

// `user` is only ever passed once real data is available (see Profile.jsx's
// loading/auth gate), so useState's initial value is never stale.
function ProfileForm({ user }) {
  const { t } = useTranslation();
  const [firstName, setFirstName] = useState(user.first_name);
  const [lastName, setLastName] = useState(user.last_name);
  const [email, setEmail] = useState(user.email);
  const [phone, setPhone] = useState(user.phone);
  const updateProfile = useUpdateProfile();

  function handleSubmit(event) {
    event.preventDefault();
    updateProfile.mutate({ first_name: firstName, last_name: lastName, email, phone });
  }

  return (
    <form className="mx-auto" style={{ maxWidth: "24rem" }} onSubmit={handleSubmit}>
      <h1 className="h4 mb-3">{t("profile.title")}</h1>

      <div className="mb-3">
        <label className="form-label" htmlFor="firstName">
          {t("profile.firstName")}
        </label>
        <input
          id="firstName"
          type="text"
          className="form-control"
          value={firstName}
          onChange={(event) => setFirstName(event.target.value)}
          autoComplete="given-name"
        />
      </div>

      <div className="mb-3">
        <label className="form-label" htmlFor="lastName">
          {t("profile.lastName")}
        </label>
        <input
          id="lastName"
          type="text"
          className="form-control"
          value={lastName}
          onChange={(event) => setLastName(event.target.value)}
          autoComplete="family-name"
        />
      </div>

      <div className="mb-3">
        <label className="form-label" htmlFor="email">
          {t("profile.email")}
        </label>
        <input
          id="email"
          type="email"
          className="form-control"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          autoComplete="email"
        />
      </div>

      <div className="mb-3">
        <label className="form-label" htmlFor="phone">
          {t("profile.phone")}
        </label>
        <input
          id="phone"
          type="tel"
          className="form-control"
          value={phone}
          onChange={(event) => setPhone(event.target.value)}
          autoComplete="tel"
          pattern={PHONE_PATTERN}
          title={t("profile.phoneHint")}
          aria-describedby="phoneHint"
        />
        <div id="phoneHint" className="form-text">
          {t("profile.phoneHint")}
        </div>
      </div>

      {updateProfile.isError ? (
        <div className="alert alert-danger py-2" role="alert">
          {t("profile.error")}
        </div>
      ) : null}
      {updateProfile.isSuccess ? (
        <div className="alert alert-success py-2" role="alert">
          {t("profile.success")}
        </div>
      ) : null}

      <button className="btn btn-primary w-100" type="submit" disabled={updateProfile.isPending}>
        {t("profile.submit")}
      </button>
    </form>
  );
}

export default ProfileForm;
