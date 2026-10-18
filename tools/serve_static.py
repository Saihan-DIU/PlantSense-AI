"""Serve site/ locally with the same headers as vercel.json.

  python tools/serve_static.py                 # http://localhost:8080
  python tools/serve_static.py --eval          # also /__eval/ accuracy check

With --eval, /__eval/ runs the in-browser pipeline over the papaya test set
and a guava sample and compares each prediction with the Python model
(reference predictions are computed once and cached in web_models/).
"""
import argparse
import json
import mimetypes
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
EVAL_PAGE = os.path.join(ROOT, "tools", "eval.html")

mimetypes.add_type("text/javascript", ".mjs")
mimetypes.add_type("application/wasm", ".wasm")

EVAL = {}  # crop -> list of {"path", "label", "ref"}


def build_eval(args):
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import export_onnx as ex
    import numpy as np
    import onnxruntime as ort

    sets = {}
    if args.papaya_test:
        from disease_info import CLASS_NAMES
        sets["papaya"] = (ex.papaya, ex.list_images(args.papaya_test, CLASS_NAMES))
    if args.guava_data:
        import guava_model
        sets["guava"] = (ex.guava, ex.list_images(args.guava_data, guava_model.CLASS_NAMES, 100, seed=0))

    for crop, (build, items) in sets.items():
        cache = os.path.join(ROOT, "web_models", f"reference_{crop}.json")
        if os.path.exists(cache):
            EVAL[crop] = json.load(open(cache))
            continue
        print(f"Computing Python reference predictions for {crop} ({len(items)} images)…", flush=True)
        _, prep, classes = build()
        sess = ort.InferenceSession(os.path.join(ROOT, "web_models", f"{crop}.fp32.onnx"))
        rows = []
        for path, label in items:
            logits = sess.run(None, {"input": prep(path)})[0][0]
            rows.append({"path": path, "label": label, "ref": int(np.argmax(logits))})
        json.dump(rows, open(cache, "w"))
        EVAL[crop] = rows


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=SITE, **kw)

    def end_headers(self):
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "credentialless")
        super().end_headers()

    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        path = unquote(urlparse(self.path).path)
        if path.startswith("/__eval"):
            return self.handle_eval(path)
        if path == "/guava":  # mimic directory handling on static hosts
            self.send_response(301)
            self.send_header("Location", "/guava/")
            self.end_headers()
            return
        return super().do_GET()

    def handle_eval(self, path):
        parts = path.strip("/").split("/")
        if len(parts) == 1:
            return self.send_bytes(open(EVAL_PAGE, "rb").read(), "text/html; charset=utf-8")
        if parts[1] == "manifest.json":
            data = {crop: [{"label": r["label"], "ref": r["ref"]} for r in rows] for crop, rows in EVAL.items()}
            return self.send_bytes(json.dumps(data).encode(), "application/json")
        if parts[1] == "img" and len(parts) == 4:
            row = EVAL[parts[2]][int(parts[3])]
            ctype = mimetypes.guess_type(row["path"])[0] or "application/octet-stream"
            return self.send_bytes(open(row["path"], "rb").read(), ctype)
        self.send_error(404)

    def send_bytes(self, body, ctype):
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--eval", action="store_true")
    ap.add_argument("--papaya-test", default="D:/final updated dataset of papaya/test")
    ap.add_argument("--guava-data", default="D:/Guava Leaf and Fruit diseases dataset/Leaf")
    args = ap.parse_args()
    if args.eval:
        build_eval(args)
    print(f"Serving {SITE} on http://localhost:{args.port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
