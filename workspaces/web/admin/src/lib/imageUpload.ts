export type CropResizeTarget = {
  width: number;
  height: number;
  mimeType?: "image/jpeg" | "image/png" | "image/webp";
  quality?: number;
};

function loadImageElementFromFile(file: File): Promise<HTMLImageElement> {
  const objectUrl = URL.createObjectURL(file);

  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => {
      URL.revokeObjectURL(objectUrl);
      resolve(image);
    };
    image.onerror = () => {
      URL.revokeObjectURL(objectUrl);
      reject(new Error("Nao foi possivel carregar a imagem selecionada."));
    };
    image.src = objectUrl;
  });
}

function resolveOutputName(fileName: string, mimeType: string): string {
  const baseName = fileName.replace(/\.[^.]+$/, "");
  if (mimeType === "image/png") {
    return `${baseName}.png`;
  }
  if (mimeType === "image/webp") {
    return `${baseName}.webp`;
  }
  return `${baseName}.jpg`;
}

async function canvasToFile(
  canvas: HTMLCanvasElement,
  sourceFileName: string,
  target: CropResizeTarget,
): Promise<File> {
  const mimeType = target.mimeType ?? "image/jpeg";
  const quality = target.quality ?? 0.9;

  const blob = await new Promise<Blob>((resolve, reject) => {
    canvas.toBlob(
      (generatedBlob) => {
        if (!generatedBlob) {
          reject(new Error("Falha ao converter imagem para upload."));
          return;
        }
        resolve(generatedBlob);
      },
      mimeType,
      quality,
    );
  });

  const outputName = resolveOutputName(sourceFileName, mimeType);
  return new File([blob], outputName, {
    type: mimeType,
    lastModified: Date.now(),
  });
}

export async function centerCropResizeImage(
  file: File,
  target: CropResizeTarget,
): Promise<File> {
  const image = await loadImageElementFromFile(file);

  const sourceWidth = image.naturalWidth || image.width;
  const sourceHeight = image.naturalHeight || image.height;
  if (sourceWidth <= 0 || sourceHeight <= 0) {
    throw new Error("A imagem selecionada esta invalida.");
  }

  const targetRatio = target.width / target.height;
  const sourceRatio = sourceWidth / sourceHeight;

  let cropWidth = sourceWidth;
  let cropHeight = sourceHeight;

  if (sourceRatio > targetRatio) {
    cropWidth = Math.round(sourceHeight * targetRatio);
  } else {
    cropHeight = Math.round(sourceWidth / targetRatio);
  }

  const cropX = Math.max(0, Math.floor((sourceWidth - cropWidth) / 2));
  const cropY = Math.max(0, Math.floor((sourceHeight - cropHeight) / 2));

  const canvas = document.createElement("canvas");
  canvas.width = target.width;
  canvas.height = target.height;

  const context = canvas.getContext("2d", { alpha: true });
  if (!context) {
    throw new Error("Falha ao preparar a imagem para upload.");
  }

  context.imageSmoothingEnabled = true;
  context.imageSmoothingQuality = "high";
  context.drawImage(
    image,
    cropX,
    cropY,
    cropWidth,
    cropHeight,
    0,
    0,
    target.width,
    target.height,
  );

  return canvasToFile(canvas, file.name, target);
}

export async function containResizeImage(
  file: File,
  target: CropResizeTarget,
): Promise<File> {
  const image = await loadImageElementFromFile(file);
  const sourceWidth = image.naturalWidth || image.width;
  const sourceHeight = image.naturalHeight || image.height;
  if (sourceWidth <= 0 || sourceHeight <= 0) {
    throw new Error("A imagem selecionada esta invalida.");
  }

  const scale = Math.min(target.width / sourceWidth, target.height / sourceHeight, 1);
  const drawWidth = Math.max(1, Math.round(sourceWidth * scale));
  const drawHeight = Math.max(1, Math.round(sourceHeight * scale));

  const canvas = document.createElement("canvas");
  canvas.width = drawWidth;
  canvas.height = drawHeight;

  const context = canvas.getContext("2d", { alpha: true });
  if (!context) {
    throw new Error("Falha ao preparar a imagem para upload.");
  }

  context.imageSmoothingEnabled = true;
  context.imageSmoothingQuality = "high";
  context.drawImage(image, 0, 0, sourceWidth, sourceHeight, 0, 0, drawWidth, drawHeight);

  return canvasToFile(canvas, file.name, target);
}
