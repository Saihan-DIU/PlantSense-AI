# Papaya Leaf Doctor

A Flask web app where farmers upload a papaya leaf photo and get an instant disease
diagnosis plus treatment instructions, powered by your trained Keras model.

Detects: Anthracnose of Papaya, Healthy Leaf, Mealybug Infestation, Papaya Black Spot,
Papaya Mosaic Virus (PMV), Papaya Ring Spot Virus (PRSV).

## Project structure

```
papaya-disease-app/
├── app.py                  # Flask app: upload, predict, render result
├── disease_info.py         # Class names + descriptions + treatment steps
├── requirements.txt
├── Procfile                 # For Render/Heroku-style start command
├── render.yaml               # Render "one click" blueprint config
├── model/
│   └── papaya_model.h5     # <-- YOU add this (see step 1 below)
├── notebook/
│   └── export_from_kaggle.py  # Instructions for exporting your Kaggle model
├── static/
│   ├── css/style.css
│   └── uploads/            # Uploaded images are temporarily saved here
└── templates/
    ├── base.html
    ├── index.html           # Upload page
    └── result.html          # Diagnosis result page
```

## Step 1 — Get your trained model out of Kaggle

At the end of your Kaggle training notebook, add:

```python
model.save("papaya_model.h5")
```

Then click **Save Version** on the notebook. Once it finishes, open that notebook
version's **Output** tab and download `papaya_model.h5`.

Also confirm two things from your notebook, since the web app needs to match them exactly:

1. **Class order** — print it and compare against `disease_info.py`'s `CLASS_NAMES` list:
   ```python
   print(train_ds.class_names)                 # image_dataset_from_directory
   # or
   print(train_generator.class_indices)          # ImageDataGenerator
   ```
   If the order differs, edit `CLASS_NAMES` in `disease_info.py` to match.

2. **Input image size** — the size you resized images to during training (e.g. 224x224,
   150x150). Update `IMG_SIZE` in `app.py` if it isn't 224x224.

Then place the downloaded file at `model/papaya_model.h5` in this project.

> If your model is PyTorch (`.pt`) or TFLite (`.tflite`) instead of Keras, say so and
> the loading code in `app.py` can be swapped accordingly — the rest of the app
> (routes, templates, disease info) stays the same.

## Step 2 — Run it locally

```bash
cd papaya-disease-app
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
python app.py
```

Open http://localhost:5000, upload a leaf photo, and confirm the prediction and
instructions look right.

## Step 3 — Put it on GitHub

```bash
git init
git add .
git commit -m "Papaya leaf disease detection web app"
git branch -M main
git remote add origin https://github.com/<your-username>/papaya-leaf-doctor.git
git push -u origin main
```

Your model file can be large — GitHub's normal file limit is 100MB. If `papaya_model.h5`
is under that, a normal push is fine. If it's larger, use
[Git LFS](https://git-lfs.com/) (`git lfs install && git lfs track "*.h5"`) before committing it.

## Step 4 — Deploy on Render (free)

1. Go to https://render.com and sign in with GitHub.
2. Click **New +** → **Web Service**, and pick your `papaya-leaf-doctor` repo.
3. Render should auto-detect `render.yaml`. If asked to confirm settings manually instead:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120`
   - **Instance Type:** Free
4. Click **Create Web Service**. The first build takes a few minutes (TensorFlow is a
   large dependency).
5. Once deployed, Render gives you a public URL like
   `https://papaya-leaf-doctor.onrender.com` — that's your live site.

### Notes about the free tier

- Free Render services **spin down after 15 minutes of inactivity** and take ~30-60s to
  wake back up on the next request — the first prediction after idle time will be slow.
- Free tier has 512MB RAM. `requirements.txt` uses plain `tensorflow` (not `tensorflow-cpu`,
  which has no Windows wheel and breaks local installs on Windows) — on Linux/Render it still
  installs CPU-only by default. If you hit memory errors on Render, consider converting your
  model to **TFLite** for a much lighter footprint — ask and this can be wired in.
- Uploaded images are saved to local disk (`static/uploads/`), which is **not persistent**
  on Render's free tier (it resets on redeploy/restart) — fine for this use case since we
  don't need to keep old uploads.

## Customizing disease info

Edit `disease_info.py` — each class has a `description` and a list of `instructions`
(treatment steps) shown on the result page. Feel free to refine the wording or add
region-specific advice.
