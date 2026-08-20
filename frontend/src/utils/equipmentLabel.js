// "X75 Trangia stove" for coded items, plain name for stock-counted ones.
export function equipmentLabel(item) {
  return item.short_code ? `${item.short_code} ${item.name}` : item.name;
}
