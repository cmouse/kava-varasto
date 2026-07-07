import { useMemo, useState } from "react";

export function useEquipmentFilter(equipment) {
  const [search, setSearch] = useState("");
  const [categoryId, setCategoryId] = useState(null);

  const categories = useMemo(() => {
    const seen = new Map();
    for (const item of equipment ?? []) {
      if (!seen.has(item.category_id)) {
        seen.set(item.category_id, item.category);
      }
    }
    return Array.from(seen, ([id, name]) => ({ id, name })).sort((a, b) => a.name.localeCompare(b.name));
  }, [equipment]);

  const filteredEquipment = useMemo(() => {
    const term = search.trim().toLowerCase();
    return (equipment ?? []).filter((item) => {
      if (categoryId !== null && item.category_id !== categoryId) {
        return false;
      }
      if (!term) {
        return true;
      }
      return item.name.toLowerCase().includes(term) || (item.short_code ?? "").toLowerCase().includes(term);
    });
  }, [equipment, search, categoryId]);

  return { search, setSearch, categoryId, setCategoryId, categories, filteredEquipment };
}
