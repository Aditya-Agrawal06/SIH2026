import tempfile
from pathlib import Path

import cv2
import streamlit as st
from ultralytics import YOLO

# Put your clip here (relative to wherever you run `streamlit run app/dashboard.py`
# from — i.e. the project root), or just use the in-app uploader instead.
DEFAULT_VIDEO_PATH = "assets/flood_clip.mp4"

VEHICLE_CLASS_IDS = {2, 3, 5, 7}  # COCO: car, motorcycle, bus, truck
CLASS_NAMES = {2: "car", 3: "motorbike", 5: "bus", 7: "truck"}

CRITICAL_DEPTH_M = 0.50           # commonly cited safe wading depth for passenger vehicles
BASELINE_VISIBLE_RATIO = 0.60     # typical DRY side-view bbox height / width ratio
ASSUMED_VEHICLE_HEIGHT_M = 1.5    # side-view reference height, typical sedan
MAX_FRAMES = 450                  # safety cap so a long clip can't hang the demo


@st.cache_resource(show_spinner="Loading YOLOv8n model…")
def load_model() -> YOLO:
    # Auto-downloads yolov8n.pt on first run (needs internet once). Run this
    # locally before an offline demo so the weights are already cached.
    return YOLO("yolov8n.pt")


def _draw_box(frame, box, color, label) -> None:
    x1, y1, x2, y2 = [int(v) for v in box]
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    cv2.putText(frame, label, (x1, max(20, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)


def _analyse_frame(model, frame, frac_threshold, baseline_ratio, vehicle_height_m):
    """Run YOLOv8 on one frame, pick the largest detected vehicle as the
    'reference ruler', and estimate submersion from how compressed / how low
    its bounding box is versus a typical dry-road vehicle."""
    h, _w = frame.shape[:2]
    results = model.predict(frame, conf=0.35, classes=list(VEHICLE_CLASS_IDS), verbose=False)
    boxes = results[0].boxes

    best, best_area = None, 0.0
    for b in boxes:
        x1, y1, x2, y2 = b.xyxy[0].tolist()
        area = (x2 - x1) * (y2 - y1)
        if area > best_area:
            best_area = area
            best = (x1, y1, x2, y2, float(b.conf[0]), int(b.cls[0]))

    # Draw every detection in green first.
    for b in boxes:
        x1, y1, x2, y2 = b.xyxy[0].tolist()
        conf, cls_id = float(b.conf[0]), int(b.cls[0])
        _draw_box(frame, (x1, y1, x2, y2), (0, 200, 0), f"{CLASS_NAMES.get(cls_id, 'vehicle')} {conf:.0%}")

    if best is None:
        return frame, None

    x1, y1, x2, y2, conf, cls_id = best
    box_h, box_w = y2 - y1, max(1.0, x2 - x1)
    bottom_frac = y2 / h
    visible_ratio = box_h / box_w
    submersion_frac = max(0.0, min(1.0, (baseline_ratio - visible_ratio) / baseline_ratio))
    est_depth_m = round(submersion_frac * vehicle_height_m, 2)
    alert = est_depth_m >= CRITICAL_DEPTH_M or bottom_frac >= frac_threshold

    # Re-draw the primary (largest) vehicle on top, in alert color if tripped.
    color = (0, 0, 255) if alert else (0, 200, 0)
    label = f"{CLASS_NAMES.get(cls_id, 'vehicle')} {conf:.0%}" + (" — SUBMERGED?" if alert else "")
    _draw_box(frame, (x1, y1, x2, y2), color, label)
    if alert:
        cv2.putText(frame, "WATER LEVEL ALERT", (12, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    return frame, {
        "bottom_frac": bottom_frac,
        "visible_ratio": visible_ratio,
        "est_depth_m": est_depth_m,
        "alert": alert,
    }


def render_cctv_tab() -> None:
    st.markdown("#### CCTV Virtual Sensor · Ultralytics YOLOv8")
    st.caption(
        "Runs a real YOLOv8n model on the uploaded footage, tracks the largest detected "
        "vehicle each frame, and treats it as a reference 'ruler': a bounding box that's "
        "shorter and lower than a typical dry-road car suggests its lower body is underwater. "
        "This proxy — vehicles as reference objects — mirrors published CCTV flood-depth "
        "research; it isn't a lab-grade depth sensor, but it's a genuine zero-extra-hardware signal."
    )

    col_feed, col_stats = st.columns([2, 1], gap="large")

    with col_stats:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("**Source clip**")
        uploaded = st.file_uploader("Upload a clip (or use the bundled sample)", type=["mp4", "mov", "avi"])
        bottom_pct = st.slider("Alert zone — bottom __% of frame", 10, 50, 20, step=5, key="cctv_bottom_pct")
        run_cv = st.checkbox("▶ Run YOLOv8 on this clip", value=False, key="cctv_running")
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("")

        with st.expander("Advanced calibration"):
            baseline_ratio = st.slider(
                "Dry baseline height/width ratio", 0.30, 1.00, BASELINE_VISIBLE_RATIO, 0.05,
                help="Lower this if your reference vehicle is naturally 'longer and lower' (e.g. a sedan vs. an SUV).",
            )
            vehicle_height = st.slider(
                "Assumed vehicle height (m)", 1.0, 2.5, ASSUMED_VEHICLE_HEIGHT_M, 0.1,
                help="Real-world height of the vehicle type in your clip.",
            )

        depth_placeholder = st.empty()
        status_placeholder = st.empty()
        detail_placeholder = st.empty()

        with st.expander("How this virtual sensor works"):
            st.write(
                "YOLOv8n (pretrained — no custom training needed) detects vehicles frame by "
                "frame. We take the largest detected vehicle and compare its bounding-box "
                "height-to-width ratio against a typical dry side-view ratio. A shorter-than-"
                "expected box suggests the lower body is occluded by water; combined with how "
                "close the box sits to the bottom of frame, this drives the estimate and alert."
            )

    frac_threshold = 1 - bottom_pct / 100.0

    video_path = None
    if uploaded is not None:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded.name).suffix or ".mp4")
        tmp.write(uploaded.read())
        tmp.flush()
        video_path = tmp.name
    elif Path(DEFAULT_VIDEO_PATH).exists():
        video_path = DEFAULT_VIDEO_PATH

    with col_feed:
        frame_placeholder = st.empty()

        if not run_cv:
            frame_placeholder.info("Tick '▶ Run YOLOv8 on this clip' to start detection.")
            return

        if video_path is None:
            frame_placeholder.warning(
                f"No video found. Place your clip at `{DEFAULT_VIDEO_PATH}` in the project "
                "folder (run Streamlit from the project root), or upload one on the right."
            )
            return

        model = load_model()
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            frame_placeholder.error("Could not open that video file.")
            return

        frame_count = 0
        while frame_count < MAX_FRAMES:
            ok, frame = cap.read()
            if not ok:
                break
            frame_count += 1

            h, w = frame.shape[:2]
            if w > 640:
                scale = 640 / w
                frame = cv2.resize(frame, (640, int(h * scale)))

            annotated, metrics = _analyse_frame(model, frame, frac_threshold, baseline_ratio, vehicle_height)
            frame_placeholder.image(annotated, channels="BGR", use_container_width=True)

            if metrics is None:
                depth_placeholder.metric("Measured water depth (heuristic)", "—")
                status_placeholder.info("Scanning — no vehicle detected in this frame.")
                detail_placeholder.empty()
            else:
                depth_placeholder.metric("Measured water depth (heuristic)", f"{metrics['est_depth_m']} m")
                if metrics["alert"]:
                    status_placeholder.error("🚨 WATER LEVEL ALERT — vehicle bounding box indicates submersion.")
                else:
                    status_placeholder.success("✅ Vehicle tracking normally — no submersion signal.")
                detail_placeholder.caption(
                    f"Box bottom at {metrics['bottom_frac']:.0%} of frame height · "
                    f"height/width ratio {metrics['visible_ratio']:.2f} (dry baseline ≈ {baseline_ratio:.2f})"
                )

        cap.release()
