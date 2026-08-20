import { useTranslation } from "react-i18next";

function EquipmentFilterBar({
  search,
  onSearchChange,
  categories,
  categoryId,
  onCategoryChange,
  locations,
  locationId,
  onLocationChange,
}) {
  const { t } = useTranslation();

  return (
    <div className="mb-3">
      <input
        type="search"
        className="form-control mb-2"
        placeholder={t("equipmentFilter.searchPlaceholder")}
        value={search}
        onChange={(event) => onSearchChange(event.target.value)}
      />
      <div className="d-flex flex-wrap gap-2 mb-2">
        <button
          type="button"
          className={`btn btn-sm ${categoryId === null ? "btn-primary" : "btn-outline-secondary"}`}
          onClick={() => onCategoryChange(null)}
        >
          {t("equipmentFilter.allCategories")}
        </button>
        {categories.map((category) => (
          <button
            key={category.id}
            type="button"
            className={`btn btn-sm ${categoryId === category.id ? "btn-primary" : "btn-outline-secondary"}`}
            onClick={() => onCategoryChange(category.id)}
          >
            {category.name}
          </button>
        ))}
      </div>
      <select
        className="form-select"
        value={locationId}
        onChange={(event) => onLocationChange(event.target.value)}
      >
        <option value="">{t("equipmentFilter.allLocations")}</option>
        {locations.map((location) => (
          <option key={location.id} value={location.id}>
            {location.name}
          </option>
        ))}
      </select>
    </div>
  );
}

export default EquipmentFilterBar;
