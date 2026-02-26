import Link from "next/link";

type CallbackPageProps = {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

export default async function AppleOAuthCallbackPage({
  searchParams,
}: CallbackPageProps) {
  const params = await searchParams;
  const codeRaw = params.code;
  const errorRaw = params.error;
  const code = Array.isArray(codeRaw) ? codeRaw[0] : codeRaw;
  const error = Array.isArray(errorRaw) ? errorRaw[0] : errorRaw;

  return (
    <section className="mx-auto mt-8 max-w-2xl rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">
        OAuth Apple
      </p>
      <h1 className="mt-1 text-2xl font-bold text-text">Retorno do login social</h1>
      {error ? (
        <p className="mt-3 rounded-md border border-red-300/70 bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950/20 dark:text-red-300">
          Falha no retorno da Apple: {error}
        </p>
      ) : (
        <p className="mt-3 text-sm text-muted">
          Codigo de autorizacao recebido. Proxima etapa: trocar o <code>code</code> no backend
          para concluir sessao JWT.
        </p>
      )}
      {code && (
        <p className="mt-2 break-all rounded-md border border-border bg-bg px-3 py-2 font-mono text-xs text-muted">
          code: {code}
        </p>
      )}
      <div className="mt-4">
        <Link
          href="/conta"
          className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary"
        >
          Voltar para Conta
        </Link>
      </div>
    </section>
  );
}
