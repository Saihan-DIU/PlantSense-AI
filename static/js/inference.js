// In-browser leaf diagnosis: runs the ONNX models with onnxruntime-web.
//
// Preprocessing is a pixel-level port of the Python pipelines so browser
// predictions match the PyTorch models:
//   papaya -> timm eval transform (Resize 235 bicubic, CenterCrop 224, Normalize)
//   guava  -> guava_model.remove_background + Resize 255 bilinear + CenterCrop 224
// Resampling mirrors PIL (antialiased separable filters), and the background
// removal mirrors the OpenCV calls in guava_model.py.

const ORT_BASE = '/static/vendor/onnxruntime-web/';
const CACHE_NAME = 'plantsense-models-v1';
const MEAN = [0.485, 0.456, 0.406];
const STD = [0.229, 0.224, 0.225];
const SIZE = 224;

/* ------------------------------------------------------------------ */
/* onnxruntime-web                                                      */
/* ------------------------------------------------------------------ */

let ortPromise = null;
function loadOrt() {
  if (!ortPromise) {
    ortPromise = import(`${ORT_BASE}ort.wasm.min.mjs`).then((ort) => {
      ort.env.wasm.wasmPaths = ORT_BASE;
      ort.env.logLevel = 'error'; // graph-optimizer notices are expected and harmless
      // Threads need SharedArrayBuffer, which needs a cross-origin isolated page.
      ort.env.wasm.numThreads = self.crossOriginIsolated
        ? Math.min(4, navigator.hardwareConcurrency || 4)
        : 1;
      return ort;
    });
  }
  return ortPromise;
}

/* ------------------------------------------------------------------ */
/* Model download with progress + Cache Storage                          */
/* ------------------------------------------------------------------ */

async function fetchWithProgress(url, onProgress) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Could not download the AI model (HTTP ${res.status}).`);
  const total = Number(res.headers.get('Content-Length')) || 0;
  if (!res.body || !total) {
    const buf = await res.arrayBuffer();
    onProgress?.(1);
    return buf;
  }
  const reader = res.body.getReader();
  const chunks = [];
  let loaded = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value);
    loaded += value.length;
    onProgress?.(Math.min(loaded / total, 1));
  }
  const out = new Uint8Array(loaded);
  let offset = 0;
  for (const c of chunks) { out.set(c, offset); offset += c.length; }
  return out.buffer;
}

async function loadModelBytes(url, onProgress) {
  let cache = null;
  try { cache = await caches.open(CACHE_NAME); } catch { /* no Cache API (e.g. http) */ }
  if (cache) {
    const hit = await cache.match(url);
    if (hit) { onProgress?.(1); return hit.arrayBuffer(); }
  }
  const buf = await fetchWithProgress(url, onProgress);
  if (cache) {
    try {
      // Drop older versions of the same model before storing the new one.
      const path = new URL(url, location.href).pathname;
      for (const req of await cache.keys()) {
        if (new URL(req.url).pathname === path) await cache.delete(req);
      }
      await cache.put(url, new Response(buf.slice(0), {
        headers: { 'Content-Type': 'application/octet-stream' },
      }));
    } catch { /* storage full or blocked: still works, just not cached */ }
  }
  return buf;
}

/* ------------------------------------------------------------------ */
/* Image decoding (raw pixels, like PIL: no EXIF rotation, no ICC)       */
/* ------------------------------------------------------------------ */

// Reads the EXIF orientation tag (1-8) from a JPEG; 1 when absent.
async function readExifOrientation(blob) {
  const view = new DataView(await blob.slice(0, 131072).arrayBuffer());
  if (view.byteLength < 4 || view.getUint16(0) !== 0xffd8) return 1;
  let p = 2;
  while (p + 4 <= view.byteLength) {
    const marker = view.getUint16(p);
    const len = view.getUint16(p + 2);
    if (marker === 0xffe1 && p + 10 <= view.byteLength && view.getUint32(p + 4) === 0x45786966) {
      const tiff = p + 10;
      const le = view.getUint16(tiff) === 0x4949;
      const ifd = tiff + view.getUint32(tiff + 4, le);
      const count = view.getUint16(ifd, le);
      for (let i = 0; i < count; i++) {
        const e = ifd + 2 + i * 12;
        if (e + 10 > view.byteLength) break;
        if (view.getUint16(e, le) === 0x0112) return view.getUint16(e + 8, le) || 1;
      }
      return 1;
    }
    if ((marker & 0xff00) !== 0xff00 || marker === 0xffda) break;
    p += 2 + len;
  }
  return 1;
}

// Returns { data: Uint8Array RGB, w, h } in the file's stored orientation.
export async function decodeImage(blob) {
  const bitmap = await createImageBitmap(blob, {
    colorSpaceConversion: 'none',
    premultiplyAlpha: 'none',
  });
  const W = bitmap.width, H = bitmap.height;
  const canvas = typeof OffscreenCanvas !== 'undefined'
    ? new OffscreenCanvas(W, H)
    : Object.assign(document.createElement('canvas'), { width: W, height: H });
  const ctx = canvas.getContext('2d', { willReadFrequently: true });
  ctx.drawImage(bitmap, 0, 0);
  bitmap.close?.();
  const rgba = ctx.getImageData(0, 0, W, H).data;

  // Browsers apply EXIF orientation when decoding; PIL (and therefore the
  // training data) does not. Map displayed pixels back to stored order.
  const o = await readExifOrientation(blob);
  const swap = o >= 5;
  const w = swap ? H : W, h = swap ? W : H;
  const out = new Uint8Array(w * h * 3);
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      let dx, dy;
      switch (o) {
        case 2: dx = w - 1 - x; dy = y; break;
        case 3: dx = w - 1 - x; dy = h - 1 - y; break;
        case 4: dx = x; dy = h - 1 - y; break;
        case 5: dx = y; dy = x; break;
        case 6: dx = h - 1 - y; dy = x; break;
        case 7: dx = h - 1 - y; dy = w - 1 - x; break;
        case 8: dx = y; dy = w - 1 - x; break;
        default: dx = x; dy = y;
      }
      const s = (dy * W + dx) * 4, d = (y * w + x) * 3;
      out[d] = rgba[s]; out[d + 1] = rgba[s + 1]; out[d + 2] = rgba[s + 2];
    }
  }
  return { data: out, w, h };
}

/* ------------------------------------------------------------------ */
/* PIL-style resampling                                                 */
/* ------------------------------------------------------------------ */

const FILTERS = {
  box: { support: 0.5, fn: (x) => (x > -0.5 && x <= 0.5 ? 1 : 0) },
  bilinear: { support: 1, fn: (x) => { x = Math.abs(x); return x < 1 ? 1 - x : 0; } },
  bicubic: {
    support: 2,
    fn: (x) => {
      const a = -0.5;
      x = Math.abs(x);
      if (x < 1) return ((a + 2) * x - (a + 3)) * x * x + 1;
      if (x < 2) return (((x - 5) * x + 8) * x - 4) * a;
      return 0;
    },
  },
};

function coeffs(inSize, outSize, filter) {
  const scale = inSize / outSize;
  const fscale = Math.max(scale, 1);
  const support = filter.support * fscale;
  const ss = 1 / fscale;
  const bounds = new Int32Array(outSize * 2);
  const ksize = Math.ceil(support) * 2 + 1;
  const k = new Float64Array(outSize * ksize);
  for (let xx = 0; xx < outSize; xx++) {
    const center = (xx + 0.5) * scale;
    const xmin = Math.max(Math.trunc(center - support + 0.5), 0);
    const xcount = Math.min(Math.trunc(center + support + 0.5), inSize) - xmin;
    let ww = 0;
    for (let x = 0; x < xcount; x++) {
      const w = filter.fn((x + xmin - center + 0.5) * ss);
      k[xx * ksize + x] = w;
      ww += w;
    }
    if (ww !== 0) for (let x = 0; x < xcount; x++) k[xx * ksize + x] /= ww;
    bounds[xx * 2] = xmin;
    bounds[xx * 2 + 1] = xcount;
  }
  return { bounds, k, ksize };
}

const clip8 = (v) => (v <= 0 ? 0 : v >= 255 ? 255 : Math.floor(v + 0.5));

// Resize an RGB image like PIL Image.resize (horizontal pass, then vertical,
// each rounded to 8 bits).
export function resizePIL(img, outW, outH, filterName) {
  const filter = FILTERS[filterName];
  let { data, w, h } = img;
  if (outW !== w) {
    const { bounds, k, ksize } = coeffs(w, outW, filter);
    const tmp = new Uint8Array(outW * h * 3);
    for (let y = 0; y < h; y++) {
      for (let xx = 0; xx < outW; xx++) {
        const xmin = bounds[xx * 2], n = bounds[xx * 2 + 1];
        let r = 0, g = 0, b = 0;
        for (let x = 0; x < n; x++) {
          const c = k[xx * ksize + x], s = (y * w + xmin + x) * 3;
          r += data[s] * c; g += data[s + 1] * c; b += data[s + 2] * c;
        }
        const d = (y * outW + xx) * 3;
        tmp[d] = clip8(r); tmp[d + 1] = clip8(g); tmp[d + 2] = clip8(b);
      }
    }
    data = tmp; w = outW;
  }
  if (outH !== h) {
    const { bounds, k, ksize } = coeffs(h, outH, filter);
    const tmp = new Uint8Array(w * outH * 3);
    for (let yy = 0; yy < outH; yy++) {
      const ymin = bounds[yy * 2], n = bounds[yy * 2 + 1];
      for (let x = 0; x < w; x++) {
        let r = 0, g = 0, b = 0;
        for (let y = 0; y < n; y++) {
          const c = k[yy * ksize + y], s = ((ymin + y) * w + x) * 3;
          r += data[s] * c; g += data[s + 1] * c; b += data[s + 2] * c;
        }
        const d = (yy * w + x) * 3;
        tmp[d] = clip8(r); tmp[d + 1] = clip8(g); tmp[d + 2] = clip8(b);
      }
    }
    data = tmp; h = outH;
  }
  return { data, w, h };
}

function crop(img, left, top, cw, ch) {
  const out = new Uint8Array(cw * ch * 3);
  for (let y = 0; y < ch; y++) {
    const s = ((top + y) * img.w + left) * 3;
    out.set(img.data.subarray(s, s + cw * 3), y * cw * 3);
  }
  return { data: out, w: cw, h: ch };
}

// Python's round(): half to even (torchvision CenterCrop uses it).
function roundHalfEven(x) {
  const r = Math.round(x);
  return Math.abs(x % 1) === 0.5 && r % 2 !== 0 ? r - 1 : r;
}

function toTensor(img, ort) {
  const n = img.w * img.h;
  const t = new Float32Array(3 * n);
  for (let i = 0; i < n; i++) {
    for (let c = 0; c < 3; c++) {
      t[c * n + i] = (img.data[i * 3 + c] / 255 - MEAN[c]) / STD[c];
    }
  }
  return new ort.Tensor('float32', t, [1, 3, img.h, img.w]);
}

/* ------------------------------------------------------------------ */
/* Papaya: timm eval transform                                          */
/* ------------------------------------------------------------------ */

export function preprocessPapaya(img) {
  const scaleSize = Math.floor(SIZE / 0.95); // 235
  let w, h;
  if (img.w <= img.h) { w = scaleSize; h = Math.trunc(scaleSize * img.h / img.w); }
  else { h = scaleSize; w = Math.trunc(scaleSize * img.w / img.h); }
  const resized = resizePIL(img, w, h, 'bicubic');
  const top = roundHalfEven((h - SIZE) / 2);
  const left = roundHalfEven((w - SIZE) / 2);
  return crop(resized, left, top, SIZE, SIZE);
}

/* ------------------------------------------------------------------ */
/* Guava: OpenCV-style background removal (guava_model.remove_background) */
/* ------------------------------------------------------------------ */

// cv2.resize INTER_AREA (downscaling); single channel or RGB.
function resizeArea(src, w, h, ch, outW, outH) {
  if (outW > w || outH > h) return resizeLinear(src, w, h, ch, outW, outH);
  const tab = (inS, outS) => {
    const scale = inS / outS;
    const list = [];
    for (let o = 0; o < outS; o++) {
      const f0 = o * scale, f1 = f0 + scale;
      const items = [];
      for (let i = Math.floor(f0); i < Math.ceil(f1) && i < inS; i++) {
        const a = Math.max(f0, i), b = Math.min(f1, i + 1);
        if (b - a > 1e-9) items.push([i, (b - a) / scale]);
      }
      list.push(items);
    }
    return list;
  };
  const tx = tab(w, outW), ty = tab(h, outH);
  const tmp = new Float64Array(outW * h * ch);
  for (let y = 0; y < h; y++)
    for (let ox = 0; ox < outW; ox++)
      for (const [i, wt] of tx[ox])
        for (let c = 0; c < ch; c++) tmp[(y * outW + ox) * ch + c] += src[(y * w + i) * ch + c] * wt;
  const out = new Uint8Array(outW * outH * ch);
  for (let oy = 0; oy < outH; oy++)
    for (let ox = 0; ox < outW; ox++)
      for (let c = 0; c < ch; c++) {
        let v = 0;
        for (const [j, wt] of ty[oy]) v += tmp[(j * outW + ox) * ch + c] * wt;
        out[(oy * outW + ox) * ch + c] = clip8(v);
      }
  return out;
}

// cv2.resize INTER_LINEAR.
function resizeLinear(src, w, h, ch, outW, outH) {
  const axis = (inS, outS) => {
    const scale = inS / outS;
    const idx = new Int32Array(outS), frac = new Float64Array(outS);
    for (let o = 0; o < outS; o++) {
      let f = (o + 0.5) * scale - 0.5;
      let i = Math.floor(f);
      f -= i;
      if (i < 0) { i = 0; f = 0; }
      if (i >= inS - 1) { i = inS - 1; f = 0; }
      idx[o] = i; frac[o] = f;
    }
    return { idx, frac };
  };
  const ax = axis(w, outW), ay = axis(h, outH);
  const out = new Uint8Array(outW * outH * ch);
  for (let oy = 0; oy < outH; oy++) {
    const y0 = ay.idx[oy], y1 = Math.min(y0 + 1, h - 1), fy = ay.frac[oy];
    for (let ox = 0; ox < outW; ox++) {
      const x0 = ax.idx[ox], x1 = Math.min(x0 + 1, w - 1), fx = ax.frac[ox];
      for (let c = 0; c < ch; c++) {
        const v = (src[(y0 * w + x0) * ch + c] * (1 - fx) + src[(y0 * w + x1) * ch + c] * fx) * (1 - fy)
          + (src[(y1 * w + x0) * ch + c] * (1 - fx) + src[(y1 * w + x1) * ch + c] * fx) * fy;
        out[(oy * outW + ox) * ch + c] = clip8(v);
      }
    }
  }
  return out;
}

// cv2.cvtColor RGB2LAB for 8-bit images.
function rgbToLab8(src, n) {
  const lin = new Float64Array(256);
  for (let i = 0; i < 256; i++) {
    const x = i / 255;
    lin[i] = x <= 0.04045 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4);
  }
  const f = (t) => (t > 0.008856 ? Math.cbrt(t) : 7.787 * t + 16 / 116);
  const out = new Float64Array(n * 3);
  for (let i = 0; i < n; i++) {
    const r = lin[src[i * 3]], g = lin[src[i * 3 + 1]], b = lin[src[i * 3 + 2]];
    const X = (0.412453 * r + 0.357580 * g + 0.180423 * b) / 0.950456;
    const Y = 0.212671 * r + 0.715160 * g + 0.072169 * b;
    const Z = (0.019334 * r + 0.119193 * g + 0.950227 * b) / 1.088754;
    const L = Y > 0.008856 ? 116 * Math.cbrt(Y) - 16 : 903.3 * Y;
    const fy = f(Y);
    out[i * 3] = clip8(L * 255 / 100);
    out[i * 3 + 1] = clip8(500 * (f(X) - fy) + 128);
    out[i * 3 + 2] = clip8(200 * (fy - f(Z)) + 128);
  }
  return out;
}

function median(values) {
  values.sort((a, b) => a - b);
  const m = values.length >> 1;
  return values.length % 2 ? values[m] : (values[m - 1] + values[m]) / 2;
}

// cv2.GaussianBlur(src, (5, 5), 0) on uint8: kernel [1 4 6 4 1]/16, BORDER_REFLECT_101.
function gaussian5(src, w, h) {
  const k = [1, 4, 6, 4, 1];
  const refl = (i, n) => (i < 0 ? -i : i >= n ? 2 * n - 2 - i : i);
  const tmp = new Int32Array(w * h);
  for (let y = 0; y < h; y++)
    for (let x = 0; x < w; x++) {
      let s = 0;
      for (let j = -2; j <= 2; j++) s += k[j + 2] * src[y * w + refl(x + j, w)];
      tmp[y * w + x] = s;
    }
  const out = new Uint8Array(w * h);
  for (let y = 0; y < h; y++)
    for (let x = 0; x < w; x++) {
      let s = 0;
      for (let j = -2; j <= 2; j++) s += k[j + 2] * tmp[refl(y + j, h) * w + x];
      out[y * w + x] = Math.min(255, Math.floor((s + 128) / 256));
    }
  return out;
}

// cv2 THRESH_OTSU threshold value (replicates getThreshVal_Otsu_8u).
function otsu(src) {
  const hist = new Float64Array(256);
  for (let i = 0; i < src.length; i++) hist[src[i]]++;
  const scale = 1 / src.length;
  let mu = 0;
  for (let i = 0; i < 256; i++) mu += i * hist[i];
  mu *= scale;
  let q1 = 0, mu1 = 0, maxSigma = 0, maxVal = 0;
  const EPS = 1.1920928955078125e-7;
  for (let i = 0; i < 256; i++) {
    const p = hist[i] * scale;
    mu1 *= q1;
    q1 += p;
    const q2 = 1 - q1;
    if (Math.min(q1, q2) < EPS || Math.max(q1, q2) > 1 - EPS) continue;
    mu1 = (mu1 + i * p) / q1;
    const mu2 = (mu - q1 * mu1) / q2;
    const sigma = q1 * q2 * (mu1 - mu2) * (mu1 - mu2);
    if (sigma > maxSigma) { maxSigma = sigma; maxVal = i; }
  }
  return maxVal;
}

// 7x7 elliptical structuring element offsets (cv2.MORPH_ELLIPSE).
const ELLIPSE7 = (() => {
  const pts = [];
  for (let i = 0; i < 7; i++) {
    const dy = i - 3;
    const dx = Math.round(3 * Math.sqrt((9 - dy * dy) / 9));
    for (let j = Math.max(3 - dx, 0); j < Math.min(3 + dx + 1, 7); j++) pts.push([j - 3, dy]);
  }
  return pts;
})();

function morph(src, w, h, dilate) {
  const out = new Uint8Array(w * h);
  for (let y = 0; y < h; y++)
    for (let x = 0; x < w; x++) {
      let v = dilate ? 0 : 255;
      for (const [dx, dy] of ELLIPSE7) {
        const xx = x + dx, yy = y + dy;
        if (xx < 0 || yy < 0 || xx >= w || yy >= h) continue; // border is neutral
        const p = src[yy * w + xx];
        v = dilate ? Math.max(v, p) : Math.min(v, p);
      }
      out[y * w + x] = v;
    }
  return out;
}

function largestComponent(mask, w, h) {
  const labels = new Int32Array(w * h);
  const stack = new Int32Array(w * h);
  let best = 0, bestArea = 0, next = 0;
  for (let i = 0; i < w * h; i++) {
    if (!mask[i] || labels[i]) continue;
    next++;
    let sp = 0, area = 0;
    stack[sp++] = i; labels[i] = next;
    while (sp) {
      const p = stack[--sp];
      area++;
      const px = p % w, py = (p - px) / w;
      for (let dy = -1; dy <= 1; dy++)
        for (let dx = -1; dx <= 1; dx++) {
          const nx = px + dx, ny = py + dy;
          if (nx < 0 || ny < 0 || nx >= w || ny >= h) continue;
          const q = ny * w + nx;
          if (mask[q] && !labels[q]) { labels[q] = next; stack[sp++] = q; }
        }
    }
    if (area > bestArea) { bestArea = area; best = next; }
  }
  const out = new Uint8Array(w * h);
  if (next) for (let i = 0; i < w * h; i++) out[i] = labels[i] === best ? 255 : 0;
  return { mask: next ? out : mask, count: next };
}

// Fill holes: cv2.floodFill(~mask) from (0, 0) with 4-connectivity, then OR.
function fillHoles(mask, w, h) {
  const inv = new Uint8Array(w * h);
  for (let i = 0; i < w * h; i++) inv[i] = 255 - mask[i];
  if (inv[0] === 255) {
    const stack = [0];
    inv[0] = 0;
    while (stack.length) {
      const p = stack.pop();
      const x = p % w, y = (p - x) / w;
      for (const [nx, ny] of [[x - 1, y], [x + 1, y], [x, y - 1], [x, y + 1]]) {
        if (nx < 0 || ny < 0 || nx >= w || ny >= h) continue;
        const q = ny * w + nx;
        if (inv[q] === 255) { inv[q] = 0; stack.push(q); }
      }
    }
  }
  const out = new Uint8Array(w * h);
  for (let i = 0; i < w * h; i++) out[i] = mask[i] | inv[i];
  return out;
}

export function removeBackground(img, fill = [124, 116, 104], margin = 0.06, work = 256, maxSide = 512) {
  let { data, w, h } = img;
  if (Math.max(w, h) > maxSide) {
    const s0 = maxSide / Math.max(w, h);
    const nw = Math.trunc(w * s0), nh = Math.trunc(h * s0);
    data = resizeArea(data, w, h, 3, nw, nh);
    w = nw; h = nh;
  }
  const base = { data, w, h };
  const n = work * work;
  const small = resizeArea(data, w, h, 3, work, work);
  const lab = rgbToLab8(small, n);

  const k = Math.max(4, Math.trunc(work * 0.05));
  const ring = [[], [], []];
  const push = (x, y) => { const i = (y * work + x) * 3; for (let c = 0; c < 3; c++) ring[c].push(lab[i + c]); };
  for (let y = 0; y < k; y++) for (let x = 0; x < work; x++) push(x, y);
  for (let y = work - k; y < work; y++) for (let x = 0; x < work; x++) push(x, y);
  for (let y = 0; y < work; y++) for (let x = 0; x < k; x++) push(x, y);
  for (let y = 0; y < work; y++) for (let x = work - k; x < work; x++) push(x, y);
  const bg = ring.map(median);

  const dist = new Float64Array(n);
  let dmax = 0;
  for (let i = 0; i < n; i++) {
    const d0 = lab[i * 3] - bg[0], d1 = lab[i * 3 + 1] - bg[1], d2 = lab[i * 3 + 2] - bg[2];
    dist[i] = Math.fround(Math.sqrt(d0 * d0 + d1 * d1 + d2 * d2));
    if (dist[i] > dmax) dmax = dist[i];
  }
  let distU8 = new Uint8Array(n);
  for (let i = 0; i < n; i++) distU8[i] = Math.max(0, Math.min(255, Math.trunc(dist[i] / (dmax + 1e-6) * 255)));
  distU8 = gaussian5(distU8, work, work);

  const thr = otsu(distU8);
  let mask = new Uint8Array(n);
  for (let i = 0; i < n; i++) mask[i] = distU8[i] > thr ? 255 : 0;
  // MORPH_CLOSE x2 = dilate, dilate, erode, erode; MORPH_OPEN x1 = erode, dilate
  mask = morph(morph(mask, work, work, true), work, work, true);
  mask = morph(morph(mask, work, work, false), work, work, false);
  mask = morph(morph(mask, work, work, false), work, work, true);
  mask = largestComponent(mask, work, work).mask;
  mask = fillHoles(mask, work, work);

  let area = 0;
  for (let i = 0; i < n; i++) area += mask[i];
  area /= n * 255;
  if (area < 0.04 || area > 0.97) return base; // segmentation failed: keep original

  let full = resizeLinear(mask, work, work, 1, w, h);
  full = gaussian5(full, w, h);
  let y0 = h, y1 = 0, x0 = w, x1 = 0;
  for (let y = 0; y < h; y++)
    for (let x = 0; x < w; x++)
      if (full[y * w + x] > 127) {
        if (y < y0) y0 = y; if (y > y1) y1 = y;
        if (x < x0) x0 = x; if (x > x1) x1 = x;
      }
  y1 += 1; x1 += 1;
  const pad = Math.trunc(margin * Math.max(y1 - y0, x1 - x0));
  y0 = Math.max(0, y0 - pad); x0 = Math.max(0, x0 - pad);
  y1 = Math.min(h, y1 + pad); x1 = Math.min(w, x1 + pad);

  const hh = y1 - y0, ww = x1 - x0, s = Math.max(hh, ww);
  const out = new Uint8Array(s * s * 3);
  for (let i = 0; i < s * s; i++) { out[i * 3] = fill[0]; out[i * 3 + 1] = fill[1]; out[i * 3 + 2] = fill[2]; }
  const oy = (s - hh) >> 1, ox = (s - ww) >> 1;
  const f32 = Math.fround;
  for (let y = 0; y < hh; y++)
    for (let x = 0; x < ww; x++) {
      const a = f32(full[(y + y0) * w + x + x0] / 255);
      const ia = f32(1 - a);
      const si = ((y + y0) * w + x + x0) * 3, di = ((y + oy) * s + x + ox) * 3;
      for (let c = 0; c < 3; c++) {
        out[di + c] = Math.trunc(f32(f32(data[si + c] * a) + f32(fill[c] * ia)));
      }
    }
  return { data: out, w: s, h: s };
}

export function preprocessGuava(img) {
  const masked = removeBackground(img);
  const resizeTo = Math.trunc(SIZE * 1.14); // 255
  const resized = resizePIL(masked, resizeTo, resizeTo, 'bilinear');
  const off = (resizeTo - SIZE) >> 1;
  return crop(resized, off, off, SIZE, SIZE);
}

const PREPROCESS = { papaya: preprocessPapaya, guava: preprocessGuava };

/* ------------------------------------------------------------------ */
/* Predictor                                                            */
/* ------------------------------------------------------------------ */

export function createPredictor(config) {
  let sessionPromise = null;
  let progressListener = null;

  const ensureSession = () => {
    if (!sessionPromise) {
      sessionPromise = (async () => {
        const [ort, bytes] = await Promise.all([
          loadOrt(),
          loadModelBytes(config.model_url, (p) => progressListener?.(p)),
        ]);
        const session = await ort.InferenceSession.create(bytes, {
          executionProviders: ['wasm'],
          graphOptimizationLevel: 'all',
        });
        return { ort, session };
      })();
      sessionPromise.catch(() => { sessionPromise = null; }); // allow retry
    }
    return sessionPromise;
  };

  return {
    // Download + initialise the model ahead of time (safe to call repeatedly).
    preload(onProgress) {
      if (onProgress) progressListener = onProgress;
      return ensureSession();
    },

    async predict(file, { onDownload, onStage } = {}) {
      if (onDownload) progressListener = onDownload;
      const decoded = decodeImage(file);
      const { ort, session } = await ensureSession();
      onStage?.('analyzing');
      const img = PREPROCESS[config.preprocess](await decoded);
      const tensor = toTensor(img, ort);
      const output = await session.run({ [session.inputNames[0]]: tensor });
      const logits = Array.from(output[session.outputNames[0]].data);
      const max = Math.max(...logits);
      const exps = logits.map((v) => Math.exp(v - max));
      const sum = exps.reduce((a, b) => a + b, 0);
      const probs = exps.map((v) => v / sum);
      const order = probs.map((p, i) => i).sort((a, b) => probs[b] - probs[a]);
      return {
        index: order[0],
        className: config.classes[order[0]],
        confidence: probs[order[0]] * 100,
        probs,
        ranked: order.slice(0, 3).map((i) => [config.classes[i], probs[i] * 100]),
      };
    },
  };
}
