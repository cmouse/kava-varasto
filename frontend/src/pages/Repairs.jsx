import { useState } from "react";
import { useTranslation } from "react-i18next";

import { useCurrentUser } from "../api/auth";
import { useLoanableEquipment } from "../api/loans";
import { useCreateRepair, useDeleteRepair, useRepairs, useUpdateRepair } from "../api/repairs";
import EquipmentTagPicker from "../components/EquipmentTagPicker";
import LoginForm from "../components/LoginForm";
import { equipmentLabel } from "../utils/equipmentLabel";

const STATUSES = ["open", "in_progress", "done", "wontfix"];

function ReportForm({ equipment, onDone }) {
  const { t } = useTranslation();
  const createRepair = useCreateRepair();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [tagged, setTagged] = useState([]);

  const submit = (event) => {
    event.preventDefault();
    createRepair.mutate(
      { title, description, equipment: tagged.map((item) => item.id) },
      {
        onSuccess: () => {
          setTitle("");
          setDescription("");
          setTagged([]);
          onDone();
        },
      },
    );
  };

  return (
    <form onSubmit={submit} className="card card-body mb-3">
      <div className="mb-2">
        <label className="form-label" htmlFor="repair-title">
          {t("repairs.titleField")}
        </label>
        <input
          id="repair-title"
          className="form-control"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          placeholder={t("repairs.titlePlaceholder")}
          required
        />
      </div>
      <div className="mb-2">
        <label className="form-label" htmlFor="repair-description">
          {t("repairs.description")}
        </label>
        <textarea
          id="repair-description"
          className="form-control"
          rows={2}
          value={description}
          onChange={(event) => setDescription(event.target.value)}
        />
      </div>
      <div className="mb-3">
        <label className="form-label" htmlFor="repair-equipment">
          {t("repairs.equipmentOptional")}
        </label>
        <EquipmentTagPicker equipment={equipment} selected={tagged} onChange={setTagged} />
      </div>
      {createRepair.isError ? <p className="text-danger">{t("repairs.saveError")}</p> : null}
      <div className="d-flex gap-2">
        <button className="btn btn-primary" type="submit" disabled={createRepair.isPending}>
          {t("repairs.submit")}
        </button>
        <button className="btn btn-outline-secondary" type="button" onClick={onDone}>
          {t("repairs.cancel")}
        </button>
      </div>
    </form>
  );
}

function RepairRow({ ticket }) {
  const { t } = useTranslation();
  const updateRepair = useUpdateRepair();
  const deleteRepair = useDeleteRepair();

  return (
    <tr className={ticket.is_open ? undefined : "opacity-50"}>
      <td>
        <div>{ticket.title}</div>
        {ticket.description ? <div className="small text-muted">{ticket.description}</div> : null}
      </td>
      <td>
        {ticket.equipment.length === 0 ? (
          <span className="text-muted">&mdash;</span>
        ) : (
          <div className="d-flex flex-wrap gap-1">
            {ticket.equipment.map((item) => (
              <span key={item.id} className="badge text-bg-light">
                {equipmentLabel(item)}
              </span>
            ))}
          </div>
        )}
      </td>
      <td>
        <select
          className="form-select form-select-sm"
          // Without a floor the column collapses on narrow screens and the
          // status reads as an empty box with a chevron.
          style={{ minWidth: "8rem" }}
          aria-label={t("repairs.status")}
          value={ticket.status}
          disabled={updateRepair.isPending}
          onChange={(event) => updateRepair.mutate({ id: ticket.id, status: event.target.value })}
        >
          {STATUSES.map((status) => (
            <option key={status} value={status}>
              {t(`repairs.statuses.${status}`)}
            </option>
          ))}
        </select>
        {updateRepair.isError ? (
          <div className="small text-danger">{t("repairs.rowError")}</div>
        ) : null}
      </td>
      <td>{ticket.reported_by}</td>
      <td>{ticket.reported_at.slice(0, 10)}</td>
      <td>{ticket.resolved_by ?? <span className="text-muted">&mdash;</span>}</td>
      <td>
        <button
          type="button"
          className="btn btn-sm btn-outline-danger"
          disabled={deleteRepair.isPending}
          onClick={() => {
            if (window.confirm(t("repairs.confirmDelete", { title: ticket.title }))) {
              deleteRepair.mutate(ticket.id);
            }
          }}
        >
          {t("repairs.delete")}
        </button>
        {deleteRepair.isError ? (
          <div className="small text-danger">{t("repairs.rowError")}</div>
        ) : null}
      </td>
    </tr>
  );
}

function Repairs() {
  const { t } = useTranslation();
  const { data: user, isLoading: isUserLoading } = useCurrentUser();
  const [showClosed, setShowClosed] = useState(false);
  const [isReporting, setIsReporting] = useState(false);
  const {
    data: tickets,
    isLoading,
    isError,
  } = useRepairs({ enabled: user?.authenticated, includeClosed: showClosed });
  const { data: equipment } = useLoanableEquipment({ enabled: user?.authenticated });

  if (isUserLoading) {
    return null;
  }

  if (!user?.authenticated) {
    return <LoginForm />;
  }

  if (isLoading) {
    return null;
  }

  if (isError) {
    return <p className="text-danger">{t("repairs.error")}</p>;
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h1 className="h4 mb-0">{t("repairs.title")}</h1>
        <button
          type="button"
          className="btn btn-primary btn-sm"
          onClick={() => setIsReporting((open) => !open)}
        >
          {t("repairs.report")}
        </button>
      </div>

      {isReporting ? <ReportForm equipment={equipment} onDone={() => setIsReporting(false)} /> : null}

      <div className="form-check mb-2">
        <input
          className="form-check-input"
          type="checkbox"
          id="repairs-show-closed"
          checked={showClosed}
          onChange={(event) => setShowClosed(event.target.checked)}
        />
        <label className="form-check-label" htmlFor="repairs-show-closed">
          {t("repairs.showClosed")}
        </label>
      </div>

      {tickets.length === 0 ? (
        <p className="text-muted">{t("repairs.empty")}</p>
      ) : (
        <div className="table-responsive">
          <table className="table table-striped align-middle">
            <thead>
              <tr>
                <th>{t("repairs.titleField")}</th>
                <th>{t("repairs.equipment")}</th>
                <th>{t("repairs.status")}</th>
                <th>{t("repairs.reportedBy")}</th>
                <th>{t("repairs.reportedAt")}</th>
                <th>{t("repairs.resolvedBy")}</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {tickets.map((ticket) => (
                <RepairRow key={ticket.id} ticket={ticket} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default Repairs;
