# PlantSense AI 🌱

**PlantSense AI** is an AI-powered plant disease detection web application that helps users identify crop diseases from leaf images.

Users can upload a plant leaf image and receive an AI-based disease diagnosis along with information about the disease, prevention methods, and recommended treatment guidance.

## ✨ Features

* 🌿 AI-powered plant disease detection
* 📷 Upload leaf images for diagnosis
* 🩺 Disease identification using a trained deep learning model
* 💡 Disease information and prevention guidance
* 💊 Treatment recommendations
* 📱 Simple and responsive web interface
* ⚡ Fast prediction through a Flask-based backend

## 🛠️ Technologies Used

* **Python**
* **Flask**
* **PyTorch**
* **timm** (PyTorch Image Models — MaxViT-Tiny and ConvNeXtV2 backbones)
* **OpenCV** (background removal for the guava leaf pipeline)
* **HTML5**
* **CSS3**
* **JavaScript**
* **Pillow**

## 📂 Project Structure

```text
PlantSense-AI/
├── app.py
├── disease_info.py              # papaya disease descriptions & treatment steps
├── guava_model.py                # ConvNeXtV2-SSA architecture + preprocessing
├── guava_disease_info.py        # guava disease descriptions & treatment steps
├── requirements.txt
├── Procfile
├── render.yaml
├── model/
│   ├── MaxViT-Tiny_seed_42_best.pth      # papaya model
│   └── convnextv2_ssa_Leaf_best.pt       # guava model
├── notebook/
│   └── export_from_kaggle.py
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── app.js
│   └── images/
│       └── logo.svg
└── templates/
    ├── base.html
    ├── index.html                # papaya upload page
    ├── result.html                # papaya diagnosis result
    ├── guava_index.html          # guava upload page
    └── guava_result.html         # guava diagnosis result
```

## 🚀 Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/Saihan-DIU/PlantSense-AI.git
cd PlantSense-AI
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

**Windows:**

```bash
venv\Scripts\activate
```

**Linux/macOS:**

```bash
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Add the trained models

Place both checkpoints in the `model/` directory:
* `MaxViT-Tiny_seed_42_best.pth` (papaya — filename must match `MODEL_PATH` in `app.py`)
* `convnextv2_ssa_Leaf_best.pt` (guava — filename must match `MODEL_PATH` in `guava_model.py`)

> **Important:** Each model's class order (`CLASS_NAMES` in `disease_info.py` / `guava_model.py`) must match the order used during training (alphabetical `ImageFolder` order, by default).

> **Note:** Both checkpoints are ~120 MB each, exceeding GitHub's 100 MB single-file push limit. Track them with [Git LFS](https://git-lfs.com/) before committing:
> ```bash
> git lfs install
> git lfs track "*.pth" "*.pt"
> ```

### 6. Run the application

```bash
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

## 🤖 Models

PlantSense AI currently supports two crops, each with its own dedicated model:

**Papaya** — **MaxViT-Tiny** (`maxvit_tiny_tf_224` from `timm`), a hybrid CNN/vision-transformer, fine-tuned to classify 6 papaya leaf conditions. **99.1% validation accuracy**. Input images are resized to 224×224 and normalized with standard ImageNet statistics before inference.

**Guava** — **ConvNeXtV2-Tiny + Separable Self-Attention** (a custom architecture: a `timm` ConvNeXtV2 backbone with two lightweight, linear-complexity attention blocks applied to the final feature map before pooling), fine-tuned to classify 6 guava leaf conditions. **99.8% test accuracy**. Before inference, the leaf is segmented out from its background (the model was trained on background-masked images to prevent background shortcut-learning), then resized/center-cropped to 224×224 and normalized with ImageNet statistics.

Tomato is shown in the crop selector as "Coming Soon."

The prediction pipeline performs:

```text
Leaf Image
    ↓
Image Preprocessing
    ↓
Deep Learning Model
    ↓
Disease Prediction
    ↓
Disease Information
    ↓
Prevention & Treatment Guidance
```

## 👨‍💻 Developer 

* **Md Saihan Alam**

## 📩 Contact

**Email:** [saihan.alam.bd@gmail.com](mailto:saihan.alam.bd@gmail.com)


## 🎯 Project Goal

The goal of PlantSense AI is to make plant disease identification more accessible by providing a simple AI-based tool that can assist farmers, students, researchers, and other users in identifying diseases from plant leaf images.

## ⚠️ Disclaimer

PlantSense AI provides AI-generated disease predictions and general agricultural information. The results should not be considered a substitute for professional agricultural advice or laboratory diagnosis.

## 📄 License

This project is intended for educational and research purposes.
