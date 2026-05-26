from PIL import Image

image = Image.open("assets/img/logo.png")
image.save(
    "assets/logo.ico",
    sizes=[
        (16, 16),
        (32, 32),
        (48, 48),
        (64, 64),
        (128, 128),
        (256, 256),
    ],
)