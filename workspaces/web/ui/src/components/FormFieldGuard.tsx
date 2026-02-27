"use client";

import { useEffect } from "react";

type FieldKind =
  | "cpf"
  | "cnpj"
  | "cep"
  | "email"
  | "password_current"
  | "password_new"
  | "date";

const DATA_KIND_ATTR = "data-mrq-field-kind";
const DATA_TOUCHED_ATTR = "data-mrq-field-touched";

function normalizeText(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
}

function digitsOnly(value: string): string {
  return value.replace(/\D/g, "");
}

function formatCpf(value: string): string {
  const digits = digitsOnly(value).slice(0, 11);
  if (digits.length <= 3) return digits;
  if (digits.length <= 6) return `${digits.slice(0, 3)}.${digits.slice(3)}`;
  if (digits.length <= 9) {
    return `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6)}`;
  }
  return `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6, 9)}-${digits.slice(9)}`;
}

function formatCnpj(value: string): string {
  const digits = digitsOnly(value).slice(0, 14);
  if (digits.length <= 2) return digits;
  if (digits.length <= 5) return `${digits.slice(0, 2)}.${digits.slice(2)}`;
  if (digits.length <= 8) {
    return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5)}`;
  }
  if (digits.length <= 12) {
    return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5, 8)}/${digits.slice(8)}`;
  }
  return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5, 8)}/${digits.slice(8, 12)}-${digits.slice(12)}`;
}

function formatCep(value: string): string {
  const digits = digitsOnly(value).slice(0, 8);
  if (digits.length <= 5) return digits;
  return `${digits.slice(0, 5)}-${digits.slice(5)}`;
}

function isValidCpf(value: string): boolean {
  const digits = digitsOnly(value);
  if (digits.length !== 11) return false;
  if (/^(\d)\1{10}$/.test(digits)) return false;

  let sum = 0;
  for (let index = 0; index < 9; index += 1) {
    sum += Number(digits[index]) * (10 - index);
  }
  let check = (sum * 10) % 11;
  if (check === 10) check = 0;
  if (check !== Number(digits[9])) return false;

  sum = 0;
  for (let index = 0; index < 10; index += 1) {
    sum += Number(digits[index]) * (11 - index);
  }
  check = (sum * 10) % 11;
  if (check === 10) check = 0;
  return check === Number(digits[10]);
}

function isValidCnpj(value: string): boolean {
  const digits = digitsOnly(value);
  if (digits.length !== 14) return false;
  if (/^(\d)\1{13}$/.test(digits)) return false;

  const calcDigit = (base: string, weights: number[]) => {
    const sum = base
      .split("")
      .reduce((acc, digit, index) => acc + Number(digit) * weights[index], 0);
    const remainder = sum % 11;
    return remainder < 2 ? 0 : 11 - remainder;
  };

  const baseTwelve = digits.slice(0, 12);
  const digitOne = calcDigit(baseTwelve, [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]);
  const digitTwo = calcDigit(
    `${baseTwelve}${digitOne}`,
    [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2],
  );

  return digits === `${baseTwelve}${digitOne}${digitTwo}`;
}

function isValidEmail(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());
}

function isStrongPassword(value: string): boolean {
  return /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/.test(value);
}

function buildFieldHint(input: HTMLInputElement): string {
  const labelText = input.closest("label")?.textContent ?? "";
  const descriptor = [
    input.name,
    input.id,
    input.type,
    input.autocomplete,
    input.getAttribute("aria-label") ?? "",
    input.getAttribute("placeholder") ?? "",
    labelText,
  ]
    .join(" ")
    .trim();

  return normalizeText(descriptor);
}

function resolveFieldKind(input: HTMLInputElement): FieldKind | null {
  if (input.type === "hidden") {
    return null;
  }

  const hint = buildFieldHint(input);

  if (hint.includes("cpf")) {
    return "cpf";
  }

  if (hint.includes("cnpj")) {
    return "cnpj";
  }

  if (
    hint.includes("cep") ||
    hint.includes("postal_code") ||
    hint.includes("zipcode")
  ) {
    return "cep";
  }

  if (input.type === "email" || hint.includes("email")) {
    return "email";
  }

  const isPassword = input.type === "password" || hint.includes("senha") || hint.includes("password");
  if (isPassword) {
    if (input.autocomplete === "new-password" || hint.includes("nova senha")) {
      return "password_new";
    }
    return "password_current";
  }

  if (input.type === "date") {
    return "date";
  }

  if (
    ["text", "search", "tel"].includes(input.type) &&
    (hint.includes(" data ") ||
      hint.includes(" date ") ||
      hint.includes("nascimento") ||
      hint.includes("vencimento"))
  ) {
    return "date";
  }

  return null;
}

function applyFieldConfig(input: HTMLInputElement, fieldKind: FieldKind): void {
  input.setAttribute(DATA_KIND_ATTR, fieldKind);

  if (fieldKind === "cpf") {
    input.inputMode = "numeric";
    input.maxLength = 14;
    if (!input.placeholder) {
      input.placeholder = "000.000.000-00";
    }
    return;
  }

  if (fieldKind === "cnpj") {
    input.inputMode = "numeric";
    input.maxLength = 18;
    if (!input.placeholder) {
      input.placeholder = "00.000.000/0000-00";
    }
    return;
  }

  if (fieldKind === "cep") {
    input.inputMode = "numeric";
    input.maxLength = 9;
    if (!input.placeholder) {
      input.placeholder = "00000-000";
    }
    return;
  }

  if (fieldKind === "email") {
    if (input.type === "text") {
      input.type = "email";
    }
    input.inputMode = "email";
    if (!input.autocomplete) {
      input.autocomplete = "email";
    }
    input.autocapitalize = "off";
    input.spellcheck = false;
    return;
  }

  if (fieldKind === "password_current" || fieldKind === "password_new") {
    if (input.type === "text") {
      input.type = "password";
    }
    if (!input.autocomplete) {
      input.autocomplete =
        fieldKind === "password_new" ? "new-password" : "current-password";
    }
    if (!input.minLength || input.minLength < 8) {
      input.minLength = 8;
    }
    return;
  }

  if (fieldKind === "date") {
    if (["text", "search", "tel"].includes(input.type)) {
      input.type = "date";
    }
    input.lang = "pt-BR";
    input.inputMode = "numeric";
  }
}

function formatInputValue(input: HTMLInputElement, fieldKind: FieldKind): void {
  if (fieldKind === "cpf") {
    const formatted = formatCpf(input.value);
    if (formatted !== input.value) {
      input.value = formatted;
    }
    return;
  }

  if (fieldKind === "cnpj") {
    const formatted = formatCnpj(input.value);
    if (formatted !== input.value) {
      input.value = formatted;
    }
    return;
  }

  if (fieldKind === "cep") {
    const formatted = formatCep(input.value);
    if (formatted !== input.value) {
      input.value = formatted;
    }
  }
}

function validateInputValue(input: HTMLInputElement, fieldKind: FieldKind): void {
  const rawValue = input.value ?? "";

  if (!rawValue.trim()) {
    input.setCustomValidity("");
    return;
  }

  if (fieldKind === "cpf") {
    input.setCustomValidity(
      isValidCpf(rawValue) ? "" : "CPF invalido. Informe um CPF valido.",
    );
    return;
  }

  if (fieldKind === "cnpj") {
    input.setCustomValidity(
      isValidCnpj(rawValue) ? "" : "CNPJ invalido. Informe um CNPJ valido.",
    );
    return;
  }

  if (fieldKind === "cep") {
    const digits = digitsOnly(rawValue);
    input.setCustomValidity(
      digits.length === 8 ? "" : "CEP invalido. Informe 8 digitos.",
    );
    return;
  }

  if (fieldKind === "email") {
    input.setCustomValidity(
      isValidEmail(rawValue) ? "" : "Email invalido. Revise o formato informado.",
    );
    return;
  }

  if (fieldKind === "password_new") {
    input.setCustomValidity(
      isStrongPassword(rawValue)
        ? ""
        : "Senha fraca. Use ao menos 8 caracteres com letra maiuscula, minuscula e numero.",
    );
    return;
  }

  if (fieldKind === "password_current") {
    input.setCustomValidity(
      rawValue.length >= 8 ? "" : "Senha invalida. Minimo de 8 caracteres.",
    );
    return;
  }

  if (fieldKind === "date") {
    const dateValue = new Date(`${rawValue}T00:00:00`);
    input.setCustomValidity(
      Number.isNaN(dateValue.getTime())
        ? "Data invalida. Use o calendario para selecionar uma data."
        : "",
    );
  }
}

function configureInput(input: HTMLInputElement): void {
  const resolvedKind = resolveFieldKind(input);
  if (!resolvedKind) {
    return;
  }

  applyFieldConfig(input, resolvedKind);
  formatInputValue(input, resolvedKind);
  validateInputValue(input, resolvedKind);
}

function configureInputSafely(input: HTMLInputElement): FieldKind | null {
  try {
    configureInput(input);
    return readFieldKind(input);
  } catch (error) {
    console.warn("[mrq] FormFieldGuard falhou ao configurar input", {
      name: input.name,
      id: input.id,
      type: input.type,
      error,
    });
    return null;
  }
}

function applyFormattingAndValidationSafely(
  input: HTMLInputElement,
  fieldKind: FieldKind,
): void {
  try {
    formatInputValue(input, fieldKind);
    validateInputValue(input, fieldKind);
  } catch (error) {
    input.setCustomValidity("");
    console.warn("[mrq] FormFieldGuard falhou ao validar input", {
      name: input.name,
      id: input.id,
      type: input.type,
      fieldKind,
      error,
    });
  }
}

function configureInputsInsideNode(node: ParentNode): void {
  const inputs = node.querySelectorAll("input");
  for (const input of inputs) {
    const fieldKind = configureInputSafely(input);
    if (!fieldKind) {
      continue;
    }
    applyFormattingAndValidationSafely(input, fieldKind);
  }
}

function readFieldKind(input: HTMLInputElement): FieldKind | null {
  const value = input.getAttribute(DATA_KIND_ATTR);
  if (!value) {
    return null;
  }

  const validKinds: FieldKind[] = [
    "cpf",
    "cnpj",
    "cep",
    "email",
    "password_current",
    "password_new",
    "date",
  ];
  return validKinds.includes(value as FieldKind) ? (value as FieldKind) : null;
}

export function FormFieldGuard() {
  useEffect(() => {
    if (typeof document === "undefined") {
      return;
    }

    configureInputsInsideNode(document);

    const onInput = (event: Event) => {
      const target = event.target;
      if (!(target instanceof HTMLInputElement)) {
        return;
      }

      const fieldKind = configureInputSafely(target);
      if (!fieldKind) {
        return;
      }

      applyFormattingAndValidationSafely(target, fieldKind);
    };

    const onBlur = (event: Event) => {
      const target = event.target;
      if (!(target instanceof HTMLInputElement)) {
        return;
      }

      const fieldKind = configureInputSafely(target);
      if (!fieldKind) {
        return;
      }

      target.setAttribute(DATA_TOUCHED_ATTR, "true");
      applyFormattingAndValidationSafely(target, fieldKind);
    };

    const onSubmit = (event: Event) => {
      const target = event.target;
      if (!(target instanceof HTMLFormElement)) {
        return;
      }

      const inputs = target.querySelectorAll("input");
      for (const input of inputs) {
        const fieldKind = configureInputSafely(input);
        if (!fieldKind) {
          continue;
        }

        input.setAttribute(DATA_TOUCHED_ATTR, "true");
        applyFormattingAndValidationSafely(input, fieldKind);
      }

      if (!target.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
        target.reportValidity();
      }
    };

    const observer = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        for (const addedNode of mutation.addedNodes) {
          if (!(addedNode instanceof HTMLElement)) {
            continue;
          }
          configureInputsInsideNode(addedNode);
        }
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });

    document.addEventListener("input", onInput, true);
    document.addEventListener("blur", onBlur, true);
    document.addEventListener("submit", onSubmit, true);

    return () => {
      observer.disconnect();
      document.removeEventListener("input", onInput, true);
      document.removeEventListener("blur", onBlur, true);
      document.removeEventListener("submit", onSubmit, true);
    };
  }, []);

  return null;
}
