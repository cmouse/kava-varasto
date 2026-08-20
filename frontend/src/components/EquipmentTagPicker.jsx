import { useTranslation } from "react-i18next";

import { useEquipmentFilter } from "../hooks/useEquipmentFilter";
import { equipmentLabel } from "../utils/equipmentLabel";

const MAX_SUGGESTIONS = 8;

// Tagging is optional and usually one or two items, so this stays a search box
// with a short suggestion list rather than reusing EquipmentFilterBar, whose
// category and location controls are more machinery than a ticket needs.
function EquipmentTagPicker({ equipment, selected, onChange, disabled = false }) {
  const { t } = useTranslation();
  const { search, setSearch, filteredEquipment } = useEquipmentFilter(equipment);

  const selectedIds = new Set(selected.map((item) => item.id));
  const suggestions = search.trim()
    ? filteredEquipment.filter((item) => !selectedIds.has(item.id)).slice(0, MAX_SUGGESTIONS)
    : [];

  const add = (item) => {
    onChange([...selected, { id: item.id, name: item.name, short_code: item.short_code }]);
    setSearch("");
  };

  const remove = (id) => onChange(selected.filter((item) => item.id !== id));

  return (
    <div>
      <input
        type="search"
        className="form-control"
        value={search}
        onChange={(event) => setSearch(event.target.value)}
        onKeyDown={(event) => {
          // This box sits inside the report form, so Enter would otherwise
          // submit the ticket -- untagged -- instead of accepting the
          // suggestion the user is aiming at.
          if (event.key === "Enter") {
            event.preventDefault();
            if (suggestions.length > 0) {
              add(suggestions[0]);
            }
          }
        }}
        placeholder={t("repairs.equipmentSearch")}
        disabled={disabled}
      />
      {suggestions.length > 0 ? (
        <div className="list-group mt-1">
          {suggestions.map((item) => (
            <button
              key={item.id}
              type="button"
              className="list-group-item list-group-item-action py-1"
              onClick={() => add(item)}
            >
              {equipmentLabel(item)}
            </button>
          ))}
        </div>
      ) : null}
      {selected.length > 0 ? (
        <div className="d-flex flex-wrap gap-1 mt-2">
          {selected.map((item) => (
            <span key={item.id} className="badge text-bg-secondary d-inline-flex align-items-center gap-1">
              {equipmentLabel(item)}
              <button
                type="button"
                className="btn-close btn-close-white"
                style={{ fontSize: "0.5rem" }}
                aria-label={t("repairs.removeTag", { name: equipmentLabel(item) })}
                onClick={() => remove(item.id)}
                disabled={disabled}
              />
            </span>
          ))}
        </div>
      ) : null}
    </div>
  );
}

export default EquipmentTagPicker;
