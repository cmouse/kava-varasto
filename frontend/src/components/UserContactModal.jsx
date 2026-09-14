import { useEffect } from "react";
import { useTranslation } from "react-i18next";

function UserContactModal({ user, onClose }) {
  const { t } = useTranslation();

  useEffect(() => {
    if (!user) {
      return undefined;
    }
    const onKeyDown = (event) => {
      if (event.key === "Escape") {
        onClose();
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [user, onClose]);

  if (!user) {
    return null;
  }

  const fullName = `${user.first_name} ${user.last_name}`.trim();

  return (
    <>
      <div
        className="modal d-block"
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-labelledby="user-contact-title"
        onClick={onClose}
      >
        <div
          className="modal-dialog modal-dialog-centered modal-dialog-scrollable"
          onClick={(event) => event.stopPropagation()}
        >
          <div className="modal-content">
            <div className="modal-header">
              <h2 className="modal-title h5" id="user-contact-title">
                {fullName || user.username}
              </h2>
              <button type="button" className="btn-close" aria-label={t("userContact.close")} onClick={onClose} />
            </div>
            <div className="modal-body">
              <dl className="row mb-0">
                <dt className="col-sm-4">{t("userContact.username")}</dt>
                <dd className="col-sm-8">{user.username}</dd>
                <dt className="col-sm-4">{t("userContact.name")}</dt>
                <dd className="col-sm-8">{fullName || "–"}</dd>
                <dt className="col-sm-4">{t("userContact.email")}</dt>
                <dd className="col-sm-8">{user.email || "–"}</dd>
                <dt className="col-sm-4">{t("userContact.phone")}</dt>
                <dd className="col-sm-8">{user.phone || "–"}</dd>
              </dl>
            </div>
          </div>
        </div>
      </div>
      <div className="modal-backdrop show" />
    </>
  );
}

export default UserContactModal;
