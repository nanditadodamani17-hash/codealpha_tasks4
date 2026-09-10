const startButton =
    document.getElementById("startButton");

const stopButton =
    document.getElementById("stopButton");

const emptyStartButton =
    document.getElementById("emptyStartButton");

const cameraVideo =
    document.getElementById("cameraVideo");

const resultImage =
    document.getElementById("resultImage");

const emptyState =
    document.getElementById("emptyState");

const cameraOverlay =
    document.getElementById("cameraOverlay");

const scanLine =
    document.getElementById("scanLine");

const overlayFPS =
    document.getElementById("overlayFPS");

const objectCount =
    document.getElementById("objectCount");

const peopleCount =
    document.getElementById("peopleCount");

const fpsValue =
    document.getElementById("fpsValue");

const uniqueTracks =
    document.getElementById("uniqueTracks");

const objectList =
    document.getElementById("objectList");

const confidenceSlider =
    document.getElementById("confidenceSlider");

const confidenceValue =
    document.getElementById("confidenceValue");

const activityLog =
    document.getElementById("activityLog");

const captureButton =
    document.getElementById("captureButton");

const fullscreenButton =
    document.getElementById("fullscreenButton");

const videoArea =
    document.getElementById("videoArea");

const themeButton =
    document.getElementById("themeButton");

const loadValue =
    document.getElementById("loadValue");

const trackBar =
    document.getElementById("trackBar");

const loadBar =
    document.getElementById("loadBar");

const videoUpload =
    document.getElementById("videoUpload");

const resetButton =
    document.getElementById("resetButton");

const zoneToggle =
    document.getElementById("zoneToggle");

const zoneTag =
    document.getElementById("zoneTag");

const securityText =
    document.getElementById("securityText");

const securityEngine =
    document.getElementById("securityEngine");

const securityStatus =
    document.getElementById("zoneStatus");

const alertBanner =
    document.getElementById("alertBanner");

const alertText =
    document.getElementById("alertText");

const alertCount =
    document.getElementById("alertCount");

const analyticsUnique =
    document.getElementById("analyticsUnique");

const analyticsPeople =
    document.getElementById("analyticsPeople");

const analyticsPeopleBar =
    document.getElementById("peopleBar");

const analyticsSecurity =
    document.getElementById("analyticsSecurity");

let stream = null;

let running = false;

let processing = false;

let animationFrame = null;

let lastObjectCount = 0;

let totalAlerts = 0;

let uploadedVideoMode = false;

let uploadedVideoURL = null;

let alertTimer = null;


let lastEntryEvent = "";

let lastExitEvent = "";

let lastEvidenceEvent = "";


const canvas =
    document.createElement("canvas");

const ctx =
    canvas.getContext("2d");


function createSmartFeaturesPanel() {

    if (
        document.getElementById(
            "smartFeaturesPanel"
        )
    ) {
        return;
    }


    const panel =
        document.createElement("div");

    panel.id =
        "smartFeaturesPanel";


    panel.innerHTML = `

        <div style="
            margin:18px 0;
            padding:18px;
            border-radius:18px;
            background:linear-gradient(
                135deg,
                rgba(20,25,40,.95),
                rgba(30,35,55,.92)
            );
            border:1px solid rgba(255,255,255,.10);
            box-shadow:0 15px 40px rgba(0,0,0,.18);
        ">

            <div style="
                display:flex;
                justify-content:space-between;
                align-items:center;
                margin-bottom:15px;
            ">

                <div>

                    <div style="
                        font-size:12px;
                        letter-spacing:2px;
                        color:#8c9cff;
                        font-weight:700;
                    ">
                        INTELLIGENT SECURITY
                    </div>

                    <div style="
                        font-size:20px;
                        font-weight:800;
                        margin-top:4px;
                        color:white;
                    ">
                        Advanced Behaviour Analytics
                    </div>

                </div>

                <div style="
                    padding:7px 12px;
                    border-radius:20px;
                    background:rgba(0,220,150,.12);
                    color:#45e6aa;
                    font-size:11px;
                    font-weight:800;
                ">
                    AI ACTIVE
                </div>

            </div>


            <div style="
                display:grid;
                grid-template-columns:
                repeat(auto-fit,minmax(150px,1fr));
                gap:12px;
            ">

                <div class="smart-card">

                    <small>
                        ENTRIES
                    </small>

                    <strong id="smartEntries">
                        0
                    </strong>

                </div>


                <div class="smart-card">

                    <small>
                        EXITS
                    </small>

                    <strong id="smartExits">
                        0
                    </strong>

                </div>


                <div class="smart-card">

                    <small>
                        LOITERING
                    </small>

                    <strong id="smartLoitering">
                        0
                    </strong>

                </div>


                <div class="smart-card">

                    <small>
                        SECURITY ALERTS
                    </small>

                    <strong id="smartSecurity">
                        0
                    </strong>

                </div>


                <div class="smart-card">

                    <small>
                        EVIDENCE
                    </small>

                    <strong id="smartEvidence">
                        0
                    </strong>

                </div>

            </div>

        </div>
    `;


    const style =
        document.createElement("style");


    style.textContent = `

        .smart-card {
            padding:14px;
            border-radius:14px;
            background:rgba(255,255,255,.055);
            border:1px solid rgba(255,255,255,.08);
        }

        .smart-card small {
            display:block;
            font-size:10px;
            letter-spacing:1.2px;
            color:#9ca3b5;
            margin-bottom:7px;
            font-weight:700;
        }

        .smart-card strong {
            font-size:25px;
            color:white;
        }

        .vision-alert {
            position:fixed;
            right:22px;
            top:22px;
            z-index:99999;
            width:min(380px,calc(100vw - 44px));
            padding:18px;
            border-radius:18px;
            background:rgba(18,20,30,.96);
            border:1px solid rgba(255,80,80,.5);
            box-shadow:0 20px 60px rgba(0,0,0,.35);
            color:white;
            animation:visionAlertIn .35s ease;
        }

        .vision-alert-title {
            font-size:11px;
            letter-spacing:1.5px;
            color:#ff6868;
            font-weight:900;
            margin-bottom:7px;
        }

        .vision-alert-message {
            font-size:16px;
            font-weight:800;
        }

        .vision-alert-time {
            margin-top:6px;
            font-size:11px;
            color:#9da3b5;
        }

        @keyframes visionAlertIn {

            from {
                transform:translateX(40px);
                opacity:0;
            }

            to {
                transform:translateX(0);
                opacity:1;
            }

        }

    `;


    document.head.appendChild(style);


    const container =
        document.querySelector("main") ||
        document.querySelector(".main-content") ||
        document.body;


    container.prepend(panel);
}


async function startCamera() {

    if (uploadedVideoMode) {

        stopUploadedVideo();

    }


    if (running) return;


    if (
        !navigator.mediaDevices ||
        !navigator.mediaDevices.getUserMedia
    ) {

        alert(
            "Camera access is not supported by this browser."
        );

        return;

    }


    try {

        addActivity(
            "Requesting camera access",
            "Waiting for browser permission"
        );


        stream =
            await navigator.mediaDevices.getUserMedia({

                video: {

                    width: {
                        ideal: 640
                    },

                    height: {
                        ideal: 360
                    },

                    facingMode: "user"

                },

                audio: false

            });


        cameraVideo.srcObject =
            stream;


        await cameraVideo.play();


        cameraVideo.style.display =
            "block";


        emptyState.style.display =
            "none";


        resultImage.style.display =
            "block";


        cameraOverlay.style.display =
            "flex";


        securityStatus.style.display =
            zoneToggle && zoneToggle.checked
                ? "flex"
                : "none";


        if (scanLine) {

            scanLine.classList.add(
                "active"
            );

        }


        startButton.disabled =
            true;


        stopButton.disabled =
            false;


        running = true;

        uploadedVideoMode =
            false;


        addActivity(
            "Camera started",
            "AI vision processing active"
        );


        addActivity(
            "Behaviour analytics ready",
            "Loitering + entry/exit monitoring enabled"
        );


        processFrames();


    } catch (error) {

        console.error(error);


        addActivity(
            "Camera access failed",
            "Please allow browser camera permission"
        );


        alert(
            "Camera access was blocked. Please allow browser camera permission."
        );

    }

}


function stopCamera(
    showActivity = true
) {

    running = false;

    processing = false;


    if (animationFrame) {

        cancelAnimationFrame(
            animationFrame
        );

        animationFrame = null;

    }


    if (stream) {

        stream
            .getTracks()
            .forEach(
                track => track.stop()
            );

        stream = null;

    }


    stopUploadedVideo();


    if (cameraVideo) {

        cameraVideo.pause();

        cameraVideo.srcObject =
            null;

    }


    cameraVideo.style.display =
        "none";


    resultImage.style.display =
        "none";


    emptyState.style.display =
        "flex";


    cameraOverlay.style.display =
        "none";


    securityStatus.style.display =
        "none";


    if (scanLine) {

        scanLine.classList.remove(
            "active"
        );

    }


    startButton.disabled =
        false;


    stopButton.disabled =
        true;


    objectCount.textContent =
        "0";


    peopleCount.textContent =
        "0";


    fpsValue.textContent =
        "0";


    overlayFPS.textContent =
        "0 FPS";


    uniqueTracks.textContent =
        "0";


    if (analyticsUnique) {

        analyticsUnique.textContent =
            "0";

    }


    if (analyticsPeople) {

        analyticsPeople.textContent =
            "0";

    }


    if (loadValue) {

        loadValue.textContent =
            "0%";

    }


    if (loadBar) {

        loadBar.style.width =
            "0%";

    }


    if (trackBar) {

        trackBar.style.width =
            "0%";

    }


    if (analyticsPeopleBar) {

        analyticsPeopleBar.style.width =
            "0%";

    }


    objectList.innerHTML = `

        <div class="object-row">

            <span class="object-name">
                Waiting...
            </span>

            <span class="object-number">
                0
            </span>

        </div>

    `;


    if (showActivity) {

        addActivity(
            "Vision feed stopped",
            "AI processing disconnected"
        );

    }

}


function processFrames() {

    if (!running || uploadedVideoMode) {

        return;

    }


    if (
        cameraVideo.readyState < 2
    ) {

        animationFrame =
            requestAnimationFrame(
                processFrames
            );

        return;

    }


    if (!processing) {

        processing = true;


        canvas.width =
            640;

        canvas.height =
            360;


        ctx.drawImage(

            cameraVideo,

            0,
            0,

            640,
            360

        );


        const image =
            canvas.toDataURL(
                "image/jpeg",
                0.60
            );


        sendFrame(image);

    }


    animationFrame =
        requestAnimationFrame(
            processFrames
        );

}

async function sendFrame(
    image
) {

    try {

        const response =
            await fetch(
                "/api/detect",
                {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        image: image
                    })

                }
            );


        if (!response.ok) {

            throw new Error(
                `Server returned ${response.status}`
            );

        }


        const data =
            await response.json();


        if (!data.success) {

            throw new Error(
                data.message ||
                "Detection failed"
            );

        }


        updateDashboard(data);


    } catch (error) {

        console.error(
            "Frame error:",
            error
        );


    } finally {

        processing = false;

    }

}


function updateDashboard(
    data
) {

    if (!data) return;

    resultImage.src =
        data.image;


    const count =
        Number(
            data.tracked_count || 0
        );


    const people =
        Number(
            data.people_count || 0
        );


    const fps =
        Number(
            data.processing_fps ||
            data.fps ||
            0
        );


    const unique =
        Number(
            data.unique_tracks || 0
        );


    objectCount.textContent =
        count;


    peopleCount.textContent =
        people;


    fpsValue.textContent =
        fps.toFixed(1);


    uniqueTracks.textContent =
        unique;


    overlayFPS.textContent =
        `${fps.toFixed(1)} FPS`;

    if (analyticsUnique) {

        analyticsUnique.textContent =
            unique;

    }


    if (analyticsPeople) {

        analyticsPeople.textContent =
            people;

    }


    const load =
        Math.min(
            100,
            Math.round(
                (fps / 30) * 100
            )
        );


    if (loadValue) {

        loadValue.textContent =
            `${load}%`;

    }


    if (loadBar) {

        loadBar.style.width =
            `${load}%`;

    }


    if (trackBar) {

        trackBar.style.width =
            `${Math.min(
                unique * 10,
                100
            )}%`;

    }


    if (analyticsPeopleBar) {

        analyticsPeopleBar.style.width =
            `${Math.min(
                people * 20,
                100
            )}%`;

    }

    updateObjectList(
        data.classes || {}
    );


    updateSecurityState(
        data.zone_enabled
    );

    updateSmartFeatures(
        data
    );


    if (
        Array.isArray(data.alerts) &&
        data.alerts.length > 0
    ) {

        data.alerts.forEach(
            alert => {

                showSmartAlert(alert);

            }
        );

    }


    if (
        count !== lastObjectCount
    ) {

        if (count > 0) {

            addActivity(

                `${count} object${
                    count === 1
                        ? ""
                        : "s"
                } tracked`,

                `${people} people • ${unique} unique tracks`

            );

        }


        lastObjectCount =
            count;

    }

}


function updateSmartFeatures(
    data
) {

    const entries =
        Number(
            data.entries || 0
        );


    const exits =
        Number(
            data.exits || 0
        );


    const loitering =
        Number(
            data.loitering_alerts || 0
        );


    const zoneAlerts =
        Number(
            data.zone_alerts || 0
        );



    const evidence =
        Number(
            data.evidence_count || 0
        );

    const security =
        zoneAlerts +
        loitering;


    const entryElement =
        document.getElementById(
            "smartEntries"
        );


    const exitElement =
        document.getElementById(
            "smartExits"
        );


    const loiterElement =
        document.getElementById(
            "smartLoitering"
        );


    const securityElement =
        document.getElementById(
            "smartSecurity"
        );


    const evidenceElement =
        document.getElementById(
            "smartEvidence"
        );


    if (entryElement) {

        entryElement.textContent =
            entries;

    }


    if (exitElement) {

        exitElement.textContent =
            exits;

    }


    if (loiterElement) {

        loiterElement.textContent =
            loitering;

    }


    if (securityElement) {

        securityElement.textContent =
            security;

    }


    if (evidenceElement) {

        evidenceElement.textContent =
            evidence;

    }


    
    const entryIDs =
        Array.isArray(
            data.entries_this_frame
        )
            ? data.entries_this_frame
            : [];


    if (entryIDs.length > 0) {

        const eventKey =
            entryIDs.join(",");


        if (
            eventKey !==
            lastEntryEvent
        ) {

            entryIDs.forEach(
                id => {

                    addActivity(

                        "🟢 Entry detected",

                        `Track ID ${id} crossed entry line`

                    );

                }
            );


            lastEntryEvent =
                eventKey;

        }

    }


    

    const exitIDs =
        Array.isArray(
            data.exits_this_frame
        )
            ? data.exits_this_frame
            : [];


    if (exitIDs.length > 0) {

        const eventKey =
            exitIDs.join(",");


        if (
            eventKey !==
            lastExitEvent
        ) {

            exitIDs.forEach(
                id => {

                    addActivity(

                        "🔵 Exit detected",

                        `Track ID ${id} crossed exit line`

                    );

                }
            );


            lastExitEvent =
                eventKey;

        }

    }


    
    if (
        Array.isArray(
            data.evidence_files
        ) &&
        data.evidence_files.length > 0
    ) {

        const latestEvidence =
            data.evidence_files.join("|");


        if (
            latestEvidence !==
            lastEvidenceEvent
        ) {

            addActivity(

                "📸 Evidence captured",

                `${data.evidence_files.length} security snapshot(s) saved`

            );


            lastEvidenceEvent =
                latestEvidence;

        }

    }

}



function updateSecurityState(
    enabled
) {

    if (enabled) {

        if (zoneTag) {

            zoneTag.textContent =
                "ACTIVE";

        }


        if (securityText) {

            securityText.textContent =
                "Monitoring active";

        }


        if (securityEngine) {

            securityEngine.textContent =
                "Active";

        }


        if (analyticsSecurity) {

            analyticsSecurity.textContent =
                "ACTIVE";

        }


        if (securityStatus) {

            securityStatus.style.display =
                running
                    ? "flex"
                    : "none";

        }


    } else {

        if (zoneTag) {

            zoneTag.textContent =
                "OFF";

        }


        if (securityText) {

            securityText.textContent =
                "Monitoring disabled";

        }


        if (securityEngine) {

            securityEngine.textContent =
                "Standby";

        }


        if (analyticsSecurity) {

            analyticsSecurity.textContent =
                "STANDBY";

        }


        if (securityStatus) {

            securityStatus.style.display =
                "none";

        }

    }

}



function updateObjectList(
    classes
) {

    const names =
        Object.keys(
            classes
        );


    if (!names.length) {

        objectList.innerHTML = `

            <div class="object-row">

                <span class="object-name">
                    No objects detected
                </span>

                <span class="object-number">
                    0
                </span>

            </div>

        `;

        return;

    }


    objectList.innerHTML =

        names

            .sort(
                (a, b) =>
                    classes[b] -
                    classes[a]
            )

            .map(

                name => `

                    <div class="object-row">

                        <span class="object-name">
                            ${escapeHtml(name)}
                        </span>

                        <span class="object-number">
                            ${classes[name]}
                        </span>

                    </div>

                `

            )

            .join("");

}


function showSmartAlert(
    alert
) {

    if (!alert) return;


    totalAlerts++;


    if (alertCount) {

        alertCount.textContent =
            totalAlerts;

    }


    if (alertText) {

        alertText.textContent =
            alert.message || "Security alert";

    }


    if (alertBanner) {

        alertBanner.style.display =
            "flex";

    }


    
    const popup =
        document.createElement(
            "div"
        );


    popup.className =
        "vision-alert";


    const title =
        alert.type === "loitering"

            ? "⚠ LOITERING DETECTED"

            : "🚨 RESTRICTED ZONE";


    popup.innerHTML = `

        <div class="vision-alert-title">
            ${title}
        </div>

        <div class="vision-alert-message">
            ${escapeHtml(
                alert.message ||
                "Security alert detected"
            )}
        </div>

        <div class="vision-alert-time">
            Event time:
            ${escapeHtml(
                alert.timestamp ||
                new Date().toLocaleTimeString()
            )}
        </div>

    `;


    document.body.appendChild(
        popup
    );


    setTimeout(

        () => {

            if (popup.parentNode) {

                popup.remove();

            }

        },

        4500

    );


    /* -----------------------------------------
       ACTIVITY LOG
    ----------------------------------------- */

    if (
        alert.type === "loitering"
    ) {

        addActivity(

            "⚠ Loitering detected",

            `${alert.class || "Object"} ID:${alert.track_id} • ${alert.duration || 0}s`

        );

    } else {

        addActivity(

            "🚨 Restricted zone alert",

            `${alert.class || "Object"} ID:${alert.track_id} • ${alert.timestamp || ""}`

        );

    }


    clearTimeout(
        alertTimer
    );


    alertTimer =
        setTimeout(

            () => {

                if (alertBanner) {

                    alertBanner.style.display =
                        "none";

                }

            },

            3500

        );

}



function addActivity(
    title,
    subtitle
) {

    if (!activityLog) return;


    const item =
        document.createElement(
            "div"
        );


    item.className =
        "activity";


    item.innerHTML = `

        <span></span>

        <div>

            <strong>
                ${escapeHtml(title)}
            </strong>

            <small>
                ${escapeHtml(subtitle)}
            </small>

        </div>

    `;


    activityLog.prepend(
        item
    );


    while (
        activityLog.children.length > 6
    ) {

        activityLog.lastElementChild.remove();

    }

}



if (confidenceSlider) {

    confidenceSlider.addEventListener(

        "input",

        () => {

            const value =
                confidenceSlider.value;


            confidenceValue.textContent =
                `${value}%`;


            updateServerSettings({

                confidence:
                    Number(value) / 100

            });

        }

    );

}



if (zoneToggle) {

    zoneToggle.addEventListener(

        "change",

        () => {

            const enabled =
                zoneToggle.checked;


            updateSecurityState(
                enabled
            );


            updateServerSettings({

                zone_enabled:
                    enabled

            });


            addActivity(

                enabled
                    ? "Security zone enabled"
                    : "Security zone disabled",

                enabled
                    ? "Restricted-area monitoring active"
                    : "Restricted-area monitoring paused"

            );

        }

    );

}



async function updateServerSettings(
    settings
) {

    try {

        const response =
            await fetch(

                "/api/settings",

                {

                    method:
                        "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body:
                        JSON.stringify(
                            settings
                        )

                }

            );


        if (!response.ok) {

            throw new Error(
                `Settings server returned ${response.status}`
            );

        }


        const data =
            await response.json();


        if (!data.success) {

            throw new Error(
                data.message ||
                "Settings update failed"
            );

        }


    } catch (error) {

        console.error(
            "Settings error:",
            error
        );

    }

}



if (captureButton) {

    captureButton.addEventListener(

        "click",

        () => {

            if (

                !resultImage.src ||

                resultImage.style.display ===
                "none"

            ) {

                alert(
                    "Start the AI camera or upload a video first."
                );

                return;

            }


            const link =
                document.createElement(
                    "a"
                );


            link.href =
                resultImage.src;


            link.download =
                `visiontrack-${Date.now()}.jpg`;


            document.body.appendChild(
                link
            );


            link.click();


            link.remove();


            addActivity(

                "Frame captured",

                "AI detection snapshot saved"

            );

        }

    );

}


if (fullscreenButton) {

    fullscreenButton.addEventListener(

        "click",

        async () => {

            try {

                if (
                    !document.fullscreenElement
                ) {

                    await videoArea.requestFullscreen();

                } else {

                    await document.exitFullscreen();

                }

            } catch (error) {

                console.error(
                    "Fullscreen error:",
                    error
                );

            }

        }

    );

}



if (resetButton) {

    resetButton.addEventListener(

        "click",

        async () => {

            try {

                const response =
                    await fetch(

                        "/api/reset",

                        {
                            method:
                                "POST"
                        }

                    );


                const data =
                    await response.json();


                if (!data.success) {

                    throw new Error(
                        data.message ||
                        "Reset failed"
                    );

                }


                totalAlerts = 0;

                lastObjectCount = 0;

                lastEntryEvent = "";

                lastExitEvent = "";

                lastEvidenceEvent = "";


                if (alertCount) {

                    alertCount.textContent =
                        "0";

                }


                if (uniqueTracks) {

                    uniqueTracks.textContent =
                        "0";

                }


                if (objectCount) {

                    objectCount.textContent =
                        "0";

                }


                if (peopleCount) {

                    peopleCount.textContent =
                        "0";

                }


                if (fpsValue) {

                    fpsValue.textContent =
                        "0";

                }


                if (overlayFPS) {

                    overlayFPS.textContent =
                        "0 FPS";

                }


                if (analyticsUnique) {

                    analyticsUnique.textContent =
                        "0";

                }


                if (analyticsPeople) {

                    analyticsPeople.textContent =
                        "0";

                }


                if (analyticsSecurity) {

                    analyticsSecurity.textContent =
                        "ACTIVE";

                }


                if (loadValue) {

                    loadValue.textContent =
                        "0%";

                }


                if (loadBar) {

                    loadBar.style.width =
                        "0%";

                }


                if (trackBar) {

                    trackBar.style.width =
                        "0%";

                }


                if (analyticsPeopleBar) {

                    analyticsPeopleBar.style.width =
                        "0%";

                }


                const ids = [

                    "smartEntries",

                    "smartExits",

                    "smartLoitering",

                    "smartSecurity",

                    "smartEvidence"

                ];


                ids.forEach(

                    id => {

                        const element =
                            document.getElementById(
                                id
                            );


                        if (element) {

                            element.textContent =
                                "0";

                        }

                    }

                );


                objectList.innerHTML = `

                    <div class="object-row">

                        <span class="object-name">
                            Waiting...
                        </span>

                        <span class="object-number">
                            0
                        </span>

                    </div>

                `;


                addActivity(

                    "Tracking session reset",

                    "IDs, counters, alerts and evidence analytics cleared"

                );


            } catch (error) {

                console.error(
                    "Reset error:",
                    error
                );


                addActivity(

                    "Reset failed",

                    error.message

                );

            }

        }

    );

}




if (startButton) {

    startButton.addEventListener(
        "click",
        startCamera
    );

}


if (emptyStartButton) {

    emptyStartButton.addEventListener(
        "click",
        startCamera
    );

}


if (stopButton) {

    stopButton.addEventListener(

        "click",

        () => stopCamera()

    );

}




if (themeButton) {

    themeButton.addEventListener(

        "click",

        () => {

            document.body.classList.toggle(
                "light-mode"
            );


            const lightMode =
                document.body.classList.contains(
                    "light-mode"
                );


            themeButton.textContent =
                lightMode
                    ? "☾"
                    : "☼";


            addActivity(

                "Interface updated",

                lightMode
                    ? "Light display enabled"
                    : "Dark display enabled"

            );

        }

    );

}



document
    .querySelectorAll(".nav-item")
    .forEach(

        button => {

            button.addEventListener(

                "click",

                () => {

                    document
                        .querySelectorAll(
                            ".nav-item"
                        )
                        .forEach(

                            item =>
                                item.classList.remove(
                                    "active"
                                )

                        );


                    button.classList.add(
                        "active"
                    );


                    const targetId =
                        button.dataset.target;


                    const target =
                        document.getElementById(
                            targetId
                        );


                    if (target) {

                        target.scrollIntoView({

                            behavior:
                                "smooth",

                            block:
                                "start"

                        });

                    }

                }

            );

        }

    );



if (videoUpload) {

    videoUpload.addEventListener(

        "change",

        event => {

            const file =
                event.target.files[0];


            if (!file) return;


            startUploadedVideo(
                file
            );

        }

    );

}



function startUploadedVideo(
    file
) {

    stopCamera(false);


    if (uploadedVideoURL) {

        URL.revokeObjectURL(
            uploadedVideoURL
        );

        uploadedVideoURL =
            null;

    }


    uploadedVideoURL =
        URL.createObjectURL(
            file
        );


    uploadedVideoMode =
        true;


    running =
        true;


    processing =
        false;


    cameraVideo.srcObject =
        null;


    cameraVideo.src =
        uploadedVideoURL;


    cameraVideo.muted =
        true;


    

    cameraVideo.loop =
        false;


    cameraVideo.controls =
        false;


    cameraVideo.style.display =
        "block";


    emptyState.style.display =
        "none";


    resultImage.style.display =
        "block";


    cameraOverlay.style.display =
        "flex";


    securityStatus.style.display =
        zoneToggle && zoneToggle.checked
            ? "flex"
            : "none";


    if (scanLine) {

        scanLine.classList.add(
            "active"
        );

    }


    startButton.disabled =
        true;


    stopButton.disabled =
        false;


    cameraVideo.play()

        .then(

            () => {

                addActivity(

                    "Video loaded",

                    file.name

                );


                addActivity(

                    "AI video analysis started",

                    "YOLO + Deep SORT + behaviour analytics"

                );


                processUploadedFrames();

            }

        )

        .catch(

            error => {

                console.error(
                    error
                );


                addActivity(

                    "Video playback failed",

                    "Browser could not play this file"

                );

            }

        );

}


function processUploadedFrames() {

    if (
        !running ||
        !uploadedVideoMode
    ) {

        return;

    }


    

    if (cameraVideo.ended) {

        addActivity(

            "Video analysis completed",

            "AI processing finished successfully"

        );


        running =
            false;


        uploadedVideoMode =
            false;


        processing =
            false;


        startButton.disabled =
            false;


        stopButton.disabled =
            true;


        if (scanLine) {

            scanLine.classList.remove(
                "active"
            );

        }


        return;

    }


    if (
        cameraVideo.readyState < 2
    ) {

        animationFrame =
            requestAnimationFrame(
                processUploadedFrames
            );

        return;

    }


    if (!processing) {

        processing = true;


        canvas.width =
            640;

        canvas.height =
            360;


        ctx.drawImage(

            cameraVideo,

            0,
            0,

            640,
            360

        );


        const image =
            canvas.toDataURL(

                "image/jpeg",

                0.60

            );


        sendFrame(image);

    }


    animationFrame =
        requestAnimationFrame(
            processUploadedFrames
        );

}



function stopUploadedVideo() {

    if (!uploadedVideoMode) {

        return;

    }


    uploadedVideoMode =
        false;


    if (cameraVideo) {

        cameraVideo.pause();

        cameraVideo.removeAttribute(
            "src"
        );

        cameraVideo.load();

        cameraVideo.controls =
            false;

    }


    if (uploadedVideoURL) {

        URL.revokeObjectURL(
            uploadedVideoURL
        );

        uploadedVideoURL =
            null;

    }

}



function escapeHtml(
    value
) {

    return String(
        value
    )

        .replace(
            /&/g,
            "&amp;"
        )

        .replace(
            /</g,
            "&lt;"
        )

        .replace(
            />/g,
            "&gt;"
        )

        .replace(
            /"/g,
            "&quot;"
        )

        .replace(
            /'/g,
            "&#039;"
        );

}



createSmartFeaturesPanel();


updateSecurityState(
    true
);


addActivity(
    "VisionTrack initialized",
    "YOLO11 + Deep SORT engine ready"
);


addActivity(
    "Security monitoring ready",
    "Restricted zone protection enabled"
);


addActivity(
    "Behaviour analytics ready",
    "Loitering + entry/exit detection active"
);