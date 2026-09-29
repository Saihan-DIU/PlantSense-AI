import os
import uuid
from datetime import datetime

import numpy as np
from flask import Flask, render_template, request, url_for, flash, redirect
from PIL import Image
from werkzeug.utils import secure_filename

from disease_info import CLASS_NAMES, DISEASE_INFO

MODEL_PATH = os.path.join("model", "papaya_model.h5")
IMG_SIZE = (224, 224)  # change to match the input size your model was trained on
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


def get_model():
    """Load the Keras model lazily so the app can still start (and show a
    helpful error) even if the model file hasn't been added yet."""
    global _model
    if _model is None:
        from tensorflow.keras.models import load_model

        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Model file not found at '{MODEL_PATH}'. "
                "Export your trained model from Kaggle (model.save('papaya_model.h5')), "
                "download it, and place it in the model/ folder."
            )
        _model = load_model(MODEL_PATH)
    return _model


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def preprocess_image(image_path):
    img = Image.open(image_path).convert("RGB").resize(IMG_SIZE)
    arr = np.array(img, dtype=np.float32) / 255.0
    return np.expand_dims(arr, axis=0)


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
        model = get_model()
        batch = preprocess_image(save_path)
        predictions = model.predict(batch)[0]
        top_index = int(np.argmax(predictions))
        confidence = float(predictions[top_index]) * 100
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


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
