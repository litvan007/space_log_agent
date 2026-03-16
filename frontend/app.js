const ANOMALY_PATH = ["start", "pre_hook", "classification", "deep_research", "plan_uv", "verifier", "end"];
const NOMINAL_PATH = ["start", "pre_hook", "classification", "nominal_summary", "end"];

const GRAPH_LAYOUT = {
  width: 720,
  height: 520,
  nodeWidth: 160,
  nodeHeight: 52,
};

const GRAPH_NODES = {
  start: { x: 280, y: 18, title: "start", hint: "вход окна", kind: "system" },
  pre_hook: { x: 280, y: 92, title: "pre_hook", hint: "обогащение", kind: "pre" },
  classification: { x: 280, y: 166, title: "classification", hint: "классификация", kind: "class" },
  deep_research: { x: 470, y: 250, title: "deep_research", hint: "углубленный анализ", kind: "analysis" },
  plan_uv: { x: 470, y: 324, title: "plan_uv", hint: "формирование УВ", kind: "analysis" },
  verifier: { x: 470, y: 398, title: "post_hook", hint: "проверка плана", kind: "analysis" },
  nominal_summary: { x: 90, y: 324, title: "nominal_summary", hint: "краткий отчет", kind: "analysis" },
  end: { x: 280, y: 458, title: "final_report", hint: "отчет оператору", kind: "system" },
};

const GRAPH_EDGES = [
  { from: "start", to: "pre_hook", style: "trunk" },
  { from: "pre_hook", to: "classification", style: "trunk" },
  { from: "classification", to: "deep_research", style: "branch" },
  { from: "classification", to: "nominal_summary", style: "branch" },
  { from: "deep_research", to: "plan_uv", style: "right" },
  { from: "plan_uv", to: "verifier", style: "right" },
  { from: "verifier", to: "end", style: "merge" },
  { from: "nominal_summary", to: "end", style: "merge" },
];

const SAMPLE_WINDOW = {
  window_id: "window_02531",
  timestamp_start: "2024-05-18T18:37:00Z",
  timestamp_end: "2024-05-18T18:47:00Z",
  raw_telemetry_ref: "/data/uhf_telemetry.csv",
  tle_ref: "/data/tle_opssat.txt",
};

const DEMO_REPORT = `### Краткий вывод
В окне 18:37-18:47 UTC зафиксирована смешанная аномалия: рост температуры NanoMind и ACU2, просадка батареи и потеря устойчивости ADCS на фоне работы в затмении.

### Гипотеза причины
Наиболее вероятна комбинация перегрузки вычислительного контура и повышенного энергопотребления, которая привела к локальному перегреву и ухудшению устойчивости ориентации.

### Рекомендованные УВ
1. LIMIT_PAYLOAD_POWER: Ограничить нагрузку полезной нагрузки и отключить второстепенные потребители.
2. SWITCH_TO_BACKUP_ADCS: Перевести контур ориентации на резервную конфигурацию.
3. RUN_THERMAL_DIAGNOSTICS: Выполнить термодиагностику NanoMind и ACU2.
4. MONITOR_BATTERY_VOLTAGE: Усилить мониторинг напряжения батареи на следующих двух окнах.

### Верификация плана
valid: true
violations: none
constraints: сохранить канал связи, не включать энергоемкие режимы в тени
recommendations: проверить телеметрию EPS после разгрузки, подтвердить стабилизацию угловых скоростей`;

const DEMO_LOG_LINES = [
  "2026-03-17 01:24:11 | INFO | space_log_agent.api.routes:start_envelope_run:108 | Demo single-window run prepared for screenshot",
  "2026-03-17 01:24:12 | INFO | space_log_agent.graph:classification_node:89 | Классификация окна manual_20240518_1837_1847: anomaly=True, confidence=0.84, class=MIXED",
  "2026-03-17 01:24:13 | INFO | space_log_agent.agent:run_deep_research_sgr_async:149 | Deep research structured uv_plan получен: 4 действий",
  "2026-03-17 01:24:14 | INFO | space_log_agent.graph:post_hook_node:256 | Post-hook валидация окна manual_20240518_1837_1847: valid=True, actions=4",
];

/**
 * Build a compact telemetry point for the demo interval.
 *
 * @param {string} timestampUtc UTC timestamp of the sample point.
 * @param {Record<string, number>} values Channel values for one sample.
 * @returns {{timestamp_utc: string, values: Record<string, number>}} Demo telemetry point.
 */
function buildDemoTelemetryPoint(timestampUtc, values) {
  return { timestamp_utc: timestampUtc, values };
}

/**
 * Build telemetry samples that visually show the anomaly progression.
 *
 * @returns {{source_csv_path: string, resample_freq: string, channels: string[], points: Array}} Demo telemetry window payload.
 */
function buildDemoTelemetryWindow() {
  const channels = ["Battery_Voltage", "Battery_Temp", "NanoMind_Temp", "ACU2_Temp", "Background_RSSI", "Z_Coarse_Spin", "PD1_CSS_theta"];
  const points = [
    buildDemoTelemetryPoint("2024-05-18T18:37:00Z", { Battery_Voltage: 8212, Battery_Temp: 286.2, NanoMind_Temp: 298.4, ACU2_Temp: 295.6, Background_RSSI: -98, Z_Coarse_Spin: 0.018, PD1_CSS_theta: 0.011 }),
    buildDemoTelemetryPoint("2024-05-18T18:38:00Z", { Battery_Voltage: 8189, Battery_Temp: 289.4, NanoMind_Temp: 304.8, ACU2_Temp: 301.9, Background_RSSI: -100, Z_Coarse_Spin: 0.024, PD1_CSS_theta: 0.016 }),
    buildDemoTelemetryPoint("2024-05-18T18:39:00Z", { Battery_Voltage: 8161, Battery_Temp: 293.1, NanoMind_Temp: 311.5, ACU2_Temp: 308.7, Background_RSSI: -102, Z_Coarse_Spin: 0.033, PD1_CSS_theta: 0.024 }),
    buildDemoTelemetryPoint("2024-05-18T18:40:00Z", { Battery_Voltage: 8128, Battery_Temp: 297.6, NanoMind_Temp: 319.8, ACU2_Temp: 316.4, Background_RSSI: -104, Z_Coarse_Spin: 0.041, PD1_CSS_theta: 0.035 }),
    buildDemoTelemetryPoint("2024-05-18T18:41:00Z", { Battery_Voltage: 8096, Battery_Temp: 301.8, NanoMind_Temp: 327.7, ACU2_Temp: 323.1, Background_RSSI: -107, Z_Coarse_Spin: 0.056, PD1_CSS_theta: 0.049 }),
    buildDemoTelemetryPoint("2024-05-18T18:42:00Z", { Battery_Voltage: 8074, Battery_Temp: 305.9, NanoMind_Temp: 333.9, ACU2_Temp: 329.4, Background_RSSI: -109, Z_Coarse_Spin: 0.071, PD1_CSS_theta: 0.061 }),
    buildDemoTelemetryPoint("2024-05-18T18:43:00Z", { Battery_Voltage: 8061, Battery_Temp: 308.6, NanoMind_Temp: 337.8, ACU2_Temp: 333.2, Background_RSSI: -111, Z_Coarse_Spin: 0.079, PD1_CSS_theta: 0.072 }),
    buildDemoTelemetryPoint("2024-05-18T18:44:00Z", { Battery_Voltage: 8052, Battery_Temp: 310.1, NanoMind_Temp: 339.2, ACU2_Temp: 334.8, Background_RSSI: -112.4, Z_Coarse_Spin: 0.084, PD1_CSS_theta: 0.079 }),
  ];
  return { source_csv_path: SAMPLE_WINDOW.raw_telemetry_ref, resample_freq: "30s", channels, points };
}

/**
 * Build the enriched envelope used on the demo screen.
 *
 * @returns {{window_id: string, timestamp_start: string, timestamp_end: string, alerts: string[], errors: string[], orbit_context: Record<string, number|boolean|string>, precomputed_features: Record<string, string>, raw_telemetry_ref: string, tle_ref: string}} Demo envelope.
 */
function buildDemoEnvelope() {
  return {
    window_id: "manual_20240518_1837_1847",
    timestamp_start: SAMPLE_WINDOW.timestamp_start,
    timestamp_end: SAMPLE_WINDOW.timestamp_end,
    alerts: ["THERMAL_OVERHEAT", "POWER_DEGRADATION", "ADCS_STABILIZATION_LOSS", "SENSOR_DEGRADATION"],
    errors: ["CRITICAL_POWER_THERMAL_COUPLING"],
    orbit_context: {
      orbit_lat: 41.284,
      orbit_lon: 56.118,
      orbit_altitude_km: 516.42,
      sun_exposure: false,
      is_eclipse: true,
      ground_station_visible: true,
      distance_to_ground_station_km: 1842.6,
      orbital_phase: 0.67,
    },
    precomputed_features: { analysis_scenario: "mixed" },
    raw_telemetry_ref: SAMPLE_WINDOW.raw_telemetry_ref,
    tle_ref: SAMPLE_WINDOW.tle_ref,
  };
}

/**
 * Build a screenshot-ready dataset slice with one selected anomaly window.
 *
 * @returns {Array<object>} Demo dataset items.
 */
function buildDemoDatasetItems() {
  const telemetryWindow = buildDemoTelemetryWindow();
  const envelope = buildDemoEnvelope();
  const uvPlanDetails = [
    { action: "LIMIT_PAYLOAD_POWER", description: "Снять второстепенную нагрузку и стабилизировать энергетический контур.", priority: "HIGH", prechecks: ["Подтвердить уровень связи", "Проверить запас по батарее"], postchecks: ["Проконтролировать Battery_Voltage", "Сверить новые температуры"] },
    { action: "SWITCH_TO_BACKUP_ADCS", description: "Перевести ADCS на резервный режим для уменьшения ошибки ориентации.", priority: "HIGH", prechecks: ["Подтвердить актуальность эфемерид", "Не выполнять во время маневра"], postchecks: ["Оценить Z_Coarse_Spin", "Проверить устойчивость по CSS"] },
    { action: "RUN_THERMAL_DIAGNOSTICS", description: "Выполнить короткий цикл термодиагностики NanoMind и ACU2.", priority: "MEDIUM", prechecks: ["Сохранить текущую телеметрию"], postchecks: ["Сравнить пиковые температуры"] },
    { action: "MONITOR_BATTERY_VOLTAGE", description: "Усилить контроль деградации EPS на двух следующих окнах.", priority: "MEDIUM", prechecks: ["Подготовить окно наблюдения"], postchecks: ["Подтвердить возврат напряжения выше порога"] },
  ];
  return [
    { window_id: "window_02529", timestamp_start: "2024-05-18T18:17:00Z", timestamp_end: "2024-05-18T18:27:00Z", report: "### Краткий вывод\nНоминальное окно без подтвержденной НС.", status: "completed", summary: "Номинальный проход без подтвержденной НС.", index: 1, total: 3, classification: { anomaly_class: "UNKNOWN", confidence_alarm: 0.18, is_anomaly: false } },
    { window_id: envelope.window_id, timestamp_start: envelope.timestamp_start, timestamp_end: envelope.timestamp_end, report: DEMO_REPORT, status: "completed", summary: "Смешанная НС: тепловая и энергетическая деградация с вовлечением ADCS.", index: 2, total: 3, classification: { anomaly_class: "MIXED", confidence_alarm: 0.84, is_anomaly: true }, envelope, telemetryWindow, orbitTrack: [], orbitSource: "Источник: demo orbit projection", uv_post_check: { valid: true, violations: [], constraints: ["сохранить канал связи", "не включать энергоемкие режимы в тени"], recommendations: ["проверить EPS после разгрузки", "подтвердить стабилизацию ADCS"] }, uv_plan_details: uvPlanDetails },
    { window_id: "window_02533", timestamp_start: "2024-05-18T18:57:00Z", timestamp_end: "2024-05-18T19:07:00Z", report: "", status: "queued", summary: "Следующее окно ожидает обработки.", index: 3, total: 3, classification: { anomaly_class: "UNKNOWN", confidence_alarm: 0.0, is_anomaly: false } },
  ];
}

/**
 * Seed the dashboard with a presentable demo state for the first render.
 *
 * @returns {void}
 */
function applyDemoScene() {
  const demoItems = buildDemoDatasetItems();
  const selectedItem = demoItems[1];
  state.datasetItems = demoItems;
  state.selectedDatasetWindowId = selectedItem.window_id;
  state.finalReport = DEMO_REPORT;
  state.backendReport = DEMO_REPORT;
  state.backendEnvelope = selectedItem.envelope;
  state.backendTelemetryWindow = selectedItem.telemetryWindow;
  state.backendLogLines = [...DEMO_LOG_LINES];
  state.orbitTrack = [];
  state.orbitSource = selectedItem.orbitSource;
  state.runId = "demo_space_run_02531";
  state.runMode = "envelope";
  state.runStatus = { phase: "completed", text: "Точечный анализ окна завершён.", windowsCount: 1, processedCount: 1, currentWindowId: selectedItem.window_id, startedAtUtc: "2026-03-17T01:24:11Z", completedAtUtc: "2026-03-17T01:24:14Z", error: "" };
  state.windowProgressById = {
    [selectedItem.window_id]: { path: [...ANOMALY_PATH], branchResolved: true, currentNode: null, completedNodes: [...ANOMALY_PATH] },
    window_02529: { path: [...NOMINAL_PATH], branchResolved: true, currentNode: null, completedNodes: [...NOMINAL_PATH] },
    window_02533: { path: ["start"], branchResolved: false, currentNode: "start", completedNodes: [] },
  };
  syncManualWindowInputs(selectedItem);
}

const DASHBOARD_GRID = {
  cols: 12,
  rowHeight: 28,
  gap: 10,
};

const DEFAULT_LIVE_WINDOW_LIMIT = 12;

const WIDGET_DEFAULTS = {
  satellite_model: { x: 1, y: 1, w: 3, h: 11, minW: 3, minH: 8 },
  orbit_context: { x: 4, y: 1, w: 3, h: 7, minW: 3, minH: 6 },
  orbit_track: { x: 7, y: 1, w: 3, h: 10, minW: 3, minH: 7 },
  dataset_windows: { x: 8, y: 12, w: 5, h: 10, minW: 3, minH: 7 },
  run_status: { x: 4, y: 8, w: 3, h: 4, minW: 3, minH: 4 },
  telemetry_stream: { x: 10, y: 1, w: 3, h: 10, minW: 3, minH: 7 },
  agent_graph: { x: 1, y: 12, w: 7, h: 18, minW: 6, minH: 12 },
  final_report: { x: 8, y: 12, w: 5, h: 18, minW: 4, minH: 10 },
  uv_plan: { x: 1, y: 30, w: 4, h: 9, minW: 3, minH: 7 },
  verify_result: { x: 5, y: 30, w: 3, h: 9, minW: 3, minH: 7 },
  backend_logs: { x: 1, y: 40, w: 12, h: 18, minW: 6, minH: 10 },
};

const INTEL_TABS = ["evidence", "agent", "plan", "constraints", "logs"];

const STAGE_BOARD_ORDER = ["start", "pre_hook", "classification", "deep_research", "plan_uv", "verifier", "nominal_summary", "end"];

const STAGE_META = {
  start: { title: "__start__", hint: "вход интервала", lane: "center", row: "1" },
  pre_hook: { title: "pre_hook", hint: "обогащение", lane: "center", row: "3" },
  classification: { title: "classification", hint: "маршрутизация", lane: "center", row: "5" },
  deep_research: { title: "deep_research", hint: "углубленный анализ", lane: "right", row: "7" },
  plan_uv: { title: "plan_uv", hint: "проект УВ", lane: "right", row: "9" },
  verifier: { title: "post_hook", hint: "валидация", lane: "right", row: "11" },
  nominal_summary: { title: "nominal_summary", hint: "краткий штатный отчет", lane: "left", row: "7" },
  end: { title: "__end__", hint: "итог оператору", lane: "center", row: "13" },
};

const STAGE_LINKS = [
  { from: "start", to: "pre_hook", row: "2", lane: "center", kind: "down", glyph: "↓" },
  { from: "pre_hook", to: "classification", row: "4", lane: "center", kind: "down", glyph: "↓" },
  { from: "classification", to: "nominal_summary", row: "6", lane: "left", kind: "branch-left", glyph: "↙" },
  { from: "classification", to: "deep_research", row: "6", lane: "right", kind: "branch-right", glyph: "↘" },
  { from: "deep_research", to: "plan_uv", row: "8", lane: "right", kind: "down", glyph: "↓" },
  { from: "plan_uv", to: "verifier", row: "10", lane: "right", kind: "down", glyph: "↓" },
  { from: "nominal_summary", to: "end", row: "12", lane: "left", kind: "merge-left", glyph: "↘" },
  { from: "verifier", to: "end", row: "12", lane: "right", kind: "merge-right", glyph: "↙" },
];

const dashboard = {
  main: null,
};

const dom = {
  btnMainView: document.getElementById("btnMainView"),
  btnResearchMode: document.getElementById("btnResearchMode"),
  scenarioSelect: document.getElementById("scenarioSelect"),
  backendUrl: document.getElementById("backendUrl"),
  showDebugLogs: document.getElementById("showDebugLogs"),
  btnRun: document.getElementById("btnRun"),
  btnResetLayout: document.getElementById("btnResetLayout"),
  btnReset: document.getElementById("btnReset"),
  btnTelemetryToggle: document.getElementById("btnTelemetryToggle"),
  btnRunWindow: document.getElementById("btnRunWindow"),
  btnIntelEvidence: document.getElementById("btnIntelEvidence"),
  btnIntelAgent: document.getElementById("btnIntelAgent"),
  btnIntelPlan: document.getElementById("btnIntelPlan"),
  btnIntelConstraints: document.getElementById("btnIntelConstraints"),
  btnIntelLogs: document.getElementById("btnIntelLogs"),
  incidentBadge: document.getElementById("incidentBadge"),
  mainView: document.getElementById("mainView"),
  researchView: document.getElementById("researchView"),
  missionRunBadge: document.getElementById("missionRunBadge"),
  missionRunStatus: document.getElementById("missionRunStatus"),
  missionCaseCount: document.getElementById("missionCaseCount"),
  manualWindowStart: document.getElementById("manualWindowStart"),
  manualWindowEnd: document.getElementById("manualWindowEnd"),
  missionDatasetWindows: document.getElementById("missionDatasetWindows"),
  missionStageMeta: document.getElementById("missionStageMeta"),
  missionStageBoard: document.getElementById("missionStageBoard"),
  missionVerdictBadge: document.getElementById("missionVerdictBadge"),
  missionVerdict: document.getElementById("missionVerdict"),
  missionActionBadge: document.getElementById("missionActionBadge"),
  missionOperatorNow: document.getElementById("missionOperatorNow"),
  missionIntelContent: document.getElementById("missionIntelContent"),
  orbitContext: document.getElementById("orbitContext"),
  orbitCanvas: document.getElementById("orbitCanvas"),
  orbitSource: document.getElementById("orbitSource"),
  telemetryMeta: document.getElementById("telemetryMeta"),
  telemetryStream: document.getElementById("telemetryStream"),
  dashboardGrid: document.getElementById("dashboardGrid"),
  pipelineGraph: document.getElementById("pipelineGraph"),
  backendLogs: document.getElementById("backendLogs"),
  datasetWindows: document.getElementById("datasetWindows"),
  uvPlan: document.getElementById("uvPlan"),
  verifyBlock: document.getElementById("verifyBlock"),
  finalReport: document.getElementById("finalReport"),
  agentState: document.getElementById("agentState"),
  runStatus: document.getElementById("runStatus"),
};

const state = {
  scenarioId: "mixed",
  surface: "main",
  activeIntelTab: "evidence",
  telemetryExpanded: false,
  manualWindowStart: SAMPLE_WINDOW.timestamp_start,
  manualWindowEnd: SAMPLE_WINDOW.timestamp_end,
  graphZoom: 1,
  finalReport: "n/a",
  backendReport: "",
  datasetItems: [],
  selectedDatasetWindowId: "",
  orbitTrack: [],
  orbitSource: "n/a",
  backendEnvelope: null,
  backendTelemetryWindow: null,
  backendLogLines: [],
  showDebugLogs: false,
  detailRequestSeq: 0,
  runId: "",
  runMode: "dataset",
  runSocket: null,
  runStatus: {
    phase: "idle",
    text: "Ожидание запуска.",
    windowsCount: 0,
    processedCount: 0,
    currentWindowId: "",
    startedAtUtc: "",
    completedAtUtc: "",
    error: "",
  },
  windowProgressById: {},
  graphPan: {
    active: false,
    startX: 0,
    startY: 0,
    scrollLeft: 0,
    scrollTop: 0,
  },
};

init();

function init() {
  dom.scenarioSelect.value = state.scenarioId;
  syncSurfaceFromHash();

  if (dom.btnMainView) {
    dom.btnMainView.addEventListener("click", () => {
      setSurface("main");
    });
  }
  if (dom.btnResearchMode) {
    dom.btnResearchMode.addEventListener("click", () => {
      setSurface("research");
    });
  }
  dom.scenarioSelect.addEventListener("change", () => {
    state.scenarioId = dom.scenarioSelect.value;
    resetState();
  });
  if (dom.showDebugLogs) {
    dom.showDebugLogs.checked = false;
    dom.showDebugLogs.addEventListener("change", () => {
      dom.showDebugLogs.checked = false;
    });
  }
  if (dom.btnTelemetryToggle) {
    dom.btnTelemetryToggle.addEventListener("click", () => {
      state.telemetryExpanded = !state.telemetryExpanded;
      renderTelemetryStream();
    });
  }
  if (dom.btnIntelEvidence) {
    dom.btnIntelEvidence.addEventListener("click", () => setIntelTab("evidence"));
  }
  if (dom.btnIntelAgent) {
    dom.btnIntelAgent.addEventListener("click", () => setIntelTab("agent"));
  }
  if (dom.btnIntelPlan) {
    dom.btnIntelPlan.addEventListener("click", () => setIntelTab("plan"));
  }
  if (dom.btnIntelConstraints) {
    dom.btnIntelConstraints.addEventListener("click", () => setIntelTab("constraints"));
  }
  if (dom.btnIntelLogs) {
    dom.btnIntelLogs.addEventListener("click", () => setIntelTab("logs"));
  }

  dom.btnRun.addEventListener("click", handleRunClick);
  dom.btnRunWindow.addEventListener("click", runFocusedWindow);
  if (dom.btnResetLayout) {
    dom.btnResetLayout.addEventListener("click", resetDashboardLayout);
  }
  dom.btnReset.addEventListener("click", () => resetState());
  if (dom.manualWindowStart) {
    dom.manualWindowStart.addEventListener("input", () => {
      state.manualWindowStart = dom.manualWindowStart.value.trim();
    });
  }
  if (dom.manualWindowEnd) {
    dom.manualWindowEnd.addEventListener("input", () => {
      state.manualWindowEnd = dom.manualWindowEnd.value.trim();
    });
  }
  if (dom.pipelineGraph) {
    dom.pipelineGraph.addEventListener("wheel", onGraphWheel, { passive: false });
    dom.pipelineGraph.addEventListener("pointerdown", onGraphPointerDown);
  }
  window.addEventListener("resize", () => {
    if (dashboard.main && state.surface === "research") {
      packAndRenderPanel(dashboard.main);
    }
  });
  window.addEventListener("hashchange", syncSurfaceFromHash);

  initializeWidgetDashboard();
  resetState();
}

async function handleRunClick() {
  await startLiveDatasetRun();
}

function resetState(closeSocket = true) {
  if (closeSocket) {
    closeRunSocket();
  }

  state.finalReport = "n/a";
  state.backendReport = "";
  state.datasetItems = [];
  state.selectedDatasetWindowId = "";
  state.telemetryExpanded = false;
  state.activeIntelTab = "evidence";
  state.manualWindowStart = SAMPLE_WINDOW.timestamp_start;
  state.manualWindowEnd = SAMPLE_WINDOW.timestamp_end;
  state.backendLogLines = [];
  state.runId = "";
  state.runMode = "dataset";
  state.windowProgressById = {};
  state.runStatus = {
    phase: "idle",
    text: "Ожидание запуска.",
    windowsCount: 0,
    processedCount: 0,
    currentWindowId: "",
    startedAtUtc: "",
    completedAtUtc: "",
    error: "",
  };

  if (dom.agentState) {
    dom.agentState.textContent = "Ожидание";
  }
  setIncidentBadge(`Сценарий: ${getScenarioLabel(state.scenarioId)}`, "badge-warn");
  state.backendEnvelope = null;
  state.backendTelemetryWindow = null;
  state.orbitTrack = [];
  state.orbitSource = "n/a";
  applyDemoScene();

  if (dom.agentState) {
    dom.agentState.textContent = "Готово";
  }

  renderOrbitContext();
  renderTelemetryStream();
  renderPipeline();
  renderBackendLogs();
  renderDatasetWindows();
  renderRunStatus();
  renderUVPlan();
  renderVerify();
  renderReport();
  renderSubsystems(getCurrentAlerts());
  renderOrbitTrack();
  renderMissionControl();
  renderSurface();
}

function resetDashboardLayout() {
  if (state.surface !== "research") {
    return;
  }
  applyWidgetDefaultsToPanel(dashboard.main, WIDGET_DEFAULTS);
  state.graphZoom = 1;
  renderPipeline();
}

function syncSurfaceFromHash() {
  const targetSurface = window.location.hash === "#research" ? "research" : "main";
  setSurface(targetSurface, !window.location.hash);
}

function setSurface(surface, updateHash = true) {
  if (surface !== "main" && surface !== "research") {
    return;
  }
  state.surface = surface;
  if (updateHash) {
    const nextHash = surface === "research" ? "#research" : "#main";
    if (window.location.hash !== nextHash) {
      window.location.hash = nextHash;
    }
  }
  renderSurface();
  renderTelemetryStream();
}

function setIntelTab(tabId) {
  if (!INTEL_TABS.includes(tabId)) {
    return;
  }
  state.activeIntelTab = tabId;
  renderMissionIntel();
}

function renderSurface() {
  if (!dom.mainView || !dom.researchView || !dom.btnMainView || !dom.btnResearchMode) {
    return;
  }
  const isMain = state.surface === "main";
  dom.mainView.hidden = !isMain;
  dom.researchView.hidden = isMain;

  dom.btnMainView.classList.toggle("active", isMain);
  dom.btnMainView.setAttribute("aria-pressed", String(isMain));
  dom.btnResearchMode.classList.toggle("active", !isMain);
  dom.btnResearchMode.setAttribute("aria-pressed", String(!isMain));
  if (dom.btnResetLayout) {
    dom.btnResetLayout.hidden = isMain;
  }

  if (!isMain && dashboard.main) {
    packAndRenderPanel(dashboard.main);
  }
}

function onGraphWheel(event) {
  if (!dom.pipelineGraph.contains(event.target)) {
    return;
  }
  event.preventDefault();
  const previousZoom = state.graphZoom;
  const factor = event.deltaY < 0 ? 1.1 : 0.9;
  const nextZoom = clampNumber(previousZoom * factor, 0.55, 2.2);
  if (Math.abs(nextZoom - previousZoom) < 1e-4) {
    return;
  }

  const rect = dom.pipelineGraph.getBoundingClientRect();
  const cursorX = event.clientX - rect.left;
  const cursorY = event.clientY - rect.top;
  const originX = dom.pipelineGraph.scrollLeft + cursorX;
  const originY = dom.pipelineGraph.scrollTop + cursorY;

  state.graphZoom = nextZoom;
  renderPipeline();

  const ratio = nextZoom / previousZoom;
  dom.pipelineGraph.scrollLeft = originX * ratio - cursorX;
  dom.pipelineGraph.scrollTop = originY * ratio - cursorY;
}

function onGraphPointerDown(event) {
  if (event.target.closest(".studio-node")) {
    return;
  }

  state.graphPan = {
    active: true,
    startX: event.clientX,
    startY: event.clientY,
    scrollLeft: dom.pipelineGraph.scrollLeft,
    scrollTop: dom.pipelineGraph.scrollTop,
  };
  dom.pipelineGraph.classList.add("is-panning");

  const onPointerMove = (moveEvent) => {
    if (!state.graphPan.active) {
      return;
    }
    dom.pipelineGraph.scrollLeft = state.graphPan.scrollLeft - (moveEvent.clientX - state.graphPan.startX);
    dom.pipelineGraph.scrollTop = state.graphPan.scrollTop - (moveEvent.clientY - state.graphPan.startY);
  };

  const onPointerUp = () => {
    state.graphPan.active = false;
    dom.pipelineGraph.classList.remove("is-panning");
    window.removeEventListener("pointermove", onPointerMove);
    window.removeEventListener("pointerup", onPointerUp);
  };

  window.addEventListener("pointermove", onPointerMove);
  window.addEventListener("pointerup", onPointerUp);
}

async function startLiveDatasetRun() {
  resetState(false);
  state.runMode = "dataset";

  const baseUrl = normalizeBaseUrl(dom.backendUrl.value);
  if (!baseUrl) {
    state.runStatus = {
      ...state.runStatus,
      phase: "failed",
      text: "Не задан адрес backend.",
      error: "Укажите backend URL.",
    };
    renderRunStatus();
    renderOperatorSummary();
    return;
  }

  try {
    const response = await fetch(`${baseUrl}/api/v1/runs/dataset`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ limit_windows: DEFAULT_LIVE_WINDOW_LIMIT, scenario: state.scenarioId }),
    });
    if (!response.ok) {
      throw new Error(`run status=${response.status}`);
    }

    const data = await response.json();
    state.runId = data.run_id || "";
    state.runStatus = {
      ...state.runStatus,
      phase: "connecting",
      text: "Подключение к live stream...",
      startedAtUtc: data.created_at_utc || "",
      error: "",
    };
    renderRunStatus();
    renderOperatorSummary();
    openRunSocket(baseUrl, state.runId);
  } catch (error) {
    state.runStatus = {
      ...state.runStatus,
      phase: "failed",
      text: "Не удалось запустить dataset-run.",
      error: String(error),
    };
    state.backendLogLines.push(`ERROR: ${String(error)}`);
    renderRunStatus();
    renderOperatorSummary();
    renderBackendLogs();
  }
}

function openRunSocket(baseUrl, runId) {
  closeRunSocket();

  const wsUrl = buildWebSocketUrl(baseUrl, `/api/v1/runs/${runId}/ws`);
  const socket = new WebSocket(wsUrl);
  state.runSocket = socket;

  socket.addEventListener("open", () => {
    state.runStatus = {
      ...state.runStatus,
      phase: "streaming",
      text: "Live stream подключён.",
      error: "",
    };
    renderRunStatus();
    renderOperatorSummary();
  });

  socket.addEventListener("message", async (event) => {
    try {
      const payload = JSON.parse(event.data);
      await handleRunEvent(payload);
    } catch (error) {
      state.backendLogLines.push(`ERROR: invalid ws payload ${String(error)}`);
      renderBackendLogs();
    }
  });

  socket.addEventListener("error", () => {
    state.runStatus = {
      ...state.runStatus,
      phase: "failed",
      text: "Ошибка WebSocket соединения.",
      error: "Поток live updates недоступен.",
    };
    renderRunStatus();
    renderOperatorSummary();
  });

  socket.addEventListener("close", () => {
    if (state.runStatus.phase !== "completed" && state.runStatus.phase !== "failed") {
      state.runStatus = {
        ...state.runStatus,
        phase: "closed",
        text: "Live stream закрыт.",
      };
      renderRunStatus();
      renderOperatorSummary();
    }
  });
}

function closeRunSocket() {
  if (state.runSocket instanceof WebSocket) {
    state.runSocket.close();
  }
  state.runSocket = null;
}

async function handleRunEvent(event) {
  const eventType = String(event.type || "");
  if (eventType === "log_line") {
    appendBackendLogLine(event.line || "");
    return;
  }

  if (eventType === "run_started") {
    const runMode = String(event.mode || state.runMode || "dataset");
    state.runMode = runMode;
    state.runStatus = {
      ...state.runStatus,
      phase: "running",
      text:
        runMode === "envelope"
          ? "Запущен анализ выбранного интервала."
          : `Анализ датасета запущен. Демо-пакет ограничен ${DEFAULT_LIVE_WINDOW_LIMIT} окнами.`,
      startedAtUtc: event.timestamp_utc || state.runStatus.startedAtUtc,
      error: "",
    };
    renderRunStatus();
    renderOperatorSummary();
    return;
  }

  if (eventType === "run_windows_discovered") {
    state.runStatus = {
      ...state.runStatus,
      windowsCount: Number(event.windows_count || 0),
      text: `Найдено интервалов анализа: ${Number(event.windows_count || 0)}.`,
    };
    renderRunStatus();
    renderOperatorSummary();
    return;
  }

  if (eventType === "window_discovered") {
    upsertDatasetItem({
      window_id: event.window_id,
      timestamp_start: event.timestamp_start,
      timestamp_end: event.timestamp_end,
      report: "",
      status: "queued",
      summary: "Интервал телеметрии поставлен в очередь анализа.",
      index: Number(event.index || 0),
      total: Number(event.total || 0),
    });
    if (!state.selectedDatasetWindowId) {
      state.selectedDatasetWindowId = String(event.window_id || "");
      renderSelectedWindow();
    }
    renderDatasetWindows();
    renderRunStatus();
    return;
  }

  if (eventType === "window_started") {
    upsertDatasetItem({
      window_id: event.window_id,
      timestamp_start: event.timestamp_start,
      timestamp_end: event.timestamp_end,
      status: "running",
      summary: "Агент обрабатывает интервал телеметрии.",
      index: Number(event.index || 0),
      total: Number(event.total || 0),
    });
    state.windowProgressById[event.window_id] = {
      path: [],
      branchResolved: false,
      currentNode: "pre_hook",
      completedNodes: ["start"],
    };
    state.runStatus = {
      ...state.runStatus,
      currentWindowId: String(event.window_id || ""),
      text: `Обрабатывается интервал ${event.window_id}.`,
    };
    renderDatasetWindows();
    renderRunStatus();
    renderOperatorSummary();
    renderPipeline();
    return;
  }

  if (eventType === "window_node") {
    applyWindowNodeEvent(String(event.window_id || ""), event.payload || {});
    return;
  }

  if (eventType === "window_completed") {
    upsertDatasetItem({
      window_id: event.window_id,
      timestamp_start: event.timestamp_start,
      timestamp_end: event.timestamp_end,
      report: event.report || "",
      uv_plan_details: Array.isArray(event.uv_plan_details) ? event.uv_plan_details : [],
      status: "completed",
      summary: buildDatasetWindowSummary(event.report || "").text,
      index: Number(event.index || 0),
      total: Number(event.total || 0),
    });
    const progress = ensureWindowProgress(String(event.window_id || ""));
    progress.currentNode = null;
    progress.completedNodes = uniqueNodes([...progress.completedNodes, "end"]);

    state.runStatus = {
      ...state.runStatus,
      processedCount: state.runStatus.processedCount + 1,
      text: `Завершён интервал ${event.window_id}.`,
    };

    if (!state.selectedDatasetWindowId || state.selectedDatasetWindowId === event.window_id) {
      state.selectedDatasetWindowId = String(event.window_id || "");
      renderSelectedWindow();
      await syncBackendPanelData(getSelectedDatasetItem());
      await loadOrbitTrack(getSelectedDatasetItem());
    }

    renderDatasetWindows();
    renderRunStatus();
    renderOperatorSummary();
    renderPipeline();
    return;
  }

  if (eventType === "window_failed") {
    upsertDatasetItem({
      window_id: event.window_id,
      status: "failed",
      summary: event.error || "Ошибка анализа окна.",
      error: event.error || "",
      index: Number(event.index || 0),
      total: Number(event.total || 0),
    });
    state.runStatus = {
      ...state.runStatus,
      processedCount: state.runStatus.processedCount + 1,
      text: `Ошибка интервала ${event.window_id}.`,
      error: event.error || "",
    };
    appendBackendLogLine(`ERROR: window_failed ${event.window_id} ${event.error || ""}`);
    renderDatasetWindows();
    renderRunStatus();
    renderOperatorSummary();
    return;
  }

  if (eventType === "run_completed") {
    const completionText = state.runMode === "envelope" ? "Выбранный интервал обработан." : "Анализ датасета завершён.";
    state.runStatus = {
      ...state.runStatus,
      phase: "completed",
      text: completionText,
      completedAtUtc: event.timestamp_utc || "",
      currentWindowId: "",
    };
    renderRunStatus();
    renderOperatorSummary();
    closeRunSocket();
    return;
  }

  if (eventType === "run_failed" || eventType === "run_not_found") {
    const failureText = state.runMode === "envelope" ? "Одиночный прогон завершился с ошибкой." : "Dataset-run завершился с ошибкой.";
    state.runStatus = {
      ...state.runStatus,
      phase: "failed",
      text: failureText,
      completedAtUtc: event.timestamp_utc || "",
      error: event.error || eventType,
    };
    appendBackendLogLine(`ERROR: ${event.error || eventType}`);
    renderRunStatus();
    renderBackendLogs();
    closeRunSocket();
  }
}

function normalizeBaseUrl(rawValue) {
  return String(rawValue || "").trim().replace(/\/+$/, "");
}

function buildWebSocketUrl(baseUrl, path) {
  const url = new URL(baseUrl);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  url.pathname = path;
  url.search = "";
  url.hash = "";
  return url.toString();
}

function appendBackendLogLine(line) {
  if (!line) {
    return;
  }
  state.backendLogLines.push(String(line));
  if (state.backendLogLines.length > 600) {
    state.backendLogLines = state.backendLogLines.slice(-600);
  }
  renderBackendLogs();
  if (state.activeIntelTab === "logs") {
    renderMissionIntel();
  }
}

async function fetchRecentBackendLogs(limit = 250) {
  const baseUrl = normalizeBaseUrl(dom.backendUrl.value);
  if (!baseUrl) {
    return;
  }

  try {
    const response = await fetch(`${baseUrl}/api/v1/logs/recent?limit=${limit}`);
    if (!response.ok) {
      throw new Error(`recent logs status=${response.status}`);
    }
    const data = await response.json();
    if (Array.isArray(data.lines)) {
      state.backendLogLines = data.lines.map((line) => String(line));
      renderBackendLogs();
      if (state.activeIntelTab === "logs") {
        renderMissionIntel();
      }
    }
  } catch (error) {
    appendBackendLogLine(`ERROR: recent logs fetch failed ${String(error)}`);
  }
}

function getScenarioLabel(scenarioId) {
  const labels = {
    mixed: "Смешанная",
    thermal: "Тепловая",
    power: "Энергетическая",
    adcs: "Ориентация (ADCS)",
    rf: "Связь (RF)",
    nominal: "Номинал",
  };
  return labels[scenarioId] || scenarioId;
}

function ensureWindowProgress(windowId) {
  if (!state.windowProgressById[windowId]) {
    state.windowProgressById[windowId] = {
      path: [],
      branchResolved: false,
      currentNode: null,
      completedNodes: ["start"],
    };
  }
  return state.windowProgressById[windowId];
}

function uniqueNodes(nodes) {
  return [...new Set(nodes)];
}

function upsertDatasetItem(patch) {
  const nextItem = {
    window_id: "",
    timestamp_start: "",
    timestamp_end: "",
    report: "",
    status: "queued",
    summary: "",
    error: "",
    index: 0,
    total: 0,
    envelope: null,
    telemetryWindow: null,
    orbitTrack: [],
    orbitSource: "",
    uv_post_check: null,
    uv_plan_details: [],
    ...patch,
  };
  const itemIndex = state.datasetItems.findIndex((entry) => entry.window_id === nextItem.window_id);
  if (itemIndex === -1) {
    state.datasetItems.push(nextItem);
    state.datasetItems.sort((left, right) => left.index - right.index);
    return;
  }
  state.datasetItems[itemIndex] = {
    ...state.datasetItems[itemIndex],
    ...nextItem,
  };
}

function getSelectedDatasetItem() {
  return state.datasetItems.find((entry) => entry.window_id === state.selectedDatasetWindowId) || null;
}

function getDatasetItemById(windowId) {
  return state.datasetItems.find((entry) => entry.window_id === windowId) || null;
}

function applyWindowNodeEvent(windowId, payload) {
  const progress = ensureWindowProgress(windowId);
  const nodeName = String(payload.node || "");
  const completedNodes = [...progress.completedNodes];
  let currentNode = progress.currentNode;
  let path = progress.path;
  let branchResolved = progress.branchResolved === true;

  if (nodeName === "pre_hook") {
    currentNode = "classification";
    completedNodes.push("pre_hook");
    if (payload.envelope) {
      const item = getDatasetItemById(windowId);
      if (state.selectedDatasetWindowId === windowId) {
        state.backendEnvelope = payload.envelope;
        renderOrbitContext();
        renderSubsystems(getCurrentAlerts());
      }
      if (item && item.window_id === windowId) {
        item.envelope = payload.envelope;
      }
    }
  }

  if (nodeName === "classification") {
    completedNodes.push("classification");
    currentNode = "classification";
    const classification = payload.classification || {};
    const item = getDatasetItemById(windowId);
    branchResolved = true;
    if (classification.is_anomaly === false) {
      path = NOMINAL_PATH;
      currentNode = "nominal_summary";
    } else {
      path = ANOMALY_PATH;
      currentNode = "deep_research";
      setIncidentBadge(`Инцидент: ${classification.anomaly_class || "ANOMALY"}`, "badge-crit");
    }
    if (item && item.window_id === windowId) {
      item.classification = classification;
    }
  }

  if (nodeName === "deep_research") {
    path = ANOMALY_PATH;
    branchResolved = true;
    currentNode = "plan_uv";
    completedNodes.push("deep_research");
    const item = getDatasetItemById(windowId);
    if (item && item.window_id === windowId) {
      item.report = payload.deep_report || item.report || "";
    }
    if (state.selectedDatasetWindowId === windowId) {
      state.backendReport = payload.deep_report || state.backendReport;
      renderUVPlan();
      renderReport();
    }
  }

  if (nodeName === "nominal_summary") {
    path = NOMINAL_PATH;
    branchResolved = true;
    currentNode = "end";
    completedNodes.push("nominal_summary");
    if (state.selectedDatasetWindowId === windowId) {
      state.backendReport = payload.final_output || state.backendReport;
      renderReport();
    }
  }

  if (nodeName === "post_hook") {
    path = ANOMALY_PATH;
    branchResolved = true;
    currentNode = "end";
    completedNodes.push("plan_uv", "verifier");
    const item = getDatasetItemById(windowId);
    if (item && item.window_id === windowId) {
      item.report = payload.final_output || item.report || "";
      item.uv_post_check = payload.uv_post_check || null;
      item.uv_plan_details = Array.isArray(payload.deep_uv_plan_details) ? payload.deep_uv_plan_details : item.uv_plan_details || [];
    }
    if (state.selectedDatasetWindowId === windowId) {
      state.backendReport = payload.final_output || state.backendReport;
      renderVerify();
      renderUVPlan();
      renderReport();
    }
  }

  progress.path = path;
  progress.branchResolved = branchResolved;
  progress.currentNode = currentNode;
  progress.completedNodes = uniqueNodes(completedNodes);
  if (state.selectedDatasetWindowId === windowId) {
    if (dom.agentState) {
      dom.agentState.textContent = currentNode || "Завершено";
    }
    renderPipeline();
  }
}

function renderSelectedWindow() {
  const item = getSelectedDatasetItem();
  state.backendReport = item?.report || "";
  state.backendEnvelope = item?.envelope || null;
  state.backendTelemetryWindow = item?.telemetryWindow || null;
  state.orbitTrack = Array.isArray(item?.orbitTrack) ? item.orbitTrack : [];
  state.orbitSource = item?.orbitSource || "n/a";
  renderDatasetWindows();
  renderOrbitContext();
  renderTelemetryStream();
  renderSubsystems(getCurrentAlerts());
  renderOrbitTrack();
  renderUVPlan();
  renderVerify();
  renderReport();
  renderPipeline();
  renderMissionControl();
}

function renderMissionControl() {
  renderMissionRunStatus();
  renderMissionDatasetWindows();
  renderMissionVerdict();
  renderMissionOperatorNow();
}

function renderOperatorSummary() {
  renderMissionControl();
}

function getMissionBadgeState(item) {
  if (item?.status === "completed") {
    return { text: "Завершён", className: "badge-ok" };
  }
  if (item?.status === "running") {
    return { text: "В анализе", className: "badge-warn" };
  }
  if (item?.status === "failed" || state.runStatus.error) {
    return { text: "Ошибка", className: "badge-crit" };
  }
  if (item?.status === "queued") {
    return { text: "В очереди", className: "badge-warn" };
  }
  return { text: "Ожидание", className: "badge-warn" };
}

function renderMissionRunStatus() {
  if (!dom.missionRunStatus || !dom.missionRunBadge) {
    return;
  }
  const item = getSelectedDatasetItem();
  const badge = getMissionBadgeState(item);
  const metaLine = item?.window_id
    ? `${item.window_id} · ${getScenarioLabel(state.scenarioId)}`
    : `Рекомендация: ${state.manualWindowStart} → ${state.manualWindowEnd}`;

  dom.missionRunBadge.textContent = badge.text;
  dom.missionRunBadge.className = `badge ${badge.className}`;
  dom.missionRunStatus.innerHTML = `
    <div class="mission-run-primary">${escapeHtml(state.runStatus.text)}</div>
    <div class="mission-run-meta">${escapeHtml(metaLine)}</div>
    <div class="mission-run-grid">
      <div><span>run_id</span><strong>${escapeHtml(state.runId || "n/a")}</strong></div>
      <div><span>Интервалов</span><strong>${escapeHtml(String(state.runStatus.windowsCount))}</strong></div>
      <div><span>Обработано</span><strong>${escapeHtml(String(state.runStatus.processedCount))}</strong></div>
      <div><span>Текущий</span><strong>${escapeHtml(state.runStatus.currentWindowId || "n/a")}</strong></div>
    </div>
    <div class="mission-run-foot ${state.runStatus.error ? "bad" : "ok"}">${escapeHtml(state.runStatus.error || "Ошибок нет")}</div>
  `;
}

function renderMissionDatasetWindows() {
  if (!dom.missionDatasetWindows || !dom.missionCaseCount) {
    return;
  }
  dom.missionCaseCount.textContent = String(state.datasetItems.length);
  if (!state.datasetItems.length) {
    dom.missionDatasetWindows.innerHTML =
      '<div class="log-empty">Список интервалов появится после dataset-run. Ниже уже можно выполнить точечный запуск по рекомендованному или вручную введенному UTC-интервалу.</div>';
    return;
  }

  dom.missionDatasetWindows.innerHTML = state.datasetItems
    .map((item) => {
      const activeClass = item.window_id === state.selectedDatasetWindowId ? "active" : "";
      const statusClass = item.status || "queued";
      const summary = buildDatasetWindowSummary(item.report || item.summary || "");
      const statusLabel = item.status === "running" ? "RUN" : item.status === "completed" ? summary.badge : item.status === "failed" ? "FAIL" : "QUEUE";
      return `
        <button class="dataset-window mission-case ${activeClass} ${statusClass}" data-window-id="${escapeHtml(item.window_id)}" type="button">
          <div class="dataset-window-title">
            <span>${escapeHtml(item.window_id)}</span>
            <span>${escapeHtml(statusLabel)}</span>
          </div>
          <div class="dataset-window-time">${escapeHtml(item.timestamp_start)} - ${escapeHtml(item.timestamp_end)}</div>
          <div class="dataset-window-caption">Нажмите, чтобы подставить этот интервал в точечный запуск и обновить telemetry evidence.</div>
          <div class="dataset-window-summary">${escapeHtml(item.summary || summary.text)}</div>
        </button>
      `;
    })
    .join("");

  dom.missionDatasetWindows.querySelectorAll(".mission-case").forEach((button) => {
    button.addEventListener("click", async () => {
      const windowId = button.dataset.windowId || "";
      await selectDatasetWindow(windowId);
    });
  });
}

function renderMissionStageBoard() {
  const progress = getSelectedWindowProgress();
  const stageMeta = getMissionStageMeta();
  dom.missionStageMeta.innerHTML = `
    <span class="stage-meta-chip">${escapeHtml(stageMeta.interval)}</span>
    <span class="stage-meta-chip">${escapeHtml(stageMeta.mode)}</span>
    <span class="stage-meta-chip">${escapeHtml(stageMeta.branch)}</span>
  `;

  const linksHtml = STAGE_LINKS.map((link) => {
    const status = getEdgeState({ from: link.from, to: link.to });
    return `
      <div class="stage-link ${status} ${link.kind} lane-${link.lane}" style="grid-row:${link.row};">
        <span>${escapeHtml(link.glyph)}</span>
      </div>
    `;
  }).join("");

  const stagesHtml = STAGE_BOARD_ORDER.map((stageId) => {
    const meta = STAGE_META[stageId];
    const status = getNodeState(stageId);
    const stageSummary = getStageBoardSummary(stageId, progress);
    return `
      <article class="stage-tile ${status} lane-${meta.lane}" data-stage="${stageId}" style="grid-row:${meta.row};">
        <div class="stage-tile-head">
          <span class="stage-title">${escapeHtml(meta.title)}</span>
          <span class="stage-status">${escapeHtml(getStageStatusLabel(status))}</span>
        </div>
        <div class="stage-hint">${escapeHtml(meta.hint)}</div>
        <p class="stage-summary">${escapeHtml(stageSummary)}</p>
      </article>
    `;
  }).join("");

  dom.missionStageBoard.innerHTML = `${linksHtml}${stagesHtml}`;
}

function getMissionStageMeta() {
  const item = getSelectedDatasetItem();
  const progress = getSelectedWindowProgress();
  const branch = progress.branchResolved
    ? progress.path.includes("deep_research")
      ? "ветвь: аномалия"
      : "ветвь: номинал"
    : "ветвь ещё не выбрана";
  return {
    interval: item?.window_id || "Интервал не выбран",
    mode: getScenarioLabel(state.scenarioId),
    branch,
  };
}

function getStageStatusLabel(status) {
  if (status === "done") {
    return "готово";
  }
  if (status === "active") {
    return "в работе";
  }
  if (status === "dormant") {
    return "не выбрано";
  }
  return "ожидание";
}

function formatConfidenceValue(value) {
  if (value == null || Number.isNaN(Number(value))) {
    return "n/a";
  }
  return Number(value).toFixed(2);
}

function inferSeverityFromClassification(anomalyClass) {
  if (anomalyClass === "MIXED") {
    return "critical";
  }
  if (["POWER", "THERMAL", "ADCS"].includes(String(anomalyClass))) {
    return "high";
  }
  if (anomalyClass === "RF") {
    return "medium";
  }
  if (anomalyClass === "UNKNOWN") {
    return "low";
  }
  return "n/a";
}

function getStageBoardSummary(stageId, progress) {
  const item = getSelectedDatasetItem();
  const payload = progress.nodePayloads?.[stageId] || {};
  const classification = item?.classification || payload.classification || {};
  const alerts = Array.isArray(state.backendEnvelope?.alerts) ? state.backendEnvelope.alerts : [];
  const plan = getCurrentUVPlan();
  const verify = item?.uv_post_check || parseVerifyFromBackendReport(state.backendReport);

  if (stageId === "start") {
    return item ? "Интервал принят в контур анализа." : "Ожидается выбор интервала.";
  }
  if (stageId === "pre_hook") {
    return state.backendEnvelope ? `alerts=${alerts.length}, context готов.` : "Подготовка envelope и орбитального контекста.";
  }
  if (stageId === "classification") {
    if (classification.anomaly_class || classification.is_anomaly === false) {
      const conf = Number(classification.confidence_alarm ?? classification.confidence ?? 0);
      return `${classification.anomaly_class || "UNKNOWN"} · confidence ${conf.toFixed(2)}`;
    }
    return "Решение о ветвлении и классе НС.";
  }
  if (stageId === "deep_research") {
    return progress.path.includes("deep_research")
      ? buildDatasetWindowSummary(state.backendReport || item?.report || "").text
      : "Углубленный анализ не потребовался.";
  }
  if (stageId === "plan_uv") {
    return plan.length ? `Сформировано действий: ${plan.length}` : "Проект УВ ещё не получен.";
  }
  if (stageId === "verifier") {
    return verify.valid === null ? "Post-hook ещё не завершён." : verify.valid ? "План прошёл базовую проверку." : "Найдены ограничения и нарушения.";
  }
  if (stageId === "nominal_summary") {
    return progress.path.includes("nominal_summary") ? buildDatasetWindowSummary(state.backendReport || item?.report || "").text : "Штатная сводка не активна.";
  }
  if (stageId === "end") {
    return state.backendReport ? "Итоговый отчет готов для оператора." : "Ожидается формирование итогового отчёта.";
  }
  return "Ожидание данных.";
}

function renderMissionVerdict() {
  if (!dom.missionVerdict || !dom.missionVerdictBadge) {
    return;
  }
  const item = getSelectedDatasetItem();
  const classification = item?.classification || {};
  const anomalyClass = classification.anomaly_class || "n/a";
  const confidence = formatConfidenceValue(classification.confidence_alarm ?? classification.confidence);
  const severity = inferSeverityFromClassification(classification.anomaly_class);
  const affected = inferAffectedSubsystems(getCurrentAlerts());
  const summary = buildDatasetWindowSummary(state.backendReport || item?.report || "").text;
  const hypothesis = extractHypothesisLine(state.backendReport || item?.report || "") || "n/a";

  dom.missionVerdictBadge.textContent = anomalyClass || "UNKNOWN";
  dom.missionVerdictBadge.className = `badge ${severity === "critical" || severity === "high" ? "badge-crit" : severity === "medium" || severity === "n/a" ? "badge-warn" : "badge-ok"}`;
  dom.missionVerdict.innerHTML = `
    <div class="mission-verdict-grid">
      <div><span>Интервал</span><strong>${escapeHtml(item?.window_id || "n/a")}</strong></div>
      <div><span>Класс НС</span><strong>${escapeHtml(anomalyClass || "n/a")}</strong></div>
      <div><span>Уверенность</span><strong>${escapeHtml(confidence)}</strong></div>
      <div><span>Критичность</span><strong>${escapeHtml(severity)}</strong></div>
    </div>
    <div class="mission-verdict-block">
      <span>Гипотеза</span>
      <p>${escapeHtml(hypothesis)}</p>
    </div>
    <div class="mission-verdict-block">
      <span>Сводка по интервалу</span>
      <p>${escapeHtml(summary)}</p>
    </div>
    <div class="mission-verdict-block">
      <span>Затронутые подсистемы</span>
      <div class="subsystem-chip-row">${affected.map((name) => `<span class="subsystem-chip">${escapeHtml(name)}</span>`).join("")}</div>
    </div>
  `;
}

function renderMissionOperatorNow() {
  if (!dom.missionOperatorNow || !dom.missionActionBadge) {
    return;
  }
  const item = getSelectedDatasetItem();
  const plan = getCurrentUVPlan();
  const verify = item?.uv_post_check || parseVerifyFromBackendReport(state.backendReport);
  const primaryActions = plan.slice(0, 3);
  const badgeText = verify.valid === null ? "Ожидание" : verify.valid ? "Валидно" : "Проверить";
  const badgeClass = verify.valid === null ? "badge-warn" : verify.valid ? "badge-ok" : "badge-crit";

  dom.missionActionBadge.textContent = badgeText;
  dom.missionActionBadge.className = `badge ${badgeClass}`;
  dom.missionOperatorNow.innerHTML = `
    <div class="mission-action-block">
      <span>Следующие действия</span>
      ${primaryActions.length
        ? `<ol class="mission-action-list">${primaryActions
            .map(
              (entry) => `
                <li>
                  <strong>${escapeHtml(entry.action)}</strong>
                  <p>${escapeHtml(entry.description || "Описание не указано.")}</p>
                </li>`
            )
            .join("")}</ol>`
        : '<p>План УВ ещё не сформирован. Ожидается углубленный анализ или штатная сводка.</p>'}
    </div>
    <div class="mission-action-block">
      <span>Критичные ограничения</span>
      <ul class="mission-inline-list">
        ${buildMissionListItems((verify.violations.length ? verify.violations : verify.constraints).slice(0, 3), "Ограничений пока нет.")}
      </ul>
    </div>
    <div class="mission-action-block">
      <span>Рекомендации</span>
      <ul class="mission-inline-list">
        ${buildMissionListItems(verify.recommendations.slice(0, 3), "Рекомендаций пока нет.")}
      </ul>
    </div>
  `;
}

function renderMissionIntel() {
  if (!dom.missionIntelContent) {
    return;
  }
  [dom.btnIntelEvidence, dom.btnIntelAgent, dom.btnIntelPlan, dom.btnIntelConstraints, dom.btnIntelLogs].forEach((button) => {
    if (!button) {
      return;
    }
    const active = button.id === `btnIntel${capitalizeTab(state.activeIntelTab)}`;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  });

  if (state.activeIntelTab === "evidence") {
    dom.missionIntelContent.innerHTML = buildMissionEvidenceHtml();
    const toggleButton = dom.missionIntelContent.querySelector('[data-intel-action="toggle-evidence"]');
    if (toggleButton) {
      toggleButton.addEventListener("click", () => {
        state.telemetryExpanded = !state.telemetryExpanded;
        renderMissionIntel();
      });
    }
    return;
  }
  if (state.activeIntelTab === "agent") {
    dom.missionIntelContent.innerHTML = buildMissionAgentHtml();
    return;
  }
  if (state.activeIntelTab === "plan") {
    dom.missionIntelContent.innerHTML = buildMissionPlanHtml();
    return;
  }
  if (state.activeIntelTab === "constraints") {
    dom.missionIntelContent.innerHTML = buildMissionConstraintsHtml();
    return;
  }
  dom.missionIntelContent.innerHTML = `<div class="mission-logs">${buildBackendLogsHtml()}</div>`;
}

function capitalizeTab(tabId) {
  return tabId.charAt(0).toUpperCase() + tabId.slice(1);
}

function inferAffectedSubsystems(alerts) {
  const mapping = {
    THERMAL_OVERHEAT: ["THERMAL", "PAYLOAD"],
    POWER_DEGRADATION: ["EPS", "PAYLOAD"],
    ADCS_STABILIZATION_LOSS: ["ADCS"],
    SENSOR_DEGRADATION: ["ADCS"],
    COMM_DEGRADATION: ["COMM"],
  };
  const subsystems = new Set();
  (Array.isArray(alerts) ? alerts : []).forEach((alert) => {
    (mapping[String(alert)] || []).forEach((name) => subsystems.add(name));
  });
  return subsystems.size ? [...subsystems] : ["n/a"];
}

function extractHypothesisLine(reportText) {
  const text = String(reportText || "");
  const hypothesisMatch = text.match(/###\s+Гипотеза причины\s*\n+([^\n]+)/i);
  if (hypothesisMatch) {
    return hypothesisMatch[1].trim();
  }
  const summaryMatch = text.match(/###\s+Краткий вывод\s*\n+([^\n]+)/i);
  if (summaryMatch) {
    return summaryMatch[1].trim();
  }
  return buildDatasetWindowSummary(text).text;
}

function buildMissionListItems(items, emptyText) {
  if (!items.length) {
    return `<li class="mission-empty-item">${escapeHtml(emptyText)}</li>`;
  }
  return items.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
}

function buildMissionEvidenceHtml() {
  const item = getSelectedDatasetItem();
  const orbit = getCurrentOrbitContext();
  const alerts = getCurrentAlerts();
  const allRows = getActiveTelemetryRows();
  const anomalyRows = allRows.filter((entry) => entry.status !== "OK");
  const evidenceRows = state.telemetryExpanded ? allRows : anomalyRows.length ? anomalyRows.slice(-8) : allRows.slice(-8);
  const satelliteSvg = document.getElementById("satelliteSvg");
  const orbitPreview = dom.orbitCanvas?.toDataURL ? dom.orbitCanvas.toDataURL("image/png") : "";
  const metrics = [
    ["Интервал", item?.window_id || "n/a"],
    ["Алертов", String(alerts.length)],
    ["Аномальных строк", String(anomalyRows.length)],
    ["Орбита", orbit.altitude],
  ];
  const references = [
    ["Окно UTC", item ? `${item.timestamp_start} → ${item.timestamp_end}` : `${state.manualWindowStart} → ${state.manualWindowEnd}`],
    ["CSV telemetry", state.backendTelemetryWindow?.source_csv_path || state.backendEnvelope?.raw_telemetry_ref || "n/a"],
    ["TLE source", state.backendEnvelope?.tle_ref || "n/a"],
    ["Resample", state.backendTelemetryWindow?.resample_freq || "n/a"],
  ];

  return `
    <div class="evidence-shell">
      <section class="evidence-top">
        <div class="evidence-metrics">
          ${metrics
            .map(
              ([label, value]) => `
                <div class="evidence-metric">
                  <span>${escapeHtml(label)}</span>
                  <strong>${escapeHtml(value)}</strong>
                </div>`
            )
            .join("")}
        </div>
        <div class="evidence-highlight">
          <div class="evidence-highlight-head">
            <div>
              <h4>Телеметрическое evidence</h4>
              <p>${escapeHtml(
                allRows.length
                  ? state.telemetryExpanded
                    ? `Показан весь поток выбранного интервала: ${allRows.length} строк.`
                    : anomalyRows.length
                      ? `Показаны последние ${evidenceRows.length} предупреждений/критических строк из ${allRows.length}.`
                      : `Аномальных строк нет. Показаны последние ${evidenceRows.length} строк из ${allRows.length}.`
                  : "После загрузки данных здесь появятся ключевые строки телеметрии."
              )}</p>
            </div>
            <button class="btn btn-ghost btn-small" type="button" data-intel-action="toggle-evidence">
              ${state.telemetryExpanded ? "Показать ключевое" : "Показать весь поток"}
            </button>
          </div>
          ${
            evidenceRows.length
              ? `<div class="evidence-table-wrap">
                  <table class="evidence-table">
                    <thead>
                      <tr>
                        <th>Время</th>
                        <th>Канал</th>
                        <th>Значение</th>
                        <th>Статус</th>
                      </tr>
                    </thead>
                    <tbody>
                      ${evidenceRows
                        .map((entry) => {
                          const cls =
                            entry.status === "OK" ? "status-ok" : entry.status === "WARN" ? "status-warn" : "status-crit";
                          return `
                            <tr>
                              <td>${escapeHtml(entry.timestamp)}</td>
                              <td>${escapeHtml(entry.channel)}</td>
                              <td>${escapeHtml(entry.value)}</td>
                              <td class="${cls}">${escapeHtml(entry.status)}</td>
                            </tr>
                          `;
                        })
                        .join("")}
                    </tbody>
                  </table>
                </div>`
              : '<div class="log-empty">Telemetry evidence пока недоступно.</div>'
          }
        </div>
      </section>

      <section class="evidence-support">
        <article class="support-panel">
          <h4>Затронутые подсистемы</h4>
          <div class="subsystem-chip-row">${inferAffectedSubsystems(alerts)
            .map((name) => `<span class="subsystem-chip">${escapeHtml(name)}</span>`)
            .join("")}</div>
          <ul class="mission-inline-list evidence-alert-list">
            ${buildMissionListItems(alerts.slice(0, 5), "Явные alert-сигналы пока отсутствуют.")}
          </ul>
        </article>

        <article class="support-panel">
          <h4>Орбитальный контекст</h4>
          <div class="evidence-kv">
            ${[
              ["Высота", orbit.altitude],
              ["Широта", orbit.latitude],
              ["Долгота", orbit.longitude],
              ["Затмение", orbit.eclipse],
              ["Наземная станция", orbit.groundVisibility],
            ]
              .map(
                ([key, value]) => `
                  <div class="evidence-kv-row">
                    <span>${escapeHtml(key)}</span>
                    <strong>${escapeHtml(value)}</strong>
                  </div>`
              )
              .join("")}
          </div>
          <p class="support-caption">${escapeHtml(state.orbitSource || "n/a")}</p>
        </article>

        <article class="support-panel">
          <h4>Референсы окна</h4>
          <div class="evidence-kv">
            ${references
              .map(
                ([key, value]) => `
                  <div class="evidence-kv-row">
                    <span>${escapeHtml(key)}</span>
                    <strong>${escapeHtml(String(value || "n/a"))}</strong>
                  </div>`
              )
              .join("")}
          </div>
        </article>

        <article class="support-panel support-panel-visual">
          <h4>Контекст КА и орбиты</h4>
          <div class="support-visual-grid">
            <div class="support-visual-frame">${satelliteSvg ? satelliteSvg.outerHTML : '<div class="log-empty">Схема КА недоступна.</div>'}</div>
            <div class="support-visual-frame">
              ${orbitPreview ? `<img src="${orbitPreview}" alt="Орбита по TLE" />` : '<div class="log-empty">Орбита ещё не построена.</div>'}
            </div>
          </div>
        </article>
      </section>
    </div>
  `;
}

function buildMissionAgentHtml() {
  const progress = getSelectedWindowProgress();
  const stages = STAGE_BOARD_ORDER.filter((stageId) => stageId !== "start" && stageId !== "end");
  const reportHtml = state.backendReport ? renderMarkdown(state.backendReport) : "";

  return `
    <div class="intel-stage-list">
      ${stages
        .map((stageId) => {
          const meta = STAGE_META[stageId];
          const status = getNodeState(stageId);
          return `
            <article class="intel-stage-card ${status}">
              <div class="intel-stage-card-head">
                <div>
                  <span class="intel-stage-kicker">${escapeHtml(meta.hint)}</span>
                  <h4>${escapeHtml(meta.title)}</h4>
                </div>
                <span class="stage-status">${escapeHtml(getStageStatusLabel(status))}</span>
              </div>
              <p>${escapeHtml(getStageBoardSummary(stageId, progress))}</p>
            </article>
          `;
        })
        .join("")}
      <article class="intel-stage-report">
        <div class="intel-stage-card-head">
          <div>
            <span class="intel-stage-kicker">operator output</span>
            <h4>Итоговый фрагмент отчёта</h4>
          </div>
        </div>
        ${reportHtml || '<div class="log-empty">Итоговый отчёт ещё не сформирован.</div>'}
      </article>
    </div>
  `;
}

function buildMissionPlanHtml() {
  const plan = getCurrentUVPlan();
  if (!plan.length) {
    return '<div class="log-empty">План УВ появится после ветви deep_research и формирования операторского отчёта.</div>';
  }

  return `
    <ol class="mission-plan-list">
      ${plan
        .map(
          (entry) => `
            <li class="mission-plan-item">
              <div class="mission-plan-title">
                <strong>${escapeHtml(entry.action)}</strong>
                <span class="risk-chip risk-${escapeHtml(entry.risk || "med")}">${escapeHtml(entry.risk || "med")}</span>
              </div>
              <p>${escapeHtml(entry.description || "Описание действия отсутствует.")}</p>
              ${
                entry.prechecks?.length
                  ? `<div class="mission-plan-subline"><strong>Перед исполнением:</strong> ${escapeHtml(entry.prechecks.join("; "))}</div>`
                  : ""
              }
            </li>
          `
        )
        .join("")}
    </ol>
  `;
}

function buildMissionConstraintsHtml() {
  const item = getSelectedDatasetItem();
  const verify = item?.uv_post_check || parseVerifyFromBackendReport(state.backendReport);
  const verdict = verify.valid === null ? "Ожидание post-hook" : verify.valid ? "План валиден" : "Найдены ограничения";
  const verdictClass = verify.valid === null ? "badge-warn" : verify.valid ? "badge-ok" : "badge-crit";

  return `
    <div class="constraints-shell">
      <div class="constraints-summary">
        <span class="badge ${verdictClass}">${escapeHtml(verdict)}</span>
        <p>${escapeHtml(
          verify.valid === null
            ? "Верификатор ещё не завершил проверку плана."
            : verify.valid
              ? "Критичных нарушений не обнаружено, план может быть передан оператору."
              : "Перед исполнением нужно учесть ограничения и рекомендации ниже."
        )}</p>
      </div>
      <div class="constraints-grid">
        <article class="support-panel">
          <h4>Нарушения</h4>
          <ul class="mission-inline-list">${buildMissionListItems(verify.violations, "Нарушений не обнаружено.")}</ul>
        </article>
        <article class="support-panel">
          <h4>Ограничения</h4>
          <ul class="mission-inline-list">${buildMissionListItems(verify.constraints, "Ограничения не сформированы.")}</ul>
        </article>
        <article class="support-panel">
          <h4>Рекомендации</h4>
          <ul class="mission-inline-list">${buildMissionListItems(verify.recommendations, "Рекомендаций пока нет.")}</ul>
        </article>
      </div>
    </div>
  `;
}

function buildBackendLogsHtml() {
  const entries = parseBackendLogEntries(state.backendLogLines).filter((entry) => entry.level !== "DEBUG");
  if (!entries.length) {
    return '<div class="log-empty">После запуска здесь будут показаны INFO/WARNING/ERROR логи backend и история вызовов инструментов.</div>';
  }

  return entries
    .map((entry) => {
      const levelClass = `log-${entry.level.toLowerCase()}`;
      const compactMessage = buildCompactLogMessage(entry.body);
      return `
        <article class="log-entry ${levelClass}">
          <div class="log-meta">
            <span class="log-time">${escapeHtml(entry.time)}</span>
            <span class="log-level ${levelClass}">${escapeHtml(entry.level)}</span>
            <span class="log-source">${escapeHtml(entry.source)}</span>
            <span class="log-summary">${compactMessage}</span>
          </div>
          <div class="log-message">${renderLogBody(entry.body)}</div>
        </article>
      `;
    })
    .join("");
}

function initializeWidgetDashboard() {
  if (!dom.dashboardGrid) {
    return;
  }
  dashboard.main = buildPanelState("main", dom.dashboardGrid, WIDGET_DEFAULTS);
  packAndRenderPanel(dashboard.main);
}

function buildPanelState(name, gridElement, defaults) {
  const widgets = [];
  const cards = Array.from(gridElement.querySelectorAll(":scope > .card"));

  cards.forEach((card, order) => {
    const key = card.dataset.widgetKey || `${name}_${order}`;
    const fallback = { x: 1, y: 1 + order * 8, w: 12, h: 8, minW: 4, minH: 5 };
    const preset = defaults[key] || fallback;
    const widget = {
      id: key,
      order,
      panel: name,
      el: card,
      x: preset.x,
      y: preset.y,
      w: preset.w,
      h: preset.h,
      minW: preset.minW || 4,
      minH: preset.minH || 5,
    };
    setupWidgetElement(widget);
    bindWidgetInteractions(widget, { name, el: gridElement, widgets });
    widgets.push(widget);
  });

  return { name, el: gridElement, widgets };
}

function applyWidgetDefaultsToPanel(panel, defaults) {
  if (!panel) {
    return;
  }
  panel.widgets.forEach((widget, order) => {
    const fallback = { x: 1, y: 1 + order * 8, w: 12, h: 8, minW: 4, minH: 5 };
    const preset = defaults[widget.id] || fallback;
    widget.x = preset.x;
    widget.y = preset.y;
    widget.w = preset.w;
    widget.h = preset.h;
    widget.minW = preset.minW || widget.minW || 4;
    widget.minH = preset.minH || widget.minH || 5;
  });
  packAndRenderPanel(panel);
}

function setupWidgetElement(widget) {
  const card = widget.el;
  if (card.dataset.widgetInit !== "1") {
    card.dataset.widgetInit = "1";
    card.classList.add("widget-card");

    const header = card.querySelector("h3");
    if (header) {
      header.classList.add("widget-handle");
      header.title = "Перетащите окно";
    }

    const directions = ["n", "e", "s", "w", "ne", "nw", "se", "sw"];
    directions.forEach((dir) => {
      const handle = document.createElement("span");
      handle.className = `resize-handle ${dir}`;
      handle.dataset.dir = dir;
      card.appendChild(handle);
    });
  }
}

function bindWidgetInteractions(widget, panel) {
  let mode = null;
  let resizeDir = "";
  let startPointerX = 0;
  let startPointerY = 0;
  let startX = 0;
  let startY = 0;
  let startW = 0;
  let startH = 0;
  let dragOffsetX = 0;
  let dragOffsetY = 0;

  const onPointerMove = (event) => {
    if (!mode) {
      return;
    }
    const metrics = getPanelMetrics(panel.el);

    if (mode === "move") {
      const pxX = event.clientX - metrics.rect.left - dragOffsetX;
      const pxY = event.clientY - metrics.rect.top - dragOffsetY;
      widget.x = clampInt(Math.round(pxX / metrics.stepX) + 1, 1, DASHBOARD_GRID.cols - widget.w + 1);
      widget.y = Math.max(1, Math.round(pxY / metrics.stepY) + 1);
    } else {
      const dx = Math.round((event.clientX - startPointerX) / metrics.stepX);
      const dy = Math.round((event.clientY - startPointerY) / metrics.stepY);
      let nextX = startX;
      let nextY = startY;
      let nextW = startW;
      let nextH = startH;

      if (resizeDir.includes("e")) {
        nextW = startW + dx;
      }
      if (resizeDir.includes("s")) {
        nextH = startH + dy;
      }
      if (resizeDir.includes("w")) {
        nextW = startW - dx;
        nextX = startX + dx;
      }
      if (resizeDir.includes("n")) {
        nextH = startH - dy;
        nextY = startY + dy;
      }

      nextW = clampInt(nextW, widget.minW, DASHBOARD_GRID.cols);
      nextH = Math.max(widget.minH, nextH);
      nextX = clampInt(nextX, 1, DASHBOARD_GRID.cols - nextW + 1);
      nextY = Math.max(1, nextY);

      widget.x = nextX;
      widget.y = nextY;
      widget.w = nextW;
      widget.h = nextH;
    }

    packAndRenderPanel(panel, widget.id);
    event.preventDefault();
  };

  const onPointerUp = () => {
    if (!mode) {
      return;
    }
    mode = null;
    resizeDir = "";
    widget.el.classList.remove("widget-moving", "widget-resizing");
    document.removeEventListener("pointermove", onPointerMove);
    document.removeEventListener("pointerup", onPointerUp);

  };

  widget.el.addEventListener("pointerdown", (event) => {
    if (state.surface !== "research") {
      return;
    }
    const resizeHandle = event.target.closest(".resize-handle");
    const moveHandle = event.target.closest(".widget-handle");

    if (!resizeHandle && !moveHandle) {
      return;
    }

    const widgetRect = widget.el.getBoundingClientRect();
    const panelRect = panel.el.getBoundingClientRect();

    startPointerX = event.clientX;
    startPointerY = event.clientY;
    startX = widget.x;
    startY = widget.y;
    startW = widget.w;
    startH = widget.h;
    dragOffsetX = event.clientX - widgetRect.left;
    dragOffsetY = event.clientY - widgetRect.top;

    if (resizeHandle) {
      mode = "resize";
      resizeDir = resizeHandle.dataset.dir || "";
      widget.el.classList.add("widget-resizing");
    } else {
      mode = "move";
      widget.el.classList.add("widget-moving");
    }

    // Защита от случайного выделения текста при drag.
    if (panelRect.width > 0) {
      event.preventDefault();
    }
    document.addEventListener("pointermove", onPointerMove);
    document.addEventListener("pointerup", onPointerUp);
  });
}

function getPanelMetrics(panelElement) {
  const rect = panelElement.getBoundingClientRect();
  const gridStyle = window.getComputedStyle(panelElement);
  const gap = Number.parseFloat(gridStyle.gap || `${DASHBOARD_GRID.gap}`) || DASHBOARD_GRID.gap;
  const totalGap = gap * (DASHBOARD_GRID.cols - 1);
  const cellWidth = (rect.width - totalGap) / DASHBOARD_GRID.cols;
  const stepX = cellWidth + gap;
  const stepY = DASHBOARD_GRID.rowHeight + gap;
  return { rect, cellWidth, gap, stepX, stepY };
}

function packAndRenderPanel(panel, activeId = null) {
  const widgets = panel.widgets;
  if (!widgets.length) {
    return;
  }

  const active = activeId ? widgets.find((item) => item.id === activeId) : null;
  const ordered = [
    ...(active ? [active] : []),
    ...widgets.filter((item) => item !== active).sort((a, b) => a.order - b.order),
  ];

  const placed = [];
  for (const widget of ordered) {
    widget.w = clampInt(widget.w, widget.minW, DASHBOARD_GRID.cols);
    widget.h = Math.max(widget.minH, widget.h);
    widget.x = clampInt(widget.x, 1, DASHBOARD_GRID.cols - widget.w + 1);

    let candidateY = widget.id === activeId ? Math.max(1, widget.y) : 1;
    while (hasCollision(widget, placed, candidateY)) {
      candidateY += 1;
    }
    widget.y = candidateY;
    placed.push({ x: widget.x, y: widget.y, w: widget.w, h: widget.h, id: widget.id });
  }

  widgets.forEach((widget) => {
    widget.el.style.gridColumn = `${widget.x} / span ${widget.w}`;
    widget.el.style.gridRow = `${widget.y} / span ${widget.h}`;
    widget.el.style.left = "";
    widget.el.style.top = "";
    widget.el.style.width = "";
    widget.el.style.height = "";
  });
}

function hasCollision(widget, placed, candidateY) {
  const ax1 = widget.x;
  const ay1 = candidateY;
  const ax2 = ax1 + widget.w;
  const ay2 = ay1 + widget.h;

  return placed.some((other) => {
    const bx1 = other.x;
    const by1 = other.y;
    const bx2 = bx1 + other.w;
    const by2 = by1 + other.h;
    return ax1 < bx2 && ax2 > bx1 && ay1 < by2 && ay2 > by1;
  });
}

function clampInt(value, minValue, maxValue) {
  return Math.min(maxValue, Math.max(minValue, Math.round(value)));
}

function clampNumber(value, minValue, maxValue) {
  return Math.min(maxValue, Math.max(minValue, value));
}

function formatMaybeBool(value) {
  if (value === true) {
    return "Да";
  }
  if (value === false) {
    return "Нет";
  }
  return "n/a";
}

function formatMaybeNumber(value, suffix, digits) {
  if (value == null || Number.isNaN(Number(value))) {
    return "n/a";
  }
  return `${Number(value).toFixed(digits)}${suffix}`;
}

function pickNumber(rawValue, fallback) {
  if (rawValue == null || Number.isNaN(Number(rawValue))) {
    return fallback;
  }
  return Number(rawValue);
}

function inferChannelStatus(channel, value) {
  if (value == null || Number.isNaN(Number(value))) {
    return "WARN";
  }
  const numeric = Number(value);
  if (channel.includes("Temp")) {
    if (numeric >= 320) {
      return "CRIT";
    }
    if (numeric >= 280) {
      return "WARN";
    }
    return "OK";
  }
  if (channel.includes("Voltage")) {
    if (numeric < 8050) {
      return "CRIT";
    }
    if (numeric < 8150) {
      return "WARN";
    }
    return "OK";
  }
  if (channel.includes("RSSI")) {
    if (numeric <= -112) {
      return "CRIT";
    }
    if (numeric <= -104) {
      return "WARN";
    }
    return "OK";
  }
  if (channel.includes("Spin") || channel.includes("theta")) {
    if (Math.abs(numeric) > 0.08) {
      return "CRIT";
    }
    if (Math.abs(numeric) > 0.04) {
      return "WARN";
    }
    return "OK";
  }
  return "OK";
}

function formatChannelValue(channel, value) {
  if (value == null || Number.isNaN(Number(value))) {
    return "n/a";
  }
  const numeric = Number(value);
  if (channel.includes("Temp")) {
    return `${numeric.toFixed(1)} K`;
  }
  if (channel.includes("Voltage")) {
    return `${numeric.toFixed(1)} mV`;
  }
  if (channel.includes("RSSI")) {
    return `${numeric.toFixed(1)} dBm`;
  }
  if (channel.includes("Spin") || channel.includes("theta")) {
    return `${numeric.toFixed(4)} rad`;
  }
  return numeric.toFixed(3);
}

function buildEnvelopeFromDatasetItem(item) {
  return {
    window_id: item.window_id,
    timestamp_start: item.timestamp_start,
    timestamp_end: item.timestamp_end,
    raw_telemetry_ref: SAMPLE_WINDOW.raw_telemetry_ref,
    tle_ref: SAMPLE_WINDOW.tle_ref,
  };
}

function syncManualWindowInputs(item = null) {
  const startValue = item?.timestamp_start || state.manualWindowStart || SAMPLE_WINDOW.timestamp_start;
  const endValue = item?.timestamp_end || state.manualWindowEnd || SAMPLE_WINDOW.timestamp_end;
  state.manualWindowStart = startValue;
  state.manualWindowEnd = endValue;
  if (dom.manualWindowStart) {
    dom.manualWindowStart.value = startValue;
  }
  if (dom.manualWindowEnd) {
    dom.manualWindowEnd.value = endValue;
  }
}

function buildManualWindowId(timestampStart, timestampEnd) {
  const normalizedStart = String(timestampStart).replace(/[:TZ-]/g, "").slice(0, 12);
  const normalizedEnd = String(timestampEnd).replace(/[:TZ-]/g, "").slice(0, 12);
  return `manual_${normalizedStart}_${normalizedEnd}`;
}

function resolveFocusedWindowSelection() {
  const timestampStart = state.manualWindowStart.trim();
  const timestampEnd = state.manualWindowEnd.trim();
  const startDate = new Date(timestampStart);
  const endDate = new Date(timestampEnd);
  if (Number.isNaN(startDate.getTime()) || Number.isNaN(endDate.getTime())) {
    throw new Error("Укажите корректные UTC timestamps в ISO формате.");
  }
  if (endDate <= startDate) {
    throw new Error("timestamp_end должен быть позже timestamp_start.");
  }

  const selectedItem = getSelectedDatasetItem();
  const sameRange =
    selectedItem &&
    selectedItem.timestamp_start === timestampStart &&
    selectedItem.timestamp_end === timestampEnd;
  const windowId = sameRange ? selectedItem.window_id : buildManualWindowId(timestampStart, timestampEnd);
  return { windowId, timestampStart, timestampEnd };
}

function resolveSingleRunPath(reportText) {
  const text = String(reportText || "").toLowerCase();
  if (text.includes("номин") || text.includes("не подтверждена") || text.includes("штатн")) {
    return NOMINAL_PATH;
  }
  return ANOMALY_PATH;
}

async function runFocusedWindow() {
  closeRunSocket();
  state.runMode = "envelope";

  const baseUrl = normalizeBaseUrl(dom.backendUrl.value);
  if (!baseUrl) {
    state.runStatus = {
      ...state.runStatus,
      phase: "failed",
      text: "Не задан адрес backend.",
      error: "Укажите backend URL.",
    };
    renderRunStatus();
    renderMissionControl();
    return;
  }

  try {
    const selection = resolveFocusedWindowSelection();
    const existingItem = getDatasetItemById(selection.windowId);
    const nextIndex = existingItem?.index || state.datasetItems.length + 1;
    upsertDatasetItem({
      ...(existingItem || {}),
      window_id: selection.windowId,
      timestamp_start: selection.timestampStart,
      timestamp_end: selection.timestampEnd,
      index: nextIndex,
      total: Math.max(state.datasetItems.length || 0, nextIndex),
      status: "running",
      summary: "Точечный запуск выбранного интервала через live run.",
      error: "",
      report: "",
      envelope: null,
      telemetryWindow: null,
    });

    state.selectedDatasetWindowId = selection.windowId;
    state.backendReport = "";
    state.finalReport = "";
    state.telemetryExpanded = false;
    state.runId = "";
    state.runStatus = {
      ...state.runStatus,
      phase: "streaming",
      text: "Идет анализ выбранного интервала...",
      windowsCount: 1,
      processedCount: 0,
      currentWindowId: selection.windowId,
      error: "",
    };

    const progress = ensureWindowProgress(selection.windowId);
    progress.path = [];
    progress.branchResolved = false;
    progress.currentNode = "pre_hook";
    progress.completedNodes = ["start"];

    renderSelectedWindow();

    const targetItem = getDatasetItemById(selection.windowId);
    if (!targetItem) {
      throw new Error("Не удалось создать интервал для точечного запуска.");
    }

    await syncBackendPanelData(targetItem);
    await loadOrbitTrack(targetItem);

    progress.currentNode = "classification";
    progress.completedNodes = ["start", "pre_hook"];
    renderPipeline();
    renderMissionControl();

    const runResponse = await fetch(`${baseUrl}/api/v1/runs/envelope`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        envelope: buildEnvelopeFromDatasetItem(targetItem),
        scenario: state.scenarioId,
      }),
    });

    if (!runResponse.ok) {
      throw new Error(`single envelope run status=${runResponse.status}`);
    }

    const runData = await runResponse.json();
    state.runId = runData.run_id || "";
    state.runStatus = {
      ...state.runStatus,
      phase: "connecting",
      text: "Подключение к live stream выбранного интервала...",
      windowsCount: 1,
      processedCount: 0,
      currentWindowId: selection.windowId,
      error: "",
      startedAtUtc: runData.created_at_utc || "",
    };
    renderRunStatus();
    renderOperatorSummary();
    openRunSocket(baseUrl, state.runId);
  } catch (error) {
    const windowId = state.selectedDatasetWindowId;
    if (windowId) {
      upsertDatasetItem({
        ...(getDatasetItemById(windowId) || {}),
        window_id: windowId,
        status: "failed",
        error: String(error),
        summary: "Точечный запуск завершился ошибкой.",
      });
    }
    state.runStatus = {
      ...state.runStatus,
      phase: "failed",
      text: "Не удалось обработать выбранный интервал.",
      error: String(error),
    };
    appendBackendLogLine(`ERROR: single window run failed ${String(error)}`);
    await fetchRecentBackendLogs();
    renderSelectedWindow();
  }
}

async function selectDatasetWindow(windowId) {
  const item = state.datasetItems.find((entry) => entry.window_id === windowId);
  if (!item) {
    return;
  }

  state.selectedDatasetWindowId = windowId;
  syncManualWindowInputs(item);
  state.backendReport = item.report || "Отчет по окну отсутствует.";
  renderSelectedWindow();
  await syncBackendPanelData(item);
  await loadOrbitTrack(item);
}

async function syncBackendPanelData(datasetItem = null) {
  const baseUrl = normalizeBaseUrl(dom.backendUrl.value);
  if (!baseUrl) {
    return;
  }

  const envelope = datasetItem ? buildEnvelopeFromDatasetItem(datasetItem) : SAMPLE_WINDOW;
  const targetWindowId = datasetItem?.window_id || envelope.window_id;
  const requestSeq = ++state.detailRequestSeq;

  try {
    const [enrichResponse, telemetryResponse] = await Promise.all([
      fetch(`${baseUrl}/api/v1/envelope/enrich`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          envelope,
          scenario: state.scenarioId,
        }),
      }),
      fetch(`${baseUrl}/api/v1/telemetry/window`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          timestamp_start: envelope.timestamp_start,
          timestamp_end: envelope.timestamp_end,
          raw_telemetry_ref: envelope.raw_telemetry_ref,
          scenario: state.scenarioId,
          channels: [
            "Battery_Voltage",
            "Battery_Temp",
            "NanoMind_Temp",
            "ACU2_Temp",
            "Background_RSSI",
            "Z_Coarse_Spin",
            "PD1_CSS_theta",
          ],
        }),
      }),
    ]);

    if (enrichResponse.ok) {
      const enrichData = await enrichResponse.json();
      if (datasetItem) {
        datasetItem.envelope = enrichData?.envelope || null;
      }
    }

    if (telemetryResponse.ok) {
      const telemetryData = await telemetryResponse.json();
      if (datasetItem) {
        datasetItem.telemetryWindow = telemetryData || null;
      }
    }

    if (state.selectedDatasetWindowId !== targetWindowId || requestSeq !== state.detailRequestSeq) {
      return;
    }

    state.backendEnvelope = datasetItem?.envelope || null;
    state.backendTelemetryWindow = datasetItem?.telemetryWindow || null;
    renderSelectedWindow();
  } catch (error) {
    appendBackendLogLine(`ERROR: detail sync failed ${String(error)}`);
  }
}

function getCurrentAlerts() {
  if (state.backendEnvelope && Array.isArray(state.backendEnvelope.alerts)) {
    return state.backendEnvelope.alerts;
  }
  return [];
}

function getCurrentOrbitContext() {
  if (state.backendEnvelope?.orbit_context) {
    const context = state.backendEnvelope.orbit_context;
    return {
      altitude: formatMaybeNumber(context.orbit_altitude_km, " км", 2),
      latitude: formatMaybeNumber(context.orbit_lat, "°", 3),
      longitude: formatMaybeNumber(context.orbit_lon, "°", 3),
      eclipse: formatMaybeBool(context.is_eclipse),
      sunExposure: formatMaybeBool(context.sun_exposure),
      groundVisibility: formatMaybeBool(context.ground_station_visible),
      distanceToGs: formatMaybeNumber(context.distance_to_ground_station_km, " км", 1),
      orbitalPhase: formatMaybeNumber(context.orbital_phase, "", 3),
    };
  }
  return {
    altitude: "n/a",
    latitude: "n/a",
    longitude: "n/a",
    eclipse: "n/a",
    sunExposure: "n/a",
    groundVisibility: "n/a",
    distanceToGs: "n/a",
    orbitalPhase: "n/a",
  };
}

function getActiveSeries() {
  const points = state.backendTelemetryWindow?.points;
  if (!Array.isArray(points) || points.length === 0) {
    return null;
  }

  const labels = [];
  const anomalyFlags = [];
  const batteryVoltage = [];
  const batteryTemp = [];
  const nanoMindTemp = [];
  const acu2Temp = [];
  const rssi = [];
  const zSpin = [];
  const pd1Theta = [];

  let lastBatteryVoltage = 0;
  let lastBatteryTemp = 0;
  let lastNanoMind = 0;
  let lastAcu2 = 0;
  let lastRssi = -100;
  let lastSpin = 0;
  let lastTheta = 0;

  points.forEach((point, index) => {
    labels.push(index);
    const values = point.values || {};
    lastBatteryVoltage = pickNumber(values.Battery_Voltage, lastBatteryVoltage);
    lastBatteryTemp = pickNumber(values.Battery_Temp, lastBatteryTemp);
    lastNanoMind = pickNumber(values.NanoMind_Temp, lastNanoMind);
    lastAcu2 = pickNumber(values.ACU2_Temp, lastAcu2);
    lastRssi = pickNumber(values.Background_RSSI, lastRssi);
    lastSpin = pickNumber(values.Z_Coarse_Spin, lastSpin);
    lastTheta = pickNumber(values.PD1_CSS_theta, lastTheta);

    batteryVoltage.push(lastBatteryVoltage);
    batteryTemp.push(lastBatteryTemp);
    nanoMindTemp.push(lastNanoMind);
    acu2Temp.push(lastAcu2);
    rssi.push(lastRssi);
    zSpin.push(lastSpin);
    pd1Theta.push(lastTheta);
    anomalyFlags.push(index >= Math.max(0, points.length - 5));
  });

  return {
    labels,
    anomalyFlags,
    batteryVoltage,
    batteryTemp,
    nanoMindTemp,
    acu2Temp,
    rssi,
    zSpin,
    pd1Theta,
  };
}

function getActiveTelemetryRows() {
  const points = state.backendTelemetryWindow?.points;
  if (!Array.isArray(points) || points.length === 0) {
    return [];
  }

  const channels = state.backendTelemetryWindow.channels || [];
  const recentPoints = points.slice(-8);
  const rows = [];
  recentPoints.forEach((point) => {
    const timestamp = new Date(point.timestamp_utc).toISOString().slice(11, 19);
    channels.forEach((channel) => {
      const value = point.values?.[channel];
      rows.push({
        timestamp,
        channel,
        value: value == null ? "n/a" : formatChannelValue(channel, value),
        status: inferChannelStatus(channel, value),
      });
    });
  });
  return rows;
}

function getTelemetryRowsForDisplay() {
  const rows = getActiveTelemetryRows();
  if (state.surface !== "main" || state.telemetryExpanded) {
    return rows;
  }

  const anomalyRows = rows.filter((entry) => entry.status !== "OK");
  if (anomalyRows.length) {
    return anomalyRows.slice(-6);
  }

  return rows.slice(-6);
}

async function loadOrbitTrack(selectedDatasetItem = null) {
  const baseUrl = normalizeBaseUrl(dom.backendUrl.value);

  if (!baseUrl) {
    state.orbitTrack = [];
    state.orbitSource = "n/a";
    renderOrbitTrack();
    return;
  }

  const targetWindowId = selectedDatasetItem?.window_id || state.selectedDatasetWindowId || SAMPLE_WINDOW.window_id;
  const requestSeq = ++state.detailRequestSeq;

  try {
    const selectedItem = selectedDatasetItem || state.datasetItems.find((entry) => entry.window_id === state.selectedDatasetWindowId);
    const startUtc = selectedItem?.timestamp_start || SAMPLE_WINDOW.timestamp_start;
    const payload = {
      start_utc: startUtc,
      duration_minutes: 100,
      step_seconds: 120,
      tle_path: SAMPLE_WINDOW.tle_ref,
    };

    const response = await fetch(`${baseUrl}/api/v1/orbit/track`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`orbit status=${response.status}`);
    }

    const data = await response.json();
    if (selectedItem) {
      selectedItem.orbitTrack = Array.isArray(data.points) ? data.points : [];
      selectedItem.orbitSource = `Источник: API /api/v1/orbit/track (${selectedItem.orbitTrack.length} точек)`;
    }
    if (state.selectedDatasetWindowId !== targetWindowId || requestSeq !== state.detailRequestSeq) {
      return;
    }
    state.orbitTrack = selectedItem?.orbitTrack || [];
    state.orbitSource = selectedItem?.orbitSource || "Источник: API /api/v1/orbit/track";
  } catch (error) {
    if (selectedDatasetItem) {
      selectedDatasetItem.orbitTrack = [];
      selectedDatasetItem.orbitSource = `Источник: ошибка API (${String(error)})`;
    }
    if (state.selectedDatasetWindowId !== targetWindowId || requestSeq !== state.detailRequestSeq) {
      return;
    }
    state.orbitTrack = [];
    state.orbitSource = `Источник: ошибка API (${String(error)})`;
    appendBackendLogLine(`ERROR: orbit track failed ${String(error)}`);
  }

  renderOrbitTrack();
}

function renderPipeline() {
  dom.pipelineGraph.innerHTML = "";

  const canvas = document.createElement("div");
  canvas.className = "studio-canvas";
  canvas.style.minWidth = `${Math.round(GRAPH_LAYOUT.width * state.graphZoom)}px`;
  canvas.style.height = `${Math.round(GRAPH_LAYOUT.height * state.graphZoom)}px`;

  const scene = document.createElement("div");
  scene.className = "studio-scene";
  scene.style.width = `${GRAPH_LAYOUT.width}px`;
  scene.style.height = `${GRAPH_LAYOUT.height}px`;
  scene.style.transform = `scale(${state.graphZoom})`;
  scene.style.transformOrigin = "0 0";

  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", `0 0 ${GRAPH_LAYOUT.width} ${GRAPH_LAYOUT.height}`);
  svg.setAttribute("aria-label", "Граф исполнения в стиле LangGraph Studio");

  const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
  defs.appendChild(makeArrowMarker("graphArrowTrunk", "#d8dde9"));
  defs.appendChild(makeArrowMarker("graphArrowBranch", "#47d2c9"));
  defs.appendChild(makeArrowMarker("graphArrowRight", "#cb5ccf"));
  defs.appendChild(makeArrowMarker("graphArrowMerge", "#be64d9"));
  svg.appendChild(defs);

  GRAPH_EDGES.forEach((edge) => {
    const from = GRAPH_NODES[edge.from];
    const to = GRAPH_NODES[edge.to];

    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", buildEdgePath(edge, from, to));
    path.setAttribute("class", `studio-edge ${edge.style || "trunk"} ${getEdgeState(edge)}`);
    path.setAttribute("marker-end", `url(#${getMarkerId(edge.style)})`);
    svg.appendChild(path);
  });

  scene.appendChild(svg);

  Object.entries(GRAPH_NODES).forEach(([id, node]) => {
    const nodeElement = document.createElement("div");
    const statusClass = getNodeState(id);
    const statusLabel =
      statusClass === "done" ? "выполнено" : statusClass === "active" ? "в работе" : statusClass === "dormant" ? "не выбрано" : "ожидание";

    nodeElement.className = `studio-node kind-${node.kind || "analysis"} ${statusClass}`;
    nodeElement.style.left = `${node.x}px`;
    nodeElement.style.top = `${node.y}px`;
    nodeElement.dataset.nodeId = id;

    nodeElement.innerHTML = `
      <div class="title">${node.title}</div>
      <div class="hint">${node.hint}</div>
      <span class="state">${statusLabel}</span>
    `;

    scene.appendChild(nodeElement);
  });

  canvas.appendChild(scene);
  dom.pipelineGraph.appendChild(canvas);
}

function makeArrowMarker(id, color) {
  const marker = document.createElementNS("http://www.w3.org/2000/svg", "marker");
  marker.setAttribute("id", id);
  marker.setAttribute("markerWidth", "10");
  marker.setAttribute("markerHeight", "10");
  marker.setAttribute("refX", "8");
  marker.setAttribute("refY", "3");
  marker.setAttribute("orient", "auto");
  marker.setAttribute("markerUnits", "strokeWidth");
  const arrow = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
  arrow.setAttribute("points", "0 0, 10 3, 0 6");
  arrow.setAttribute("fill", color);
  marker.appendChild(arrow);
  return marker;
}

function getMarkerId(style) {
  if (style === "trunk") {
    return "graphArrowTrunk";
  }
  if (style === "branch") {
    return "graphArrowBranch";
  }
  if (style === "right") {
    return "graphArrowRight";
  }
  return "graphArrowMerge";
}

function buildEdgePath(edge, from, to) {
  const nodeWidth = GRAPH_LAYOUT.nodeWidth;
  const nodeHeight = GRAPH_LAYOUT.nodeHeight;

  const fromCenterX = from.x + nodeWidth / 2;
  const fromBottomY = from.y + nodeHeight;
  const toCenterX = to.x + nodeWidth / 2;
  const toTopY = to.y;

  if (edge.from === "classification" && edge.to === "deep_research") {
    return `M ${fromCenterX} ${fromBottomY} C ${fromCenterX + 120} ${fromBottomY + 16}, ${toCenterX + 48} ${toTopY - 40}, ${toCenterX} ${toTopY}`;
  }
  if (edge.from === "classification" && edge.to === "nominal_summary") {
    return `M ${fromCenterX} ${fromBottomY} C ${fromCenterX - 120} ${fromBottomY + 16}, ${toCenterX - 48} ${toTopY - 40}, ${toCenterX} ${toTopY}`;
  }
  if (edge.to === "end") {
    const curveSign = fromCenterX < toCenterX ? 1 : -1;
    return `M ${fromCenterX} ${fromBottomY} C ${fromCenterX + curveSign * 30} ${fromBottomY + 62}, ${toCenterX + curveSign * 80} ${toTopY - 54}, ${toCenterX} ${toTopY}`;
  }
  if (Math.abs(fromCenterX - toCenterX) < 1) {
    return `M ${fromCenterX} ${fromBottomY} L ${toCenterX} ${toTopY}`;
  }
  return `M ${fromCenterX} ${fromBottomY} C ${fromCenterX} ${fromBottomY + 36}, ${toCenterX} ${toTopY - 36}, ${toCenterX} ${toTopY}`;
}

function getNodeState(nodeId) {
  const progress = getSelectedWindowProgress();
  if (progress.completedNodes.includes(nodeId)) {
    return "done";
  }
  if (progress.currentNode === nodeId) {
    return "active";
  }
  if (progress.branchResolved !== true) {
    return "pending";
  }
  if (!progress.path.includes(nodeId)) {
    return "dormant";
  }
  return "pending";
}

function getEdgeState(edge) {
  const progress = getSelectedWindowProgress();
  if (progress.completedNodes.includes(edge.to)) {
    return "done";
  }
  if (progress.currentNode === edge.to || progress.currentNode === edge.from) {
    return "active";
  }
  if (progress.branchResolved !== true) {
    return "pending";
  }
  const fromIndex = progress.path.indexOf(edge.from);
  const toIndex = progress.path.indexOf(edge.to);
  const pathEdge = fromIndex !== -1 && toIndex !== -1 && toIndex === fromIndex + 1;

  if (!pathEdge) {
    return "dormant";
  }
  return "pending";
}

function getSelectedWindowProgress() {
  if (!state.selectedDatasetWindowId) {
    return { path: [], branchResolved: false, currentNode: null, completedNodes: [] };
  }
  return ensureWindowProgress(state.selectedDatasetWindowId);
}

function renderBackendLogs() {
  if (!dom.backendLogs) {
    return;
  }

  const previousScrollTop = dom.backendLogs.scrollTop;
  const previousScrollHeight = dom.backendLogs.scrollHeight;
  const viewportHeight = dom.backendLogs.clientHeight;
  const wasNearBottom = previousScrollHeight - (previousScrollTop + viewportHeight) < 24;

  dom.backendLogs.innerHTML = buildBackendLogsHtml();

  if (wasNearBottom) {
    dom.backendLogs.scrollTop = dom.backendLogs.scrollHeight;
    return;
  }

  const nextScrollHeight = dom.backendLogs.scrollHeight;
  const heightDelta = nextScrollHeight - previousScrollHeight;
  dom.backendLogs.scrollTop = previousScrollTop + Math.max(0, heightDelta);
}

function renderDatasetWindows() {
  if (!dom.datasetWindows) {
    return;
  }

  if (!state.datasetItems.length) {
    dom.datasetWindows.innerHTML = '<div class="log-empty">После запуска здесь появятся интервалы анализа, найденные в датасете.</div>';
    return;
  }

  dom.datasetWindows.innerHTML = state.datasetItems
    .map((item) => {
      const activeClass = item.window_id === state.selectedDatasetWindowId ? "active" : "";
      const statusClass = item.status || "queued";
      const summary = buildDatasetWindowSummary(item.report || item.summary || "");
      return `
        <button class="dataset-window ${activeClass} ${statusClass}" data-window-id="${escapeHtml(item.window_id)}" type="button">
          <div class="dataset-window-title">
            <span>${escapeHtml(item.window_id)}</span>
            <span>${escapeHtml(item.status === "running" ? "RUN" : item.status === "completed" ? summary.badge : item.status === "failed" ? "FAIL" : "QUEUE")}</span>
          </div>
          <div class="dataset-window-time">${escapeHtml(item.timestamp_start)} - ${escapeHtml(item.timestamp_end)}</div>
          <div class="dataset-window-caption">Временной интервал телеметрии для отдельного прогона агентного анализа.</div>
          <div class="dataset-window-summary">${escapeHtml(item.summary || summary.text)}</div>
        </button>
      `;
    })
    .join("");

  dom.datasetWindows.querySelectorAll(".dataset-window").forEach((button) => {
    button.addEventListener("click", async () => {
      const windowId = button.dataset.windowId || "";
      await selectDatasetWindow(windowId);
    });
  });
}

function renderRunStatus() {
  if (!dom.runStatus) {
    return;
  }

  const info = state.runStatus;
  dom.runStatus.className = "verify run-status";
  dom.runStatus.innerHTML = `
    <strong>${escapeHtml(info.text)}</strong>
    <div class="meta">run_id: ${escapeHtml(state.runId || "n/a")}</div>
    <div class="meta">интервалов: ${info.windowsCount} · обработано: ${info.processedCount}</div>
    <div class="meta">текущий интервал: ${escapeHtml(info.currentWindowId || "n/a")}</div>
    <div class="meta">старт: ${escapeHtml(info.startedAtUtc || "n/a")}</div>
    <div class="meta">завершение: ${escapeHtml(info.completedAtUtc || "n/a")}</div>
    <div class="${info.error ? "bad" : "ok"}">${escapeHtml(info.error || "ошибок нет")}</div>
  `;
}

function renderUVPlan() {
  dom.uvPlan.innerHTML = "";
  const plan = getCurrentUVPlan();

  if (!plan.length) {
    dom.uvPlan.innerHTML = "<li>Структурированный план УВ не получен. Ориентируйтесь на итоговый отчет и backend-логи.</li>";
    return;
  }

  plan.forEach((item) => {
    const li = document.createElement("li");
    li.innerHTML = `
      <span class="risk ${item.risk}">${item.risk.toUpperCase()}</span>
      <strong>${escapeHtml(item.action)}</strong>
      <div>${escapeHtml(item.description)}</div>
      ${item.prechecks?.length ? `<div>${escapeHtml(`Перед исполнением: ${item.prechecks.join("; ")}`)}</div>` : ""}
    `;
    dom.uvPlan.appendChild(li);
  });
}

function renderVerify() {
  const selectedItem = getSelectedDatasetItem();
  const verify = selectedItem?.uv_post_check || parseVerifyFromBackendReport(state.backendReport);
  if (verify.valid === null) {
    dom.verifyBlock.innerHTML = "<div>Данных post-hook пока нет.</div>";
    return;
  }

  const validBlock = verify.valid
    ? '<div class="ok"><strong>valid: true</strong></div>'
    : '<div class="bad"><strong>valid: false</strong></div>';

  dom.verifyBlock.innerHTML = `
    ${validBlock}
    <div><strong>Нарушения:</strong> ${verify.violations.length ? verify.violations.join(", ") : "нет"}</div>
    <div><strong>Ограничения:</strong> ${verify.constraints.join("; ") || "нет"}</div>
    <div><strong>Рекомендации:</strong> ${verify.recommendations.join("; ") || "нет"}</div>
  `;
}

function renderReport() {
  const reportText = state.backendReport || state.finalReport;
  if (!reportText) {
    dom.finalReport.innerHTML = '<div class="log-empty">Итоговый отчет появится после анализа выбранного окна.</div>';
    return;
  }
  dom.finalReport.innerHTML = renderMarkdown(reportText);
}

function renderOrbitContext() {
  if (!dom.orbitContext) {
    return;
  }
  const item = getSelectedDatasetItem();
  const orbit = getCurrentOrbitContext();
  const classification = item?.classification || {};
  const alerts = getCurrentAlerts();
  const anomalyClass = classification.anomaly_class || "n/a";
  const confidence = formatConfidenceValue(classification.confidence_alarm ?? classification.confidence);
  const rows = [
    ["Интервал", item?.window_id || "n/a"],
    ["Класс НС", anomalyClass],
    ["Уверенность", confidence],
    ["Алерты", alerts.length ? alerts.join(", ") : "n/a"],
    ["Высота орбиты", orbit.altitude],
    ["Широта", orbit.latitude],
    ["Долгота", orbit.longitude],
    ["Затмение", orbit.eclipse],
    ["Видимость НС", orbit.groundVisibility],
    ["Фаза орбиты", orbit.orbitalPhase],
  ];

  dom.orbitContext.innerHTML = rows
    .map(
      ([key, value]) => `
        <div class="science-kv-row">
          <span>${escapeHtml(key)}</span>
          <strong>${escapeHtml(String(value || "n/a"))}</strong>
        </div>`
    )
    .join("");
}

function renderTelemetryStream() {
  if (!dom.telemetryStream || !dom.telemetryMeta || !dom.btnTelemetryToggle) {
    return;
  }
  const rows = getActiveTelemetryRows();
  const visibleRows = rows;

  dom.btnTelemetryToggle.hidden = true;
  dom.btnTelemetryToggle.textContent = "Поток полностью показан";

  if (!rows.length) {
    dom.telemetryMeta.textContent = "Полный поток телеметрии выбранного интервала будет показан здесь после загрузки данных.";
  } else {
    dom.telemetryMeta.textContent = `Показан полный поток телеметрии выбранного интервала: ${rows.length} строк.`;
  }

  if (!rows.length) {
    dom.telemetryStream.innerHTML = `
      <tr>
        <td colspan="4">Backend телеметрия пока не загружена.</td>
      </tr>
    `;
    return;
  }

  dom.telemetryStream.innerHTML = visibleRows
    .map((entry) => {
      const cls = entry.status === "OK" ? "status-ok" : entry.status === "WARN" ? "status-warn" : "status-crit";
      return `
      <tr>
        <td>${entry.timestamp}</td>
        <td>${entry.channel}</td>
        <td>${entry.value}</td>
        <td class="${cls}">${entry.status}</td>
      </tr>`;
    })
    .join("");
}

function parseBackendLogEntries(lines) {
  const entries = [];
  const prefixedPattern = /^([^|]+?)\s+\|\s+([A-Z]+)\s+\|\s+([^|]+?)\s+\|\s*(.*)$/;
  const uvicornPattern = /^([A-Z]+):\s+(.*)$/;

  lines.forEach((line) => {
    const prefixedMatch = line.match(prefixedPattern);
    if (prefixedMatch) {
      entries.push({
        time: prefixedMatch[1].trim(),
        level: prefixedMatch[2].trim(),
        source: prefixedMatch[3].trim(),
        body: prefixedMatch[4],
      });
      return;
    }

    const uvicornMatch = line.match(uvicornPattern);
    if (uvicornMatch) {
      entries.push({
        time: "runtime",
        level: uvicornMatch[1].trim(),
        source: "uvicorn",
        body: uvicornMatch[2],
      });
      return;
    }

    if (entries.length) {
      entries[entries.length - 1].body += `\n${line}`;
      return;
    }

    entries.push({
      time: "runtime",
      level: "INFO",
      source: "backend",
      body: line,
    });
  });

  return entries.slice(-240);
}

function renderLogBody(body) {
  const decodedAnswer = extractJsonStringField(body, "answer");
  if (decodedAnswer) {
    return `<div class="log-markdown">${renderMarkdown(decodedAnswer)}</div><pre class="log-raw">${escapeHtml(body)}</pre>`;
  }

  const decodedReasoning = extractJsonStringField(body, "reasoning");
  if (decodedReasoning) {
    return `<div class="log-markdown">${renderMarkdown(decodedReasoning)}</div><pre class="log-raw">${escapeHtml(body)}</pre>`;
  }

  return `<pre class="log-raw">${escapeHtml(body)}</pre>`;
}

function buildCompactLogMessage(body) {
  const firstLine = String(body).split("\n")[0].trim();
  return escapeHtml(firstLine.length > 180 ? `${firstLine.slice(0, 177)}...` : firstLine || "...");
}

function buildDatasetWindowSummary(reportText) {
  const text = String(reportText || "");
  const anomalyMatch = text.match(/Классификация:\s*([A-Z_]+)/i) || text.match(/Обнаружена НС класса\s+([A-Z_]+)/i);
  const badge = anomalyMatch ? anomalyMatch[1].toUpperCase() : "ИНТЕРВАЛ";
  const firstContentLine = text
    .split("\n")
    .map((line) => line.trim())
    .find((line) => line && !line.startsWith("#"));
  return {
    badge,
    text: firstContentLine || "n/a",
  };
}

function normalizeUvPlanEntry(rawEntry) {
  return {
    action: String(rawEntry?.action || ""),
    description: String(rawEntry?.description || ""),
    risk: String(rawEntry?.priority || rawEntry?.risk || "MEDIUM").toLowerCase().replace("medium", "med").replace("high", "high").replace("low", "low"),
    prechecks: Array.isArray(rawEntry?.prechecks) ? rawEntry.prechecks.map((item) => String(item)) : [],
    postchecks: Array.isArray(rawEntry?.postchecks) ? rawEntry.postchecks.map((item) => String(item)) : [],
  };
}

function getCurrentUVPlan() {
  const selectedItem = getSelectedDatasetItem();
  if (Array.isArray(selectedItem?.uv_plan_details) && selectedItem.uv_plan_details.length) {
    return selectedItem.uv_plan_details.map((entry) => normalizeUvPlanEntry(entry));
  }
  return parseUvPlanFromBackendReport(state.backendReport);
}

function parseUvPlanFromBackendReport(reportText) {
  if (!reportText) {
    return [];
  }

  const lines = String(reportText).split("\n");
  const plan = [];
  let inSection = false;

  lines.forEach((line) => {
    const trimmed = line.trim();
    if (!trimmed) {
      return;
    }
    if (trimmed.includes("### Структурированный план УВ")) {
      inSection = true;
      return;
    }
    if (!inSection && trimmed.includes("### Рекомендованные УВ")) {
      inSection = true;
      return;
    }
    if (inSection && trimmed.startsWith("### ")) {
      inSection = false;
      return;
    }
    if (!inSection) {
      return;
    }

    const numbered = trimmed.match(/^\d+\.\s+\**(.+?)\**(?::\s*(.+))?$/);
    if (numbered) {
      plan.push({
        action: numbered[1],
        description: numbered[2] || "",
        risk: "med",
        prechecks: [],
        postchecks: [],
      });
      return;
    }

    const bullet = trimmed.match(/^[-*]\s+(.+)$/);
    if (bullet) {
      plan.push({
        action: bullet[1],
        description: "",
        risk: "med",
        prechecks: [],
        postchecks: [],
      });
    }
  });

  return plan;
}

function parseVerifyFromBackendReport(reportText) {
  const result = {
    valid: null,
    violations: [],
    constraints: [],
    recommendations: [],
  };

  if (!reportText) {
    return result;
  }

  const validMatch = reportText.match(/valid:\s*(true|false)/i);
  if (validMatch) {
    result.valid = validMatch[1].toLowerCase() === "true";
  }

  const constraintsMatch = reportText.match(/constraints:\s*(.+)/i);
  if (constraintsMatch) {
    result.constraints = constraintsMatch[1]
      .replace(/[\[\]]/g, "")
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
  }

  const recommendationsMatch = reportText.match(/recommendations:\s*(.+)/i);
  if (recommendationsMatch) {
    result.recommendations = recommendationsMatch[1]
      .replace(/[\[\]]/g, "")
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
  }

  const violationsMatch = reportText.match(/violations:\s*(.+)/i);
  if (violationsMatch) {
    result.violations = violationsMatch[1]
      .replace(/[\[\]]/g, "")
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
  }

  return result;
}

function extractJsonStringField(raw, fieldName) {
  const fieldPattern = new RegExp(`"${fieldName}":\\s*"((?:\\\\.|[^"])*)"`, "s");
  const match = raw.match(fieldPattern);
  if (!match) {
    return "";
  }

  try {
    return JSON.parse(`"${match[1]}"`);
  } catch (error) {
    return "";
  }
}

function renderMarkdown(markdownText) {
  const normalized = markdownText.replace(/\r\n/g, "\n").trim();
  if (!normalized) {
    return "";
  }

  const blocks = [];
  const lines = normalized.split("\n");
  let index = 0;

  while (index < lines.length) {
    const line = lines[index].trimEnd();
    if (!line.trim()) {
      index += 1;
      continue;
    }

    if (line.startsWith("```")) {
      const codeLines = [];
      index += 1;
      while (index < lines.length && !lines[index].startsWith("```")) {
        codeLines.push(lines[index]);
        index += 1;
      }
      index += 1;
      blocks.push(`<pre><code>${escapeHtml(codeLines.join("\n"))}</code></pre>`);
      continue;
    }

    if (/^###\s+/.test(line)) {
      blocks.push(`<h3>${renderInlineMarkdown(line.replace(/^###\s+/, ""))}</h3>`);
      index += 1;
      continue;
    }

    if (/^##\s+/.test(line)) {
      blocks.push(`<h2>${renderInlineMarkdown(line.replace(/^##\s+/, ""))}</h2>`);
      index += 1;
      continue;
    }

    if (/^#\s+/.test(line)) {
      blocks.push(`<h1>${renderInlineMarkdown(line.replace(/^#\s+/, ""))}</h1>`);
      index += 1;
      continue;
    }

    if (/^[-*]\s+/.test(line)) {
      const items = [];
      while (index < lines.length && /^[-*]\s+/.test(lines[index].trim())) {
        items.push(`<li>${renderInlineMarkdown(lines[index].trim().replace(/^[-*]\s+/, ""))}</li>`);
        index += 1;
      }
      blocks.push(`<ul>${items.join("")}</ul>`);
      continue;
    }

    if (/^\d+\.\s+/.test(line)) {
      const items = [];
      while (index < lines.length && /^\d+\.\s+/.test(lines[index].trim())) {
        items.push(`<li>${renderInlineMarkdown(lines[index].trim().replace(/^\d+\.\s+/, ""))}</li>`);
        index += 1;
      }
      blocks.push(`<ol>${items.join("")}</ol>`);
      continue;
    }

    if (/^>\s*/.test(line)) {
      const quoteLines = [];
      while (index < lines.length && /^>\s*/.test(lines[index].trim())) {
        quoteLines.push(renderInlineMarkdown(lines[index].trim().replace(/^>\s*/, "")));
        index += 1;
      }
      blocks.push(`<blockquote>${quoteLines.join("<br />")}</blockquote>`);
      continue;
    }

    const paragraphLines = [];
    while (index < lines.length && lines[index].trim()) {
      paragraphLines.push(renderInlineMarkdown(lines[index].trim()));
      index += 1;
    }
    blocks.push(`<p>${paragraphLines.join("<br />")}</p>`);
  }

  return blocks.join("");
}

function renderInlineMarkdown(text) {
  return escapeHtml(text)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>");
}

function renderSubsystems(alerts) {
  const map = { EPS: "ok", ADCS: "ok", COMM: "ok", THERMAL: "ok", PAYLOAD: "ok" };

  if (alerts.includes("POWER_DEGRADATION")) {
    map.EPS = "crit";
    map.PAYLOAD = "warn";
  }
  if (alerts.includes("THERMAL_OVERHEAT")) {
    map.THERMAL = "crit";
    map.PAYLOAD = "warn";
  }
  if (alerts.includes("ADCS_STABILIZATION_LOSS")) {
    map.ADCS = "crit";
  }
  if (alerts.includes("COMM_DEGRADATION")) {
    map.COMM = "warn";
  }
  if (alerts.includes("SENSOR_DEGRADATION")) {
    map.ADCS = map.ADCS === "crit" ? "crit" : "warn";
  }

  Object.entries(map).forEach(([name, value]) => {
    const el = document.getElementById(`subsystem-${name}`);
    if (!el) {
      return;
    }
    el.classList.remove("ok", "warn", "crit");
    el.classList.add(value);
  });
}

function renderOrbitTrack() {
  const canvas = dom.orbitCanvas;
  if (!canvas) {
    return;
  }
  const ctx = canvas.getContext("2d");
  if (!ctx) {
    return;
  }

  const width = canvas.width;
  const height = canvas.height;
  const cx = width * 0.5;
  const cy = height * 0.5;
  const r = Math.min(width, height) * 0.36;

  ctx.clearRect(0, 0, width, height);

  ctx.strokeStyle = "rgba(182, 205, 255, 0.14)";
  ctx.lineWidth = 1;
  ctx.setLineDash([6, 8]);
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, Math.PI * 2);
  ctx.stroke();
  ctx.setLineDash([]);

  ctx.strokeStyle = "rgba(182, 205, 255, 0.12)";
  ctx.beginPath();
  ctx.moveTo(cx - r, cy);
  ctx.lineTo(cx + r, cy);
  ctx.stroke();

  ctx.beginPath();
  ctx.moveTo(cx, cy - r);
  ctx.lineTo(cx, cy + r);
  ctx.stroke();

  // Трек орбиты
  if (state.orbitTrack.length > 1) {
    ctx.lineWidth = 2.2;
    for (let idx = 0; idx < state.orbitTrack.length - 1; idx += 1) {
      const p1 = projectOrbitPoint(state.orbitTrack[idx], cx, cy, r * 0.9);
      const p2 = projectOrbitPoint(state.orbitTrack[idx + 1], cx, cy, r * 0.9);
      ctx.strokeStyle = state.orbitTrack[idx].is_eclipse ? "rgba(255, 183, 3, 0.75)" : "rgba(71, 210, 201, 0.9)";
      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.stroke();
    }

    const current = projectOrbitPoint(state.orbitTrack[state.orbitTrack.length - 1], cx, cy, r * 0.9);
    ctx.fillStyle = "#f94144";
    ctx.beginPath();
    ctx.arc(current.x, current.y, 4, 0, Math.PI * 2);
    ctx.fill();
  }

  // Наземная станция (Москва)
  const gs = projectOrbitPoint({ lat_deg: 55.7558, lon_deg: 37.6173 }, cx, cy, r * 0.9);
  ctx.fillStyle = "#47d2c9";
  ctx.beginPath();
  ctx.arc(gs.x, gs.y, 3, 0, Math.PI * 2);
  ctx.fill();

  if (dom.orbitSource) {
    dom.orbitSource.textContent = state.orbitSource;
  }
}

function projectOrbitPoint(point, cx, cy, radius) {
  const lat = (Number(point.lat_deg || 0) * Math.PI) / 180;
  const lon = (Number(point.lon_deg || 0) * Math.PI) / 180;
  const x = cx + radius * Math.cos(lat) * Math.sin(lon);
  const y = cy - radius * Math.sin(lat);
  return { x, y };
}

function setIncidentBadge(text, badgeClass) {
  dom.incidentBadge.textContent = text;
  dom.incidentBadge.classList.remove("badge-warn", "badge-ok", "badge-crit");
  dom.incidentBadge.classList.add("badge", badgeClass);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
