"""Export the papaya and guava PyTorch models to ONNX for in-browser inference,
plus smaller variants, and check that each variant agrees with PyTorch.

Variants written to web_models/:
  <crop>.fp32.onnx       full precision (reference)
  <crop>.fp16.onnx       half precision weights (~1/2 size)
  <crop>.int8.onnx       8-bit static QDQ quantization (~1/4 size)

Usage (from the project root):
  python tools/export_onnx.py --papaya-test "D:/final updated dataset of papaya/test" \
      --papaya-calib "D:/final updated dataset of papaya/train" \
      --guava-data "D:/Guava Leaf and Fruit diseases dataset/Leaf"
"""
import argparse
import json
import os
import random
import sys
import time

import numpy as np
import onnx
import onnxruntime as ort
import torch
from onnxconverter_common import float16
from onnxruntime.quantization import (CalibrationDataReader, QuantFormat,
                                      QuantType, quantize_static)
from onnxruntime.quantization.shape_inference import quant_pre_process
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)  # model paths in app.py / guava_model.py are relative

ort.set_default_logger_severity(3)  # errors only

OUT_DIR = os.path.join(ROOT, "web_models")
IMG_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".bmp")


# ---------- model + preprocessing per crop ----------

def papaya():
    import app
    model, transform = app.get_model_and_transform()

    def prep(path):
        return transform(Image.open(path).convert("RGB")).unsqueeze(0).numpy()

    from disease_info import CLASS_NAMES
    return model, prep, CLASS_NAMES


def guava():
    import guava_model
    model = guava_model.get_model()

    def prep(path):
        return guava_model.preprocess_image(path).numpy()

    return model, prep, guava_model.CLASS_NAMES


# ---------- data ----------

def list_images(folder, classes, per_class=None, seed=0, exclude=()):
    items = []
    rng = random.Random(seed)
    for label, name in enumerate(classes):
        d = os.path.join(folder, name)
        files = sorted(f for f in os.listdir(d) if f.lower().endswith(IMG_EXTS))
        files = [os.path.join(d, f) for f in files]
        files = [f for f in files if f not in exclude]
        if per_class:
            rng.shuffle(files)
            files = files[:per_class]
        items += [(f, label) for f in files]
    return items


class Reader(CalibrationDataReader):
    def __init__(self, tensors):
        self.it = iter([{"input": t} for t in tensors])

    def get_next(self):
        return next(self.it, None)


# ---------- export ----------

def export(crop, model, calib_tensors):
    os.makedirs(OUT_DIR, exist_ok=True)
    fp32 = os.path.join(OUT_DIR, f"{crop}.fp32.onnx")
    dummy = torch.from_numpy(calib_tensors[0])
    torch.onnx.export(
        model, dummy, fp32, input_names=["input"], output_names=["logits"],
        opset_version=17, dynamo=False, do_constant_folding=True,
    )
    onnx.checker.check_model(fp32)

    fp16 = os.path.join(OUT_DIR, f"{crop}.fp16.onnx")
    # Keep existing Cast nodes in fp32 (the converter mistypes them otherwise)
    # and drop stale shape info so it is re-inferred for the fp16 graph.
    m = onnx.load(fp32)
    del m.graph.value_info[:]
    casts = [n.name for n in m.graph.node if n.op_type == "Cast"]
    m16 = float16.convert_float_to_float16(m, keep_io_types=True, node_block_list=casts)
    onnx.save(m16, fp16)

    pre = os.path.join(OUT_DIR, f"{crop}.pre.onnx")
    quant_pre_process(fp32, pre, skip_symbolic_shape=True)
    int8 = os.path.join(OUT_DIR, f"{crop}.int8.onnx")
    quantize_static(
        pre, int8, Reader(calib_tensors), quant_format=QuantFormat.QDQ,
        per_channel=True, activation_type=QuantType.QUInt8, weight_type=QuantType.QInt8,
    )
    os.remove(pre)
    return {"fp32": fp32, "fp16": fp16, "int8": int8}


# ---------- evaluate ----------

def softmax(x):
    e = np.exp(x - x.max())
    return e / e.sum()


def evaluate(model, prep, items, paths):
    sessions = {k: ort.InferenceSession(p, providers=["CPUExecutionProvider"]) for k, p in paths.items()}
    names = ["pytorch"] + list(sessions)
    preds = {n: [] for n in names}
    probs = {n: [] for n in names}
    times = {n: 0.0 for n in names}
    labels = []
    for i, (path, label) in enumerate(items):
        x = prep(path)
        labels.append(label)
        t = time.perf_counter()
        with torch.no_grad():
            out = model(torch.from_numpy(x))[0].numpy()
        times["pytorch"] += time.perf_counter() - t
        preds["pytorch"].append(int(out.argmax())); probs["pytorch"].append(softmax(out))
        for k, s in sessions.items():
            t = time.perf_counter()
            out = s.run(None, {"input": x})[0][0].astype(np.float32)
            times[k] += time.perf_counter() - t
            preds[k].append(int(out.argmax())); probs[k].append(softmax(out))
        if (i + 1) % 100 == 0:
            print(f"  {i + 1}/{len(items)}", flush=True)

    labels = np.array(labels)
    ref_pred, ref_prob = np.array(preds["pytorch"]), np.array(probs["pytorch"])
    result = {}
    for n in names:
        p, pr = np.array(preds[n]), np.array(probs[n])
        result[n] = {
            "accuracy": round(float((p == labels).mean() * 100), 2),
            "agree_with_pytorch": round(float((p == ref_pred).mean() * 100), 2),
            "disagreements": int((p != ref_pred).sum()),
            "max_conf_diff_pct": round(float(np.abs(pr - ref_prob).max() * 100), 2),
            "mean_conf_diff_pct": round(float(np.abs(pr - ref_prob).max(axis=1).mean() * 100), 3),
            "ms_per_image_cpu": round(times[n] / len(items) * 1000, 1),
            "size_mb": round(os.path.getsize(paths[n]) / 1e6, 1) if n in paths else None,
        }
    return result


def run(crop, build, eval_items, calib_items):
    print(f"\n=== {crop}: {len(eval_items)} eval images, {len(calib_items)} calibration images ===", flush=True)
    model, prep, _ = build()
    calib = [prep(p) for p, _ in calib_items]
    paths = export(crop, model, calib)
    print("  exported:", ", ".join(f"{k} {os.path.getsize(v) / 1e6:.0f} MB" for k, v in paths.items()), flush=True)
    return evaluate(model, prep, eval_items, paths)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--papaya-test")
    ap.add_argument("--papaya-calib")
    ap.add_argument("--guava-data")
    ap.add_argument("--guava-per-class", type=int, default=100)
    ap.add_argument("--calib-per-class", type=int, default=20)
    args = ap.parse_args()

    torch.set_num_threads(os.cpu_count() or 4)
    results = {}

    if args.papaya_test:
        from disease_info import CLASS_NAMES
        results["papaya"] = run(
            "papaya", papaya,
            list_images(args.papaya_test, CLASS_NAMES),
            list_images(args.papaya_calib, CLASS_NAMES, args.calib_per_class, seed=1),
        )

    if args.guava_data:
        import guava_model
        classes = guava_model.CLASS_NAMES
        eval_items = list_images(args.guava_data, classes, args.guava_per_class, seed=0)
        used = {p for p, _ in eval_items}
        calib_items = list_images(args.guava_data, classes, args.calib_per_class, seed=1, exclude=used)
        results["guava"] = run("guava", guava, eval_items, calib_items)

    print(json.dumps(results, indent=2))
    with open(os.path.join(OUT_DIR, "comparison.json"), "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()
