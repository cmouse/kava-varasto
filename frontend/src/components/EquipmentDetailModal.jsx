import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

function EquipmentDetailModal({ item, onClose }) {
  const { t } = useTranslation();

  useEffect(() => {
    if (!item) {
      return undefined;
    }
    const onKeyDown = (event) => {
      if (event.key === "Escape") {
        onClose();
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [item, onClose]);

  if (!item) {
    return null;
  }

  return (
    <>
      <div
        className="modal d-block"
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-labelledby="equipment-detail-title"
        onClick={onClose}
      >
        <div className="modal-dialog modal-dialog-centered modal-dialog-scrollable" onClick={(event) => event.stopPropagation()}>
          <div className="modal-content">
            <div className="modal-header">
              <h2 className="modal-title h5" id="equipment-detail-title">
                {item.short_code ? `${item.short_code} ${item.name}` : item.name}
              </h2>
              <button type="button" className="btn-close" aria-label={t("equipmentDetail.close")} onClick={onClose} />
            </div>
            <div className="modal-body">
              {item.image ? (
                <img src={item.image} alt={item.name} className="img-fluid rounded mb-3 d-block mx-auto" />
              ) : (
                <div
                  className="bg-light text-muted rounded d-flex align-items-center justify-content-center mb-3"
                  style={{ height: "10rem" }}
                >
                  {t("equipmentDetail.noImage")}
                </div>
              )}
              <dl className="row mb-0">
                <dt className="col-sm-5">{t("storage.shortCode")}</dt>
                <dd className="col-sm-7">{item.short_code || "–"}</dd>
                <dt className="col-sm-5">{t("equipmentDetail.category")}</dt>
                <dd className="col-sm-7">{item.category}</dd>
                <dt className="col-sm-5">{t("storage.quantity")}</dt>
                <dd className="col-sm-7">{item.quantity}</dd>
                <dt className="col-sm-5">{t("storage.broken")}</dt>
                <dd className="col-sm-7">{item.broken_quantity}</dd>
                <dt className="col-sm-5">{t("storage.available")}</dt>
                <dd className="col-sm-7">{item.available_quantity}</dd>
                <dt className="col-sm-5">{t("equipmentDetail.loanable")}</dt>
                <dd className="col-sm-7">{item.loanable_quantity}</dd>
                <dt className="col-sm-5">{t("storage.externalLoanable")}</dt>
                <dd className="col-sm-7">
                  {item.is_external_loanable ? (
                    <span className="badge text-bg-success">{t("storage.yes")}</span>
                  ) : (
                    <span className="badge text-bg-secondary">{t("storage.no")}</span>
                  )}
                </dd>
                <dt className="col-sm-5">{t("storage.activeLoans")}</dt>
                <dd className="col-sm-7">
                  {item.active_loan_ids?.length
                    ? item.active_loan_ids.map((loanId, index) => (
                        <span key={loanId}>
                          {index > 0 ? ", " : null}
                          <Link to={`/loans/${loanId}`}>#{loanId}</Link>
                        </span>
                      ))
                    : "–"}
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>
      <div className="modal-backdrop show" />
    </>
  );
}

export default EquipmentDetailModal;
