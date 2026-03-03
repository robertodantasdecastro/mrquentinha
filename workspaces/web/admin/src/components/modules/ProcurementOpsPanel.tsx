"use client";

import Image from "next/image";
import { type ChangeEvent, type FormEvent, useEffect, useMemo, useState } from "react";
import { StatusPill, type StatusTone } from "@mrquentinha/ui";
import { InlinePreloader } from "@/components/InlinePreloader";

import {
  applyOcrJobAdmin,
  ApiError,
  createOcrJobAdmin,
  createPurchaseAdmin,
  generatePurchaseRequestFromMenuAdmin,
  listIngredientsAdmin,
  listMenuDaysAdmin,
  listPurchaseRequestsAdmin,
  listPurchasesAdmin,
  uploadPurchaseItemLabelImageAdmin,
  uploadPurchaseReceiptImageAdmin,
  updatePurchaseRequestStatusAdmin,
} from "@/lib/api";
import { containResizeImage } from "@/lib/imageUpload";
import { formatProcurementStatusLabel } from "@/lib/labels";
import type {
  IngredientData,
  IngredientUnit,
  MenuDayData,
  ProcurementRequestStatus,
  PurchaseData,
  PurchaseRequestData,
  PurchaseRequestFromMenuResultData,
} from "@/types/api";

const REQUEST_STATUS_OPTIONS: ProcurementRequestStatus[] = [
  "OPEN",
  "APPROVED",
  "BOUGHT",
  "CANCELED",
];

const UNIT_OPTIONS: IngredientUnit[] = ["g", "kg", "ml", "l", "unidade"];
const OCR_CAPTURE_TARGET = {
  width: 1800,
  height: 1800,
  mimeType: "image/jpeg",
  quality: 0.86,
} as const;

type ItemImageType = "front" | "back" | "product" | "price";

type OcrDraftJobInfo = {
  jobId: number;
  kind: "LABEL_FRONT" | "LABEL_BACK" | "PRODUCT" | "PRICE_TAG";
  status: "PENDING" | "PROCESSED" | "APPLIED" | "FAILED";
};

type PurchaseItemDraft = {
  ingredientId: string;
  qty: string;
  unit: IngredientUnit;
  unitPrice: string;
  taxAmount: string;
  labelFrontImageFile: File | null;
  labelBackImageFile: File | null;
  productImageFile: File | null;
  priceTagImageFile: File | null;
  ocrJobs: Partial<Record<ItemImageType, OcrDraftJobInfo>>;
  ocrStatus: "idle" | "processing" | "processed" | "failed";
  ocrNotes: string[];
};

function resolveErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Falha inesperada ao carregar módulo de compras.";
}

function formatDate(valueRaw: string): string {
  const dateValue = new Date(valueRaw);
  if (Number.isNaN(dateValue.getTime())) {
    return valueRaw;
  }

  return dateValue.toLocaleDateString("pt-BR");
}

function formatDateTime(valueRaw: string): string {
  const dateValue = new Date(valueRaw);
  if (Number.isNaN(dateValue.getTime())) {
    return valueRaw;
  }

  return dateValue.toLocaleString("pt-BR");
}

function formatCurrency(value: string): string {
  const numericValue = Number(value);
  if (Number.isNaN(numericValue)) {
    return value;
  }

  return numericValue.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
}

function buildTodayDateIso(): string {
  const now = new Date();
  const offset = now.getTimezoneOffset() * 60_000;
  const local = new Date(now.getTime() - offset);
  return local.toISOString().slice(0, 10);
}

function countByStatus(
  items: PurchaseRequestData[],
  status: ProcurementRequestStatus,
): number {
  return items.filter((item) => item.status === status).length;
}

function resolveRequestStatusTone(status: ProcurementRequestStatus): StatusTone {
  if (status === "OPEN") {
    return "warning";
  }

  if (status === "APPROVED") {
    return "info";
  }

  if (status === "BOUGHT") {
    return "success";
  }

  return "danger";
}

function buildStatusDrafts(
  requests: PurchaseRequestData[],
): Record<number, ProcurementRequestStatus> {
  return requests.reduce<Record<number, ProcurementRequestStatus>>(
    (accumulator, requestItem) => {
      accumulator[requestItem.id] = requestItem.status;
      return accumulator;
    },
    {},
  );
}

function buildDefaultPurchaseItem(
  ingredients: IngredientData[],
): PurchaseItemDraft {
  const defaultUnit = ingredients[0]?.unit ?? "kg";

  return {
    ingredientId: "",
    qty: "",
    unit: defaultUnit,
    unitPrice: "",
    taxAmount: "",
    labelFrontImageFile: null,
    labelBackImageFile: null,
    productImageFile: null,
    priceTagImageFile: null,
    ocrJobs: {},
    ocrStatus: "idle",
    ocrNotes: [],
  };
}

function asRecord(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object") {
    return {};
  }
  return value as Record<string, unknown>;
}

function parseRecognizedIngredientId(parsed: Record<string, unknown>): number | null {
  const recognized = asRecord(parsed.recognized_ingredient);
  const ingredientId = Number(recognized.ingredient_id);
  if (!Number.isFinite(ingredientId) || ingredientId <= 0) {
    return null;
  }
  return ingredientId;
}

function parsePackageSize(parsed: Record<string, unknown>): { qty: string; unit: IngredientUnit } | null {
  const packageSize = asRecord(parsed.package_size);
  const rawQty = String(packageSize.value ?? "").replace(",", ".").trim();
  const rawUnit = String(packageSize.unit ?? "").trim().toLowerCase();
  if (!rawQty || !rawUnit) {
    return null;
  }
  if (!["g", "kg", "ml", "l", "unidade"].includes(rawUnit)) {
    return null;
  }
  return {
    qty: rawQty,
    unit: rawUnit as IngredientUnit,
  };
}

function parsePriceValue(parsed: Record<string, unknown>): string | null {
  const candidates = [parsed.unit_price, parsed.total_price];
  for (const candidate of candidates) {
    const normalized = String(candidate ?? "").replace(",", ".").trim();
    if (!normalized) {
      continue;
    }
    const value = Number(normalized);
    if (Number.isNaN(value) || value < 0) {
      continue;
    }
    return normalized;
  }
  return null;
}

export function ProcurementOpsPanel() {
  const [requests, setRequests] = useState<PurchaseRequestData[]>([]);
  const [purchases, setPurchases] = useState<PurchaseData[]>([]);
  const [menuDays, setMenuDays] = useState<MenuDayData[]>([]);
  const [ingredients, setIngredients] = useState<IngredientData[]>([]);
  const [statusDrafts, setStatusDrafts] = useState<
    Record<number, ProcurementRequestStatus>
  >({});
  const [selectedMenuDayId, setSelectedMenuDayId] = useState<string>("");
  const [fromMenuResult, setFromMenuResult] =
    useState<PurchaseRequestFromMenuResultData | null>(null);

  const [supplierName, setSupplierName] = useState("");
  const [invoiceNumber, setInvoiceNumber] = useState("");
  const [purchaseDate, setPurchaseDate] = useState(buildTodayDateIso());
  const [purchaseItems, setPurchaseItems] = useState<PurchaseItemDraft[]>([]);
  const [receiptImageFile, setReceiptImageFile] = useState<File | null>(null);
  const [applyOcrFromImages, setApplyOcrFromImages] = useState<boolean>(true);

  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [updatingRequestId, setUpdatingRequestId] = useState<number | null>(null);
  const [generating, setGenerating] = useState<boolean>(false);
  const [creatingPurchase, setCreatingPurchase] = useState<boolean>(false);
  const [processingReceiptOcr, setProcessingReceiptOcr] = useState<boolean>(false);
  const [processingItemOcrIndex, setProcessingItemOcrIndex] = useState<number | null>(null);
  const [message, setMessage] = useState<string>("");
  const [errorMessage, setErrorMessage] = useState<string>("");

  async function loadProcurement({ silent = false }: { silent?: boolean } = {}) {
    if (silent) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    try {
      const [requestsPayload, purchasesPayload, menuDaysPayload, ingredientsPayload] =
        await Promise.all([
          listPurchaseRequestsAdmin(),
          listPurchasesAdmin(),
          listMenuDaysAdmin(),
          listIngredientsAdmin(),
        ]);

      const menuCandidates = menuDaysPayload.filter(
        (menuDay) => menuDay.menu_items.length > 0,
      );
      const activeIngredients = ingredientsPayload
        .filter((ingredient) => ingredient.is_active)
        .sort((left, right) => left.name.localeCompare(right.name, "pt-BR"));

      setRequests(requestsPayload);
      setPurchases(purchasesPayload);
      setMenuDays(menuCandidates);
      setIngredients(activeIngredients);

      setStatusDrafts((previous) => {
        const next = buildStatusDrafts(requestsPayload);
        for (const [requestIdRaw, status] of Object.entries(previous)) {
          const requestId = Number(requestIdRaw);
          if (next[requestId]) {
            next[requestId] = status;
          }
        }
        return next;
      });

      if (menuCandidates.length > 0) {
        const hasSelected = menuCandidates.some(
          (menuDay) => String(menuDay.id) === selectedMenuDayId,
        );
        if (!hasSelected) {
          setSelectedMenuDayId(String(menuCandidates[0].id));
        }
      } else {
        setSelectedMenuDayId("");
      }

      if (purchaseItems.length === 0) {
        setPurchaseItems([buildDefaultPurchaseItem(activeIngredients)]);
      }

      setErrorMessage("");
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    void loadProcurement();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const openRequests = useMemo(() => countByStatus(requests, "OPEN"), [requests]);
  const approvedRequests = useMemo(
    () => countByStatus(requests, "APPROVED"),
    [requests],
  );
  const totalPurchasesValue = useMemo(() => {
    return purchases.reduce((accumulator, purchase) => {
      const amount = Number(purchase.total_amount);
      if (Number.isNaN(amount)) {
        return accumulator;
      }

      return accumulator + amount;
    }, 0);
  }, [purchases]);

  function addPurchaseItemDraft() {
    setPurchaseItems((previous) => [
      ...previous,
      buildDefaultPurchaseItem(ingredients),
    ]);
  }

  function removePurchaseItemDraft(index: number) {
    setPurchaseItems((previous) => previous.filter((_, rowIndex) => rowIndex !== index));
  }

  function updatePurchaseItemDraft(
    index: number,
    patch: Partial<PurchaseItemDraft>,
  ) {
    setPurchaseItems((previous) =>
      previous.map((item, rowIndex) => {
        if (rowIndex !== index) {
          return item;
        }

        return {
          ...item,
          ...patch,
        };
      }),
    );
  }

  async function handleReceiptImageChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.currentTarget.files?.[0] ?? null;
    setErrorMessage("");

    if (!file) {
      setReceiptImageFile(null);
      return;
    }

    try {
      const preparedFile = await containResizeImage(file, OCR_CAPTURE_TARGET);
      setReceiptImageFile(preparedFile);
      setMessage("Comprovante otimizado para OCR e armazenamento.");
    } catch (error) {
      setReceiptImageFile(null);
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      event.currentTarget.value = "";
    }
  }

  async function handleItemImageChange(
    index: number,
    type: ItemImageType,
    file: File | null,
  ) {
    if (!file) {
      const patch: Partial<PurchaseItemDraft> = {};
      if (type === "front") {
        patch.labelFrontImageFile = null;
      } else if (type === "back") {
        patch.labelBackImageFile = null;
      } else if (type === "product") {
        patch.productImageFile = null;
      } else {
        patch.priceTagImageFile = null;
      }
      updatePurchaseItemDraft(index, patch);
      return;
    }

    try {
      const preparedFile = await containResizeImage(file, OCR_CAPTURE_TARGET);
      const patch: Partial<PurchaseItemDraft> = {};
      if (type === "front") {
        patch.labelFrontImageFile = preparedFile;
      } else if (type === "back") {
        patch.labelBackImageFile = preparedFile;
      } else if (type === "product") {
        patch.productImageFile = preparedFile;
      } else {
        patch.priceTagImageFile = preparedFile;
      }
      updatePurchaseItemDraft(index, patch);
      setMessage("Imagem do item otimizada para OCR e armazenamento.");
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    }
  }

  async function runReceiptOcrPreview() {
    if (!receiptImageFile) {
      setErrorMessage("Selecione uma imagem de comprovante para processar OCR.");
      return;
    }

    setProcessingReceiptOcr(true);
    setMessage("");
    setErrorMessage("");
    try {
      const receiptJob = await createOcrJobAdmin("RECEIPT", receiptImageFile);
      if (receiptJob.status === "FAILED") {
        throw new Error(receiptJob.error_message || "OCR do comprovante falhou.");
      }
      const parsed = asRecord(receiptJob.parsed_json);
      const supplier = String(parsed.supplier_name ?? "").trim();
      const invoice = String(parsed.invoice_number ?? "").trim();
      const total = String(parsed.total_amount ?? "").replace(",", ".").trim();

      if (!supplierName.trim() && supplier) {
        setSupplierName(supplier);
      }
      if (!invoiceNumber.trim() && invoice) {
        setInvoiceNumber(invoice);
      }
      setMessage(
        "OCR do comprovante processado. Revise fornecedor/NF/total antes de salvar.",
      );
      if (total && Number.isFinite(Number(total)) && Number(total) > 0) {
        setMessage(
          "OCR do comprovante processado. Fornecedor/NF sugeridos; total identificado no OCR.",
        );
      }
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setProcessingReceiptOcr(false);
    }
  }

  async function runItemOcrPreview(index: number) {
    const current = purchaseItems[index];
    if (!current) {
      return;
    }

    const images = [
      {
        type: "front" as const,
        kind: "LABEL_FRONT" as const,
        file: current.labelFrontImageFile,
      },
      {
        type: "back" as const,
        kind: "LABEL_BACK" as const,
        file: current.labelBackImageFile,
      },
      {
        type: "product" as const,
        kind: "PRODUCT" as const,
        file: current.productImageFile,
      },
      {
        type: "price" as const,
        kind: "PRICE_TAG" as const,
        file: current.priceTagImageFile,
      },
    ].filter((entry) => Boolean(entry.file));

    if (images.length === 0) {
      setErrorMessage(
        "Anexe ao menos uma foto (frente, verso, produto ou preço) para OCR.",
      );
      return;
    }

    setProcessingItemOcrIndex(index);
    setErrorMessage("");
    setMessage("");
    updatePurchaseItemDraft(index, { ocrStatus: "processing", ocrNotes: [] });

    const notes: string[] = [];
    const ocrJobs: Partial<Record<ItemImageType, OcrDraftJobInfo>> = {
      ...current.ocrJobs,
    };
    let nextIngredientId = current.ingredientId;
    let nextQty = current.qty;
    let nextUnit = current.unit;
    let nextUnitPrice = current.unitPrice;

    try {
      for (const imageEntry of images) {
        const job = await createOcrJobAdmin(imageEntry.kind, imageEntry.file as File);
        ocrJobs[imageEntry.type] = {
          jobId: job.id,
          kind: imageEntry.kind,
          status: job.status,
        };

        if (job.status === "FAILED") {
          notes.push(`${imageEntry.kind}: OCR falhou.`);
          continue;
        }

        const parsed = asRecord(job.parsed_json);
        const recognizedIngredientId = parseRecognizedIngredientId(parsed);
        if (recognizedIngredientId && !nextIngredientId) {
          const matched = ingredients.find(
            (candidate) => candidate.id === recognizedIngredientId,
          );
          if (matched) {
            nextIngredientId = String(matched.id);
            nextUnit = matched.unit;
            notes.push(`Ingrediente reconhecido: ${matched.name}.`);
          }
        }

        const packageSize = parsePackageSize(parsed);
        if (packageSize && !nextQty.trim()) {
          nextQty = packageSize.qty;
          nextUnit = packageSize.unit;
          notes.push(
            `Quantidade sugerida pelo OCR: ${packageSize.qty} ${packageSize.unit}.`,
          );
        }

        const priceValue = parsePriceValue(parsed);
        if (priceValue && !nextUnitPrice.trim()) {
          nextUnitPrice = priceValue;
          notes.push(`Preco unitario sugerido pelo OCR: ${priceValue}.`);
        }
      }

      updatePurchaseItemDraft(index, {
        ingredientId: nextIngredientId,
        qty: nextQty,
        unit: nextUnit,
        unitPrice: nextUnitPrice,
        ocrJobs,
        ocrStatus: "processed",
        ocrNotes: notes,
      });
      setMessage(
        "OCR do item concluido. Revise os campos sugeridos; o preenchimento manual permanece disponivel.",
      );
    } catch (error) {
      updatePurchaseItemDraft(index, {
        ocrJobs,
        ocrStatus: "failed",
        ocrNotes: notes.length > 0 ? notes : ["Falha ao processar OCR deste item."],
      });
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setProcessingItemOcrIndex(null);
    }
  }

  async function handleUpdateRequestStatus(requestItem: PurchaseRequestData) {
    const nextStatus = statusDrafts[requestItem.id] ?? requestItem.status;
    if (nextStatus === requestItem.status) {
      return;
    }

    setUpdatingRequestId(requestItem.id);
    setMessage("");
    setErrorMessage("");

    try {
      await updatePurchaseRequestStatusAdmin(requestItem.id, nextStatus);
      setMessage(
        `Requisição #${requestItem.id} atualizada para ${formatProcurementStatusLabel(nextStatus)}.`,
      );
      await loadProcurement({ silent: true });
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setUpdatingRequestId(null);
    }
  }

  async function handleGenerateFromMenu(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setGenerating(true);
    setMessage("");
    setErrorMessage("");

    try {
      const parsedMenuDayId = Number.parseInt(selectedMenuDayId, 10);
      if (Number.isNaN(parsedMenuDayId) || parsedMenuDayId <= 0) {
        throw new Error("Selecione um cardápio válido para gerar a requisição.");
      }

      const result = await generatePurchaseRequestFromMenuAdmin(parsedMenuDayId);
      setFromMenuResult(result);
      setMessage(result.message);
      await loadProcurement({ silent: true });
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setGenerating(false);
    }
  }

  async function handleCreatePurchase(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setCreatingPurchase(true);
    setMessage("");
    setErrorMessage("");

    try {
      if (!supplierName.trim()) {
        throw new Error("Informe o fornecedor da compra.");
      }

      const payloadItems = purchaseItems
        .map((item, index) => ({
          index,
          ingredientId: Number.parseInt(item.ingredientId, 10),
          ingredientName:
            ingredients.find(
              (candidate) => candidate.id === Number.parseInt(item.ingredientId, 10),
            )?.name ?? "produto",
          qty: item.qty.replace(",", ".").trim(),
          unit: item.unit,
          unitPrice: item.unitPrice.replace(",", ".").trim(),
          taxAmount: item.taxAmount.replace(",", ".").trim(),
          labelFrontImageFile: item.labelFrontImageFile,
          labelBackImageFile: item.labelBackImageFile,
          productImageFile: item.productImageFile,
          priceTagImageFile: item.priceTagImageFile,
          ocrJobs: item.ocrJobs,
        }))
        .filter(
          (item) =>
            item.ingredientId > 0 && item.qty !== "" && item.unitPrice !== "",
        );

      if (payloadItems.length === 0) {
        throw new Error("Adicione ao menos um item válido na compra.");
      }

      const ingredientIds = payloadItems.map((item) => item.ingredientId);
      if (ingredientIds.length !== new Set(ingredientIds).size) {
        throw new Error("Ingrediente duplicado na compra.");
      }

      const warnings: string[] = [];

      let createdPurchase = await createPurchaseAdmin({
        supplier_name: supplierName.trim(),
        invoice_number: invoiceNumber.trim() || undefined,
        purchase_date: purchaseDate,
        items: payloadItems.map((item) => ({
          ingredient: item.ingredientId,
          qty: item.qty,
          unit: item.unit,
          unit_price: item.unitPrice,
          tax_amount: item.taxAmount || undefined,
        })),
      });

      if (receiptImageFile) {
        createdPurchase = await uploadPurchaseReceiptImageAdmin(
          createdPurchase.id,
          receiptImageFile,
        );
      }

      if (applyOcrFromImages && receiptImageFile) {
        try {
          const receiptJob = await createOcrJobAdmin("RECEIPT", receiptImageFile);
          if (receiptJob.status === "FAILED") {
            warnings.push("OCR do comprovante nao processou.");
          } else {
            await applyOcrJobAdmin(receiptJob.id, {
              target_type: "PURCHASE",
              target_id: createdPurchase.id,
              mode: "merge",
            });
          }
        } catch {
          warnings.push("Falha ao aplicar OCR do comprovante.");
        }
      }

      for (const item of payloadItems) {
        const purchaseItem = createdPurchase.purchase_items.find(
          (candidate) => candidate.ingredient.id === item.ingredientId,
        );
        if (!purchaseItem) {
          warnings.push(
            `Item ${item.ingredientName}: nao foi encontrado para salvar foto.`,
          );
          continue;
        }

        const imageByType: Array<{ type: ItemImageType; file: File | null }> = [
          { type: "front", file: item.labelFrontImageFile },
          { type: "back", file: item.labelBackImageFile },
          { type: "product", file: item.productImageFile },
          { type: "price", file: item.priceTagImageFile },
        ];

        for (const imageEntry of imageByType) {
          if (!imageEntry.file) {
            continue;
          }
          await uploadPurchaseItemLabelImageAdmin(
            createdPurchase.id,
            purchaseItem.id,
            imageEntry.file,
            imageEntry.type,
          );
        }

        if (!applyOcrFromImages) {
          continue;
        }

        const jobsQueue: Array<{ type: ItemImageType; job: OcrDraftJobInfo }> = [];
        const kindByType: Record<ItemImageType, OcrDraftJobInfo["kind"]> = {
          front: "LABEL_FRONT",
          back: "LABEL_BACK",
          product: "PRODUCT",
          price: "PRICE_TAG",
        };
        for (const imageEntry of imageByType) {
          if (!imageEntry.file) {
            continue;
          }

          const existingJob = item.ocrJobs[imageEntry.type];
          if (existingJob && existingJob.status !== "FAILED") {
            jobsQueue.push({ type: imageEntry.type, job: existingJob });
            continue;
          }

          try {
            const generatedJob = await createOcrJobAdmin(
              kindByType[imageEntry.type],
              imageEntry.file,
            );
            if (generatedJob.status === "FAILED") {
              warnings.push(
                `OCR ${generatedJob.kind} do item ${item.ingredientName} falhou.`,
              );
              continue;
            }
            jobsQueue.push({
              type: imageEntry.type,
              job: {
                jobId: generatedJob.id,
                kind: kindByType[imageEntry.type],
                status: generatedJob.status,
              },
            });
          } catch {
            warnings.push(`Falha ao processar OCR ${imageEntry.type} do item ${item.ingredientName}.`);
          }
        }

        for (const queuedJob of jobsQueue) {
          try {
            await applyOcrJobAdmin(queuedJob.job.jobId, {
              target_type: "PURCHASE_ITEM",
              target_id: purchaseItem.id,
              mode: "merge",
            });
            if (queuedJob.job.kind === "LABEL_FRONT" || queuedJob.job.kind === "LABEL_BACK") {
              await applyOcrJobAdmin(queuedJob.job.jobId, {
                target_type: "INGREDIENT",
                target_id: item.ingredientId,
                mode: "merge",
              });
            }
          } catch {
            warnings.push(
              `Falha ao aplicar OCR ${queuedJob.job.kind} no item ${item.ingredientName}.`,
            );
          }
        }
      }

      setSupplierName("");
      setInvoiceNumber("");
      setPurchaseDate(buildTodayDateIso());
      setPurchaseItems([buildDefaultPurchaseItem(ingredients)]);
      setReceiptImageFile(null);
      if (warnings.length > 0) {
        setMessage(
          `Compra registrada com sucesso e estoque atualizado. Alertas: ${warnings.join(" | ")}`,
        );
      } else {
        setMessage("Compra registrada com sucesso e estoque atualizado.");
      }
      await loadProcurement({ silent: true });
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setCreatingPurchase(false);
    }
  }

  return (
    <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-text">Compras</h3>
          <p className="text-sm text-muted">
            Gere requisições por cardápio e registre compras para alimentar estoque e produção.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void loadProcurement({ silent: true })}
          disabled={refreshing || loading}
          className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-70"
        >
          {refreshing ? "Atualizando..." : "Atualizar"}
        </button>
      </div>

      {loading && <InlinePreloader message="Carregando módulo de compras..." className="mt-4 justify-start bg-surface/70" />}

      {!loading && (
        <>
          <div className="mt-4 grid gap-3 md:grid-cols-4">
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Requisições</p>
              <p className="mt-1 text-2xl font-semibold text-text">{requests.length}</p>
            </article>

            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Abertas</p>
              <p className="mt-1 text-2xl font-semibold text-text">{openRequests}</p>
            </article>

            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Aprovadas</p>
              <p className="mt-1 text-2xl font-semibold text-text">{approvedRequests}</p>
            </article>

            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Valor comprado</p>
              <p className="mt-1 text-sm font-semibold text-text">
                {totalPurchasesValue.toLocaleString("pt-BR", {
                  style: "currency",
                  currency: "BRL",
                })}
              </p>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-2">
            <section className="rounded-xl border border-border bg-bg p-4">
              <h4 className="text-base font-semibold text-text">Gerar requisição por cardápio</h4>
              {menuDays.length === 0 && (
                <p className="mt-3 text-sm text-muted">
                  Nenhum cardápio com itens disponível para gerar requisição.
                </p>
              )}

              {menuDays.length > 0 && (
                <form
                  onSubmit={(event) => void handleGenerateFromMenu(event)}
                  className="mt-3 grid gap-2 sm:grid-cols-[1fr_auto]"
                >
                  <label className="grid gap-1 text-sm text-muted">
                    Cardápio do dia
                    <select
                      required
                      value={selectedMenuDayId}
                      onChange={(event) => setSelectedMenuDayId(event.currentTarget.value)}
                      className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                    >
                      {menuDays.map((menuDay) => (
                        <option key={menuDay.id} value={menuDay.id}>
                          {menuDay.title} ({formatDate(menuDay.menu_date)})
                        </option>
                      ))}
                    </select>
                  </label>

                  <div className="self-end">
                    <button
                      type="submit"
                      disabled={generating}
                      className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-70"
                    >
                      {generating ? "Gerando..." : "Gerar"}
                    </button>
                  </div>
                </form>
              )}

              {fromMenuResult && (
                <div className="mt-3 rounded-lg border border-border bg-surface p-3">
                  <p className="text-sm font-semibold text-text">
                    Resultado: {fromMenuResult.message}
                  </p>
                  <p className="text-xs text-muted">
                    PR: {fromMenuResult.purchase_request_id ?? "não criada"} | Itens: {fromMenuResult.items.length}
                  </p>
                  {fromMenuResult.items.length > 0 && (
                    <ul className="mt-2 space-y-1 text-xs text-muted">
                      {fromMenuResult.items.slice(0, 8).map((item) => (
                        <li key={item.ingredient_id}>
                          {item.ingredient_name}: {item.required_qty} {item.unit}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </section>

            <section className="rounded-xl border border-border bg-bg p-4">
              <h4 className="text-base font-semibold text-text">Registrar compra</h4>
              <p className="mt-1 text-xs text-muted">
                O fluxo OCR continua disponível no backend; este formulário acelera o ciclo operacional.
              </p>
              <form onSubmit={(event) => void handleCreatePurchase(event)} className="mt-3 space-y-3">
                <div className="grid gap-3 sm:grid-cols-2">
                  <label className="grid gap-1 text-sm text-muted">
                    Fornecedor
                    <input
                      required
                      value={supplierName}
                      onChange={(event) => setSupplierName(event.currentTarget.value)}
                      className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                      placeholder="Ex.: Distribuidora Central"
                    />
                  </label>
                  <label className="grid gap-1 text-sm text-muted">
                    Data da compra
                    <input
                      type="date"
                      required
                      value={purchaseDate}
                      onChange={(event) => setPurchaseDate(event.currentTarget.value)}
                      className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                    />
                  </label>
                </div>
                <label className="grid gap-1 text-sm text-muted">
                  Nota fiscal (opcional)
                  <input
                    value={invoiceNumber}
                    onChange={(event) => setInvoiceNumber(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                    placeholder="NF-000123"
                  />
                </label>

                <div className="rounded-lg border border-border bg-surface p-3">
                  <p className="text-sm font-semibold text-text">
                    Comprovante da compra (upload/camera)
                  </p>
                  <label className="mt-2 grid gap-1 text-sm text-muted">
                    Foto do comprovante
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleReceiptImageChange}
                      className="rounded-md border border-border bg-bg px-2 py-2 text-sm text-text file:mr-3 file:rounded-md file:border-0 file:bg-primary/10 file:px-3 file:py-1 file:text-xs file:font-semibold file:text-primary"
                    />
                  </label>
                  {receiptImageFile && (
                    <p className="mt-2 text-xs text-muted">
                      Arquivo selecionado: {receiptImageFile.name}
                    </p>
                  )}
                  <div className="mt-2 flex flex-wrap items-center gap-2">
                    <button
                      type="button"
                      onClick={() => void runReceiptOcrPreview()}
                      disabled={!receiptImageFile || processingReceiptOcr}
                      className="rounded-md border border-border bg-bg px-3 py-1 text-xs font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-70"
                    >
                      {processingReceiptOcr ? "Processando OCR..." : "Processar OCR do comprovante"}
                    </button>
                    <span className="text-[11px] text-muted">
                      Se nao reconhecer tudo, complete manualmente os campos acima.
                    </span>
                  </div>
                  <label className="mt-2 inline-flex items-center gap-2 text-xs text-muted">
                    <input
                      type="checkbox"
                      checked={applyOcrFromImages}
                      onChange={(event) => setApplyOcrFromImages(event.currentTarget.checked)}
                    />
                    Aplicar OCR automaticamente nas fotos enviadas.
                  </label>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-semibold text-text">Itens da compra</p>
                    <button
                      type="button"
                      onClick={addPurchaseItemDraft}
                      className="rounded-md border border-border bg-bg px-3 py-1 text-xs font-semibold text-text transition hover:border-primary hover:text-primary"
                    >
                      + Item
                    </button>
                  </div>
                  {purchaseItems.map((item, index) => (
                    <div
                      key={`${index}-${item.ingredientId}`}
                      className="rounded-lg border border-border bg-surface p-2"
                    >
                      <div className="grid gap-2 md:grid-cols-12">
                        <select
                          value={item.ingredientId}
                          onChange={(event) => {
                            const nextIngredientId = event.currentTarget.value;
                            const ingredient = ingredients.find(
                              (candidate) => String(candidate.id) === nextIngredientId,
                            );
                            updatePurchaseItemDraft(index, {
                              ingredientId: nextIngredientId,
                              unit: ingredient?.unit ?? item.unit,
                            });
                          }}
                          className="rounded-md border border-border bg-bg px-2 py-1.5 text-sm text-text md:col-span-4"
                        >
                          <option value="">Ingrediente</option>
                          {ingredients.map((ingredient) => (
                            <option key={ingredient.id} value={ingredient.id}>
                              {ingredient.name}
                            </option>
                          ))}
                        </select>
                        <input
                          value={item.qty}
                          onChange={(event) =>
                            updatePurchaseItemDraft(index, { qty: event.currentTarget.value })
                          }
                          className="rounded-md border border-border bg-bg px-2 py-1.5 text-sm text-text md:col-span-2"
                          placeholder="Qtd"
                        />
                        <select
                          value={item.unit}
                          onChange={(event) =>
                            updatePurchaseItemDraft(index, {
                              unit: event.currentTarget.value as IngredientUnit,
                            })
                          }
                          className="rounded-md border border-border bg-bg px-2 py-1.5 text-sm text-text md:col-span-2"
                        >
                          {UNIT_OPTIONS.map((unitOption) => (
                            <option key={unitOption} value={unitOption}>
                              {unitOption}
                            </option>
                          ))}
                        </select>
                        <input
                          value={item.unitPrice}
                          onChange={(event) =>
                            updatePurchaseItemDraft(index, { unitPrice: event.currentTarget.value })
                          }
                          className="rounded-md border border-border bg-bg px-2 py-1.5 text-sm text-text md:col-span-2"
                          placeholder="Preço"
                        />
                        <input
                          value={item.taxAmount}
                          onChange={(event) =>
                            updatePurchaseItemDraft(index, { taxAmount: event.currentTarget.value })
                          }
                          className="rounded-md border border-border bg-bg px-2 py-1.5 text-sm text-text md:col-span-1"
                          placeholder="Imp."
                        />
                        <button
                          type="button"
                          onClick={() => removePurchaseItemDraft(index)}
                          disabled={purchaseItems.length === 1}
                          className="rounded-md border border-border bg-bg px-2 py-1.5 text-xs font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-60 md:col-span-1"
                        >
                          X
                        </button>
                      </div>
                      <label className="mt-2 grid gap-1 text-xs text-muted">
                        OCR por imagem (camera/upload):
                        frente, verso, produto e etiqueta de preco
                      </label>
                      <div className="grid gap-2 sm:grid-cols-2">
                        <label className="grid gap-1 text-[11px] text-muted">
                          Rotulo frente
                          <input
                            type="file"
                            accept="image/*"
                            onChange={(event) =>
                              void handleItemImageChange(
                                index,
                                "front",
                                event.currentTarget.files?.[0] ?? null,
                              )
                            }
                            className="rounded-md border border-border bg-bg px-2 py-1.5 text-xs text-text file:mr-2 file:rounded-md file:border-0 file:bg-primary/10 file:px-2 file:py-1 file:text-[11px] file:font-semibold file:text-primary"
                          />
                          {item.labelFrontImageFile && (
                            <span>Selecionado: {item.labelFrontImageFile.name}</span>
                          )}
                        </label>
                        <label className="grid gap-1 text-[11px] text-muted">
                          Rotulo verso
                          <input
                            type="file"
                            accept="image/*"
                            onChange={(event) =>
                              void handleItemImageChange(
                                index,
                                "back",
                                event.currentTarget.files?.[0] ?? null,
                              )
                            }
                            className="rounded-md border border-border bg-bg px-2 py-1.5 text-xs text-text file:mr-2 file:rounded-md file:border-0 file:bg-primary/10 file:px-2 file:py-1 file:text-[11px] file:font-semibold file:text-primary"
                          />
                          {item.labelBackImageFile && (
                            <span>Selecionado: {item.labelBackImageFile.name}</span>
                          )}
                        </label>
                        <label className="grid gap-1 text-[11px] text-muted">
                          Produto completo
                          <input
                            type="file"
                            accept="image/*"
                            onChange={(event) =>
                              void handleItemImageChange(
                                index,
                                "product",
                                event.currentTarget.files?.[0] ?? null,
                              )
                            }
                            className="rounded-md border border-border bg-bg px-2 py-1.5 text-xs text-text file:mr-2 file:rounded-md file:border-0 file:bg-primary/10 file:px-2 file:py-1 file:text-[11px] file:font-semibold file:text-primary"
                          />
                          {item.productImageFile && (
                            <span>Selecionado: {item.productImageFile.name}</span>
                          )}
                        </label>
                        <label className="grid gap-1 text-[11px] text-muted">
                          Etiqueta de preco
                          <input
                            type="file"
                            accept="image/*"
                            onChange={(event) =>
                              void handleItemImageChange(
                                index,
                                "price",
                                event.currentTarget.files?.[0] ?? null,
                              )
                            }
                            className="rounded-md border border-border bg-bg px-2 py-1.5 text-xs text-text file:mr-2 file:rounded-md file:border-0 file:bg-primary/10 file:px-2 file:py-1 file:text-[11px] file:font-semibold file:text-primary"
                          />
                          {item.priceTagImageFile && (
                            <span>Selecionado: {item.priceTagImageFile.name}</span>
                          )}
                        </label>
                      </div>
                      <div className="mt-2 flex flex-wrap items-center gap-2">
                        <button
                          type="button"
                          onClick={() => void runItemOcrPreview(index)}
                          disabled={processingItemOcrIndex === index}
                          className="rounded-md border border-border bg-bg px-3 py-1 text-xs font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-70"
                        >
                          {processingItemOcrIndex === index
                            ? "Processando OCR..."
                            : "Processar OCR deste item"}
                        </button>
                        <span className="text-[11px] text-muted">
                          Status: {item.ocrStatus}
                        </span>
                      </div>
                      {item.ocrNotes.length > 0 && (
                        <div className="mt-2 rounded-md border border-border bg-bg px-2 py-2 text-[11px] text-muted">
                          {item.ocrNotes.join(" | ")}
                        </div>
                      )}
                      <label className="mt-2 grid gap-1 text-xs text-muted">
                        Foto do produto para OCR (compatibilidade)
                        <input
                          type="file"
                          accept="image/*"
                          onChange={(event) =>
                            void handleItemImageChange(
                              index,
                              "front",
                              event.currentTarget.files?.[0] ?? null,
                            )
                          }
                          className="rounded-md border border-border bg-bg px-2 py-1.5 text-xs text-text file:mr-3 file:rounded-md file:border-0 file:bg-primary/10 file:px-3 file:py-1 file:text-xs file:font-semibold file:text-primary"
                        />
                        {item.labelFrontImageFile && (
                          <span className="text-[11px] text-muted">
                            Foto selecionada: {item.labelFrontImageFile.name}
                          </span>
                        )}
                      </label>
                    </div>
                  ))}
                </div>

                <div className="flex justify-end">
                  <button
                    type="submit"
                    disabled={creatingPurchase || ingredients.length === 0}
                    className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-70"
                  >
                    {creatingPurchase ? "Registrando..." : "Registrar compra"}
                  </button>
                </div>
              </form>
            </section>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-2">
            <section className="rounded-xl border border-border bg-bg p-4">
              <h4 className="text-base font-semibold text-text">Compras recentes</h4>
              {purchases.length === 0 && (
                <p className="mt-3 text-sm text-muted">Nenhuma compra encontrada.</p>
              )}
              {purchases.length > 0 && (
                <div className="mt-3 space-y-2">
                  {purchases.slice(0, 10).map((purchase) => (
                    <article
                      key={purchase.id}
                      className="rounded-lg border border-border bg-surface px-3 py-2"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-sm font-semibold text-text">{purchase.supplier_name}</p>
                        {purchase.receipt_image_url && (
                          <Image
                            src={purchase.receipt_image_url}
                            alt={`Comprovante compra ${purchase.id}`}
                            width={28}
                            height={28}
                            className="h-7 w-7 rounded object-cover"
                            unoptimized
                          />
                        )}
                      </div>
                      <p className="text-xs text-muted">
                        Data: {formatDate(purchase.purchase_date)} | Itens: {purchase.purchase_items.length}
                      </p>
                      <p className="text-xs text-muted">
                        Total: <strong className="text-text">{formatCurrency(purchase.total_amount)}</strong>
                      </p>
                      {purchase.purchase_items.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-2">
                          {purchase.purchase_items.slice(0, 5).map((item) => {
                            const iconUrl =
                              item.label_front_image_url ||
                              item.label_back_image_url ||
                              item.product_image_url ||
                              item.price_tag_image_url ||
                              item.ingredient.image_url;
                            return (
                              <span
                                key={item.id}
                                className="inline-flex items-center gap-1 rounded-full border border-border bg-bg px-2 py-1 text-[11px] text-muted"
                              >
                                {iconUrl && (
                                  <Image
                                    src={iconUrl}
                                    alt={item.ingredient.name}
                                    width={16}
                                    height={16}
                                    className="h-4 w-4 rounded-full object-cover"
                                    unoptimized
                                  />
                                )}
                                {item.ingredient.name}
                              </span>
                            );
                          })}
                        </div>
                      )}
                    </article>
                  ))}
                </div>
              )}
            </section>

            <section className="rounded-xl border border-border bg-bg p-4">
              <h4 className="text-base font-semibold text-text">Requisições recentes</h4>
              {requests.length === 0 && (
                <p className="mt-3 text-sm text-muted">Nenhuma requisição encontrada.</p>
              )}
              {requests.length > 0 && (
                <div className="mt-3 space-y-2">
                  {requests.slice(0, 12).map((requestItem) => {
                    const selectedStatus = statusDrafts[requestItem.id] ?? requestItem.status;
                    const isDirty = selectedStatus !== requestItem.status;

                    return (
                      <article
                        key={requestItem.id}
                        className="rounded-lg border border-border bg-surface px-3 py-2"
                      >
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-semibold text-text">PR #{requestItem.id}</p>
                          <StatusPill tone={resolveRequestStatusTone(requestItem.status)}>
                            {formatProcurementStatusLabel(requestItem.status)}
                          </StatusPill>
                        </div>
                        <p className="text-xs text-muted">
                          Itens: {requestItem.request_items.length} | Data: {formatDateTime(requestItem.requested_at)}
                        </p>

                        <div className="mt-2 flex flex-wrap items-center gap-2">
                          <select
                            value={selectedStatus}
                            onChange={(event) => {
                              const nextStatus =
                                event.currentTarget.value as ProcurementRequestStatus;
                              setStatusDrafts((previous) => ({
                                ...previous,
                                [requestItem.id]: nextStatus,
                              }));
                            }}
                            className="rounded-md border border-border bg-bg px-2 py-1 text-xs text-text"
                          >
                            {REQUEST_STATUS_OPTIONS.map((option) => (
                              <option key={option} value={option}>
                                {formatProcurementStatusLabel(option)}
                              </option>
                            ))}
                          </select>

                          <button
                            type="button"
                            onClick={() => void handleUpdateRequestStatus(requestItem)}
                            disabled={!isDirty || updatingRequestId === requestItem.id}
                            className="rounded-md border border-border bg-bg px-3 py-1 text-xs font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-70"
                          >
                            {updatingRequestId === requestItem.id ? "Salvando..." : "Salvar status"}
                          </button>
                        </div>
                      </article>
                    );
                  })}
                </div>
              )}
            </section>
          </div>
        </>
      )}

      {message && (
        <div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
          {message}
        </div>
      )}

      {errorMessage && (
        <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {errorMessage}
        </div>
      )}
    </section>
  );
}
