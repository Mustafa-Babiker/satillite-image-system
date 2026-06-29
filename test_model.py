import numpy as np
import matplotlib.pyplot as plt
import torch
import segmentation_models_pytorch as smp


# =========================
# 1. تحميل النموذج
# =========================
def load_model():

    model = smp.Unet(
        encoder_name="resnet34",
        encoder_weights=None,
        in_channels=4,
        classes=1
    )

    model.load_state_dict(torch.load("agri_unet.pth", map_location="cpu"))
    model.eval()
    return model


model = load_model()
print("Model loaded ")


# =========================
# 2. تحميل الصورة
# =========================

# لو npy استخدم:
img = np.load(r"dataset/train/images/290.npy").astype(np.float32)

mask_gt = np.load(r"dataset/train/masks/290.npy").astype(np.float32)


# =========================
# 3. تجهيز الصورة للنموذج
# =========================
img_norm = img * 0.0001
img_tensor = torch.tensor(img_norm).permute(2,0,1).unsqueeze(0)


# =========================
# 4. prediction
# =========================
with torch.no_grad():
    pred = model(img_tensor)
    pred = torch.sigmoid(pred).squeeze().numpy()


# =========================
# 5. استخراج RGB للعرض فقط
# =========================
rgb = img[:, :, :3]
rgb = rgb * 0.0001
rgb = np.clip(rgb * 3, 0, 1)   # تحسين الإضاءة


# =========================
# 6. العرض المقارن
# =========================
plt.figure(figsize=(15,5))

plt.subplot(1,3,1)
plt.title("Original Image")
plt.imshow(rgb)
plt.axis("off")

plt.subplot(1,3,2)
plt.title("Ground Truth Mask")
plt.imshow(mask_gt, cmap="gray")
plt.axis("off")

plt.subplot(1,3,3)
plt.title("Predicted Mask")
plt.imshow(pred, cmap="gray")
plt.axis("off")

plt.tight_layout()
plt.show()