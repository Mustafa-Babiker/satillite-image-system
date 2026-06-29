from sentinelhub import (
    SentinelHubRequest,
    DataCollection,
    MimeType,
    CRS,
    BBox,
    SHConfig
)

import numpy as np
import random
import os
import cv2


# ==================================
# SENTINEL HUB
# ==================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_env_file():
    env_path = os.path.join(BASE_DIR, ".env")
    if not os.path.exists(env_path):
        return

    with open(env_path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


load_env_file()

config = SHConfig()
config.sh_client_id = os.environ.get("SH_CLIENT_ID") or os.environ.get("SENTINEL_HUB_CLIENT_ID")
config.sh_client_secret = os.environ.get("SH_CLIENT_SECRET") or os.environ.get("SENTINEL_HUB_CLIENT_SECRET")

if not config.sh_client_id or not config.sh_client_secret:
    raise RuntimeError("Missing Sentinel Hub credentials: set SH_CLIENT_ID and SH_CLIENT_SECRET environment variables.")


# ==================================
# DATASET FOLDERS
# ==================================

IMAGES_DIR = "dataset/train/images"
MASKS_DIR = "dataset/train/masks"

os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(MASKS_DIR, exist_ok=True)


# ==================================
# AGRICULTURAL REGIONS
# ==================================

REGIONS = [
    (33.0, 14.0, 33.8, 15.0),
    (35.5, 13.5, 36.8, 15.0),
    (33.8, 12.5, 34.8, 13.8),
    (31.5, 13.0, 33.0, 14.5)
]


# ==================================
# RANDOM BBOX
# ==================================

def random_bbox():
    region = random.choice(REGIONS)

    min_lon, min_lat, max_lon, max_lat = region

    lon = random.uniform(min_lon, max_lon)
    lat = random.uniform(min_lat, max_lat)

    size = 0.02

    return BBox(
        bbox=[lon, lat, lon + size, lat + size],
        crs=CRS.WGS84
    )


# ==================================
# DOWNLOAD IMAGE (4 BANDS ONLY)
# ==================================

def download_patch(bbox):

    request = SentinelHubRequest(

        evalscript="""
        //VERSION=3

        function setup() {
            return {
                input: ["B02","B03","B04","B08"],
                output: {
                    bands: 4,
                    sampleType: "FLOAT32"
                }
            };
        }

        function evaluatePixel(s) {
            return [
                s.B02,  // Blue
                s.B03,  // Green
                s.B04,  // Red
                s.B08   // NIR
            ];
        }
        """,

        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A,
                time_interval=("2025-01-01", "2025-12-31")
            )
        ],

        responses=[
            SentinelHubRequest.output_response("default", MimeType.TIFF)
        ],

        bbox=bbox,
        size=(512, 512),
        config=config
    )

    return request.get_data()[0]


# ==================================
# CREATE MASK (NDVI)
# ==================================

def create_mask(image):

    blue = image[:, :, 0]
    green = image[:, :, 1]
    red = image[:, :, 2]
    nir = image[:, :, 3]

    ndvi = (nir - red) / (nir + red + 1e-10)

    mask = (ndvi > 0.3).astype(np.uint8)

    kernel = np.ones((5, 5), np.uint8)

    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    return mask


# ==================================
# SAVE SAMPLE (IMPORTANT FIX)
# ==================================

def save_sample(index, image):

    # =========================
    # SAVE 4-BAND IMAGE (NO RGB)
    # =========================
    np.save(
        os.path.join(IMAGES_DIR, f"{index}.npy"),
        image.astype(np.float32)
    )

    # =========================
    # SAVE MASK
    # =========================
    mask = create_mask(image)

    np.save(
        os.path.join(MASKS_DIR, f"{index}.npy"),
        mask.astype(np.uint8)
    )


# ==================================
# GENERATE DATASET
# ==================================

NUM_IMAGES = 500

for i in range(1, NUM_IMAGES + 1):

    try:
        print(f"Downloading {i}/{NUM_IMAGES}")

        bbox = random_bbox()
        image = download_patch(bbox)

        save_sample(i, image)

    except Exception as e:
        print(f"Failed image {i}:", e)

print("Dataset Completed")