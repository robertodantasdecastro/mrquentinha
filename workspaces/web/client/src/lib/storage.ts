const ORDER_IDS_STORAGE_KEY = "mrq-client-order-ids";

export function rememberOrderId(orderId: number): void {
  if (typeof window === "undefined") {
    return;
  }

  const currentIds = getRememberedOrderIds();
  if (currentIds.includes(orderId)) {
    return;
  }

  const updatedIds = [orderId, ...currentIds].slice(0, 200);
  window.localStorage.setItem(ORDER_IDS_STORAGE_KEY, JSON.stringify(updatedIds));
}

export function getRememberedOrderIds(): number[] {
  if (typeof window === "undefined") {
    return [];
  }

  const raw = window.localStorage.getItem(ORDER_IDS_STORAGE_KEY);
  if (!raw) {
    return [];
  }

  try {
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) {
      return [];
    }

    return parsed
      .map((item) => Number(item))
      .filter((item) => Number.isInteger(item) && item > 0);
  } catch {
    return [];
  }
}
