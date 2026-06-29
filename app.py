from flask import Flask, request, jsonify, render_template, redirect, session
import psycopg2
import bcrypt
from sentinelhub import SentinelHubRequest, DataCollection, MimeType, BBox, CRS, SHConfig

from PIL import Image
import numpy as np
import os
import time
import urllib.request
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import torch
import segmentation_models_pytorch as smp

app = Flask(__name__)

# FOLDERS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_FOLDER = os.path.join(BASE_DIR, "static", "results")
STATIC_RESULTS_PATH = "static/results"
MODEL_PATH = os.path.join(BASE_DIR, "agri_unet.pth")
MODEL_URL = os.environ.get("MODEL_URL")
os.makedirs(RESULTS_FOLDER, exist_ok=True)


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

# Use environment variable for Flask secret key (do not commit secrets)
app.secret_key = os.environ.get("SECRET_KEY", "change_me")

# Database

def get_connection():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        database=os.environ.get("DB_NAME", "agriculture_system"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASSWORD", "m")
    )



# SENTINEL CONFIG

DEFAULT_SH_CLIENT_ID = "5418b19c-c3ef-4ca5-ad90-c7a07db91a00"
DEFAULT_SH_CLIENT_SECRET = "ltsA3OD82aKbZoflYQC5LAX527jJ0pUF"
config = SHConfig()
config.sh_client_id = os.environ.get("SH_CLIENT_ID") or os.environ.get("SENTINEL_HUB_CLIENT_ID") or DEFAULT_SH_CLIENT_ID
config.sh_client_secret = os.environ.get("SH_CLIENT_SECRET") or os.environ.get("SENTINEL_HUB_CLIENT_SECRET") or DEFAULT_SH_CLIENT_SECRET



# MODEL

def ensure_model_available():
    if os.path.exists(MODEL_PATH):
        return MODEL_PATH

    if MODEL_URL:
        print(f"Model not found locally. Downloading from {MODEL_URL}")
        try:
            urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
            if os.path.exists(MODEL_PATH):
                return MODEL_PATH
        except Exception as exc:
            print(f"Failed to download model: {exc}")

    return None


def load_model():
    model = smp.Unet(
        encoder_name="resnet34",
        encoder_weights=None,
        in_channels=4,
        classes=1,
        activation=None
    )

    model_path = ensure_model_available()
    if not model_path:
        print("Model file not found and no MODEL_URL was provided. The app will run without segmentation.")
        return None

    state_dict = torch.load(model_path, map_location="cpu")
    model.load_state_dict(state_dict)

    model.eval()
    print("Model loaded")

    return model


model = None


def get_model():
    global model
    if model is None:
        model = load_model()
    return model

#satellite image preprocessing

def preprocess(image):

    image = image.astype(np.float32)
    image = image / 10000.0
    image = np.clip(image, 0, 1)

    image = np.transpose(image, (2, 0, 1))  # HWC → CHW

    return torch.tensor(image).unsqueeze(0).float()


#flask main

@app.route("/")
def login_page():
    return render_template("login.html")

@app.route("/create-account")
def create_account():
    return render_template("register.html")

@app.route("/register", methods=["POST"])
def register():

    first_name = request.form["first_name"]
    last_name = request.form["last_name"]
    email = request.form["email"]
    password = request.form["password"]
    confirm_password = request.form["confirm_password"]

    if password != confirm_password:
        return "Passwords do not match"

    conn = get_connection()
    cur = conn.cursor()

  
    cur.execute(
        "SELECT id FROM users WHERE email=%s",
        (email,)
    )

    if cur.fetchone():

        cur.close()
        conn.close()

        return "Email already exists"

    hashed = bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    )

    cur.execute(
        """
        INSERT INTO users
        (
            first_name,
            last_name,
            email,
            password
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s
        )
        RETURNING id
        """,
        (
            first_name,
            last_name,
            email,
            hashed.decode()
        )
    )

    user_id = cur.fetchone()[0]

    conn.commit()

    cur.close()
    conn.close()

    session["user_id"] = user_id
    session["email"] = email
    session["first_name"] = first_name

    return redirect("/")

@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
SELECT
    id,
    email,
    password,
    is_admin
FROM users
WHERE email=%s
""",(email,))
    user = cur.fetchone()

    cur.close()
    conn.close()

    if user and bcrypt.checkpw(password.encode(), user[2].encode()):
        session["user_id"] = user[0]
        session["email"] = user[1]
        session["is_admin"] = user[3]
        if user[3]:
            return redirect("/admin")
        return redirect("/system")

    return "Invalid Login"

@app.route("/admin")
def admin():

    if "user_id" not in session:
        return redirect("/")
    if not session.get("is_admin"):
        return "Access Denied", 403

    conn = get_connection()
    cur = conn.cursor()

  
    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]


    cur.execute("SELECT COUNT(*) FROM analysis")
    total_analysis = cur.fetchone()[0]


    cur.execute("SELECT created_at FROM analysis ORDER BY created_at DESC LIMIT 1")
    latest = cur.fetchone()
    latest_analysis = latest[0] if latest else "لا يوجد"


    cur.execute("""
        SELECT 
            u.id,
            u.first_name,
            u.last_name,
            u.email,
            COUNT(a.id) AS analysis_count
        FROM users u
        LEFT JOIN analysis a ON u.id = a.user_id
        GROUP BY u.id
        ORDER BY u.id
    """)

    columns = [desc[0] for desc in cur.description]
    users = [dict(zip(columns, row)) for row in cur.fetchall()]

    cur.close()
    conn.close()

    return render_template(
        "admin.html",
        users=users,
        total_users=total_users,
        total_analysis=total_analysis,
        latest_analysis=latest_analysis
    )
@app.route("/admin/user/<int:user_id>")
def user_details(user_id):

    if not session.get("is_admin"):
        return "Access Denied", 403

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, first_name, last_name, email
        FROM users
        WHERE id=%s
    """, (user_id,))
    user = cur.fetchone()

    cur.execute("""
        SELECT 
            id,
            healthy_pixels,
            medium_pixels,
            damaged_pixels,
            ndvi_min,
            ndvi_max,
            created_at,
            original_image,
            health_map
        FROM analysis
        WHERE user_id=%s
        ORDER BY created_at DESC
    """, (user_id,))

    analyses = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "user_details.html",
        user=user,
        analyses=analyses
    )


@app.route("/system")
def system():
    if "user_id" not in session:
        return redirect("/")
    return render_template("index.html")


#download satellite image, analyze it, and save results

@app.route("/download", methods=["POST"])
def analyze():

    if "user_id" not in session:
        return jsonify({"error": "not logged in"})

    try:
        data = request.json
        bbox = BBox(data["bbox"], crs=CRS.WGS84)

        request_sentinel = SentinelHubRequest(
            evalscript="""
            //VERSION=3
            function setup(){
                return {
                    input:["B02","B03","B04","B08"],
                    output:{bands:4,sampleType:"FLOAT32"}
                };
            }
            function evaluatePixel(s){
                return [s.B02,s.B03,s.B04,s.B08];
            }
            """,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DataCollection.SENTINEL2_L2A,
                    time_interval=("2026-06-01","2026-06-30")
                )
            ],
            responses=[
                SentinelHubRequest.output_response(
                    "default",
                    MimeType.TIFF
                )
            ],
            bbox=bbox,
            size=(512, 512),
            config=config
        )

        satellite = request_sentinel.get_data()[0]

        timestamp = int(time.time())
        user_id = session["user_id"]

#show the RGB image of the satellite image

        blue = satellite[:, :, 0]
        green = satellite[:, :, 1]
        red = satellite[:, :, 2]
        nir = satellite[:, :, 3]

        rgb = np.stack(
            [red, green, blue],
            axis=-1
        )

        rgb = np.clip(
            rgb * 255,
            0,
            255
        ).astype(np.uint8)

        rgb_filename = f"{user_id}_{timestamp}_rgb.png"
        rgb_path = os.path.join(STATIC_RESULTS_PATH, rgb_filename)
        rgb_full_path = os.path.join(RESULTS_FOLDER, rgb_filename)

        Image.fromarray(rgb).save(rgb_full_path)
        # Image.fromarray(rgb).save(rgb_path)

#model prediction for segmentation mask

        tensor = preprocess(satellite)

        seg_model = get_model()
        if seg_model is not None:
            with torch.no_grad():
                output = seg_model(tensor)
                prob = torch.sigmoid(output)
                mask = (
                    prob.squeeze().cpu().numpy() > 0.5
                ).astype(np.uint8)
        else:
            mask = np.zeros((rgb.shape[0], rgb.shape[1]), dtype=np.uint8)

#saving the mask image

        mask_filename = f"{user_id}_{timestamp}_mask.png"
        mask_path = os.path.join(STATIC_RESULTS_PATH, mask_filename)
        mask_full_path = os.path.join(RESULTS_FOLDER, mask_filename)

        plt.figure(figsize=(6, 6))
        plt.imshow(mask, cmap="gray")
        plt.axis("off")
        plt.savefig(mask_full_path, bbox_inches="tight", pad_inches=0)
        plt.close()

# NDVI in the masked area

        ndvi = (
            (nir - red)
            /
            (nir + red + 1e-10)
        )

        valid = mask == 1

        healthy = np.sum(
            (ndvi >= 0.5) & valid
        )

        medium = np.sum(
            (ndvi >= 0.2)
            &
            (ndvi < 0.5)
            &
            valid
        )

        damaged = np.sum(
            (ndvi < 0.2)
            &
            valid
        )


#plotting the NDVI overlay on the original RGB image

        overlay = rgb.copy().astype(np.float32)

        healthy_mask = (
            (ndvi >= 0.5)
            &
            valid
        )

        overlay[healthy_mask] = (
            overlay[healthy_mask] * 0.4
            +
            np.array([0, 255, 0]) * 0.6
        )

        medium_mask = (
            (ndvi >= 0.2)
            &
            (ndvi < 0.5)
            &
            valid
        )

        overlay[medium_mask] = (
            overlay[medium_mask] * 0.4
            +
            np.array([255, 255, 0]) * 0.6
        )

        damaged_mask = (
            (ndvi < 0.2)
            &
            valid
        )

        overlay[damaged_mask] = (
            overlay[damaged_mask] * 0.4
            +
            np.array([255, 0, 0]) * 0.6
        )

        overlay = np.clip(
            overlay,
            0,
            255
        ).astype(np.uint8)

        ndvi_filename = f"{user_id}_{timestamp}_ndvi.png"
        ndvi_path = os.path.join(STATIC_RESULTS_PATH, ndvi_filename)
        ndvi_full_path = os.path.join(RESULTS_FOLDER, ndvi_filename)

        Image.fromarray(overlay).save(ndvi_full_path)
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
    INSERT INTO analysis (
        user_id,
        healthy_pixels,
        medium_pixels,
        damaged_pixels,
        ndvi_min,
        ndvi_max,
        original_image,
        health_map,
        created_at
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,NOW())
""", (
    user_id,
    int(healthy),
    int(medium),
    int(damaged),
    float(np.min(ndvi)),
    float(np.max(ndvi)),
    rgb_path,
    ndvi_path
))

        conn.commit()
        cur.close()
        conn.close()

        # Image.fromarray(
        #     overlay
        # ).save(ndvi_path)

#displaying the results in the session for the result page

        session["result"] = {
            "healthy": int(healthy),
            "medium": int(medium),
            "damaged": int(damaged),
            "original": os.path.basename(rgb_path),
            "ndvi": os.path.basename(ndvi_path),
            "mask": os.path.basename(mask_path)
        }
        
    
        return redirect("/result")
    
    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": str(e)})
    
@app.route("/result")
def result():
    data = session.get("result", {})
    return render_template(
        "result.html",
        healthy=data.get("healthy", 0),
        medium=data.get("medium", 0),
        damaged=data.get("damaged", 0),
        original=data.get("original", ""),
        ndvi=data.get("ndvi", ""),
        mask=data.get("mask", "")
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)