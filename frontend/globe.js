(function () {
  const assetRoot = window.location.pathname.includes("/frontend/") ? "../" : "./";
  const manifestUrl = assetUrl("data/manifests/firms_next_day_explorer_manifest.json");
  const state = {
    manifest: null,
    viewer: null,
    selectedIndex: 0,
    entities: [],
  };

  const els = {
    caseList: document.getElementById("globeCaseList"),
    caseId: document.getElementById("globeCaseId"),
    caseName: document.getElementById("globeCaseName"),
    peakProbability: document.getElementById("globePeakProbability"),
    improvement: document.getElementById("globeImprovement"),
    targetTime: document.getElementById("globeTargetTime"),
    zoomIn: document.getElementById("zoomIn"),
    zoomOut: document.getElementById("zoomOut"),
    tiltView: document.getElementById("tiltView"),
    northUp: document.getElementById("northUp"),
    flyHome: document.getElementById("flyHome"),
    openExplorer: document.getElementById("openExplorer"),
    error: document.getElementById("globeError"),
  };

  function assetUrl(path) {
    return `${assetRoot}${path}`;
  }

  function percent(value, digits = 0) {
    return `${(Number(value) * 100).toFixed(digits)}%`;
  }

  function signedDecimal(value, digits = 5) {
    const number = Number(value);
    const sign = number > 0 ? "+" : "";
    return `${sign}${number.toFixed(digits)}`;
  }

  function dateLabel(value) {
    const parsed = new Date(value);
    if (Number.isNaN(parsed.valueOf())) {
      return value;
    }
    return parsed.toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  }

  function colorForCase(index, alpha = 1) {
    const colors = [
      window.Cesium.Color.ORANGERED,
      window.Cesium.Color.GOLD,
      window.Cesium.Color.SPRINGGREEN,
    ];
    return colors[index % colors.length].withAlpha(alpha);
  }

  async function loadManifest() {
    const response = await fetch(manifestUrl, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`Manifest request failed: ${response.status}`);
    }
    const manifest = await response.json();
    if (!Array.isArray(manifest.cases) || manifest.cases.length === 0) {
      throw new Error("Manifest has no cases");
    }
    return manifest;
  }

  function createSatelliteImageryProvider() {
    return new window.Cesium.UrlTemplateImageryProvider({
      url: "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
      credit: "Source: Esri, Maxar, Earthstar Geographics, and the GIS User Community",
      maximumLevel: 19,
    });
  }

  function createViewer() {
    if (!window.Cesium) {
      throw new Error("Cesium is not loaded");
    }
    const viewer = new window.Cesium.Viewer("globe", {
      animation: false,
      baseLayerPicker: false,
      fullscreenButton: false,
      geocoder: false,
      homeButton: false,
      infoBox: false,
      navigationHelpButton: false,
      sceneModePicker: false,
      selectionIndicator: false,
      timeline: false,
      baseLayer: new window.Cesium.ImageryLayer(createSatelliteImageryProvider()),
      terrainProvider: new window.Cesium.EllipsoidTerrainProvider(),
    });
    viewer.scene.globe.enableLighting = true;
    viewer.scene.globe.showGroundAtmosphere = true;
    viewer.scene.screenSpaceCameraController.enableRotate = true;
    viewer.scene.screenSpaceCameraController.enableTranslate = true;
    viewer.scene.screenSpaceCameraController.enableZoom = true;
    viewer.scene.screenSpaceCameraController.enableTilt = true;
    viewer.scene.screenSpaceCameraController.enableLook = true;
    return viewer;
  }

  function addCaseEntities() {
    state.entities = state.manifest.cases.map((caseData, index) => {
      const bbox = caseData.wgs84_bbox;
      const center = caseData.center_lon_lat;
      const color = colorForCase(index);
      const entity = state.viewer.entities.add({
        id: caseData.case_id,
        name: caseData.case_name,
        position: window.Cesium.Cartesian3.fromDegrees(center.lon, center.lat, 2200),
        point: {
          pixelSize: 13,
          color,
          outlineColor: window.Cesium.Color.WHITE.withAlpha(0.95),
          outlineWidth: 2,
        },
        label: {
          text: caseData.case_name,
          font: "15px sans-serif",
          fillColor: window.Cesium.Color.WHITE,
          outlineColor: window.Cesium.Color.BLACK,
          outlineWidth: 3,
          style: window.Cesium.LabelStyle.FILL_AND_OUTLINE,
          pixelOffset: new window.Cesium.Cartesian2(0, -28),
          verticalOrigin: window.Cesium.VerticalOrigin.BOTTOM,
          disableDepthTestDistance: Number.POSITIVE_INFINITY,
        },
        rectangle: {
          coordinates: window.Cesium.Rectangle.fromDegrees(
            bbox.west,
            bbox.south,
            bbox.east,
            bbox.north
          ),
          material: colorForCase(index, 0.24),
          outline: true,
          outlineColor: colorForCase(index, 0.95),
        },
      });
      entity.description = [
        `<strong>${caseData.case_name}</strong>`,
        `<br>Peak probability: ${percent(caseData.sample_peak_probability)}`,
        `<br>Brier improvement: ${signedDecimal(caseData.brier_improvement_vs_persistence)}`,
      ].join("");
      return entity;
    });
  }

  function renderCaseButtons() {
    els.caseList.replaceChildren();
    state.manifest.cases.forEach((caseData, index) => {
      const button = document.createElement("button");
      button.className = "case-card";
      button.type = "button";
      button.setAttribute("aria-current", index === state.selectedIndex ? "true" : "false");
      const label = document.createElement("span");
      const name = document.createElement("strong");
      const target = document.createElement("span");
      const probability = document.createElement("span");
      name.textContent = caseData.case_name;
      target.textContent = dateLabel(caseData.target_time);
      probability.className = "probability";
      probability.textContent = percent(caseData.sample_peak_probability);
      label.append(name, target);
      button.append(label, probability);
      button.addEventListener("click", () => selectCase(index, true));
      els.caseList.append(button);
    });
  }

  function renderSelectedCase() {
    const caseData = state.manifest.cases[state.selectedIndex];
    els.caseId.textContent = caseData.case_id;
    els.caseName.textContent = caseData.case_name;
    els.peakProbability.textContent = percent(caseData.sample_peak_probability, 1);
    els.improvement.textContent = signedDecimal(caseData.brier_improvement_vs_persistence);
    els.targetTime.textContent = dateLabel(caseData.target_time);
    renderCaseButtons();
  }

  function flyToAllCases() {
    const bounds = state.manifest.cases.reduce(
      (merged, caseData) => ({
        west: Math.min(merged.west, caseData.wgs84_bbox.west),
        south: Math.min(merged.south, caseData.wgs84_bbox.south),
        east: Math.max(merged.east, caseData.wgs84_bbox.east),
        north: Math.max(merged.north, caseData.wgs84_bbox.north),
      }),
      { west: 180, south: 90, east: -180, north: -90 }
    );
    state.viewer.camera.flyTo({
      destination: window.Cesium.Rectangle.fromDegrees(
        bounds.west,
        bounds.south,
        bounds.east,
        bounds.north
      ),
      duration: 1.3,
    });
  }

  function caseCameraHeight(caseData) {
    const bbox = caseData.wgs84_bbox;
    const center = caseData.center_lon_lat;
    const latScale = Math.max(0.35, Math.cos(window.Cesium.Math.toRadians(center.lat)));
    const widthMeters = Math.abs(bbox.east - bbox.west) * 111320 * latScale;
    const heightMeters = Math.abs(bbox.north - bbox.south) * 110540;
    return Math.max(55000, Math.max(widthMeters, heightMeters) * 2.4);
  }

  function flyToCase(caseData) {
    const center = caseData.center_lon_lat;
    state.viewer.camera.flyTo({
      destination: window.Cesium.Cartesian3.fromDegrees(
        center.lon,
        center.lat,
        caseCameraHeight(caseData)
      ),
      orientation: {
        heading: window.Cesium.Math.toRadians(0),
        pitch: window.Cesium.Math.toRadians(-58),
        roll: 0,
      },
      duration: 1.1,
    });
  }

  function selectCase(index, fly) {
    state.selectedIndex = index;
    renderSelectedCase();
    const caseData = state.manifest.cases[index];
    if (fly) {
      flyToCase(caseData);
    }
  }

  function zoomCamera(direction) {
    if (!state.viewer) {
      return;
    }
    const height = state.viewer.camera.positionCartographic.height;
    const step = Math.max(1500, height * 0.32);
    if (direction === "in") {
      state.viewer.camera.zoomIn(step);
    } else {
      state.viewer.camera.zoomOut(step);
    }
  }

  function tiltCurrentCase() {
    if (!state.viewer || !state.manifest) {
      return;
    }
    flyToCase(state.manifest.cases[state.selectedIndex]);
  }

  function resetNorthUp() {
    if (!state.viewer) {
      return;
    }
    const camera = state.viewer.camera;
    camera.flyTo({
      destination: window.Cesium.Cartesian3.clone(camera.position),
      orientation: {
        heading: 0,
        pitch: camera.pitch,
        roll: 0,
      },
      duration: 0.5,
    });
  }

  function bindControls() {
    els.zoomIn.addEventListener("click", () => zoomCamera("in"));
    els.zoomOut.addEventListener("click", () => zoomCamera("out"));
    els.tiltView.addEventListener("click", tiltCurrentCase);
    els.northUp.addEventListener("click", resetNorthUp);
    els.flyHome.addEventListener("click", flyToAllCases);
    els.openExplorer.addEventListener("click", () => {
      window.location.href = "./index.html";
    });
  }

  async function init() {
    bindControls();
    try {
      state.manifest = await loadManifest();
      state.viewer = createViewer();
      addCaseEntities();
      renderSelectedCase();
      flyToAllCases();
    } catch (error) {
      console.error(error);
      els.error.hidden = false;
    }
  }

  init();
})();
