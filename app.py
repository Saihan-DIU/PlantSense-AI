import os
import uuid
from datetime import datetime

import torch
import torch.nn.functional as F
from flask import Flask, render_template, request, url_for, flash, redirect
from PIL import Image
from werkzeug.utils import secure_filename

from disease_info import CLASS_NAMES, DISEASE_INFO
import guava_model
from guava_disease_info import DISEASE_INFO as GUAVA_DISEASE_INFO

MODEL_ARCH = "maxvit_tiny_tf_224"  # must match the architecture the .pth was trained with
MODEL_PATH = os.path.join("model", "MaxViT-Tiny_seed_42_best.pth")
UPLOAD_FOLDER = os.path.join("static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

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


@app.route("/predict", methods=["POST"])
def predict():
    if "leaf_image" not in request.files:
        flash("No file selected.")
        return redirect(url_for("index"))

    file = request.files["leaf_image"]

    if file.filename == "":
        flash("No file selected.")
        return redirect(url_for("index"))

    if not allowed_file(file.filename):
        flash("Unsupported file type. Please upload a PNG or JPG image.")
        return redirect(url_for("index"))

    filename = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
    file.save(save_path)

    try:
        model, transform = get_model_and_transform()
        batch = preprocess_image(save_path, transform)

        with torch.no_grad():
            logits = model(batch)[0]
            predictions = F.softmax(logits, dim=0)

        top_index = int(torch.argmax(predictions).item())
        confidence = float(predictions[top_index].item()) * 100
        predicted_class = CLASS_NAMES[top_index]
        info = DISEASE_INFO.get(predicted_class, {})

        ranked = sorted(
            zip(CLASS_NAMES, predictions.tolist()), key=lambda x: x[1], reverse=True
        )[:3]

        return render_template(
            "result.html",
            image_url=url_for("static", filename=f"uploads/{unique_name}"),
            predicted_class=predicted_class,
            confidence=round(confidence, 2),
            description=info.get("description", ""),
            instructions=info.get("instructions", []),
            is_healthy=info.get("is_healthy", False),
            ranked=[(name, round(prob * 100, 2)) for name, prob in ranked],
        )
    except FileNotFoundError as e:
        flash(str(e))
        return redirect(url_for("index"))
    except Exception as e:
        flash(f"Something went wrong while analyzing the image: {e}")
        return redirect(url_for("index"))


@app.route("/guava", methods=["GET"])
def guava_index():
    return render_template("guava_index.html")


@app.route("/guava/predict", methods=["POST"])
def guava_predict():
    if "leaf_image" not in request.files:
        flash("No file selected.")
        return redirect(url_for("guava_index"))

    file = request.files["leaf_image"]

    if file.filename == "":
        flash("No file selected.")
        return redirect(url_for("guava_index"))

    if not allowed_file(file.filename):
        flash("Unsupported file type. Please upload a PNG or JPG image.")
        return redirect(url_for("guava_index"))

    filename = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
    file.save(save_path)

    try:
        model = guava_model.get_model()
        batch = guava_model.preprocess_image(save_path)

        with torch.no_grad():
            logits = model(batch)[0]
            predictions = F.softmax(logits, dim=0)

        top_index = int(torch.argmax(predictions).item())
        confidence = float(predictions[top_index].item()) * 100
        predicted_class = guava_model.CLASS_NAMES[top_index]
        info = GUAVA_DISEASE_INFO.get(predicted_class, {})

        ranked = sorted(
            zip(guava_model.CLASS_NAMES, predictions.tolist()), key=lambda x: x[1], reverse=True
        )[:3]

        return render_template(
            "guava_result.html",
            image_url=url_for("static", filename=f"uploads/{unique_name}"),
            predicted_class=predicted_class.replace("_", " "),
            confidence=round(confidence, 2),
            description=info.get("description", ""),
            instructions=info.get("instructions", []),
            is_healthy=info.get("is_healthy", False),
            ranked=[(name.replace("_", " "), round(prob * 100, 2)) for name, prob in ranked],
        )
    except FileNotFoundError as e:
        flash(str(e))
        return redirect(url_for("guava_index"))
    except Exception as e:
        flash(f"Something went wrong while analyzing the image: {e}")
        return redirect(url_for("guava_index"))


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
