import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { useCurrentUser } from "../api/auth";
import { useLoanableEquipment } from "../api/loans";
import EquipmentDetailModal from "../components/EquipmentDetailModal";
import EquipmentFilterBar from "../components/EquipmentFilterBar";
import LoginForm from "../components/LoginForm";
import { useEquipmentFilter } from "../hooks/useEquipmentFilter";
import { groupByCategory } from "../utils/groupByCategory";

function Storage() {
  const { t } = useTranslation();
  const [selectedId, setSelectedId] = useState(null);
  const { data: user, isLoading: isUserLoading } = useCurrentUser();
  const { data, isLoading, isError } = useLoanableEquipment({ enabled: user?.authenticated });
  const { search, setSearch, categoryId, setCategoryId, categories, filteredEquipment } = useEquipmentFilter(data);
  const selectedItem = data?.find((item) => item.id === selectedId) ?? null;

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
    return <p className="text-danger">{t("storage.error")}</p>;
  }

  return (
    <div>
      <h1 className="h4 mb-3">{t("storage.title")}</h1>
      <EquipmentFilterBar
        search={search}
        onSearchChange={setSearch}
        categories={categories}
        categoryId={categoryId}
        onCategoryChange={setCategoryId}
      />
      {filteredEquipment.length === 0 ? (
        <p className="text-muted">{t("storage.noResults")}</p>
      ) : (
        <div className="table-responsive">
          <table className="table table-striped align-middle">
            <thead>
              <tr>
                <th>{t("storage.shortCode")}</th>
                <th>{t("storage.name")}</th>
                <th className="text-end">{t("storage.quantity")}</th>
                <th className="text-end">{t("storage.broken")}</th>
                <th className="text-end">{t("storage.available")}</th>
                <th>{t("storage.status")}</th>
                <th>{t("storage.externalLoanable")}</th>
                <th>{t("storage.activeLoans")}</th>
              </tr>
            </thead>
            {groupByCategory(filteredEquipment).map((group) => (
              <tbody key={group.category} className="table-group-divider">
                <tr className="table-light">
                  <th colSpan={8}>{group.category}</th>
                </tr>
                {group.items.map((item) => (
                  <tr
                    key={item.id}
                    style={{ cursor: "pointer" }}
                    tabIndex={0}
                    onClick={(event) => {
                      // Let the active-loan links navigate instead of opening the modal.
                      if (event.target.closest("a")) {
                        return;
                      }
                      setSelectedId(item.id);
                    }}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        setSelectedId(item.id);
                      }
                    }}
                  >
                    <td>{item.short_code || "–"}</td>
                    <td>{item.name}</td>
                    <td className="text-end">{item.quantity}</td>
                    <td className="text-end">{item.broken_quantity}</td>
                    <td className="text-end">{item.loanable_quantity}</td>
                    <td>
                      {item.loanable_quantity > 0 ? (
                        <span className="badge text-bg-success">{t("storage.availableBadge")}</span>
                      ) : (
                        <span className="badge text-bg-secondary">{t("storage.unavailableBadge")}</span>
                      )}
                    </td>
                    <td>
                      {item.is_external_loanable ? (
                        <span className="badge text-bg-success">{t("storage.yes")}</span>
                      ) : (
                        <span className="badge text-bg-secondary">{t("storage.no")}</span>
                      )}
                    </td>
                    <td>
                      {item.active_loan_ids?.length
                        ? item.active_loan_ids.map((loanId, index) => (
                            <span key={loanId}>
                              {index > 0 ? ", " : null}
                              <Link to={`/loans/${loanId}`}>#{loanId}</Link>
                            </span>
                          ))
                        : "–"}
                    </td>
                  </tr>
                ))}
              </tbody>
            ))}
          </table>
        </div>
      )}
      <EquipmentDetailModal item={selectedItem} onClose={() => setSelectedId(null)} />
    </div>
  );
}

export default Storage;
