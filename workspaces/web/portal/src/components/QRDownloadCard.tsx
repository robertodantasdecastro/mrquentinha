"use client";

import { QRCodeSVG } from "qrcode.react";

const PORTAL_APP_URL = "https://www.mrquentinha.com.br/app";

// TODO: atualizar para o link final do APK publicado.
const ANDROID_DOWNLOAD_URL = "https://www.mrquentinha.com.br/downloads/android.apk";

// TODO: atualizar para o link final da App Store/TestFlight.
const IOS_DOWNLOAD_URL = "https://apps.apple.com/br";

export function QRDownloadCard() {
  return (
    <section className="rounded-lg border border-border bg-surface/80 p-6 md:p-8">
      <div className="grid gap-6 md:grid-cols-[220px_1fr] md:items-center">
        <div className="mx-auto rounded-lg border border-border bg-white p-4 shadow-sm">
          <QRCodeSVG value={PORTAL_APP_URL} size={180} bgColor="#ffffff" fgColor="#1f1f1f" />
        </div>

        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-primary">
            Download do aplicativo
          </p>
          <h2 className="mt-1 text-2xl font-bold text-text">Escaneie o QR Code</h2>
          <p className="mt-3 text-sm leading-6 text-muted md:text-base">
            Aponte a camera para abrir a pagina oficial do aplicativo e escolher a
            loja desejada.
          </p>

          <div className="mt-5 flex flex-wrap gap-3">
            <a
              href={ANDROID_DOWNLOAD_URL}
              target="_blank"
              rel="noreferrer"
              className="rounded-md bg-primary px-5 py-3 text-sm font-semibold text-white transition hover:bg-primary-soft"
            >
              Baixar Android (APK)
            </a>
            <a
              href={IOS_DOWNLOAD_URL}
              target="_blank"
              rel="noreferrer"
              className="rounded-md border border-border bg-bg px-5 py-3 text-sm font-semibold text-text transition hover:border-primary hover:text-primary"
            >
              Baixar iOS
            </a>
          </div>

          <p className="mt-4 text-xs text-muted">
            Links editaveis em: <code>src/components/QRDownloadCard.tsx</code>
          </p>
        </div>
      </div>
    </section>
  );
}
