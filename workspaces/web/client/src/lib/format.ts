export function formatCurrency(value: string | number): string {
  const amount = Number(value);
  if (Number.isNaN(amount)) {
    return String(value);
  }

  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(amount);
}

export function getTodayIsoDate(): string {
  const now = new Date();
  const localDate = new Date(now.getTime() - now.getTimezoneOffset() * 60000);
  return localDate.toISOString().slice(0, 10);
}
