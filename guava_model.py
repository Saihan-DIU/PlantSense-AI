"""
Guava leaf disease model: ConvNeXtV2 backbone + Separable Self-Attention (SSA).

Architecture and preprocessing are copied exactly from the training notebook
(01_convnextv2_separable_attention.ipynb) so the checkpoint loads with
strict=True and inference matches what the model was evaluated on
(99.8% test accuracy, 487 test images).
"""
import os

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import timm
from PIL import Image

IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)
IMG_SIZE = 224
BACKBONE_NAME = "convnextv2_tiny.fcmae_ft_in22k_in1k"
MODEL_PATH = os.path.join("model", "convnextv2_ssa_Leaf_best.pt")

CLASS_NAMES = [
    "Anthracnose",
    "Dried",
    "Healthy",
    "Insect_Infestation",
    "Senescence",
    "Sooty_Mould",
]


class SeparableSelfAttention(nn.Module):
    """Linear-complexity self-attention (MobileViTv2-style): a single softmax
    over per-token context scores replaces the O(N^2) token-token attention
    matrix, so it stays cheap even on high-resolution conv feature maps."""

    def __init__(self, dim, attn_drop=0.1):
        super().__init__()
        self.qkv_proj = nn.Conv2d(dim, 1 + 2 * dim, kernel_size=1, bias=True)
        self.out_proj = nn.Conv2d(dim, dim, kernel_size=1, bias=True)
        self.drop = nn.Dropout(attn_drop)
        self.dim = dim

    def forward(self, x):
        B, C, H, W = x.shape
        qkv = self.qkv_proj(x)
        q_score, k, v = torch.split(qkv, [1, self.dim, self.dim], dim=1)
        context_scores = F.softmax(q_score.flatten(2), dim=-1)
        k_flat = k.flatten(2)
        context_vector = (k_flat * context_scores).sum(-1, keepdim=True)
        context_vector = self.drop(context_vector)
        v_flat = v.flatten(2)
        out = F.relu(v_flat) * context_vector
        out = out.reshape(B, C, H, W)
        return self.out_proj(out)


class ConvNeXtV2SSA(nn.Module):
    def __init__(self, num_classes, backbone_name=BACKBONE_NAME, pretrained=False):
        super().__init__()
        self.backbone = timm.create_model(backbone_name, pretrained=pretrained, features_only=True)
        feat_dim = self.backbone.feature_info.channels()[-1]
        self.ssa1 = SeparableSelfAttention(feat_dim)
        self.norm1 = nn.GroupNorm(1, feat_dim)
        self.ssa2 = SeparableSelfAttention(feat_dim)
        self.norm2 = nn.GroupNorm(1, feat_dim)
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.head = nn.Sequential(
            nn.Flatten(), nn.LayerNorm(feat_dim), nn.Dropout(0.3),
            nn.Linear(feat_dim, num_classes),
        )

    def forward(self, x):
        feat = self.backbone(x)[-1]
        feat = feat + self.ssa1(self.norm1(feat))
        feat = feat + self.ssa2(self.norm2(feat))
        feat = self.pool(feat)
        return self.head(feat)


def remove_background(img_rgb, fill=(124, 116, 104), margin=0.06, work=256, max_side=512):
    """Foreground (leaf) extraction on plain capture backgrounds, copied verbatim
    from the training notebook so inference matches training preprocessing
    (the Leaf model was trained on background-masked images)."""
    h0, w0 = img_rgb.shape[:2]
    if max(h0, w0) > max_side:
        s0 = max_side / max(h0, w0)
        img_rgb = cv2.resize(img_rgb, (int(w0 * s0), int(h0 * s0)), interpolation=cv2.INTER_AREA)
    h, w = img_rgb.shape[:2]
    small = cv2.resize(img_rgb, (work, work), interpolation=cv2.INTER_AREA)
    lab = cv2.cvtColor(small, cv2.COLOR_RGB2LAB).astype(np.float32)
    k = max(4, int(work * 0.05))
    ring = np.concatenate([lab[:k].reshape(-1, 3), lab[-k:].reshape(-1, 3),
                           lab[:, :k].reshape(-1, 3), lab[:, -k:].reshape(-1, 3)])
    bg = np.median(ring, axis=0)
    dist = np.linalg.norm(lab - bg, axis=2)
    dist_u8 = np.clip(dist / (dist.max() + 1e-6) * 255, 0, 255).astype(np.uint8)
    dist_u8 = cv2.GaussianBlur(dist_u8, (5, 5), 0)
    thr, mask = cv2.threshold(dist_u8, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    n, comp, stats, _ = cv2.connectedComponentsWithStats(mask)
    if n > 1:
        keep = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        mask = np.where(comp == keep, 255, 0).astype(np.uint8)
    inv = cv2.bitwise_not(mask)
    ff = inv.copy()
    fm = np.zeros((work + 2, work + 2), np.uint8)
    cv2.floodFill(ff, fm, (0, 0), 0)
    mask = mask | ff
    area = mask.mean() / 255.0
    if area < 0.04 or area > 0.97:  # segmentation failed -> keep original
        return img_rgb, None, area
    mask_full = cv2.resize(mask, (w, h), interpolation=cv2.INTER_LINEAR)
    mask_full = cv2.GaussianBlur(mask_full, (5, 5), 0)
    ys, xs = np.where(mask_full > 127)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    pad = int(margin * max(y1 - y0, x1 - x0))
    y0, x0 = max(0, y0 - pad), max(0, x0 - pad)
    y1, x1 = min(h, y1 + pad), min(w, x1 + pad)
    alpha = (mask_full.astype(np.float32) / 255.0)[..., None]
    out = img_rgb.astype(np.float32) * alpha + np.array(fill, np.float32) * (1 - alpha)
    out = out[y0:y1, x0:x1].astype(np.uint8)
    hh, ww = out.shape[:2]
    s = max(hh, ww)
    canvas = np.empty((s, s, 3), np.uint8)
    canvas[:] = fill
    canvas[(s - hh) // 2:(s - hh) // 2 + hh, (s - ww) // 2:(s - ww) // 2 + ww] = out
    return canvas, mask_full, area


_model = None


def get_model():
    """Load the ConvNeXtV2-SSA model lazily so the app can still start (and
    show a helpful error) even if the checkpoint hasn't been added yet."""
    global _model
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Guava model file not found at '{MODEL_PATH}'. "
                "Copy convnextv2_ssa_Leaf_best.pt into the model/ folder."
            )
        state_dict = torch.load(MODEL_PATH, map_location="cpu", weights_only=False)
        model = ConvNeXtV2SSA(num_classes=len(CLASS_NAMES))
        model.load_state_dict(state_dict, strict=True)
        model.eval()
        _model = model
    return _model


def preprocess_image(image_path):
    """Mirrors build_eval_transform(IMG_SIZE) from the training notebook:
    background removal -> resize(1.14x) -> center crop -> normalize."""
    pil_img = Image.open(image_path).convert("RGB")
    img_rgb = np.array(pil_img)

    masked, _, _ = remove_background(img_rgb)
    masked_pil = Image.fromarray(masked)

    resize_to = int(IMG_SIZE * 1.14)
    resized = masked_pil.resize((resize_to, resize_to), Image.BILINEAR)

    left = (resize_to - IMG_SIZE) // 2
    top = (resize_to - IMG_SIZE) // 2
    cropped = resized.crop((left, top, left + IMG_SIZE, top + IMG_SIZE))

    arr = np.asarray(cropped, dtype=np.float32) / 255.0
    mean = np.array(IMAGENET_MEAN, dtype=np.float32)
    std = np.array(IMAGENET_STD, dtype=np.float32)
    arr = (arr - mean) / std

    tensor = torch.from_numpy(arr.transpose(2, 0, 1)).unsqueeze(0).float()
    return tensor
