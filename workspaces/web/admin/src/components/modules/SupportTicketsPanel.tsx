"use client";

import { useEffect, useState } from "react";
import { StatusPill } from "@mrquentinha/ui";

import { InlinePreloader } from "@/components/InlinePreloader";
import {
  ApiError,
  createSupportTicketMessageAdmin,
  fetchSupportTicketAdmin,
  listSupportTicketsAdmin,
  updateSupportTicketAdmin,
} from "@/lib/api";
import type {
  SupportTicketData,
  SupportTicketMessageData,
  SupportTicketPriority,
  SupportTicketStatus,
} from "@/types/api";

function resolveErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Falha inesperada ao carregar tickets.";
}

const STATUS_OPTIONS: Array<{ value: SupportTicketStatus; label: string }> = [
  { value: "OPEN", label: "Aberto" },
  { value: "IN_PROGRESS", label: "Em andamento" },
  { value: "WAITING_CUSTOMER", label: "Aguardando cliente" },
  { value: "RESOLVED", label: "Resolvido" },
  { value: "CLOSED", label: "Encerrado" },
];

const PRIORITY_OPTIONS: Array<{ value: SupportTicketPriority; label: string }> = [
  { value: "LOW", label: "Baixa" },
  { value: "NORMAL", label: "Normal" },
  { value: "HIGH", label: "Alta" },
  { value: "URGENT", label: "Urgente" },
];

function resolveStatusTone(status: SupportTicketStatus) {
  if (status === "OPEN" || status === "WAITING_CUSTOMER") {
    return "warning" as const;
  }
  if (status === "IN_PROGRESS") {
    return "info" as const;
  }
  if (status === "RESOLVED" || status === "CLOSED") {
    return "success" as const;
  }
  return "neutral" as const;
}

export function SupportTicketsPanel() {
  const [tickets, setTickets] = useState<SupportTicketData[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [selectedTicket, setSelectedTicket] = useState<SupportTicketData | null>(null);
  const [messages, setMessages] = useState<SupportTicketMessageData[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [messageDraft, setMessageDraft] = useState("");
  const [internalNote, setInternalNote] = useState("");
  const [statusDraft, setStatusDraft] = useState<SupportTicketStatus>("OPEN");
  const [priorityDraft, setPriorityDraft] = useState<SupportTicketPriority>("NORMAL");
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  async function loadTickets() {
    setLoading(true);
    try {
      const payload = await listSupportTicketsAdmin();
      setTickets(payload);
      if (payload.length > 0) {
        setSelectedId((current) => current ?? payload[0].id);
      } else {
        setSelectedId(null);
        setSelectedTicket(null);
        setMessages([]);
      }
      setErrorMessage("");
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  async function loadTicket(ticketId: number) {
    try {
      const payload = await fetchSupportTicketAdmin(ticketId);
      setSelectedTicket(payload);
      setMessages(payload.messages ?? []);
      setStatusDraft(payload.status);
      setPriorityDraft(payload.priority);
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    }
  }

  useEffect(() => {
    void loadTickets();
  }, []);

  useEffect(() => {
    if (selectedId) {
      void loadTicket(selectedId);
    }
  }, [selectedId]);

  async function handleUpdateTicket() {
    if (!selectedId) {
      return;
    }
    setBusy(true);
    setErrorMessage("");
    setSuccessMessage("");
    try {
      const payload = await updateSupportTicketAdmin(selectedId, {
        status: statusDraft,
        priority: priorityDraft,
        internal_note: internalNote || undefined,
      });
      setSelectedTicket(payload);
      setInternalNote("");
      setSuccessMessage("Ticket atualizado com sucesso.");
      await loadTickets();
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  async function handleSendMessage() {
    if (!selectedId || !messageDraft.trim()) {
      return;
    }
    setBusy(true);
    setErrorMessage("");
    setSuccessMessage("");
    try {
      const payload = await createSupportTicketMessageAdmin(selectedId, {
        message: messageDraft.trim(),
        is_internal: false,
      });
      setMessages((current) => [...current, payload]);
      setMessageDraft("");
      setSuccessMessage("Resposta enviada ao cliente.");
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return <InlinePreloader message="Carregando tickets de suporte..." className="justify-start bg-surface/70" />;
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[260px,1fr]">
      <aside className="rounded-2xl border border-border bg-surface/80 p-4 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Tickets recentes</p>
        <div className="mt-3 space-y-2">
          {tickets.map((ticket) => (
            <button
              key={ticket.id}
              type="button"
              onClick={() => setSelectedId(ticket.id)}
              className={[
                "w-full rounded-xl border px-3 py-2 text-left text-sm transition",
                ticket.id === selectedId ? "border-primary bg-primary/10" : "border-border bg-bg",
              ].join(" ")}
            >
              <p className="font-semibold text-text">#{ticket.id} {ticket.subject}</p>
              <div className="mt-1 flex items-center gap-2 text-xs text-muted">
                <StatusPill tone={resolveStatusTone(ticket.status)}>{ticket.status}</StatusPill>
                <span>{ticket.customer_username || "Cliente"}</span>
              </div>
            </button>
          ))}
          {tickets.length === 0 && (
            <p className="text-xs text-muted">Sem tickets abertos no momento.</p>
          )}
        </div>
      </aside>

      <section className="rounded-2xl border border-border bg-surface/80 p-5 shadow-sm">
        {selectedTicket ? (
          <>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h3 className="text-lg font-semibold text-text">
                  Ticket #{selectedTicket.id} - {selectedTicket.subject}
                </h3>
                <p className="mt-1 text-sm text-muted">
                  Cliente: {selectedTicket.customer_username} | {selectedTicket.customer_email}
                </p>
              </div>
              <StatusPill tone={resolveStatusTone(selectedTicket.status)}>
                {selectedTicket.status}
              </StatusPill>
            </div>

            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <label className="grid gap-1 text-sm text-muted">
                Status
                <select
                  value={statusDraft}
                  onChange={(event) => setStatusDraft(event.currentTarget.value as SupportTicketStatus)}
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                >
                  {STATUS_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="grid gap-1 text-sm text-muted">
                Prioridade
                <select
                  value={priorityDraft}
                  onChange={(event) => setPriorityDraft(event.currentTarget.value as SupportTicketPriority)}
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                >
                  {PRIORITY_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <label className="mt-4 grid gap-1 text-sm text-muted">
              Nota interna (opcional)
              <textarea
                value={internalNote}
                onChange={(event) => setInternalNote(event.currentTarget.value)}
                className="min-h-20 rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
              />
            </label>

            <div className="mt-3 flex flex-wrap items-center gap-2">
              <button
                type="button"
                disabled={busy}
                onClick={handleUpdateTicket}
                className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:opacity-70"
              >
                Salvar ticket
              </button>
              {successMessage && <span className="text-sm text-primary">{successMessage}</span>}
              {errorMessage && <span className="text-sm text-rose-600">{errorMessage}</span>}
            </div>

            <div className="mt-6">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">
                Conversa
              </p>
              <div className="mt-3 space-y-2">
                {messages.map((entry) => (
                  <div key={entry.id} className="rounded-xl border border-border bg-bg p-3">
                    <p className="text-xs text-muted">
                      {entry.author_type} • {new Date(entry.created_at).toLocaleString("pt-BR")}
                    </p>
                    <p className="mt-1 text-sm text-text">{entry.message}</p>
                  </div>
                ))}
                {messages.length === 0 && (
                  <p className="text-xs text-muted">Nenhuma mensagem registrada.</p>
                )}
              </div>
            </div>

            <label className="mt-4 grid gap-1 text-sm text-muted">
              Responder ao cliente
              <textarea
                value={messageDraft}
                onChange={(event) => setMessageDraft(event.currentTarget.value)}
                className="min-h-20 rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
              />
            </label>
            <button
              type="button"
              disabled={busy || !messageDraft.trim()}
              onClick={handleSendMessage}
              className="mt-2 rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary disabled:opacity-70"
            >
              Enviar resposta
            </button>
          </>
        ) : (
          <p className="text-sm text-muted">Selecione um ticket para ver detalhes.</p>
        )}
      </section>
    </div>
  );
}
