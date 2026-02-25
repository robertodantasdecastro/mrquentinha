import type {
  OrderStatus,
  ProcurementRequestStatus,
  ProductionBatchStatus,
} from "@/types/api";

export function formatOrderStatusLabel(status: OrderStatus): string {
  switch (status) {
    case "CREATED":
      return "Criado";
    case "CONFIRMED":
      return "Confirmado";
    case "IN_PROGRESS":
      return "Em preparo";
    case "DELIVERED":
      return "Entregue";
    case "CANCELED":
      return "Cancelado";
    default:
      return status;
  }
}

export function formatProcurementStatusLabel(status: ProcurementRequestStatus): string {
  switch (status) {
    case "OPEN":
      return "Aberta";
    case "APPROVED":
      return "Aprovada";
    case "BOUGHT":
      return "Comprada";
    case "CANCELED":
      return "Cancelada";
    default:
      return status;
  }
}

export function formatProductionStatusLabel(status: ProductionBatchStatus): string {
  switch (status) {
    case "PLANNED":
      return "Planejado";
    case "IN_PROGRESS":
      return "Em progresso";
    case "DONE":
      return "Concluído";
    case "CANCELED":
      return "Cancelado";
    default:
      return status;
  }
}
