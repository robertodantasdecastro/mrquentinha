type DateLike = string | Date;

function toLocalIsoDate(value: Date): string {
  const offset = value.getTimezoneOffset() * 60_000;
  return new Date(value.getTime() - offset).toISOString().slice(0, 10);
}

export function normalizeDateKey(value: DateLike): string {
  if (value instanceof Date) {
    return toLocalIsoDate(value);
  }

  if (!value) {
    return "";
  }

  return value.includes("T") ? value.slice(0, 10) : value;
}

export function buildRecentDateKeys(days: number, endDate: Date = new Date()): string[] {
  const keys: string[] = [];

  for (let index = days - 1; index >= 0; index -= 1) {
    const date = new Date(endDate);
    date.setDate(endDate.getDate() - index);
    keys.push(toLocalIsoDate(date));
  }

  return keys;
}

export function sumByDateKey<T>(
  items: T[],
  getDate: (item: T) => DateLike,
  getValue: (item: T) => number,
): Record<string, number> {
  return items.reduce<Record<string, number>>((accumulator, item) => {
    const key = normalizeDateKey(getDate(item));
    if (!key) {
      return accumulator;
    }

    accumulator[key] = (accumulator[key] ?? 0) + getValue(item);
    return accumulator;
  }, {});
}

export function buildSeriesFromTotals(
  dateKeys: string[],
  totals: Record<string, number>,
): number[] {
  return dateKeys.map((key) => totals[key] ?? 0);
}
