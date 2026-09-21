(function () {
  const assetRoot = window.location.pathname.includes("/frontend/") ? "../" : "./";
  const manifestUrl = assetUrl("data/manifests/firms_next_day_explorer_manifest.json");
  const apiBase = (new URLSearchParams(window.location.search).get("api") || "").replace(
    /\/$/,
    ""
  );
  const initialCaseId = new URLSearchParams(window.location.search).get("case") || "";
  const state = {
    manifest: null,
    viewer: null,
    selectedIndex: 0,
    entities: [],
    scenarioOverlay: null,
    scenarioCanvas: null,
    forecastVisible: true,
    observedVisible: true,
    scenarioVisible: true,
    overlayOpacity: 0.78,
    simulationSamples: [],
    simulationApiAvailable: false,
    scenarioRequestId: 0,
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
    forecastLayerToggle: document.getElementById("forecastLayerToggle"),
    observedLayerToggle: document.getElementById("observedLayerToggle"),
    overlayOpacity: document.getElementById("overlayOpacity"),
    scenarioStatus: document.getElementById("scenarioStatus"),
    scenarioSample: document.getElementById("scenarioSample"),
    scenarioPeak: document.getElementById("scenarioPeak"),
    scenarioMean: document.getElementById("scenarioMean"),
    scenarioFootprint: document.getElementById("scenarioFootprint"),
    scenarioUpdated: document.getElementById("scenarioUpdated"),
    windSpeedMultiplier: document.getElementById("windSpeedMultiplier"),
    windSpeedValue: document.getElementById("windSpeedValue"),
    windDirectionDelta: document.getElementById("windDirectionDelta"),
    windDirectionValue: document.getElementById("windDirectionValue"),
    spreadRateMultiplier: document.getElementById("spreadRateMultiplier"),
    spreadRateValue: document.getElementById("spreadRateValue"),
    runScenario: document.getElementById("runScenario"),
    resetScenario: document.getElementById("resetScenario"),
    flyHome: document.getElementById("flyHome"),
    openExplorer: document.getElementById("openExplorer"),
    error: document.getElementById("globeError"),
    scenarioLayerToggle: document.getElementById("scenarioLayerToggle"),
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

  async function loadSimulationSamples() {
    const response = await fetch(`${apiBase}/api/simulation/samples`, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`Simulation sample request failed: ${response.status}`);
    }
    const payload = await response.json();
    if (!Array.isArray(payload.samples) || payload.samples.length === 0) {
      throw new Error("Simulation API returned no samples");
    }
    return payload.samples;
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
      const rectangle = window.Cesium.Rectangle.fromDegrees(
        bbox.west,
        bbox.south,
        bbox.east,
        bbox.north
      );
      const forecast = state.viewer.entities.add({
        id: `${caseData.case_id}-forecast-overlay`,
        name: `${caseData.case_name} forecast footprint`,
        show: state.forecastVisible,
        rectangle: {
          coordinates: rectangle,
          material: new window.Cesium.ImageMaterialProperty({
            image: assetUrl(caseData.forecast_overlay_png),
            transparent: true,
            color: window.Cesium.Color.WHITE.withAlpha(state.overlayOpacity),
          }),
        },
      });
      const observed = state.viewer.entities.add({
        id: `${caseData.case_id}-observed-overlay`,
        name: `${caseData.case_name} observed FIRMS evidence`,
        show: state.observedVisible,
        rectangle: {
          coordinates: rectangle,
          material: new window.Cesium.ImageMaterialProperty({
            image: assetUrl(caseData.observed_overlay_png),
            transparent: true,
            color: window.Cesium.Color.WHITE.withAlpha(Math.min(1, state.overlayOpacity + 0.12)),
          }),
        },
      });
      const extent = state.viewer.entities.add({
        id: `${caseData.case_id}-analysis-extent`,
        name: `${caseData.case_name} analysis extent`,
        rectangle: {
          coordinates: rectangle,
          material: colorForCase(index, 0.04),
          outline: true,
          outlineColor: colorForCase(index, 0.95),
        },
      });
      const marker = state.viewer.entities.add({
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
      });
      marker.description = [
        `<strong>${caseData.case_name}</strong>`,
        `<br>Peak probability: ${percent(caseData.sample_peak_probability)}`,
        `<br>Brier improvement: ${signedDecimal(caseData.brier_improvement_vs_persistence)}`,
      ].join("");
      return { forecast, observed, extent, marker };
    });
    updateOverlayLayers();
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
    renderScenarioSample();
    renderCaseButtons();
  }

  function selectedSimulationSampleId() {
    if (state.simulationSamples.length > 0) {
      return state.simulationSamples[state.selectedIndex % state.simulationSamples.length].case_id;
    }
    return `phase5b_sim_${String(state.selectedIndex).padStart(4, "0")}`;
  }

  function renderScenarioSample() {
    els.scenarioSample.textContent = selectedSimulationSampleId();
    els.scenarioPeak.textContent = "--";
    els.scenarioMean.textContent = "--";
    els.scenarioFootprint.textContent = "--";
    els.scenarioUpdated.textContent = "--";
  }

  function scenarioControls() {
    return {
      wind_speed_multiplier: Number(els.windSpeedMultiplier.value),
      wind_direction_delta_degrees: Number(els.windDirectionDelta.value),
      base_spread_rate_multiplier: Number(els.spreadRateMultiplier.value),
      include_probability_grid: true,
      max_grid_size: 64,
    };
  }

  function renderScenarioControlValues() {
    els.windSpeedValue.textContent = `${Number(els.windSpeedMultiplier.value).toFixed(2)}x`;
    els.windDirectionValue.textContent = `${Number(els.windDirectionDelta.value).toFixed(0)} deg`;
    els.spreadRateValue.textContent = `${Number(els.spreadRateMultiplier.value).toFixed(2)}x`;
  }

  function setScenarioStatus(label, stateName) {
    els.scenarioStatus.textContent = label;
    els.scenarioStatus.dataset.state = stateName;
  }

  function scenarioCanvasFromGrid(grid) {
    const height = grid.length;
    const width = height > 0 && Array.isArray(grid[0]) ? grid[0].length : 0;
    if (height === 0 || width === 0) {
      throw new Error("Scenario probability grid is empty");
    }
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const context = canvas.getContext("2d");
    if (!context) {
      throw new Error("Scenario canvas is unavailable");
    }
    const imageData = context.createImageData(width, height);
    grid.forEach((row, y) => {
      row.forEach((value, x) => {
        const probability = Math.max(0, Math.min(1, Number(value)));
        const offset = (y * width + x) * 4;
        const warm = Math.min(1, probability * 1.35);
        imageData.data[offset] = Math.round(255);
        imageData.data[offset + 1] = Math.round(210 - warm * 150);
        imageData.data[offset + 2] = Math.round(40 - warm * 30);
        imageData.data[offset + 3] = probability < 0.08 ? 0 : Math.round(35 + probability * 205);
      });
    });
    context.putImageData(imageData, 0, 0);
    return canvas;
  }

  function removeScenarioOverlay() {
    if (state.viewer && state.scenarioOverlay) {
      state.viewer.entities.remove(state.scenarioOverlay);
    }
    state.scenarioOverlay = null;
    state.scenarioCanvas = null;
  }

  function updateScenarioOverlay(payload) {
    const grid = payload.probability_grid;
    if (!Array.isArray(grid) || grid.length === 0) {
      removeScenarioOverlay();
      return;
    }
    const latestHorizon = grid[grid.length - 1];
    const caseData = state.manifest.cases[state.selectedIndex];
    const bbox = caseData.wgs84_bbox;
    removeScenarioOverlay();
    state.scenarioCanvas = scenarioCanvasFromGrid(latestHorizon);
    state.scenarioOverlay = state.viewer.entities.add({
      id: `${caseData.case_id}-scenario-overlay`,
      name: `${caseData.case_name} scenario probability`,
      show: state.scenarioVisible,
      rectangle: {
        coordinates: window.Cesium.Rectangle.fromDegrees(
          bbox.west,
          bbox.south,
          bbox.east,
          bbox.north
        ),
        material: new window.Cesium.ImageMaterialProperty({
          image: state.scenarioCanvas,
          transparent: true,
          color: window.Cesium.Color.WHITE.withAlpha(Math.min(1, state.overlayOpacity + 0.08)),
        }),
      },
    });
  }

  async function runScenarioInference() {
    if (!state.simulationApiAvailable) {
      setScenarioStatus("API offline", "offline");
      return;
    }
    const requestId = (state.scenarioRequestId += 1);
    const sampleId = selectedSimulationSampleId();
    setScenarioStatus("Running", "running");
    els.runScenario.disabled = true;
    try {
      const response = await fetch(
        `${apiBase}/api/simulation/surrogate/${encodeURIComponent(sampleId)}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(scenarioControls()),
        }
      );
      if (!response.ok) {
        throw new Error(`Simulation inference failed: ${response.status}`);
      }
      const payload = await response.json();
      if (requestId !== state.scenarioRequestId) {
        return;
      }
      const summary = payload.summary || {};
      els.scenarioPeak.textContent = percent(summary.peak_probability || 0, 1);
      els.scenarioMean.textContent = percent(summary.mean_probability || 0, 1);
      els.scenarioFootprint.textContent = percent(summary.predicted_positive_fraction || 0, 1);
      els.scenarioUpdated.textContent = new Date().toLocaleTimeString(undefined, {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });
      updateScenarioOverlay(payload);
      setScenarioStatus("Updated", "ready");
    } catch (error) {
      console.error(error);
      setScenarioStatus("API error", "offline");
    } finally {
      if (requestId === state.scenarioRequestId) {
        els.runScenario.disabled = false;
      }
    }
  }

  function resetScenarioControls() {
    els.windSpeedMultiplier.value = "1";
    els.windDirectionDelta.value = "0";
    els.spreadRateMultiplier.value = "1";
    renderScenarioControlValues();
    renderScenarioSample();
    void runScenarioInference();
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
    void runScenarioInference();
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

  function updateOverlayLayers() {
    state.entities.forEach(({ forecast, observed }) => {
      forecast.show = state.forecastVisible;
      observed.show = state.observedVisible;
      forecast.rectangle.material.color = window.Cesium.Color.WHITE.withAlpha(
        state.overlayOpacity
      );
      observed.rectangle.material.color = window.Cesium.Color.WHITE.withAlpha(
        Math.min(1, state.overlayOpacity + 0.12)
      );
    });
    if (state.scenarioOverlay) {
      state.scenarioOverlay.show = state.scenarioVisible;
      state.scenarioOverlay.rectangle.material.color = window.Cesium.Color.WHITE.withAlpha(
        Math.min(1, state.overlayOpacity + 0.08)
      );
    }
  }

  function bindControls() {
    els.zoomIn.addEventListener("click", () => zoomCamera("in"));
    els.zoomOut.addEventListener("click", () => zoomCamera("out"));
    els.tiltView.addEventListener("click", tiltCurrentCase);
    els.northUp.addEventListener("click", resetNorthUp);
    els.forecastLayerToggle.addEventListener("change", () => {
      state.forecastVisible = els.forecastLayerToggle.checked;
      updateOverlayLayers();
    });
    els.observedLayerToggle.addEventListener("change", () => {
      state.observedVisible = els.observedLayerToggle.checked;
      updateOverlayLayers();
    });
    els.scenarioLayerToggle.addEventListener("change", () => {
      state.scenarioVisible = els.scenarioLayerToggle.checked;
      updateOverlayLayers();
    });
    els.overlayOpacity.addEventListener("input", () => {
      state.overlayOpacity = Number(els.overlayOpacity.value);
      updateOverlayLayers();
    });
    [
      els.windSpeedMultiplier,
      els.windDirectionDelta,
      els.spreadRateMultiplier,
    ].forEach((input) => {
      input.addEventListener("input", renderScenarioControlValues);
      input.addEventListener("change", () => void runScenarioInference());
    });
    els.runScenario.addEventListener("click", () => void runScenarioInference());
    els.resetScenario.addEventListener("click", resetScenarioControls);
    els.flyHome.addEventListener("click", flyToAllCases);
    els.openExplorer.addEventListener("click", () => {
      window.location.href = "./index.html";
    });
  }

  async function init() {
    bindControls();
    renderScenarioControlValues();
    try {
      state.manifest = await loadManifest();
      const initialIndex = state.manifest.cases.findIndex((caseData) => {
        return caseData.case_id === initialCaseId;
      });
      if (initialIndex >= 0) {
        state.selectedIndex = initialIndex;
      }
      state.viewer = createViewer();
      addCaseEntities();
      renderSelectedCase();
      flyToAllCases();
      try {
        state.simulationSamples = await loadSimulationSamples();
        state.simulationApiAvailable = true;
        setScenarioStatus("API ready", "ready");
        renderScenarioSample();
        void runScenarioInference();
      } catch (error) {
        console.info(error);
        state.simulationApiAvailable = false;
        setScenarioStatus("API offline", "offline");
      }
    } catch (error) {
      console.error(error);
      els.error.hidden = false;
    }
  }

  init();
})();
