/**
 * Client-side Image Reader & Resizer Utility.
 * Supports variable dimensions (H x W) without forcing fixed 256x256 resizing.
 * Optionally scales down images that exceed maxDimension (default 2048px) for performance.
 */

export async function processImageFile(file, maxDimension = 2048) {
  return new Promise((resolve, reject) => {
    if (!file || !file.type.startsWith("image/")) {
      return reject(new Error("Invalid image file"));
    }

    const reader = new FileReader();
    reader.onerror = () => reject(new Error("Failed to read image file"));

    reader.onload = (e) => {
      const img = new Image();
      img.onerror = () => reject(new Error("Failed to load image element"));

      img.onload = () => {
        const originalWidth = img.width;
        const originalHeight = img.height;

        let targetWidth = originalWidth;
        let targetHeight = originalHeight;

        // If image is exceptionally large, scale down proportionally to maxDimension
        if (originalWidth > maxDimension || originalHeight > maxDimension) {
          if (originalWidth > originalHeight) {
            targetWidth = maxDimension;
            targetHeight = Math.round((originalHeight / originalWidth) * maxDimension);
          } else {
            targetHeight = maxDimension;
            targetWidth = Math.round((originalWidth / originalHeight) * maxDimension);
          }
        }

        const needsResize = targetWidth !== originalWidth || targetHeight !== originalHeight;

        if (!needsResize) {
          // Return original file directly
          const dataUrl = e.target.result;
          const b64 = dataUrl.split(",")[1];
          return resolve({
            processedFile: file,
            previewB64: b64,
            width: originalWidth,
            height: originalHeight,
            originalWidth,
            originalHeight,
            isResized: false,
          });
        }

        // Resize on canvas proportionally
        const canvas = document.createElement("canvas");
        canvas.width = targetWidth;
        canvas.height = targetHeight;
        const ctx = canvas.getContext("2d");

        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = "high";
        ctx.drawImage(img, 0, 0, targetWidth, targetHeight);

        const dataUrl = canvas.toDataURL("image/png");
        const b64 = dataUrl.split(",")[1];

        canvas.toBlob(
          (blob) => {
            if (!blob) {
              return reject(new Error("Canvas failed to create image blob"));
            }
            const resizedFile = new File([blob], file.name.replace(/\.[^/.]+$/, "") + "_scaled.png", {
              type: "image/png",
              lastModified: Date.now(),
            });

            resolve({
              processedFile: resizedFile,
              previewB64: b64,
              width: targetWidth,
              height: targetHeight,
              originalWidth,
              originalHeight,
              isResized: true,
            });
          },
          "image/png"
        );
      };

      img.src = e.target.result;
    };

    reader.readAsDataURL(file);
  });
}

// Backwards compatibility alias
export const resizeImage = processImageFile;

