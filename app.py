import os
import uuid
from datetime import datetime

import torch
import torch.nn.functional as F
from flask import Flask, render_template, request, url_for, flash, redirect
from PIL import Image
from werkzeug.utils import secure_filename

import i18n
from disease_info import CLASS_NAMES
import guava_model

MODEL_ARCH = "maxvit_tiny_tf_224"  # must match the architecture the .pth was trained with
MODEL_PATH = os.path.join("model", "MaxViT-Tiny_seed_42_best.pth")
UPLOAD_FOLDER = os.path.join("static", "uploads")
# The browser converts HEIC/HEIF and AVIF to PNG before uploading (static/js/image-formats.js)
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "jfif", "webp", "gif", "bmp", "tif", "tiff"}

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB upload limit

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.context_processor
def inject_current_year():
    return {"current_year": datetime.now().year}


_model = None
_transform = None


def get_model_and_transform():
    """Load the PyTorch/timm model lazily so the app can still start (and show
    a helpful error) even if the checkpoint file hasn't been added yet."""
    global _model, _transform
    if _model is None:
        import timm
        from timm.data import create_transform, resolve_data_config

        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Model file not found at '{MODEL_PATH}'. "
                "Copy your trained checkpoint (e.g. MaxViT-Tiny_seed_42_best.pth) "
                "into the model/ folder."
            )

        checkpoint = torch.load(MODEL_PATH, map_location="cpu", weights_only=False)
        state_dict = checkpoint["model_state_dict"] if "model_state_dict" in checkpoint else checkpoint
        # Drop thop profiling buffers (total_ops/total_params) that aren't real weights.
        state_dict = {
            k: v for k, v in state_dict.items()
            if "total_ops" not in k and "total_params" not in k
        }

        model = timm.create_model(MODEL_ARCH, pretrained=False, num_classes=len(CLASS_NAMES))
        model.load_state_dict(state_dict, strict=True)
        model.eval()

        config = resolve_data_config({}, model=model)
        _transform = create_transform(**config)
        _model = model

    return _model, _transform


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def preprocess_image(image_path, transform):
    img = Image.open(image_path).convert("RGB")
    return transform(img).unsqueeze(0)


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


def _back(endpoint, lang):
    return redirect(i18n.lang_path(url_for(endpoint), lang))


def _save_upload(back_endpoint, lang):
    """Validate and store the uploaded file; returns (path, url) or a redirect."""
    t = i18n.translator(lang)
    file = request.files.get("leaf_image")
    if file is None or file.filename == "":
        flash(t("server.no_file"))
        return _back(back_endpoint, lang)
    if not allowed_file(file.filename):
        flash(t("server.unsupported"))
        return _back(back_endpoint, lang)
    unique_name = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
    file.save(save_path)
    return save_path, url_for("static", filename=f"uploads/{unique_name}")


def _render_result(template, crop, class_names, predictions, image_url, lang):
    info = i18n.localized_info(crop, lang, class_names)
    probs = predictions.tolist()
    top = max(range(len(probs)), key=probs.__getitem__)
    ranked = sorted(zip(class_names, probs), key=lambda x: x[1], reverse=True)[:3]
    chosen = info[class_names[top]]
    return render_template(
        template,
        image_url=image_url,
        display_name=chosen["name"],
        confidence=round(probs[top] * 100, 2),
        description=chosen["description"],
        instructions=chosen["instructions"],
        is_healthy=chosen["is_healthy"],
        ranked=[(info[name]["name"], round(prob * 100, 2)) for name, prob in ranked],
    )


@app.route("/predict", methods=["POST"])
def predict():
    lang = i18n.request_lang()
    saved = _save_upload("index", lang)
    if not isinstance(saved, tuple):
        return saved
    save_path, image_url = saved

    try:
        model, transform = get_model_and_transform()
        batch = preprocess_image(save_path, transform)
        with torch.no_grad():
            predictions = F.softmax(model(batch)[0], dim=0)
        return _render_result("result.html", "papaya", CLASS_NAMES, predictions, image_url, lang)
    except FileNotFoundError as e:
        flash(str(e))
        return _back("index", lang)
    except Exception as e:
        flash(i18n.translator(lang)("server.failed", error=e))
        return _back("index", lang)


@app.route("/guava", methods=["GET"])
def guava_index():
    return render_template("guava_index.html")


@app.route("/guava/predict", methods=["POST"])
def guava_predict():
    lang = i18n.request_lang()
    saved = _save_upload("guava_index", lang)
    if not isinstance(saved, tuple):
        return saved
    save_path, image_url = saved

    try:
        model = guava_model.get_model()
        batch = guava_model.preprocess_image(save_path)
        with torch.no_grad():
            predictions = F.softmax(model(batch)[0], dim=0)
        return _render_result("guava_result.html", "guava", guava_model.CLASS_NAMES, predictions, image_url, lang)
    except FileNotFoundError as e:
        flash(str(e))
        return _back("guava_index", lang)
    except Exception as e:
        flash(i18n.translator(lang)("server.failed", error=e))
        return _back("guava_index", lang)


@app.route("/health")
def health():
    return {"status": "ok"}


i18n.register(app)  # Bangla routes (/bn/, /bn/guava) + template helpers


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
