"use client";

import { useEffect, useState } from "react";

import { InlinePreloader } from "@/components/InlinePreloader";
import { ApiError, listCustomerNotificationSubscribersAdmin } from "@/lib/api";

type SubscriberItem = {
  id: number;
  email: string;
  full_name: string;
  marketing_opt_in_at: string | null;
  notifications_opt_in_at: string | null;
};

function resolveErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Falha inesperada ao carregar inscritos.";
}

function formatDateTime(value: string | null): string {
  if (!value) {
    return "-";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleString("pt-BR");
}

export function NotificationSubscribersPanel() {
  const [subscribers, setSubscribers] = useState<SubscriberItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    let mounted = true;

    async function loadSubscribers() {
      try {
        const payload = await listCustomerNotificationSubscribersAdmin();
        if (mounted) {
          setSubscribers(payload);
          setErrorMessage("");
        }
      } catch (error) {
        if (mounted) {
          setErrorMessage(resolveErrorMessage(error));
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    void loadSubscribers();
    return () => {
      mounted = false;
    };
  }, []);

  if (loading) {
    return <InlinePreloader message="Carregando emails para notificacao..." className="justify-start bg-surface/70" />;
  }

  return (
    <section className="rounded-2xl border border-border bg-surface/80 p-5 shadow-sm">
      <h3 className="text-lg font-semibold text-text">Banco de emails para notificacao</h3>
      <p className="mt-1 text-sm text-muted">
        Lista de clientes com opt-in de marketing ou notificacoes operacionais.
      </p>

      {errorMessage && (
        <p className="mt-3 rounded-lg border border-rose-300 bg-rose-50 px-3 py-2 text-xs text-rose-700">
          {errorMessage}
        </p>
      )}

      <div className="mt-4 overflow-x-auto">
        <table className="w-full min-w-[560px] text-left text-sm">
          <thead className="text-xs uppercase tracking-[0.08em] text-muted">
            <tr>
              <th className="px-3 py-2">Cliente</th>
              <th className="px-3 py-2">Email</th>
              <th className="px-3 py-2">Marketing opt-in</th>
              <th className="px-3 py-2">Notificacoes opt-in</th>
            </tr>
          </thead>
          <tbody>
            {subscribers.map((item) => (
              <tr key={item.id} className="border-t border-border">
                <td className="px-3 py-2 text-text">{item.full_name || "-"}</td>
                <td className="px-3 py-2 text-muted">{item.email}</td>
                <td className="px-3 py-2 text-muted">{formatDateTime(item.marketing_opt_in_at)}</td>
                <td className="px-3 py-2 text-muted">{formatDateTime(item.notifications_opt_in_at)}</td>
              </tr>
            ))}
            {subscribers.length === 0 && (
              <tr>
                <td colSpan={4} className="px-3 py-6 text-center text-xs text-muted">
                  Nenhum cliente com opt-in registrado.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
