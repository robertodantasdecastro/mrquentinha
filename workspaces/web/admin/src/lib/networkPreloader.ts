type NetworkListener = (pendingRequests: number) => void;

const listeners = new Set<NetworkListener>();
let pendingRequests = 0;

function notifyListeners(): void {
  for (const listener of listeners) {
    listener(pendingRequests);
  }
}

export function subscribeNetworkPreloader(listener: NetworkListener): () => void {
  listeners.add(listener);
  listener(pendingRequests);

  return () => {
    listeners.delete(listener);
  };
}

export function trackNetworkRequest<T>(runner: () => Promise<T>): Promise<T> {
  pendingRequests += 1;
  notifyListeners();

  return runner().finally(() => {
    pendingRequests = Math.max(0, pendingRequests - 1);
    notifyListeners();
  });
}
