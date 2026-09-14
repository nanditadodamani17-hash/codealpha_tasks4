import os
import time
import base64
import threading

import cv2
import numpy as np

from flask import Flask, render_template, request, jsonify, send_from_directory

from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort


# ============================================================
# APPLICATION
# ============================================================

app = Flask(__name__)

app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024


# ============================================================
# FOLDERS
# ============================================================

UPLOAD_FOLDER = "uploads"
EVIDENCE_FOLDER = "evidence"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EVIDENCE_FOLDER, exist_ok=True)


# ============================================================
# PERFORMANCE
# ============================================================

PROCESS_WIDTH = 640
PROCESS_HEIGHT = 360


# ============================================================
# YOLO
# ============================================================

print()
print("========================================")
print("        VISIONTRACK AI")
print("========================================")
print("Loading YOLO11n model...")

model = YOLO("yolo11n.pt")

print("YOLO11n loaded successfully.")
print()


# ============================================================
# DEEP SORT
# ============================================================

tracker = DeepSort(
    max_age=30,
    n_init=2,
    max_iou_distance=0.7,
    max_cosine_distance=0.3
)

tracker_lock = threading.Lock()


# ============================================================
# SETTINGS
# ============================================================

settings = {

    "confidence": 0.35,

    "zone_enabled": True,

    "zone": {
        "x": 0.60,
        "y": 0.20,
        "width": 0.30,
        "height": 0.60
    },

    # Person staying this long = loitering
    "loitering_seconds": 10,

    # Virtual entry/exit line
    "line_position": 0.50

}


# ============================================================
# TRACKING MEMORY
# ============================================================

unique_track_ids = set()

track_first_seen = {}

track_last_seen = {}

track_previous_center = {}

track_zone_start = {}

track_loiter_alerted = set()

track_entry_state = {}

last_zone_alert_time = {}

last_loiter_alert_time = {}

last_evidence_time = {}


# ============================================================
# ANALYTICS
# ============================================================

total_entries = 0

total_exits = 0

total_loitering_alerts = 0

total_zone_alerts = 0


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return render_template("index.html")


# ============================================================
# HEALTH
# ============================================================

@app.route("/health")
def health():

    return jsonify({

        "status": "online",

        "model": "YOLO11n",

        "tracker": "Deep SORT",

        "features": [

            "YOLO object detection",

            "Deep SORT tracking",

            "people counting",

            "restricted zone",

            "loitering detection",

            "entry exit counting",

            "automatic evidence capture",

            "real time analytics"

        ]

    })


# ============================================================
# EVIDENCE FILES
# ============================================================

@app.route("/evidence/<path:filename>")
def evidence_file(filename):

    return send_from_directory(
        EVIDENCE_FOLDER,
        filename
    )


# ============================================================
# RESET
# ============================================================

@app.route("/api/reset", methods=["POST"])
def reset_tracking():

    global total_entries
    global total_exits
    global total_loitering_alerts
    global total_zone_alerts

    with tracker_lock:

        unique_track_ids.clear()

        track_first_seen.clear()

        track_last_seen.clear()

        track_previous_center.clear()

        track_zone_start.clear()

        track_loiter_alerted.clear()

        track_entry_state.clear()

        last_zone_alert_time.clear()

        last_loiter_alert_time.clear()

        last_evidence_time.clear()

    total_entries = 0

    total_exits = 0

    total_loitering_alerts = 0

    total_zone_alerts = 0

    return jsonify({

        "success": True,

        "message": "Tracking session reset."

    })


# ============================================================
# SETTINGS
# ============================================================

@app.route("/api/settings", methods=["POST"])
def update_settings():

    try:

        data = request.get_json() or {}


        # ----------------------------------------------------
        # CONFIDENCE
        # ----------------------------------------------------

        if "confidence" in data:

            confidence = float(
                data["confidence"]
            )

            confidence = max(
                0.10,
                min(
                    confidence,
                    0.95
                )
            )

            settings["confidence"] = confidence


        # ----------------------------------------------------
        # ZONE
        # ----------------------------------------------------

        if "zone_enabled" in data:

            settings["zone_enabled"] = bool(
                data["zone_enabled"]
            )


        # ----------------------------------------------------
        # LOITERING TIME
        # ----------------------------------------------------

        if "loitering_seconds" in data:

            seconds = int(
                data["loitering_seconds"]
            )

            settings["loitering_seconds"] = max(
                3,
                min(
                    seconds,
                    300
                )
            )


        # ----------------------------------------------------
        # ZONE POSITION
        # ----------------------------------------------------

        if "zone" in data:

            zone = data["zone"]

            settings["zone"] = {

                "x": max(
                    0,
                    min(
                        float(
                            zone.get(
                                "x",
                                0.60
                            )
                        ),
                        1
                    )
                ),

                "y": max(
                    0,
                    min(
                        float(
                            zone.get(
                                "y",
                                0.20
                            )
                        ),
                        1
                    )
                ),

                "width": max(
                    0,
                    min(
                        float(
                            zone.get(
                                "width",
                                0.30
                            )
                        ),
                        1
                    )
                ),

                "height": max(
                    0,
                    min(
                        float(
                            zone.get(
                                "height",
                                0.60
                            )
                        ),
                        1
                    )
                )

            }


        return jsonify({

            "success": True,

            "confidence":
                settings["confidence"],

            "zone_enabled":
                settings["zone_enabled"],

            "loitering_seconds":
                settings["loitering_seconds"],

            "zone":
                settings["zone"]

        })


    except Exception as error:

        return jsonify({

            "success": False,

            "message": str(error)

        }), 400


# ============================================================
# POINT INSIDE ZONE
# ============================================================

def point_inside_zone(
    center_x,
    center_y,
    frame_width,
    frame_height
):

    zone = settings["zone"]

    zx = zone["x"] * frame_width

    zy = zone["y"] * frame_height

    zw = zone["width"] * frame_width

    zh = zone["height"] * frame_height

    return (

        zx <= center_x <= zx + zw

        and

        zy <= center_y <= zy + zh

    )


# ============================================================
# SECURITY ALERT
# ============================================================

def create_zone_alert(
    track_id,
    class_name
):

    global total_zone_alerts

    now = time.time()

    previous = last_zone_alert_time.get(
        track_id,
        0
    )

    if now - previous < 3:

        return None

    last_zone_alert_time[
        track_id
    ] = now

    total_zone_alerts += 1

    return {

        "type": "restricted_zone",

        "track_id": track_id,

        "class": class_name,

        "message": (
            f"{class_name.upper()} "
            f"ID:{track_id} "
            f"entered restricted zone"
        ),

        "timestamp": time.strftime(
            "%H:%M:%S"
        )

    }


# ============================================================
# LOITERING ALERT
# ============================================================

def create_loitering_alert(
    track_id,
    class_name,
    duration
):

    global total_loitering_alerts

    now = time.time()

    previous = last_loiter_alert_time.get(
        track_id,
        0
    )

    if now - previous < 10:

        return None

    last_loiter_alert_time[
        track_id
    ] = now

    total_loitering_alerts += 1

    track_loiter_alerted.add(
        track_id
    )

    return {

        "type": "loitering",

        "track_id": track_id,

        "class": class_name,

        "duration": duration,

        "message": (
            f"{class_name.upper()} "
            f"ID:{track_id} "
            f"loitering detected "
            f"for {duration}s"
        ),

        "timestamp": time.strftime(
            "%H:%M:%S"
        )

    }


# ============================================================
# EVIDENCE CAPTURE
# ============================================================

def save_evidence(
    frame,
    alert_type,
    track_id,
    class_name
):

    now = time.time()

    previous = last_evidence_time.get(
        track_id,
        0
    )

    # Avoid saving many images
    # for the same person.

    if now - previous < 5:

        return None

    last_evidence_time[
        track_id
    ] = now

    timestamp = time.strftime(
        "%Y%m%d_%H%M%S"
    )

    filename = (
        f"{alert_type}_"
        f"ID{track_id}_"
        f"{timestamp}.jpg"
    )

    filepath = os.path.join(
        EVIDENCE_FOLDER,
        filename
    )

    # Add evidence header
    evidence_frame = frame.copy()

    cv2.rectangle(
        evidence_frame,
        (0, 0),
        (640, 48),
        (20, 20, 20),
        -1
    )

    text = (
        f"VISIONTRACK AI | "
        f"{alert_type.upper()} | "
        f"{class_name.upper()} ID:{track_id}"
    )

    cv2.putText(
        evidence_frame,
        text,
        (12, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2
    )

    cv2.imwrite(
        filepath,
        evidence_frame,
        [
            cv2.IMWRITE_JPEG_QUALITY,
            90
        ]
    )

    return filename


# ============================================================
# DETECTION API
# ============================================================

@app.route(
    "/api/detect",
    methods=["POST"]
)
def detect():

    try:

        global total_entries
        global total_exits


        # ====================================================
        # TIMER
        # ====================================================

        start_time = time.perf_counter()


        # ====================================================
        # REQUEST
        # ====================================================

        data = request.get_json()

        if not data or "image" not in data:

            return jsonify({

                "success": False,

                "message":
                    "No image received."

            }), 400


        # ====================================================
        # BASE64
        # ====================================================

        image_data = data["image"]


        if "," in image_data:

            image_data = image_data.split(
                ",",
                1
            )[1]


        image_bytes = base64.b64decode(
            image_data
        )


        np_arr = np.frombuffer(
            image_bytes,
            np.uint8
        )


        frame = cv2.imdecode(
            np_arr,
            cv2.IMREAD_COLOR
        )


        if frame is None:

            return jsonify({

                "success": False,

                "message":
                    "Could not decode image."

            }), 400


        # ====================================================
        # RESIZE
        # ====================================================

        frame = cv2.resize(

            frame,

            (
                PROCESS_WIDTH,
                PROCESS_HEIGHT
            ),

            interpolation=cv2.INTER_AREA

        )


        frame_height, frame_width = (
            frame.shape[:2]
        )


        # ====================================================
        # YOLO
        # ====================================================

        results = model.predict(

            frame,

            conf=settings[
                "confidence"
            ],

            imgsz=640,

            verbose=False

        )


        detections = []

        result = results[0]


        # ====================================================
        # DETECTIONS
        # ====================================================

        if result.boxes is not None:

            for box in result.boxes:

                confidence = float(
                    box.conf[0]
                )

                class_id = int(
                    box.cls[0]
                )

                x1, y1, x2, y2 = map(

                    int,

                    box.xyxy[
                        0
                    ].tolist()

                )

                width = x2 - x1

                height = y2 - y1

                class_name = model.names[
                    class_id
                ]

                detections.append(

                    (
                        [
                            x1,
                            y1,
                            width,
                            height
                        ],

                        confidence,

                        class_name

                    )

                )


        # ====================================================
        # DEEP SORT
        # ====================================================

        with tracker_lock:

            tracks = tracker.update_tracks(

                detections,

                frame=frame

            )


        # ====================================================
        # DATA
        # ====================================================

        tracked_objects = []

        alerts = []

        evidence_files = []

        entries_this_frame = 0

        exits_this_frame = 0


        # ====================================================
        # RESTRICTED ZONE
        # ====================================================

        zone = settings["zone"]


        zone_x1 = int(
            zone["x"] *
            frame_width
        )

        zone_y1 = int(
            zone["y"] *
            frame_height
        )

        zone_x2 = int(
            (
                zone["x"] +
                zone["width"]
            )
            *
            frame_width
        )

        zone_y2 = int(
            (
                zone["y"] +
                zone["height"]
            )
            *
            frame_height
        )


        # ====================================================
        # DRAW RESTRICTED ZONE
        # ====================================================

        if settings["zone_enabled"]:

            cv2.rectangle(

                frame,

                (
                    zone_x1,
                    zone_y1
                ),

                (
                    zone_x2,
                    zone_y2
                ),

                (0, 0, 255),

                2

            )

            cv2.putText(

                frame,

                "RESTRICTED ZONE",

                (
                    zone_x1 + 8,

                    max(
                        22,
                        zone_y1 - 8
                    )

                ),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.55,

                (0, 0, 255),

                2

            )


        # ====================================================
        # ENTRY / EXIT LINE
        # ====================================================

        line_y = int(
            settings["line_position"]
            * frame_height
        )


        cv2.line(

            frame,

            (
                0,
                line_y
            ),

            (
                frame_width,
                line_y
            ),

            (255, 200, 0),

            2

        )


        cv2.putText(

            frame,

            "ENTRY / EXIT",

            (
                10,
                max(
                    25,
                    line_y - 10
                )

            ),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.50,

            (255, 200, 0),

            2

        )


        # ====================================================
        # PROCESS TRACKS
        # ====================================================

        for track in tracks:

            if not track.is_confirmed():

                continue


            if track.time_since_update > 1:

                continue


            track_id = int(
                track.track_id
            )


            ltrb = track.to_ltrb()


            if ltrb is None:

                continue


            x1, y1, x2, y2 = map(

                int,

                ltrb

            )


            class_name = (
                track.get_det_class()
            )


            if class_name is None:

                class_name = "object"


            # ------------------------------------------------
            # LIMIT BOX
            # ------------------------------------------------

            x1 = max(
                0,
                min(
                    x1,
                    frame_width - 1
                )
            )

            y1 = max(
                0,
                min(
                    y1,
                    frame_height - 1
                )
            )

            x2 = max(
                0,
                min(
                    x2,
                    frame_width - 1
                )
            )

            y2 = max(
                0,
                min(
                    y2,
                    frame_height - 1
                )
            )


            # ------------------------------------------------
            # CENTER
            # ------------------------------------------------

            center_x = int(
                (x1 + x2) / 2
            )

            center_y = int(
                (y1 + y2) / 2
            )


            # ------------------------------------------------
            # TRACK MEMORY
            # ------------------------------------------------

            now = time.time()


            if track_id not in track_first_seen:

                track_first_seen[
                    track_id
                ] = now


            track_last_seen[
                track_id
            ] = now


            unique_track_ids.add(
                track_id
            )


            duration = int(

                now -
                track_first_seen[
                    track_id
                ]

            )


            # =================================================
            # ENTRY / EXIT
            # =================================================

            previous_center = (
                track_previous_center.get(
                    track_id
                )
            )


            if previous_center is not None:

                previous_y = (
                    previous_center[1]
                )


                # ---------------------------------------------
                # ENTER
                # ---------------------------------------------

                if (
                    previous_y < line_y
                    and center_y >= line_y
                ):

                    entries_this_frame += 1

                    total_entries += 1

                    track_entry_state[
                        track_id
                    ] = "entered"


                # ---------------------------------------------
                # EXIT
                # ---------------------------------------------

                elif (
                    previous_y > line_y
                    and center_y <= line_y
                ):

                    exits_this_frame += 1

                    total_exits += 1

                    track_entry_state[
                        track_id
                    ] = "exited"


            track_previous_center[
                track_id
            ] = (
                center_x,
                center_y
            )


            # =================================================
            # RESTRICTED ZONE
            # =================================================

            inside_zone = False


            if settings["zone_enabled"]:

                inside_zone = point_inside_zone(

                    center_x,

                    center_y,

                    frame_width,

                    frame_height

                )


                # ---------------------------------------------
                # START ZONE TIMER
                # ---------------------------------------------

                if inside_zone:

                    if track_id not in track_zone_start:

                        track_zone_start[
                            track_id
                        ] = now


                    zone_duration = int(

                        now -
                        track_zone_start[
                            track_id
                        ]

                    )


                    # -----------------------------------------
                    # RESTRICTED ZONE ALERT
                    # -----------------------------------------

                    zone_alert = (
                        create_zone_alert(

                            track_id,

                            class_name

                        )
                    )


                    if zone_alert:

                        alerts.append(
                            zone_alert
                        )


                        evidence = save_evidence(

                            frame,

                            "restricted_zone",

                            track_id,

                            class_name

                        )


                        if evidence:

                            evidence_files.append(
                                evidence
                            )


                    # -----------------------------------------
                    # LOITERING
                    # -----------------------------------------

                    if (
                        zone_duration
                        >=
                        settings[
                            "loitering_seconds"
                        ]
                    ):

                        if track_id not in track_loiter_alerted:

                            loiter_alert = (
                                create_loitering_alert(

                                    track_id,

                                    class_name,

                                    zone_duration

                                )
                            )


                            if loiter_alert:

                                alerts.append(
                                    loiter_alert
                                )


                                evidence = save_evidence(

                                    frame,

                                    "loitering",

                                    track_id,

                                    class_name

                                )


                                if evidence:

                                    evidence_files.append(
                                        evidence
                                    )


                else:

                    # Person left zone
                    track_zone_start.pop(
                        track_id,
                        None
                    )

                    track_loiter_alerted.discard(
                        track_id
                    )


            # =================================================
            # BOX COLOR
            # =================================================

            if inside_zone:

                box_color = (
                    0,
                    0,
                    255
                )

            else:

                box_color = (
                    255,
                    255,
                    255
                )


            # =================================================
            # DRAW BOX
            # =================================================

            cv2.rectangle(

                frame,

                (
                    x1,
                    y1
                ),

                (
                    x2,
                    y2
                ),

                box_color,

                2

            )


            # =================================================
            # LABEL
            # =================================================

            label = (

                f"{class_name.upper()} "

                f"ID:{track_id} "

                f"{duration}s"

            )


            (
                text_width,
                text_height
            ), _ = cv2.getTextSize(

                label,

                cv2.FONT_HERSHEY_SIMPLEX,

                0.45,

                2

            )


            label_y1 = max(
                0,
                y1 - 28
            )


            cv2.rectangle(

                frame,

                (
                    x1,
                    label_y1
                ),

                (
                    x1 +
                    text_width +
                    10,

                    y1
                ),

                box_color,

                -1

            )


            cv2.putText(

                frame,

                label,

                (
                    x1 + 5,

                    y1 - 8

                ),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.45,

                (20, 20, 20),

                2

            )


            # =================================================
            # CENTER
            # =================================================

            cv2.circle(

                frame,

                (
                    center_x,
                    center_y
                ),

                4,

                box_color,

                -1

            )


            # =================================================
            # OBJECT DATA
            # =================================================

            tracked_objects.append({

                "id":
                    track_id,

                "class":
                    class_name,

                "confidence":
                    0,

                "x":
                    x1,

                "y":
                    y1,

                "width":
                    x2 - x1,

                "height":
                    y2 - y1,

                "center_x":
                    center_x,

                "center_y":
                    center_y,

                "duration":
                    duration,

                "inside_zone":
                    inside_zone

            })


        # ====================================================
        # FPS
        # ====================================================

        processing_time = (
            time.perf_counter()
            - start_time
        )


        if processing_time > 0:

            processing_fps = (
                1 /
                processing_time
            )

        else:

            processing_fps = 0


        # ====================================================
        # ENCODE
        # ====================================================

        success, buffer = cv2.imencode(

            ".jpg",

            frame,

            [
                cv2.IMWRITE_JPEG_QUALITY,
                75
            ]

        )


        if not success:

            return jsonify({

                "success": False,

                "message":
                    "Could not encode frame."

            }), 500


        encoded_image = (
            base64.b64encode(
                buffer
            ).decode("utf-8")
        )


        # ====================================================
        # CLASS COUNTS
        # ====================================================

        class_counts = {}

        people_count = 0


        for obj in tracked_objects:

            class_name = obj["class"]


            class_counts[
                class_name
            ] = (

                class_counts.get(
                    class_name,
                    0
                )
                + 1

            )


            if class_name == "person":

                people_count += 1


        # ====================================================
        # UNIQUE TRACKS
        # ====================================================

        unique_count = len(
            unique_track_ids
        )


        # ====================================================
        # RESPONSE
        # ====================================================

        return jsonify({

            "success":
                True,

            "image":
                (
                    "data:image/jpeg;base64,"
                    +
                    encoded_image
                ),

            "fps":
                round(
                    processing_fps,
                    1
                ),

            "processing_fps":
                round(
                    processing_fps,
                    1
                ),

            "processing_time":
                round(
                    processing_time * 1000,
                    1
                ),

            "tracked_count":
                len(
                    tracked_objects
                ),

            "people_count":
                people_count,

            "unique_tracks":
                unique_count,

            "detections":
                tracked_objects,

            "classes":
                class_counts,

            "alerts":
                alerts,

            "evidence_files":
                [
                    "/evidence/" + name
                    for name in evidence_files
                ],

            "zone_enabled":
                settings[
                    "zone_enabled"
                ],

            "zone":
                settings[
                    "zone"
                ],

            "loitering_seconds":
                settings[
                    "loitering_seconds"
                ],

            "entries":
                total_entries,

            "exits":
                total_exits,

            "entries_this_frame":
                entries_this_frame,

            "exits_this_frame":
                exits_this_frame,

            "loitering_alerts":
                total_loitering_alerts,

            "zone_alerts":
                total_zone_alerts

        })


    except Exception as error:

        print(
            "Detection Error:",
            error
        )


        return jsonify({

            "success":
                False,

            "message":
                str(error)

        }), 500


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    port = int(

        os.environ.get(
            "PORT",
            5000
        )

    )


    app.run(

        host="0.0.0.0",

        port=port,

        debug=True

    )