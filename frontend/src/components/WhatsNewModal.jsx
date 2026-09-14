import { useEffect } from "react";

// English only, deliberately -- see DESIGN.md's "What's new dialog" section.
// No i18n keys here, unlike its UserContactModal/EquipmentDetailModal
// siblings this is modelled on.
//
// Always renders the full `entries` list, newest first, exactly as the API
// returns it -- the unseen/seen comparison only decides whether Layout pops
// this open automatically, it never filters what's shown here.
function WhatsNewModal({ entries, onClose }) {
  useEffect(() => {
    if (!entries) {
      return undefined;
    }
    const onKeyDown = (event) => {
      if (event.key === "Escape") {
        onClose();
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [entries, onClose]);

  if (!entries) {
    return null;
  }

  return (
    <>
      <div
        className="modal d-block"
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-labelledby="whats-new-title"
        onClick={onClose}
      >
        <div
          className="modal-dialog modal-dialog-centered modal-dialog-scrollable"
          onClick={(event) => event.stopPropagation()}
        >
          <div className="modal-content">
            <div className="modal-header">
              <h2 className="modal-title h5" id="whats-new-title">
                What&apos;s new
              </h2>
              <button type="button" className="btn-close" aria-label="Close" onClick={onClose} />
            </div>
            <div className="modal-body">
              {entries.map((entry) => (
                <div key={entry.version} className="mb-3">
                  <h3 className="h6">{entry.version}</h3>
                  <ul className="mb-0">
                    {entry.changes.map((change) => (
                      <li key={change}>{change}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
            <div className="modal-footer">
              <button type="button" className="btn btn-primary" onClick={onClose}>
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
      <div className="modal-backdrop show" />
    </>
  );
}

export default WhatsNewModal;
