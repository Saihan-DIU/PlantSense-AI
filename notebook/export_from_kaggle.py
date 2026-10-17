"""
Notes on the trained checkpoint used by this app.

The current model (model/MaxViT-Tiny_seed_42_best.pth) is a PyTorch checkpoint
trained with timm's `maxvit_tiny_tf_224` architecture, saved as a dict:

    {
        "epoch": ..., "epochs_total": ..., "run_signature": ...,
        "model_state_dict": <state_dict>,
        "train_loss": ..., "train_acc": ..., "val_loss": ..., "val_acc": ...,
        "history": {...},
    }

app.py loads it with:

    import timm
    model = timm.create_model("maxvit_tiny_tf_224", pretrained=False, num_classes=6)
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)

If you retrain or fine-tune a new checkpoint, save it the same way so app.py
doesn't need changes:

    torch.save({
        "epoch": epoch,
        "epochs_total": total_epochs,
        "model_state_dict": model.state_dict(),
        "train_loss": train_loss, "train_acc": train_acc,
        "val_loss": val_loss, "val_acc": val_acc,
        "history": history,
    }, "MaxViT-Tiny_seed_42_best.pth")

IMPORTANT — class order:
CLASS_NAMES in disease_info.py must exactly match the class order your training
dataloader used (typically alphabetical folder order, e.g. torchvision's
ImageFolder). If you retrain with a different dataset/folder layout, print
`dataset.classes` (ImageFolder) and update CLASS_NAMES to match.

Then copy the new checkpoint into: model/<your-filename>.pth
and update MODEL_PATH in app.py to match the filename.
"""
