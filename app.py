import os
import cv2
import time
import base64
import threading
import numpy as np

from flask import Flask, render_template, request, jsonify


# =========================================================
# VISIONTRACK AI - LIGHTWEIGHT RENDER VERSION
# =========================================================

app = Flask(__name__)

PORT = int(os.environ.get("PORT", 10000))

PROCESS_WIDTH = 640
PROCESS_HEIGHT = 360

UPLOAD_FOLDER = "uploads"
EVIDENCE_FOLDER = "evidence"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EVIDENCE_FOLDER, exist_ok=True)


# =========================================================
# SETTINGS
# =========================================================

settings = {
    "confidence": 0.35,
    "zone_enabled": True,
    "loitering_seconds": 10,
    "line_position": 0.50,

    "zone": {
        "x": 0.60,
        "y": 0.20,
        "width": 0.30,
        "height": 0.60
    }
}


# =========================================================
# TRACKING MEMORY
# =========================================================

tracks = {}

next_track_id = 1

counted_entry_ids = set()
counted_exit_ids = set()

track_zone_start = {}
track_loiter_alerted = set()
track_inside_zone = {}

last_evidence_time = {}

tracker_lock = threading.Lock()


# =========================================================
# ANALYTICS
# =========================================================

total_entries = 0
total_exits = 0
total_loitering_alerts = 0
total_zone_alerts = 0
total_evidence = 0

unique_track_ids = set()


# =========================================================
# RESET
# =========================================================

def reset_tracking():

    global tracks
    global next_track_id

    global counted_entry_ids
    global counted_exit_ids

    global track_zone_start
    global track_loiter_alerted
    global track_inside_zone

    global last_evidence_time

    global total_entries
    global total_exits
    global total_loitering_alerts
    global total_zone_alerts
    global total_evidence

    global unique_track_ids

    with tracker_lock:

        tracks = {}

        next_track_id = 1

        counted_entry_ids.clear()
        counted_exit_ids.clear()

        track_zone_start.clear()
        track_loiter_alerted.clear()
        track_inside_zone.clear()

        last_evidence_time.clear()

        total_entries = 0
        total_exits = 0
        total_loitering_alerts = 0
        total_zone_alerts = 0
        total_evidence = 0

        unique_track_ids.clear()


# =========================================================
# IMAGE DECODER
# =========================================================

def decode_image(data):

    try:

        if "," in data:
            data = data.split(",", 1)[1]

        raw = base64.b64decode(data)

        array = np.frombuffer(raw, dtype=np.uint8)

        frame = cv2.imdecode(array, cv2.IMREAD_COLOR)

        return frame

    except Exception:

        return None


# =========================================================
# SIMPLE LIGHTWEIGHT OBJECT DETECTOR
# =========================================================
#
# This version intentionally avoids PyTorch/YOLO.
#
# It uses OpenCV's lightweight motion/contour detection
# so the Render FREE instance can run within limited RAM.
#
# =========================================================

def detect_objects(frame):

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    gray = cv2.GaussianBlur(gray, (7, 7), 0)

    return gray


# =========================================================
# SIMPLE TRACKING
# =========================================================

def update_tracks(detections):

    global next_track_id

    current_ids = []

    used_ids = set()

    with tracker_lock:

        # Match current detections with previous tracks
        for detection in detections:

            cx, cy, x1, y1, x2, y2, class_name = detection

            best_id = None
            best_distance = 999999

            for track_id, track in tracks.items():

                if track_id in used_ids:
                    continue

                old_cx = track["cx"]
                old_cy = track["cy"]

                distance = np.sqrt(
                    (cx - old_cx) ** 2 +
                    (cy - old_cy) ** 2
                )

                if distance < best_distance and distance < 100:

                    best_distance = distance
                    best_id = track_id

            if best_id is None:

                best_id = next_track_id
                next_track_id += 1

            tracks[best_id] = {
                "cx": cx,
                "cy": cy,
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "class_name": class_name,
                "last_seen": time.time()
            }

            used_ids.add(best_id)

            current_ids.append(best_id)

    return current_ids


# =========================================================
# MOTION DETECTION
# =========================================================

previous_gray = None


def motion_detection(frame):

    global previous_gray

    gray = detect_objects(frame)

    if previous_gray is None:

        previous_gray = gray.copy()

        return []

    difference = cv2.absdiff(previous_gray, gray)

    previous_gray = gray.copy()

    _, threshold = cv2.threshold(
        difference,
        25,
        255,
        cv2.THRESH_BINARY
    )

    threshold = cv2.dilate(
        threshold,
        None,
        iterations=2
    )

    contours, _ = cv2.findContours(
        threshold,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    detections = []

    frame_area = frame.shape[0] * frame.shape[1]

    for contour in contours:

        x, y, w, h = cv2.boundingRect(contour)

        area = w * h

        if area < frame_area * 0.003:
            continue

        if w < 20 or h < 20:
            continue

        if w > frame.shape[1] * 0.8:
            continue

        if h > frame.shape[0] * 0.8:
            continue

        cx = x + w // 2
        cy = y + h // 2

        # Lightweight classification
        if h > w * 1.15:
            class_name = "person"
        else:
            class_name = "object"

        detections.append(
            (
                cx,
                cy,
                x,
                y,
                x + w,
                y + h,
                class_name
            )
        )

    return detections


# =========================================================
# EVIDENCE CAPTURE
# =========================================================

def save_evidence(frame, x1, y1, x2, y2, track_id, reason):

    global total_evidence

    now = time.time()

    last_time = last_evidence_time.get(track_id, 0)

    if now - last_time < 5:
        return None

    filename = (
        f"evidence_{track_id}_"
        f"{int(now)}_{reason}.jpg"
    )

    path = os.path.join(
        EVIDENCE_FOLDER,
        filename
    )

    evidence = frame.copy()

    cv2.rectangle(
        evidence,
        (x1, y1),
        (x2, y2),
        (0, 0, 255),
        3
    )

    cv2.putText(
        evidence,
        f"TRACK {track_id} - {reason.upper()}",
        (20, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 0, 255),
        2
    )

    try:

        cv2.imwrite(path, evidence)

        last_evidence_time[track_id] = now

        total_evidence += 1

        return filename

    except Exception:

        return None


# =========================================================
# ZONE CHECK
# =========================================================

def is_inside_zone(cx, cy, width, height):

    zone = settings["zone"]

    zx1 = int(zone["x"] * width)
    zy1 = int(zone["y"] * height)

    zx2 = int(
        (zone["x"] + zone["width"]) * width
    )

    zy2 = int(
        (zone["y"] + zone["height"]) * height
    )

    return (
        zx1 <= cx <= zx2
        and
        zy1 <= cy <= zy2
    )


# =========================================================
# MAIN DETECTION API
# =========================================================

@app.route("/api/detect", methods=["POST"])
def detect():

    global total_entries
    global total_exits
    global total_loitering_alerts
    global total_zone_alerts

    start_time = time.time()

    data = request.get_json(silent=True)

    if not data or "image" not in data:

        return jsonify({
            "success": False,
            "message": "No image received"
        }), 400

    frame = decode_image(data["image"])

    if frame is None:

        return jsonify({
            "success": False,
            "message": "Invalid image"
        }), 400

    frame = cv2.resize(
        frame,
        (PROCESS_WIDTH, PROCESS_HEIGHT)
    )

    height, width = frame.shape[:2]

    # -----------------------------------------------------
    # DETECTION
    # -----------------------------------------------------

    detections = motion_detection(frame)

    # -----------------------------------------------------
    # TRACKING
    # -----------------------------------------------------

    current_ids = update_tracks(detections)

    alerts = []

    evidence_files = []

    entries_this_frame = 0
    exits_this_frame = 0

    people_count = 0

    object_classes = []

    # -----------------------------------------------------
    # PROCESS TRACKS
    # -----------------------------------------------------

    for track_id in current_ids:

        track = tracks[track_id]

        cx = track["cx"]
        cy = track["cy"]

        x1 = track["x1"]
        y1 = track["y1"]
        x2 = track["x2"]
        y2 = track["y2"]

        class_name = track["class_name"]

        object_classes.append(class_name)

        if class_name == "person":

            people_count += 1

        unique_track_ids.add(track_id)

        # -------------------------------------------------
        # DRAW BOUNDING BOX
        # -------------------------------------------------

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (255, 180, 0),
            2
        )

        cv2.putText(
            frame,
            f"{class_name} | ID {track_id}",
            (x1, max(20, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 180, 0),
            2
        )

        # -------------------------------------------------
        # ENTRY / EXIT LINE
        # -------------------------------------------------

        line_y = int(
            settings["line_position"] * height
        )

        previous_y = track.get("previous_y")

        if previous_y is not None:

            if class_name == "person":

                # ENTRY
                if (
                    previous_y < line_y - 4
                    and
                    cy >= line_y + 2
                    and
                    track_id not in counted_entry_ids
                ):

                    counted_entry_ids.add(track_id)

                    total_entries += 1

                    entries_this_frame += 1

                    alerts.append(
                        f"ENTRY detected - ID {track_id}"
                    )

                # EXIT
                if (
                    previous_y > line_y + 4
                    and
                    cy <= line_y - 2
                    and
                    track_id not in counted_exit_ids
                ):

                    counted_exit_ids.add(track_id)

                    total_exits += 1

                    exits_this_frame += 1

                    alerts.append(
                        f"EXIT detected - ID {track_id}"
                    )

        track["previous_y"] = cy

        # -------------------------------------------------
        # RESTRICTED ZONE
        # -------------------------------------------------

        inside_zone = is_inside_zone(
            cx,
            cy,
            width,
            height
        )

        was_inside = track_inside_zone.get(
            track_id,
            False
        )

        if settings["zone_enabled"]:

            if inside_zone and not was_inside:

                total_zone_alerts += 1

                alerts.append(
                    f"RESTRICTED ZONE - ID {track_id}"
                )

                evidence = save_evidence(
                    frame,
                    x1,
                    y1,
                    x2,
                    y2,
                    track_id,
                    "zone"
                )

                if evidence:

                    evidence_files.append(evidence)

            track_inside_zone[track_id] = inside_zone

        # -------------------------------------------------
        # LOITERING
        # -------------------------------------------------

        if inside_zone:

            if track_id not in track_zone_start:

                track_zone_start[track_id] = time.time()

            elapsed = (
                time.time()
                -
                track_zone_start[track_id]
            )

            if (
                elapsed >= settings["loitering_seconds"]
                and
                track_id not in track_loiter_alerted
            ):

                track_loiter_alerted.add(track_id)

                total_loitering_alerts += 1

                alerts.append(
                    f"LOITERING detected - ID {track_id}"
                )

                evidence = save_evidence(
                    frame,
                    x1,
                    y1,
                    x2,
                    y2,
                    track_id,
                    "loitering"
                )

                if evidence:

                    evidence_files.append(evidence)

        else:

            track_zone_start.pop(
                track_id,
                None
            )

    # -----------------------------------------------------
    # DRAW SECURITY ZONE
    # -----------------------------------------------------

    if settings["zone_enabled"]:

        zone = settings["zone"]

        zx1 = int(zone["x"] * width)
        zy1 = int(zone["y"] * height)

        zx2 = int(
            (zone["x"] + zone["width"]) * width
        )

        zy2 = int(
            (zone["y"] + zone["height"]) * height
        )

        cv2.rectangle(
            frame,
            (zx1, zy1),
            (zx2, zy2),
            (0, 0, 255),
            2
        )

        cv2.putText(
            frame,
            "RESTRICTED ZONE",
            (zx1, max(20, zy1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 0, 255),
            2
        )

    # -----------------------------------------------------
    # DRAW ENTRY / EXIT LINE
    # -----------------------------------------------------

    line_y = int(
        settings["line_position"] * height
    )

    cv2.line(
        frame,
        (0, line_y),
        (width, line_y),
        (255, 255, 0),
        2
    )

    cv2.putText(
        frame,
        "ENTRY / EXIT LINE",
        (10, max(20, line_y - 8)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 0),
        2
    )

    # -----------------------------------------------------
    # ENCODE RESULT
    # -----------------------------------------------------

    success, encoded = cv2.imencode(
        ".jpg",
        frame,
        [cv2.IMWRITE_JPEG_QUALITY, 75]
    )

    if not success:

        return jsonify({
            "success": False,
            "message": "Could not encode result"
        }), 500

    image_base64 = base64.b64encode(
        encoded.tobytes()
    ).decode("utf-8")

    processing_time = time.time() - start_time

    processing_fps = (
        1 / processing_time
        if processing_time > 0
        else 0
    )

    # -----------------------------------------------------
    # RESPONSE
    # -----------------------------------------------------

    return jsonify({

        "success": True,

        "image": (
            "data:image/jpeg;base64,"
            + image_base64
        ),

        "fps": round(processing_fps, 2),

        "processing_fps": round(
            processing_fps,
            2
        ),

        "processing_time": round(
            processing_time,
            4
        ),

        "tracked_count": len(current_ids),

        "people_count": people_count,

        "unique_tracks": len(
            unique_track_ids
        ),

        "detections": len(
            detections
        ),

        "classes": object_classes,

        "alerts": alerts,

        "evidence_files": evidence_files,

        "evidence_count": total_evidence,

        "zone_enabled": settings[
            "zone_enabled"
        ],

        "zone": settings["zone"],

        "loitering_seconds": settings[
            "loitering_seconds"
        ],

        "line_position": settings[
            "line_position"
        ],

        "entries": total_entries,

        "exits": total_exits,

        "entries_this_frame":
            entries_this_frame,

        "exits_this_frame":
            exits_this_frame,

        "loitering_alerts":
            total_loitering_alerts,

        "zone_alerts":
            total_zone_alerts
    })


# =========================================================
# SETTINGS API
# =========================================================

@app.route("/api/settings", methods=["POST"])
def update_settings():

    data = request.get_json(
        silent=True
    ) or {}

    if "confidence" in data:

        try:

            settings["confidence"] = float(
                data["confidence"]
            )

        except Exception:
            pass

    if "zone_enabled" in data:

        settings["zone_enabled"] = bool(
            data["zone_enabled"]
        )

    if "loitering_seconds" in data:

        try:

            settings[
                "loitering_seconds"
            ] = max(
                1,
                float(
                    data["loitering_seconds"]
                )
            )

        except Exception:
            pass

    if "line_position" in data:

        try:

            settings[
                "line_position"
            ] = min(
                0.95,
                max(
                    0.05,
                    float(
                        data["line_position"]
                    )
                )
            )

        except Exception:
            pass

    if "zone" in data:

        if isinstance(
            data["zone"],
            dict
        ):

            for key in [
                "x",
                "y",
                "width",
                "height"
            ]:

                if key in data["zone"]:

                    try:

                        settings[
                            "zone"
                        ][key] = float(
                            data["zone"][key]
                        )

                    except Exception:
                        pass

    return jsonify({
        "success": True,
        "settings": settings
    })


# =========================================================
# RESET API
# =========================================================

@app.route("/api/reset", methods=["POST"])
def reset():

    reset_tracking()

    return jsonify({
        "success": True,
        "message": "Tracking reset successfully"
    })


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/health")
def health():

    return jsonify({
        "status": "ok",
        "service": "VisionTrack AI"
    })


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False
    )