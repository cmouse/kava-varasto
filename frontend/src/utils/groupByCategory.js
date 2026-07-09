export function groupByCategory(list) {
  const groups = new Map();
  for (const item of list) {
    if (!groups.has(item.category)) {
      groups.set(item.category, []);
    }
    groups.get(item.category).push(item);
  }
  return Array.from(groups, ([category, items]) => ({ category, items }));
}
