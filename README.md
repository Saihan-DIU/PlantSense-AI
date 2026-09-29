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
* **TensorFlow / Keras**
* **HTML5**
* **CSS3**
* **JavaScript**
* **NumPy**
* **Pillow**

## 📂 Project Structure

```text
PlantSense-AI/
├── app.py
├── disease_info.py
├── requirements.txt
├── Procfile
├── render.yaml
├── model/
│   └── trained_model.h5
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
    ├── index.html
    └── result.html
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

### 5. Add the trained model

Place the trained Keras model in the `model/` directory using the filename expected by `app.py`.

> **Important:** The model's class order and input image size must match the configuration used during training.

### 6. Run the application

```bash
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

## 🤖 Model

PlantSense AI uses a deep learning image-classification model trained to identify plant diseases from leaf images.

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
