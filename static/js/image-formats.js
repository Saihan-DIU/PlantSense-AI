// Turns any supported photo into something every browser (and the model) can read.
//
// JPEG, PNG, WebP, GIF, BMP and AVIF are decoded by the browser itself.
// HEIC/HEIF (iPhone photos) and TIFF are converted to PNG in the browser with
// small libraries that are only downloaded when such a file is chosen.

const CDN = 'https://cdn.jsdelivr.net/npm/';
const LIBS = {
  heic2any: `${CDN}heic2any@0.0.4/dist/heic2any.min.js`,
  pako: `${CDN}pako@1.0.11/dist/pako_inflate.min.js`,
  utif: `${CDN}utif@3.1.0/UTIF.js`,
};

export const EXTENSIONS = ['jpg', 'jpeg', 'jfif', 'png', 'webp', 'gif', 'bmp', 'avif', 'heic', 'heif', 'tif', 'tiff'];
export const ACCEPT = 'image/*,.heic,.heif,.tif,.tiff,.avif';

const extOf = (name) => (name.split('.').pop() || '').toLowerCase();

export function kindOf(file) {
  const ext = extOf(file.name);
  const type = (file.type || '').toLowerCase();
  if (type === 'image/heic' || type === 'image/heif' || ext === 'heic' || ext === 'heif') return 'heic';
  if (type === 'image/tiff' || ext === 'tif' || ext === 'tiff') return 'tiff';
  if (type.startsWith('image/') || EXTENSIONS.includes(ext)) return 'native';
  return null;
}

// Errors carry a message key from i18n.py (shown by app.js in the page language)
function fail(key) {
  const err = new Error(key);
  err.key = key;
  return err;
}

const scripts = {};
function loadScript(url) {
  if (!scripts[url]) {
    scripts[url] = new Promise((resolve, reject) => {
      const s = document.createElement('script');
      s.src = url;
      s.async = true;
      s.crossOrigin = 'anonymous';
      s.onload = resolve;
      s.onerror = () => { delete scripts[url]; reject(new Error(`Could not load ${url}`)); };
      document.head.appendChild(s);
    });
  }
  return scripts[url];
}

const pngName = (name) => name.replace(/\.[^.]+$/, '') + '.png';

async function heicToPng(file) {
  await loadScript(LIBS.heic2any);
  const out = await self.heic2any({ blob: file, toType: 'image/png' });
  const blob = Array.isArray(out) ? out[0] : out; // multi-image HEIC: use the first
  return new File([blob], pngName(file.name), { type: 'image/png' });
}

async function tiffToPng(file) {
  await loadScript(LIBS.pako);
  await loadScript(LIBS.utif);
  const buf = await file.arrayBuffer();
  const ifds = self.UTIF.decode(buf);
  const page = ifds.find((ifd) => ifd.width && ifd.height) || ifds[0];
  self.UTIF.decodeImage(buf, page, ifds);
  const rgba = self.UTIF.toRGBA8(page);
  const canvas = document.createElement('canvas');
  canvas.width = page.width;
  canvas.height = page.height;
  canvas.getContext('2d').putImageData(new ImageData(new Uint8ClampedArray(rgba.buffer, 0, page.width * page.height * 4), page.width, page.height), 0, 0);
  const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/png'));
  return new File([blob], pngName(file.name), { type: 'image/png' });
}

// Formats the Flask server (Pillow) can open; others are converted before upload.
const SERVER_EXTENSIONS = ['jpg', 'jpeg', 'jfif', 'png', 'webp', 'gif', 'bmp', 'tif', 'tiff'];

async function canvasToPng(file) {
  const bitmap = await createImageBitmap(file);
  const canvas = document.createElement('canvas');
  canvas.width = bitmap.width;
  canvas.height = bitmap.height;
  canvas.getContext('2d').drawImage(bitmap, 0, 0);
  bitmap.close?.();
  const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/png'));
  return new File([blob], pngName(file.name), { type: 'image/png' });
}

// Returns a File the browser can decode (the original, or a PNG conversion).
// With forServer, also converts formats the Flask server can't open (e.g. AVIF).
// Throws an Error with a user-facing message if the image can't be read.
export async function normalizeImage(file, { forServer = false } = {}) {
  const kind = kindOf(file);
  if (!kind) throw fail('js.unsupported');

  let out = file;
  try {
    if (kind === 'heic') out = await heicToPng(file);
    else if (kind === 'tiff') out = await tiffToPng(file);
  } catch (err) {
    console.error(err);
    throw fail(navigator.onLine === false ? 'js.convert_offline' : 'js.convert_failed');
  }

  // Make sure the browser can actually decode it (e.g. AVIF on old browsers, corrupt files).
  try {
    const bitmap = await createImageBitmap(out);
    bitmap.close?.();
  } catch {
    throw fail('js.unreadable');
  }
  if (forServer && out === file && !SERVER_EXTENSIONS.includes(extOf(file.name))) {
    out = await canvasToPng(file);
  }
  return out;
}
