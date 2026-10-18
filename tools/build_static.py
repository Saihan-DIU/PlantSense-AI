"""Build the static, in-browser version of the site into site/.

The pages are rendered from the same Jinja templates as the Flask app, with
static_build=True so the upload form runs the ONNX models in the browser
(static/js/inference.js) instead of posting to the server. The output needs no
Python at runtime and can be hosted on Vercel or any static host.

Usage (from the project root, after tools/export_onnx.py has produced
web_models/*.fp16.onnx):
  python tools/build_static.py
  python tools/build_static.py --model-base https://cdn.example.com/models/
"""
import argparse
import ast
import hashlib
import json
import os
import shutil
import sys
import urllib.request

from flask import Flask, render_template

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from datetime import datetime  # noqa: E402

import disease_info  # noqa: E402
import guava_disease_info  # noqa: E402

OUT = os.path.join(ROOT, "site")
MODELS_SRC = os.path.join(ROOT, "web_models")
ORT_VERSION = "1.30.0"
ORT_FILES = ["ort.wasm.min.mjs", "ort-wasm-simd-threaded.mjs", "ort-wasm-simd-threaded.wasm"]
ORT_DIR = f"static/vendor/onnxruntime-web-{ORT_VERSION}"


def guava_class_names():
    """Read guava_model.CLASS_NAMES without importing torch."""
    tree = ast.parse(open(os.path.join(ROOT, "guava_model.py"), encoding="utf-8").read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "CLASS_NAMES":
            return ast.literal_eval(node.value)
    raise RuntimeError("CLASS_NAMES not found in guava_model.py")


CROPS = {
    "papaya": {
        "label": "Papaya",
        "template": "index.html",
        "endpoint_path": "/",
        "out": "index.html",
        "classes": disease_info.CLASS_NAMES,
        "info": disease_info.DISEASE_INFO,
    },
    "guava": {
        "label": "Guava",
        "template": "guava_index.html",
        "endpoint_path": "/guava",
        "out": os.path.join("guava", "index.html"),
        "classes": guava_class_names(),
        "info": guava_disease_info.DISEASE_INFO,
    },
}


def file_hash(path, n=10):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:n]


def make_app():
    """A Flask app with the same endpoints as app.py, but no model code."""
    app = Flask(__name__, root_path=ROOT)
    app.secret_key = "static-build"
    noop = lambda: ""  # noqa: E731
    app.add_url_rule("/", "index", noop)
    app.add_url_rule("/predict", "predict", noop, methods=["POST"])
    app.add_url_rule("/guava", "guava_index", noop)
    app.add_url_rule("/guava/predict", "guava_predict", noop, methods=["POST"])
    app.context_processor(lambda: {"current_year": datetime.now().year})
    return app


def fetch_ort(dest_dir):
    """Download the onnxruntime-web runtime once (cached in web_models/)."""
    cache = os.path.join(MODELS_SRC, f"onnxruntime-web-{ORT_VERSION}")
    os.makedirs(cache, exist_ok=True)
    for name in ORT_FILES:
        cached = os.path.join(cache, name)
        if not os.path.exists(cached):
            url = f"https://cdn.jsdelivr.net/npm/onnxruntime-web@{ORT_VERSION}/dist/{name}"
            print(f"  downloading {url}")
            urllib.request.urlretrieve(url, cached)
    shutil.copytree(cache, dest_dir)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-base", default="/models/",
                    help="URL prefix the browser downloads models from")
    ap.add_argument("--no-copy-models", action="store_true",
                    help="don't copy model files into site/models (when hosted elsewhere)")
    args = ap.parse_args()

    # Start clean, but keep .vercel/ (the Vercel CLI's project link)
    os.makedirs(OUT, exist_ok=True)
    for name in os.listdir(OUT):
        if name == ".vercel":
            continue
        path = os.path.join(OUT, name)
        shutil.rmtree(path) if os.path.isdir(path) else os.remove(path)

    # Static assets (minus runtime uploads), runtime, and models
    shutil.copytree(os.path.join(ROOT, "static"), os.path.join(OUT, "static"),
                    ignore=shutil.ignore_patterns("uploads"))
    fetch_ort(os.path.join(OUT, ORT_DIR))
    inference_module = f"/static/js/inference.js?v={file_hash(os.path.join(ROOT, 'static/js/inference.js'))}"
    # inference.js locates the runtime through ORT_BASE; point it at the versioned folder
    inf_path = os.path.join(OUT, "static/js/inference.js")
    src = open(inf_path, encoding="utf-8").read()
    src = src.replace("const ORT_BASE = '/static/vendor/onnxruntime-web/';",
                      f"const ORT_BASE = '/{ORT_DIR}/';")
    open(inf_path, "w", encoding="utf-8", newline="\n").write(src)

    app = make_app()
    for crop, c in CROPS.items():
        model_file = os.path.join(MODELS_SRC, f"{crop}.fp16.onnx")
        if not os.path.exists(model_file):
            sys.exit(f"Missing {model_file}. Run tools/export_onnx.py first.")
        if not args.no_copy_models:
            os.makedirs(os.path.join(OUT, "models"), exist_ok=True)
            shutil.copy2(model_file, os.path.join(OUT, "models", f"{crop}.fp16.onnx"))

        config = {
            "crop": crop,
            "crop_label": c["label"],
            "preprocess": crop,
            "classes": list(c["classes"]),
            "info": {name: c["info"].get(name, {}) for name in c["classes"]},
            "model_url": f"{args.model_base}{crop}.fp16.onnx?v={file_hash(model_file)}",
            "model_size_mb": round(os.path.getsize(model_file) / 1e6),
            "inference_module": inference_module,
        }
        with app.test_request_context(c["endpoint_path"]):
            html = render_template(
                c["template"],
                static_build=True,
                crop_config=config,
                # Placeholders for the result view; filled in by app.js
                predicted_class="", confidence=0, description="", instructions=[],
                is_healthy=False, ranked=[("", 0)], image_url="",
            )
        dest = os.path.join(OUT, c["out"])
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8", newline="\n") as f:
            f.write(html)
        print(f"  wrote {os.path.relpath(dest, ROOT)}")

    shutil.copy2(os.path.join(ROOT, "vercel.json"), os.path.join(OUT, "vercel.json"))
    # Never upload local env/token files the Vercel CLI may create here
    with open(os.path.join(OUT, ".vercelignore"), "w", encoding="utf-8", newline="\n") as f:
        f.write(".env*\n.gitignore\n")
    print(f"Built static site in {os.path.relpath(OUT, ROOT)}/")


if __name__ == "__main__":
    main()
