(function () {
  const assetRoot = window.location.pathname.includes("/frontend/") ? "../" : "./";
  const manifestUrl = assetUrl("data/manifests/firms_next_day_explorer_manifest.json");
  const state = {
    manifest: null,
    selectedIndex: 0,
    zoom: 1,
  };

  const els = {
    caseList: document.getElementById("caseList"),
    guardrailList: document.getElementById("guardrailList"),
    caseId: document.getElementById("caseId"),
    caseName: document.getElementById("caseName"),
    peakProbability: document.getElementById("peakProbability"),
    threshold: document.getElementById("threshold"),
    brier: document.getElementById("brier"),
    ece: document.getElementById("ece"),
    previewImage: document.getElementById("previewImage"),
    referenceTime: document.getElementById("referenceTime"),
    targetTime: document.getElementById("targetTime"),
    sampleIndex: document.getElementById("sampleIndex"),
    precision: document.getElementById("precision"),
    recall: document.getElementById("recall"),
    f1: document.getElementById("f1"),
    gridShape: document.getElementById("gridShape"),
    gridCrs: document.getElementById("gridCrs"),
    resolution: document.getElementById("resolution"),
    loadError: document.getElementById("loadError"),
    zoomOut: document.getElementById("zoomOut"),
    zoomIn: document.getElementById("zoomIn"),
    resetZoom: document.getElementById("resetZoom"),
  };

  function percent(value, digits = 1) {
    return `${(Number(value) * 100).toFixed(digits)}%`;
  }

  function decimal(value, digits = 3) {
    return Number(value).toFixed(digits);
  }

  function dateLabel(value) {
    const parsed = new Date(value);
    if (Number.isNaN(parsed.valueOf())) {
      return value;
    }
    return parsed.toLocaleString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  function assetUrl(path) {
    return `${assetRoot}${path}`;
  }

  function setZoom(nextZoom) {
    state.zoom = Math.min(2.2, Math.max(0.65, nextZoom));
    els.previewImage.style.transform = `scale(${state.zoom})`;
  }

  function renderCaseButtons() {
    els.caseList.replaceChildren();
    state.manifest.cases.forEach((caseData, index) => {
      const button = document.createElement("button");
      button.className = "case-button";
      button.type = "button";
      button.setAttribute("aria-current", index === state.selectedIndex ? "true" : "false");
      const label = document.createElement("span");
      const name = document.createElement("strong");
      const target = document.createElement("span");
      const probability = document.createElement("span");
      name.textContent = caseData.case_name;
      target.textContent = dateLabel(caseData.target_time);
      probability.className = "probability";
      probability.textContent = percent(caseData.sample_peak_probability, 0);
      label.append(name, target);
      button.append(label, probability);
      button.addEventListener("click", () => {
        state.selectedIndex = index;
        setZoom(1);
        render();
      });
      els.caseList.append(button);
    });
  }

  function renderGuardrails() {
    els.guardrailList.replaceChildren();
    state.manifest.guardrails.forEach((guardrail) => {
      const item = document.createElement("li");
      item.textContent = guardrail;
      els.guardrailList.append(item);
    });
  }

  function renderSelectedCase() {
    const caseData = state.manifest.cases[state.selectedIndex];
    document.title = `FireTwin Explorer - ${caseData.case_name}`;
    els.caseId.textContent = caseData.case_id;
    els.caseName.textContent = caseData.case_name;
    els.peakProbability.textContent = percent(caseData.sample_peak_probability);
    els.threshold.textContent = decimal(caseData.recommended_threshold, 3);
    els.brier.textContent = decimal(caseData.observed_brier_score, 5);
    els.ece.textContent = decimal(caseData.expected_calibration_error, 5);
    els.previewImage.src = assetUrl(caseData.preview_png);
    els.previewImage.alt = `${caseData.case_name} learned forecast preview`;
    els.referenceTime.textContent = dateLabel(caseData.reference_time);
    els.targetTime.textContent = dateLabel(caseData.target_time);
    els.sampleIndex.textContent = String(caseData.sample_index);
    els.precision.textContent = percent(caseData.recommended_precision);
    els.recall.textContent = percent(caseData.recommended_recall);
    els.f1.textContent = decimal(caseData.recommended_f1_score, 3);
    els.gridShape.textContent = `${caseData.grid_shape.height} x ${caseData.grid_shape.width}`;
    els.gridCrs.textContent = caseData.grid_crs;
    els.resolution.textContent = caseData.resolution_m
      ? `${caseData.resolution_m.toFixed(0)} m`
      : "unknown";
  }

  function render() {
    renderCaseButtons();
    renderSelectedCase();
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

  function bindControls() {
    els.zoomOut.addEventListener("click", () => setZoom(state.zoom - 0.15));
    els.zoomIn.addEventListener("click", () => setZoom(state.zoom + 0.15));
    els.resetZoom.addEventListener("click", () => setZoom(1));
    document.addEventListener("keydown", (event) => {
      if (!state.manifest) {
        return;
      }
      if (event.key === "ArrowRight") {
        state.selectedIndex = (state.selectedIndex + 1) % state.manifest.cases.length;
        setZoom(1);
        render();
      }
      if (event.key === "ArrowLeft") {
        state.selectedIndex =
          (state.selectedIndex - 1 + state.manifest.cases.length) % state.manifest.cases.length;
        setZoom(1);
        render();
      }
    });
  }

  async function init() {
    bindControls();
    try {
      state.manifest = await loadManifest();
      renderGuardrails();
      render();
    } catch (error) {
      console.error(error);
      els.loadError.hidden = false;
    }
  }

  init();
})();
