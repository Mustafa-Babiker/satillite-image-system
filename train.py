import torch
from torch.utils.data import DataLoader
import segmentation_models_pytorch as smp

from dataset import AgricultureDataset
from model import build_model


def train():

    print("========== TRAINING STARTED ==========")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("Device:", device)

    dataset = AgricultureDataset(
        img_dir=r"c:\Users\Mustafa Babiker\Desktop\satillite image system\the system\dataset\train\images",
        mask_dir=r"c:\Users\Mustafa Babiker\Desktop\satillite image system\the system\dataset\train\masks"
    )

    print("Dataset size:", len(dataset))

    # اختبار أول عينة
    x0, y0 = dataset[0]

    print("First image shape:", x0.shape)
    print("First mask shape :", y0.shape)
    print("Image dtype      :", x0.dtype)
    print("Mask dtype       :", y0.dtype)

    loader = DataLoader(
        dataset,
        batch_size=2,
        shuffle=True,
        num_workers=0,
        pin_memory=False
    )

    print("DataLoader created")

    model = build_model().to(device)

    print("Model loaded")
    print(model.__class__.__name__)

    dice = smp.losses.DiceLoss(mode="binary")
    bce = torch.nn.BCEWithLogitsLoss()

    def loss_fn(pred, target):
        return dice(pred, target) + bce(pred, target)

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=1e-4
    )

    epochs = 5

    print("Starting training loop...")

    for epoch in range(epochs):

        print(f"\n===== Epoch {epoch + 1}/{epochs} =====")

        model.train()

        total_loss = 0

        for batch_idx, (x, y) in enumerate(loader):

            if batch_idx == 0:
                print("First batch loaded")
                print("Batch image shape:", x.shape)
                print("Batch mask shape :", y.shape)

            x = x.to(device)
            y = y.to(device)

            pred = model(x)

            loss = loss_fn(pred, y)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

            if batch_idx % 10 == 0:
                print(
                    f"Epoch {epoch+1} | Batch {batch_idx}/{len(loader)} | Loss {loss.item():.4f}"
                )

        avg_loss = total_loss / len(loader)

        print(
            f"Epoch {epoch+1}/{epochs} completed | Average Loss = {avg_loss:.4f}"
        )

    torch.save(
        model.state_dict(),
        "agri_unet.pth"
    )

    print("\nModel saved: agri_unet.pth")
    print("========== TRAINING FINISHED ==========")


if __name__ == "__main__":
    train()