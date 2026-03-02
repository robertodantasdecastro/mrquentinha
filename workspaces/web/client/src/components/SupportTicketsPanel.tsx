"use client";

import { useEffect, useState } from "react";

import { InlinePreloader } from "@/components/InlinePreloader";
import {
  ApiError,
  createMySupportTicket,
  createMySupportTicketMessage,
  fetchMySupportTicket,
  listMySupportTickets,
} from "@/lib/api";
import type { SupportTicketData } from "@/types/api";

function resolveErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Falha inesperada ao carregar suporte.";
}

export function SupportTicketsPanel() {
  const [tickets, setTickets] = useState<SupportTicketData[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [selectedTicket, setSelectedTicket] = useState<SupportTicketData | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [subject, setSubject] = useState("");
  const [messageDraft, setMessageDraft] = useState("");
  const [replyDraft, setReplyDraft] = useState("");
  const [message, setMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  async function loadTickets() {
    setLoading(true);
    try {
      const payload = await listMySupportTickets();
      setTickets(payload);
      if (payload.length > 0) {
        setSelectedId((current) => current ?? payload[0].id);
      } else {
        setSelectedId(null);
        setSelectedTicket(null);
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
      const payload = await fetchMySupportTicket(ticketId);
      setSelectedTicket(payload);
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

  async function handleCreateTicket() {
    if (!subject.trim() || !messageDraft.trim()) {
      setErrorMessage("Preencha assunto e descricao do chamado.");
      return;
    }
    setBusy(true);
    setErrorMessage("");
    setMessage("");
    try {
      const ticket = await createMySupportTicket({
        subject: subject.trim(),
        message: messageDraft.trim(),
      });
      setSubject("");
      setMessageDraft("");
      setSelectedId(ticket.id);
      setMessage("Chamado criado com sucesso.");
      await loadTickets();
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  async function handleReply() {
    if (!selectedId || !replyDraft.trim()) {
      return;
    }
    setBusy(true);
    setErrorMessage("");
    setMessage("");
    try {
      await createMySupportTicketMessage(selectedId, { message: replyDraft.trim() });
      setReplyDraft("");
      await loadTicket(selectedId);
      setMessage("Resposta enviada.");
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return <InlinePreloader message="Carregando suporte..." className="justify-start bg-surface/70" />;
  }

  return (
    <section className="rounded-2xl border border-border bg-bg p-4 shadow-sm">
      <h3 className="text-base font-semibold text-text">Suporte e chamados</h3>
      <p className="mt-1 text-sm text-muted">Abra chamados e acompanhe respostas da equipe.</p>

      <div className="mt-3 grid gap-3 md:grid-cols-[220px,1fr]">
        <div className="space-y-2">
          {tickets.map((ticket) => (
            <button
              key={ticket.id}
              type="button"
              onClick={() => setSelectedId(ticket.id)}
              className={[
                "w-full rounded-lg border px-3 py-2 text-left text-sm transition",
                ticket.id === selectedId ? "border-primary bg-primary/10" : "border-border bg-bg",
              ].join(" ")}
            >
              <p className="font-semibold text-text">#{ticket.id} {ticket.subject}</p>
              <p className="text-xs text-muted">{ticket.status}</p>
            </button>
          ))}
          {tickets.length === 0 && (
            <p className="text-xs text-muted">Nenhum chamado aberto.</p>
          )}
        </div>

        <div className="space-y-3">
          {selectedTicket ? (
            <>
              <div className="rounded-lg border border-border bg-surface p-3">
                <p className="text-sm font-semibold text-text">{selectedTicket.subject}</p>
                <p className="text-xs text-muted">Status: {selectedTicket.status}</p>
              </div>
              <div className="space-y-2">
                {(selectedTicket.messages ?? []).map((msg) => (
                  <div key={msg.id} className="rounded-lg border border-border bg-bg p-3 text-sm">
                    <p className="text-xs text-muted">
                      {msg.author_type} • {new Date(msg.created_at).toLocaleString("pt-BR")}
                    </p>
                    <p className="mt-1 text-text">{msg.message}</p>
                  </div>
                ))}
              </div>
              <label className="grid gap-1 text-sm text-muted">
                Responder
                <textarea
                  value={replyDraft}
                  onChange={(event) => setReplyDraft(event.currentTarget.value)}
                  className="min-h-20 rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                />
              </label>
              <button
                type="button"
                disabled={busy || !replyDraft.trim()}
                onClick={handleReply}
                className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary disabled:opacity-70"
              >
                Enviar resposta
              </button>
            </>
          ) : (
            <p className="text-sm text-muted">Selecione um chamado.</p>
          )}
        </div>
      </div>

      <div className="mt-4 rounded-lg border border-border bg-surface p-3">
        <p className="text-sm font-semibold text-text">Abrir novo chamado</p>
        <label className="mt-2 grid gap-1 text-sm text-muted">
          Assunto
          <input
            value={subject}
            onChange={(event) => setSubject(event.currentTarget.value)}
            className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
          />
        </label>
        <label className="mt-2 grid gap-1 text-sm text-muted">
          Descricao
          <textarea
            value={messageDraft}
            onChange={(event) => setMessageDraft(event.currentTarget.value)}
            className="min-h-20 rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
          />
        </label>
        <button
          type="button"
          disabled={busy}
          onClick={handleCreateTicket}
          className="mt-2 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:opacity-70"
        >
          Criar chamado
        </button>
      </div>

      {message && <p className="mt-3 text-sm text-primary">{message}</p>}
      {errorMessage && <p className="mt-3 text-sm text-rose-600">{errorMessage}</p>}
    </section>
  );
}
