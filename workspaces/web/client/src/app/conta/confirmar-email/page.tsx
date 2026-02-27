"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { InlinePreloader } from "@/components/InlinePreloader";
import { ApiError, confirmEmailVerificationToken } from "@/lib/api";

type ConfirmState = "loading" | "success" | "error";

function resolveErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Falha ao confirmar e-mail.";
}

export default function ConfirmarEmailPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") ?? "";

  const [state, setState] = useState<ConfirmState>("loading");
  const [message, setMessage] = useState<string>("Validando token de confirmacao...");

  useEffect(() => {
    let mounted = true;

    async function confirmToken() {
      if (!token.trim()) {
        if (mounted) {
          setState("error");
          setMessage("Token de confirmacao nao informado.");
        }
        return;
      }

      try {
        const payload = await confirmEmailVerificationToken(token);
        if (!mounted) {
          return;
        }
        setState("success");
        setMessage(payload.detail || "E-mail confirmado com sucesso.");
        setTimeout(() => {
          router.replace("/conta?email_confirmed=1");
        }, 1200);
      } catch (error) {
        if (!mounted) {
          return;
        }
        setState("error");
        setMessage(resolveErrorMessage(error));
      }
    }

    void confirmToken();
    return () => {
      mounted = false;
    };
  }, [router, token]);

  return (
    <section className="space-y-4">
      <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-primary">
          Confirmacao de e-mail
        </p>
        <h1 className="mt-1 text-2xl font-bold text-text">Validacao da conta</h1>

        {state === "loading" && (
          <InlinePreloader
            message="Confirmando e-mail..."
            className="mt-4 justify-start bg-surface/80"
          />
        )}

        {state !== "loading" && (
          <p
            className={`mt-4 rounded-md border px-3 py-2 text-sm ${
              state === "success"
                ? "border-emerald-300/70 bg-emerald-50 text-emerald-700 dark:bg-emerald-950/20 dark:text-emerald-300"
                : "border-red-300/70 bg-red-50 text-red-700 dark:bg-red-950/20 dark:text-red-300"
            }`}
          >
            {message}
          </p>
        )}

        <div className="mt-4 flex flex-wrap gap-2 text-xs font-semibold uppercase tracking-[0.08em]">
          <Link
            href="/conta"
            className="rounded-full border border-border bg-bg px-3 py-1.5 text-muted transition hover:border-primary hover:text-primary"
          >
            Voltar para conta
          </Link>
          <Link
            href="/cardapio"
            className="rounded-full border border-border bg-bg px-3 py-1.5 text-muted transition hover:border-primary hover:text-primary"
          >
            Ir para cardapio
          </Link>
        </div>
      </section>
    </section>
  );
}
