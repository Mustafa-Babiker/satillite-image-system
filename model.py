import segmentation_models_pytorch as smp


def build_model():

    model = smp.Unet(
        encoder_name="resnet34",
        encoder_weights="imagenet",
        in_channels=4,
        classes=1,
        activation=None
    )

    return model