// Toast Notification System
class ToastNotifier {
  constructor(containerId = "toastContainer") {
    this.container = document.querySelector(`#${containerId}`);
    if (!this.container) {
      this.container = document.createElement("div");
      this.container.id = containerId;
      this.container.className = "toast-container";
      document.body.appendChild(this.container);
    }
  }

  show(message, type = "info", duration = 4000) {
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;

    const icons = { success: "✓", error: "✕", warning: "⚠", info: "ℹ" };
    const icon = icons[type] || "•";

    toast.innerHTML = `
      <span class="toast-icon">${icon}</span>
      <span class="toast-message">${this._escapeHtml(message)}</span>
      <button class="toast-close" type="button">×</button>
    `;

    this.container.appendChild(toast);

    const closeBtn = toast.querySelector(".toast-close");
    closeBtn.addEventListener("click", () => this._removeToast(toast));

    if (duration > 0) {
      setTimeout(() => this._removeToast(toast), duration);
    }

    return toast;
  }

  _removeToast(toast) {
    toast.style.animation = "slideOut 200ms ease forwards";
    setTimeout(() => toast.remove(), 200);
  }

  _escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  success(message, duration) { return this.show(message, "success", duration); }
  error(message, duration) { return this.show(message, "error", duration || 5000); }
  warning(message, duration) { return this.show(message, "warning", duration); }
  info(message, duration) { return this.show(message, "info", duration); }
}

const toast = new ToastNotifier();

// Auto-refresh configuration
const AUTO_REFRESH_INTERVAL = 3000;
let autoRefreshTimer = null;
let isAutoRefreshEnabled = true;

function startAutoRefresh() {
  if (autoRefreshTimer) return;
  autoRefreshTimer = setInterval(() => {
    if (isAutoRefreshEnabled && !turboRunInProgress && !turboImportInProgress) {
      refreshStatus();
    }
  }, AUTO_REFRESH_INTERVAL);
}

function stopAutoRefresh() {
  if (autoRefreshTimer) {
    clearInterval(autoRefreshTimer);
    autoRefreshTimer = null;
  }
}

function refreshStatus() {
  if (currentWorkflowMode === "turbo") {
    loadTurboEngineStatus();
    loadTurboStatus();
  }
  loadPackageList();
}

const packageList = document.querySelector("#packageList");
const packageCount = document.querySelector("#packageCount");
const uploadCount = document.querySelector("#uploadCount");
const nextAction = document.querySelector("#nextAction");
const lastUpdated = document.querySelector("#lastUpdated");
const refreshButton = document.querySelector("#refreshButton");
const userIdInput = document.querySelector("#userIdInput");
const assetStatus = document.querySelector("#assetStatus");
const assetSummaryText = document.querySelector("#assetSummaryText");
const clearAssetsButton = document.querySelector("#clearAssetsButton");
const workflowModeSummary = document.querySelector("#workflowModeSummary");
const workflowModeTabs = [...document.querySelectorAll("[data-workflow-mode-target]")];
const videoForm = document.querySelector("#videoForm");
const imageForm = document.querySelector("#imageForm");
const musicForm = document.querySelector("#musicForm");
const turboStatus = document.querySelector("#turboStatus");
const turboEngineStatus = document.querySelector("#turboEngineStatus");
const turboTopicInput = document.querySelector("#turboTopicInput");
const runTurboButton = document.querySelector("#runTurboButton");
const turboVideoSelect = document.querySelector("#turboVideoSelect");
const importTurboButton = document.querySelector("#importTurboButton");
const videoAssetList = document.querySelector("#videoAssetList");
const imageAssetList = document.querySelector("#imageAssetList");
const musicAssetList = document.querySelector("#musicAssetList");
const workPackageForm = document.querySelector("#workPackageForm");
const workMediaSelect = document.querySelector("#workMediaSelect");
const workMusicSelect = document.querySelector("#workMusicSelect");
const workDurationSelect = document.querySelector("#workDurationSelect");
const workTitleInput = document.querySelector("#workTitleInput");
const workStatus = document.querySelector("#workStatus");
const workSubmitButton = document.querySelector("#workSubmitButton");
const subtitleForm = document.querySelector("#subtitleForm");
const subtitlePackage = document.querySelector("#subtitlePackage");
const subtitleStatus = document.querySelector("#subtitleStatus");
const selectedPackageSummary = document.querySelector("#selectedPackageSummary");
const uploadReview = document.querySelector("#uploadReview");
const finalPreviewPanel = document.querySelector("#finalPreviewPanel");
const finalPreviewVideo = document.querySelector("#finalPreviewVideo");
const finalPreviewStatus = document.querySelector("#finalPreviewStatus");
const approveFinalPreviewButton = document.querySelector("#approveFinalPreviewButton");
const goSubtitleButton = document.querySelector("#goSubtitleButton");
const instagramAuthStatus = document.querySelector("#instagramAuthStatus");
const connectInstagramButton = document.querySelector("#connectInstagramButton");
const methodInputs = [...document.querySelectorAll("input[name='subtitleMethod']")];
const methodPanels = [...document.querySelectorAll("[data-method-panel]")];
const stepPanels = [...document.querySelectorAll("[data-step]")];
const stepTabs = [...document.querySelectorAll("[data-step-target]")];
const wizardProgressFill = document.querySelector("#wizardProgressFill");
const stepOrder = ["files", "packages", "subtitles", "review"];

let currentStep = "files";
let currentPackages = [];
let currentAssets = { videos: [], images: [], music: [] };
let instagramConnected = false;
let turboRunInProgress = false;
let turboImportInProgress = false;
let turboEngineCanRun = false;
let turboImportAvailable = false;
let currentWorkflowMode = localStorage.getItem("youtubeBirdWorkflowMode") || "bird";
let selectedPackageName = localStorage.getItem("youtubeBirdSelectedPackage") || "";

userIdInput.value = localStorage.getItem("youtubeBirdUserId") || "local";

function apiUrl(path) {
  const url = new URL(path, window.location.origin);
  const userId = userIdInput.value.trim();
  if (userId) {
    url.searchParams.set("user_id", userId);
  }
  return url.toString();
}

function badge(text, warning = false) {
  const span = document.createElement("span");
  span.className = warning ? "badge warn" : "badge success";
  span.textContent = text;
  return span;
}

function selectedPackage() {
  return currentPackages.find((item) => item.name === selectedPackageName) || currentPackages[0] || null;
}

function previewApprovalKey(packageName) {
  return `youtubeBirdPreviewApproved:${packageName}`;
}

function isFinalPreviewApproved(packageName) {
  return localStorage.getItem(previewApprovalKey(packageName)) === "true";
}

function setWorkflowMode(mode) {
  currentWorkflowMode = mode === "turbo" ? "turbo" : "bird";
  localStorage.setItem("youtubeBirdWorkflowMode", currentWorkflowMode);
  document.body.dataset.workflowMode = currentWorkflowMode;
  for (const tab of workflowModeTabs) {
    tab.classList.toggle("is-active", tab.dataset.workflowModeTarget === currentWorkflowMode);
  }
  workflowModeSummary.textContent =
    currentWorkflowMode === "turbo"
      ? "MoneyPrinter Turbo 결과와 직접 촬영한 영상/사진을 함께 가져올 수 있습니다."
      : "가져온 파일로 일반 자동 작업을 진행합니다.";
  if (currentWorkflowMode === "turbo") {
    loadTurboEngineStatus();
    loadTurboStatus();
  }
}

function setWizardProgress(stepName) {
  const activeIndex = Math.max(0, stepOrder.indexOf(stepName));
  const progress = stepOrder.length > 1 ? (activeIndex / (stepOrder.length - 1)) * 100 : 0;
  if (wizardProgressFill) {
    wizardProgressFill.style.width = `${progress}%`;
  }
  document.body.dataset.currentStep = stepName;
  for (const tab of stepTabs) {
    const tabIndex = Number(tab.dataset.stepIndex);
    tab.classList.toggle("is-complete", Number.isFinite(tabIndex) && tabIndex < activeIndex);
  }
}

function showStep(stepName) {
  currentStep = stepName;
  for (const panel of stepPanels) {
    const isActive = panel.dataset.step === stepName;
    panel.classList.toggle("hidden", !isActive);
    panel.classList.toggle("is-current", isActive);
  }
  for (const tab of stepTabs) {
    tab.classList.toggle("is-active", tab.dataset.stepTarget === stepName);
  }
  setWizardProgress(stepName);
  renderNextAction();
}

function renderNextAction() {
  const hasFiles = currentAssets.videos.length > 0 || currentAssets.images.length > 0 || currentAssets.music.length > 0;
  const item = selectedPackage();
  if (!hasFiles) {
    nextAction.textContent = "파일 준비";
    return;
  }
  if (!item) {
    nextAction.textContent = "작업 영상 확인";
    return;
  }
  if (item.has_final_video && !isFinalPreviewApproved(item.name)) {
    nextAction.textContent = "프리뷰 확인";
    return;
  }
  if (!item.has_subtitled_video) {
    nextAction.textContent = "자막 설정";
    return;
  }
  nextAction.textContent = item.youtube_video_id ? "YouTube 확인" : "업로드 준비";
}

function renderPackages(packages) {
  currentPackages = packages;
  if (!selectedPackageName && packages.length) {
    selectedPackageName = packages[0].name;
  }
  packageList.replaceChildren();
  packageCount.textContent = String(packages.length);
  uploadCount.textContent = String(packages.filter((item) => item.youtube_video_id).length);
  lastUpdated.textContent = `갱신 ${new Date().toLocaleTimeString()}`;
  renderSubtitlePackageOptions(packages);
  renderSelectedPackageSummary();
  renderFinalPreview();
  renderUploadReview();
  renderNextAction();

  if (!packages.length) {
    const empty = document.createElement("div");
    empty.className = "empty";
    empty.textContent = "아직 작업 영상이 없습니다. 먼저 영상과 음악을 가져온 뒤 패키지를 생성하세요.";
    packageList.append(empty);
    return;
  }

  for (const item of packages) {
    packageList.append(renderPackageCard(item));
  }
}

function renderPackageCard(item) {
  const row = document.createElement("article");
  row.className = item.name === selectedPackageName ? "package-item is-selected" : "package-item";

  const main = document.createElement("div");
  main.className = "package-main";

  const titleWrap = document.createElement("div");
  const title = document.createElement("div");
  title.className = "package-title";
  title.textContent = item.title || item.name;
  const path = document.createElement("p");
  path.textContent = item.name;
  titleWrap.append(title, path);

  const actions = document.createElement("div");
  actions.className = "package-actions";
  const selectButton = document.createElement("button");
  selectButton.type = "button";
  selectButton.className = item.name === selectedPackageName ? "secondary-button" : "";
  selectButton.textContent = item.name === selectedPackageName ? "선택됨" : "이 작업 영상 선택";
  selectButton.addEventListener("click", () => {
    selectedPackageName = item.name;
    localStorage.setItem("youtubeBirdSelectedPackage", selectedPackageName);
    renderPackages(currentPackages);
    showStep("packages");
  });
  actions.append(selectButton);
  if (item.youtube_url) {
    const link = document.createElement("a");
    link.className = "link-button";
    link.href = item.youtube_url;
    link.target = "_blank";
    link.rel = "noreferrer";
    link.textContent = "YouTube에서 보기";
    actions.append(link);
  }

  main.append(titleWrap, actions);

  const meta = document.createElement("div");
  meta.className = "package-meta";
  meta.append(badge(item.has_final_video ? "최종 영상 있음" : "최종 영상 없음", !item.has_final_video));
  meta.append(badge(item.has_subtitled_video ? "자막 영상 있음" : "자막 필요", !item.has_subtitled_video));
  meta.append(badge(item.youtube_video_id ? "YouTube 업로드 완료" : "YouTube 대기", !item.youtube_video_id));
  meta.append(badge(item.privacy_status || "공개 상태 미설정", !item.privacy_status));
  meta.append(badge(`Instagram ${item.instagram_status || "대기"}`, !["ready", "uploaded"].includes(item.instagram_status)));

  row.append(main, meta);
  return row;
}

function renderWorkOptions() {
  const mediaValues = new Set([...workMediaSelect.selectedOptions].map((option) => option.value));
  const musicValues = new Set([...workMusicSelect.selectedOptions].map((option) => option.value));
  const shouldAutoSelectMedia = mediaValues.size === 0;
  const shouldAutoSelectMusic = musicValues.size === 0;
  workMediaSelect.replaceChildren();
  for (const asset of currentAssets.videos) {
    const option = document.createElement("option");
    option.value = `video:${asset.name}`;
    option.textContent = `영상: ${asset.name}`;
    option.selected = shouldAutoSelectMedia || mediaValues.has(option.value);
    workMediaSelect.append(option);
  }
  for (const asset of currentAssets.images) {
    const option = document.createElement("option");
    option.value = `image:${asset.name}`;
    option.textContent = `사진: ${asset.name}`;
    option.selected = shouldAutoSelectMedia || mediaValues.has(option.value);
    workMediaSelect.append(option);
  }
  if (!workMediaSelect.options.length) {
    const option = document.createElement("option");
    option.textContent = "먼저 영상 또는 사진을 가져오세요.";
    option.disabled = true;
    workMediaSelect.append(option);
  }
  workMusicSelect.replaceChildren();
  for (const asset of currentAssets.music) {
    const option = document.createElement("option");
    option.value = asset.name;
    option.textContent = asset.name;
    option.selected = shouldAutoSelectMusic || musicValues.has(option.value);
    workMusicSelect.append(option);
  }
  if (!workMusicSelect.options.length) {
    const option = document.createElement("option");
    option.textContent = "먼저 음악을 가져오세요.";
    option.disabled = true;
    workMusicSelect.append(option);
  }
}

function renderSubtitlePackageOptions(packages) {
  const currentValue = selectedPackageName || subtitlePackage.value;
  subtitlePackage.replaceChildren();
  for (const item of packages.filter((entry) => entry.has_final_video)) {
    const option = document.createElement("option");
    option.value = item.name;
    option.textContent = item.title ? `${item.title} (${item.name})` : item.name;
    subtitlePackage.append(option);
  }
  if (currentValue) {
    subtitlePackage.value = currentValue;
  }
}

function renderSelectedPackageSummary() {
  const item = selectedPackage();
  if (!item) {
    selectedPackageSummary.textContent = "작업 영상을 선택한 뒤 자막을 입힐 수 있습니다.";
    return;
  }
  selectedPackageSummary.textContent = `선택된 작업 영상: ${item.title || item.name}`;
}

function renderFinalPreview() {
  const item = selectedPackage();
  if (!item || !item.has_final_video) {
    finalPreviewPanel.classList.add("hidden");
    finalPreviewVideo.removeAttribute("src");
    finalPreviewVideo.load();
    goSubtitleButton.disabled = true;
    return;
  }
  const approved = isFinalPreviewApproved(item.name);
  const previewUrl = `/api/package-file?package_name=${encodeURIComponent(item.name)}&file=final_video.mp4`;
  finalPreviewPanel.classList.remove("hidden");
  finalPreviewVideo.src = `${apiUrl(previewUrl)}&t=${Date.now()}`;
  finalPreviewStatus.textContent = approved ? "확인 완료" : "확인 필요";
  approveFinalPreviewButton.textContent = approved ? "프리뷰 확인됨" : "프리뷰 확인 완료";
  goSubtitleButton.disabled = !approved;
}

function renderUploadReview() {
  uploadReview.replaceChildren();
  const item = selectedPackage();
  if (!item) {
    const empty = document.createElement("div");
    empty.className = "empty";
    empty.textContent = "확인할 작업 영상이 없습니다.";
    uploadReview.append(empty);
    return;
  }

  const title = document.createElement("strong");
  title.textContent = item.title || item.name;
  const meta = document.createElement("div");
  meta.className = "package-meta";
  meta.append(badge(item.has_subtitled_video ? "자막 영상 완료" : "자막 영상 없음", !item.has_subtitled_video));
  meta.append(badge(item.music_volume_approved ? `음악 볼륨 승인 ${item.music_gain_db}dB` : "음악 볼륨 확인 필요", !item.music_volume_approved));
  meta.append(badge(item.youtube_video_id ? "YouTube 업로드 완료" : "YouTube 업로드 대기", !item.youtube_video_id));
  meta.append(badge(item.privacy_status || "공개 상태 미설정", !item.privacy_status));
  meta.append(badge(`Instagram ${item.instagram_status || "대기"}`, !["ready", "uploaded"].includes(item.instagram_status)));
  uploadReview.append(title, meta);
  renderMusicVolumeControls(item);

  if (item.youtube_url) {
    const link = document.createElement("a");
    link.className = "link-button";
    link.href = item.youtube_url;
    link.target = "_blank";
    link.rel = "noreferrer";
    link.textContent = "YouTube에서 보기";
    uploadReview.append(link);
  }
  if (item.instagram_url) {
    const instagramLink = document.createElement("a");
    instagramLink.className = "link-button";
    instagramLink.href = item.instagram_url;
    instagramLink.target = "_blank";
    instagramLink.rel = "noreferrer";
    instagramLink.textContent = "Instagram에서 보기";
    uploadReview.append(instagramLink);
  } else {
    const uploadButton = document.createElement("button");
    uploadButton.type = "button";
    uploadButton.textContent = "Instagram 자동 업로드";
    const previewRequired = item.has_final_video && !isFinalPreviewApproved(item.name);
    uploadButton.disabled = !instagramConnected || previewRequired;
    uploadButton.addEventListener("click", async () => {
      try {
        await uploadInstagramPackage(item.name);
      } catch (error) {
        subtitleStatus.textContent = `Instagram 실패: ${error.message.slice(0, 80)}`;
      }
    });
    const note = document.createElement("p");
    note.className = "note";
    note.textContent = previewRequired
      ? "프리뷰 확인 후 업로드할 수 있습니다."
      : instagramConnected
      ? "공개 video_url이 설정된 패키지만 Instagram Reels로 업로드할 수 있습니다."
      : "먼저 Instagram 로그인으로 본인 Business/Creator 계정을 연결하세요.";
    uploadReview.append(uploadButton, note);
  }
}

function renderMusicVolumeControls(item) {
  if (!item.has_final_video) {
    return;
  }
  const panel = document.createElement("div");
  panel.className = "music-volume-panel";
  const heading = document.createElement("strong");
  heading.textContent = "배경음악 볼륨 프리뷰";
  const label = document.createElement("label");
  label.textContent = "음악 볼륨";
  const slider = document.createElement("input");
  slider.type = "range";
  slider.min = "-42";
  slider.max = "-16";
  slider.step = "1";
  slider.value = item.music_gain_db || "-28";
  const value = document.createElement("span");
  value.textContent = `${slider.value}dB`;
  slider.addEventListener("input", () => {
    value.textContent = `${slider.value}dB`;
  });
  label.append(slider, value);

  const previewButton = document.createElement("button");
  previewButton.type = "button";
  previewButton.textContent = "프리뷰 만들기";
  const approveButton = document.createElement("button");
  approveButton.type = "button";
  approveButton.textContent = "이 볼륨으로 승인";
  const previewSlot = document.createElement("div");
  previewSlot.className = "music-preview-slot";

  previewButton.addEventListener("click", async () => {
    await createMusicVolumePreview(item.name, Number(slider.value), previewSlot);
  });
  approveButton.addEventListener("click", async () => {
    await approveMusicVolume(item.name, Number(slider.value));
  });
  panel.append(heading, label, previewButton, approveButton, previewSlot);
  uploadReview.append(panel);
}

async function createMusicVolumePreview(packageName, musicGainDb, previewSlot) {
  subtitleStatus.textContent = "볼륨 프리뷰 생성 중";
  const response = await fetch(apiUrl("/api/music-volume/preview"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ package_name: packageName, music_gain_db: musicGainDb }),
  });
  if (!response.ok) {
    subtitleStatus.textContent = "볼륨 프리뷰 실패";
    throw new Error(await response.text());
  }
  const data = await response.json();
  const video = document.createElement("video");
  video.controls = true;
  video.src = `${data.preview_url}&t=${Date.now()}`;
  previewSlot.replaceChildren(video);
  subtitleStatus.textContent = "볼륨 프리뷰 완료";
}

async function approveMusicVolume(packageName, musicGainDb) {
  subtitleStatus.textContent = "볼륨 승인 렌더링 중";
  const response = await fetch(apiUrl("/api/music-volume/approve"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ package_name: packageName, music_gain_db: musicGainDb }),
  });
  if (!response.ok) {
    subtitleStatus.textContent = "볼륨 승인 실패";
    throw new Error(await response.text());
  }
  subtitleStatus.textContent = "볼륨 승인 완료";
  await loadPackages();
  showStep("review");
}

function formatBytes(size) {
  if (!size) return "0 B";
  const mb = size / 1024 / 1024;
  return mb >= 1 ? `${mb.toFixed(1)} MB` : `${Math.round(size / 1024)} KB`;
}

function renderAssetList(container, assets, emptyText, kind) {
  container.replaceChildren();
  if (!assets.length) {
    const empty = document.createElement("div");
    empty.className = "empty";
    empty.textContent = emptyText;
    container.append(empty);
    return;
  }

  for (const asset of assets) {
    const item = document.createElement("div");
    item.className = "asset-item";
    const name = document.createElement("strong");
    name.textContent = asset.name;
    const meta = document.createElement("span");
    meta.textContent = formatBytes(asset.size_bytes);
    const deleteButton = document.createElement("button");
    deleteButton.type = "button";
    deleteButton.className = "icon-text-button";
    deleteButton.textContent = "삭제";
    deleteButton.addEventListener("click", async () => {
      await deleteAsset(kind, asset.name);
    });
    item.append(name, meta, deleteButton);
    container.append(item);
  }
}

async function loadAssets() {
  const response = await fetch(apiUrl("/api/assets"));
  const data = await response.json();
  currentAssets = { videos: data.videos || [], images: data.images || [], music: data.music || [] };
  assetSummaryText.textContent = `영상 ${currentAssets.videos.length}개 · 사진 ${currentAssets.images.length}개 · 음악 ${currentAssets.music.length}개`;
  clearAssetsButton.disabled =
    currentAssets.videos.length + currentAssets.images.length + currentAssets.music.length === 0;
  renderAssetList(videoAssetList, currentAssets.videos, "가져온 영상이 없습니다.", "video");
  renderAssetList(imageAssetList, currentAssets.images, "가져온 사진이 없습니다.", "image");
  renderAssetList(musicAssetList, currentAssets.music, "가져온 음악이 없습니다.", "music");
  renderWorkOptions();
  renderNextAction();
}

async function deleteAsset(kind, name) {
  assetStatus.textContent = "파일 삭제 중";
  const response = await fetch(apiUrl("/api/assets/delete"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ kind, name }),
  });
  if (!response.ok) {
    assetStatus.textContent = "삭제 실패";
    throw new Error(await response.text());
  }
  assetStatus.textContent = "삭제 완료";
  await loadAssets();
}

async function clearAssets() {
  if (!confirm("가져온 영상, 사진, 음악 목록을 비울까요? 작업 영상 기록은 삭제하지 않습니다.")) {
    return;
  }
  assetStatus.textContent = "새 작업 비우는 중";
  const response = await fetch(apiUrl("/api/assets/clear"), { method: "POST" });
  if (!response.ok) {
    assetStatus.textContent = "비우기 실패";
    throw new Error(await response.text());
  }
  assetStatus.textContent = "새 작업 준비 완료";
  await loadAssets();
}

async function importFile(kind, form) {
  const input = form.querySelector("input[type='file']");
  if (!input.files.length) {
    assetStatus.textContent = "파일을 선택하세요.";
    return;
  }
  const submitButton = form.querySelector("button[type='submit']");
  const originalText = submitButton.textContent;
  const originallyDisabled = submitButton.disabled;
  const body = new FormData();
  body.append("file", input.files[0]);
  assetStatus.textContent = "가져오는 중";
  submitButton.textContent = "불러오는 중...";
  submitButton.disabled = true;
  try {
    const response = await fetch(apiUrl(`/api/import/${kind}`), {
      method: "POST",
      body,
    });
    if (!response.ok) {
      assetStatus.textContent = "실패";
      throw new Error(await response.text());
    }
    const data = await response.json();
    input.value = "";
    assetStatus.textContent = data.asset?.already_exists ? "이미 불러온 파일입니다." : "완료";
    await loadAssets();
  } finally {
    submitButton.textContent = originalText;
    submitButton.disabled = originallyDisabled;
  }
}

async function loadTurboStatus() {
  try {
    const response = await fetch(apiUrl("/api/turbo/status"));
    if (!response.ok) {
      throw new Error(await response.text());
    }
    const data = await response.json();
    turboVideoSelect.replaceChildren();
    for (const video of data.videos || []) {
      const option = document.createElement("option");
      option.value = video.name;
      option.textContent = video.name;
      turboVideoSelect.append(option);
    }
    turboImportAvailable = Boolean(data.configured && turboVideoSelect.options.length);
    if (!turboImportInProgress) {
      if (!data.configured) {
        turboStatus.textContent = "설정 필요";
      } else if (!turboVideoSelect.options.length) {
        turboStatus.textContent = "결과 없음";
      } else {
        turboStatus.textContent = `${turboVideoSelect.options.length}개`;
      }
    }
    importTurboButton.disabled = turboImportInProgress || !turboImportAvailable;
  } catch (error) {
    turboImportAvailable = false;
    if (!turboImportInProgress) {
      turboStatus.textContent = "확인 실패";
    }
    importTurboButton.disabled = true;
  }
}

async function loadTurboEngineStatus() {
  try {
    const response = await fetch(apiUrl("/api/turbo/engine-status"));
    if (!response.ok) {
      throw new Error(await response.text());
    }
    const data = await response.json();
    turboEngineCanRun = Boolean(data.installed && data.command_configured);
    if (!turboRunInProgress) {
      if (!data.installed) {
        turboEngineStatus.textContent = "설치 필요";
      } else if (!data.command_configured) {
        turboEngineStatus.textContent = "명령 필요";
      } else if (!data.api_running) {
        turboEngineStatus.textContent = "서버 시작 가능";
      } else {
        turboEngineStatus.textContent = "API 준비됨";
      }
    }
    runTurboButton.disabled = turboRunInProgress || !turboEngineCanRun;
  } catch (error) {
    turboEngineCanRun = false;
    if (!turboRunInProgress) {
      turboEngineStatus.textContent = "확인 실패";
    }
    runTurboButton.disabled = true;
  }
}

async function runTurboEngine() {
  if (turboRunInProgress) return;
  const topic = turboTopicInput.value.trim();
  if (!topic) {
    turboEngineStatus.textContent = "주제 필요";
    return;
  }
  let finalStatus = "";
  turboRunInProgress = true;
  turboEngineStatus.textContent = "실행 중";
  runTurboButton.disabled = true;
  try {
    const response = await fetch(apiUrl("/api/turbo/run"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topic }),
    });
    if (!response.ok) {
      throw new Error(await response.text());
    }
    const data = await response.json();
    finalStatus =
      data.report?.status === "started"
        ? "작업 등록됨"
        : data.report?.status === "completed"
        ? "생성 완료"
        : "실패";
    turboEngineStatus.textContent = finalStatus;
    await loadTurboStatus();
  } catch (error) {
    finalStatus = `실패: ${error.message.slice(0, 60)}`;
    turboEngineStatus.textContent = finalStatus;
  } finally {
    await loadTurboEngineStatus();
    turboRunInProgress = false;
    runTurboButton.disabled = !turboEngineCanRun;
    if (finalStatus) {
      turboEngineStatus.textContent = finalStatus;
    }
  }
}

async function importTurboVideo() {
  if (turboImportInProgress) return;
  if (!turboVideoSelect.value) {
    turboStatus.textContent = "선택 필요";
    return;
  }
  const originalText = importTurboButton.textContent;
  let finalStatus = "";
  turboImportInProgress = true;
  turboStatus.textContent = "가져오는 중";
  importTurboButton.textContent = "불러오는 중...";
  importTurboButton.disabled = true;
  try {
    const response = await fetch(apiUrl("/api/turbo/import"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ video_name: turboVideoSelect.value }),
    });
    if (!response.ok) {
      throw new Error(await response.text());
    }
    finalStatus = "가져오기 완료";
    await loadAssets();
  } catch (error) {
    finalStatus = `실패: ${error.message.slice(0, 60)}`;
  } finally {
    importTurboButton.textContent = originalText;
    await loadTurboStatus();
    turboImportInProgress = false;
    importTurboButton.disabled = !turboImportAvailable;
    turboStatus.textContent = finalStatus;
  }
}

async function createWorkPackage() {
  const mediaItems = [...workMediaSelect.selectedOptions].map((option) => {
    const [kind, name] = option.value.split(":");
    return { kind, name };
  });
  const musicItems = [...workMusicSelect.selectedOptions].map((option) => option.value);
  if (!mediaItems.length || !musicItems.length) {
    assetStatus.textContent = "영상/사진과 음악을 선택하세요.";
    workStatus.textContent = "선택 필요";
    return;
  }
  assetStatus.textContent = "작업 영상 생성 중";
  workStatus.textContent = "작업 중";
  workSubmitButton.disabled = true;
  workSubmitButton.textContent = "작업 중";
  try {
    const response = await fetch(apiUrl("/api/packages/create"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        media_kind: mediaItems[0].kind,
        media_name: mediaItems[0].name,
        music_name: musicItems[0],
        media_items: mediaItems,
        music_items: musicItems,
        duration_seconds: Number(workDurationSelect.value),
        title: workTitleInput.value,
      }),
    });
    if (!response.ok) {
      assetStatus.textContent = "작업 실패";
      workStatus.textContent = "실패";
      throw new Error(await response.text());
    }
    const data = await response.json();
    if (data.package?.name) {
      selectedPackageName = data.package.name;
      localStorage.setItem("youtubeBirdSelectedPackage", selectedPackageName);
      localStorage.removeItem(previewApprovalKey(selectedPackageName));
    }
    assetStatus.textContent = "작업 영상 생성 완료";
    workStatus.textContent = "완료";
    await loadPackages();
    showStep("packages");
  } finally {
    workSubmitButton.disabled = false;
    workSubmitButton.textContent = "작업하기";
  }
}

function activeSubtitleMethod() {
  return methodInputs.find((input) => input.checked)?.value || "intro_outro";
}

function updateSubtitlePanels() {
  const method = activeSubtitleMethod();
  for (const panel of methodPanels) {
    panel.classList.toggle("hidden", panel.dataset.methodPanel !== method);
  }
}

function numberValue(selector, fallback) {
  const value = Number(document.querySelector(selector).value);
  return Number.isFinite(value) ? value : fallback;
}

function timedCaptionsFromTextarea() {
  return document
    .querySelector("#timedLines")
    .value.split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [start, end, ...textParts] = line.split(",");
      return {
        start_seconds: Number(start),
        end_seconds: Number(end),
        text: textParts.join(",").trim(),
      };
    })
    .filter((caption) => caption.text && Number.isFinite(caption.start_seconds) && Number.isFinite(caption.end_seconds));
}

function buildSubtitleSettings() {
  const method = activeSubtitleMethod();
  const base = {
    method,
    position: document.querySelector("#subtitlePosition").value,
    font_size: numberValue("#subtitleFontSize", 44),
    box: document.querySelector("#subtitleBox").checked,
  };
  if (method === "intro_outro") {
    return {
      ...base,
      text: document.querySelector("#introText").value,
      intro_seconds: numberValue("#introSeconds", 3),
      outro_seconds: numberValue("#outroSeconds", 3),
      duration_seconds: numberValue("#subtitleDuration", 37),
    };
  }
  if (method === "lower_third") {
    return {
      ...base,
      text: document.querySelector("#lowerText").value,
      start_seconds: numberValue("#lowerStart", 2),
      end_seconds: numberValue("#lowerEnd", 8),
    };
  }
  return {
    ...base,
    captions: timedCaptionsFromTextarea(),
  };
}

async function renderSubtitles() {
  if (!subtitlePackage.value) {
    subtitleStatus.textContent = "패키지를 선택하세요.";
    return;
  }
  selectedPackageName = subtitlePackage.value;
  localStorage.setItem("youtubeBirdSelectedPackage", selectedPackageName);
  subtitleStatus.textContent = "자막 만드는 중";
  const response = await fetch(apiUrl("/api/subtitles/render"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      package_name: selectedPackageName,
      settings: buildSubtitleSettings(),
    }),
  });
  if (!response.ok) {
    subtitleStatus.textContent = "실패";
    throw new Error(await response.text());
  }
  subtitleStatus.textContent = "자막 영상 완료";
  await loadPackages();
  showStep("review");
}

async function uploadInstagramPackage(packageName) {
  subtitleStatus.textContent = "Instagram 업로드 중";
  const response = await fetch(apiUrl("/api/instagram/upload"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ package_name: packageName }),
  });
  if (!response.ok) {
    subtitleStatus.textContent = "Instagram 실패";
    throw new Error(await response.text());
  }
  subtitleStatus.textContent = "Instagram 완료";
  await loadPackages();
  showStep("review");
}

async function loadPackages() {
  refreshButton.disabled = true;
  try {
    const response = await fetch(apiUrl("/api/packages"));
    const data = await response.json();
    renderPackages(data.packages || []);
  } catch (error) {
    packageList.textContent = `대시보드 데이터를 읽지 못했습니다: ${error.message}`;
  } finally {
    refreshButton.disabled = false;
  }
}

async function loadInstagramStatus() {
  try {
    const response = await fetch(apiUrl("/api/instagram/status"));
    if (!response.ok) {
      throw new Error(await response.text());
    }
    const status = await response.json();
    instagramConnected = Boolean(status.connected);
    instagramAuthStatus.textContent = status.connected
      ? `Instagram 연결됨 ${status.instagram_username || status.instagram_user_id}`
      : "Instagram 미연결";
  } catch (error) {
    instagramConnected = false;
    instagramAuthStatus.textContent = "Instagram 상태 확인 실패";
  }
  renderUploadReview();
}

async function connectInstagram() {
  instagramAuthStatus.textContent = "Instagram 로그인 준비";
  const response = await fetch(apiUrl("/api/instagram/auth-url"));
  if (!response.ok) {
    instagramAuthStatus.textContent = "Instagram 설정 필요";
    throw new Error(await response.text());
  }
  const data = await response.json();
  window.open(data.auth_url, "_blank", "noopener,noreferrer");
}

refreshButton.addEventListener("click", async () => {
  await loadAssets();
  await loadTurboEngineStatus();
  await loadTurboStatus();
  await loadPackages();
  await loadInstagramStatus();
});
userIdInput.addEventListener("change", async () => {
  localStorage.setItem("youtubeBirdUserId", userIdInput.value.trim() || "local");
  selectedPackageName = "";
  localStorage.removeItem("youtubeBirdSelectedPackage");
  await loadAssets();
  await loadTurboStatus();
  await loadPackages();
  await loadInstagramStatus();
});
for (const tab of stepTabs) {
  tab.addEventListener("click", () => showStep(tab.dataset.stepTarget));
}
for (const tab of workflowModeTabs) {
  tab.addEventListener("click", () => setWorkflowMode(tab.dataset.workflowModeTarget));
}
for (const button of document.querySelectorAll("[data-step-next]")) {
  button.addEventListener("click", () => showStep(button.dataset.stepNext));
}
clearAssetsButton.addEventListener("click", async () => {
  try {
    await clearAssets();
  } catch (error) {
    assetStatus.textContent = `비우기 실패: ${error.message.slice(0, 80)}`;
  }
});
videoForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    await importFile("video", videoForm);
  } catch (error) {
    assetStatus.textContent = `실패: ${error.message.slice(0, 80)}`;
  }
});
imageForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    await importFile("image", imageForm);
  } catch (error) {
    assetStatus.textContent = `실패: ${error.message.slice(0, 80)}`;
  }
});
musicForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    await importFile("music", musicForm);
  } catch (error) {
    assetStatus.textContent = `실패: ${error.message.slice(0, 80)}`;
  }
});
importTurboButton.addEventListener("click", importTurboVideo);
runTurboButton.addEventListener("click", runTurboEngine);
workPackageForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    await createWorkPackage();
  } catch (error) {
    assetStatus.textContent = `작업 실패: ${error.message.slice(0, 80)}`;
  }
});
for (const input of methodInputs) {
  input.addEventListener("change", updateSubtitlePanels);
}
subtitlePackage.addEventListener("change", () => {
  selectedPackageName = subtitlePackage.value;
  localStorage.setItem("youtubeBirdSelectedPackage", selectedPackageName);
  renderSelectedPackageSummary();
  renderFinalPreview();
  renderUploadReview();
  renderNextAction();
});
approveFinalPreviewButton.addEventListener("click", () => {
  const item = selectedPackage();
  if (!item) return;
  localStorage.setItem(previewApprovalKey(item.name), "true");
  renderFinalPreview();
  renderUploadReview();
  renderNextAction();
});
subtitleForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    await renderSubtitles();
  } catch (error) {
    subtitleStatus.textContent = `실패: ${error.message.slice(0, 80)}`;
  }
});
connectInstagramButton.addEventListener("click", async () => {
  try {
    await connectInstagram();
  } catch (error) {
    instagramAuthStatus.textContent = `Instagram 실패: ${error.message.slice(0, 80)}`;
  }
});

// YouTube Upload Form
const youtubeUploadForm = document.getElementById('youtubeUploadForm');
const youtubeUploadBtn = document.getElementById('youtubeUploadBtn');
const youtubeAuthBtn = document.getElementById('youtubeAuthBtn');

if (youtubeUploadForm) {
  youtubeUploadForm.addEventListener('submit', uploadToYouTube);
}

if (youtubeAuthBtn) {
  youtubeAuthBtn.addEventListener('click', () => {
    window.location.href = 'https://accounts.google.com/o/oauth2/v2/auth?scope=https://www.googleapis.com/auth/youtube.upload';
  });
}

// Instagram Upload Form
const instagramUploadForm = document.getElementById('instagramUploadForm');
const instagramUploadBtn = document.getElementById('instagramUploadBtn');
const instagramAuthBtn = document.getElementById('instagramAuthBtn');

if (instagramUploadForm) {
  instagramUploadForm.addEventListener('submit', uploadToInstagram);
}

if (instagramAuthBtn) {
  instagramAuthBtn.addEventListener('click', () => {
    window.location.href = 'https://api.instagram.com/oauth/authorize?scope=instagram_basic,instagram_graph_user_media';
  });
}

// ===== UPLOAD SERVICE =====
async function uploadToYouTube(event) {
  event.preventDefault();
  const title = document.getElementById('youtubeTitle').value;
  const description = document.getElementById('youtubeDescription').value;
  const tags = document.getElementById('youtubeTags').value.split(',').map(t => t.trim()).filter(Boolean);
  const privacy = document.getElementById('youtubePrivacy').value;

  try {
    showProgressBar();
    const response = await fetch(apiUrl('/api/upload/youtube'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title,
        description,
        tags,
        privacy_status: privacy,
        package_name: selectedPackageName,
      }),
    });

    const result = await response.json();
    hideProgressBar();

    if (result.success) {
      notifier.success(`YouTube 업로드 완료: ${result.video_id}`);
      document.getElementById('youtubeUploadForm').classList.add('hidden');
      document.getElementById('youtubeStatus').textContent = '업로드됨';
      document.getElementById('youtubeStatus').classList.add('success');
    } else {
      notifier.error(`YouTube 업로드 실패: ${result.error}`);
    }
  } catch (error) {
    hideProgressBar();
    notifier.error(`YouTube 업로드 오류: ${error.message}`);
  }
}

async function uploadToInstagram(event) {
  event.preventDefault();
  const caption = document.getElementById('instagramCaption').value;
  const hashtags = document.getElementById('instagramHashtags').value.split(',').map(t => t.trim()).filter(Boolean);

  try {
    showProgressBar();
    const response = await fetch(apiUrl('/api/upload/instagram'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        caption,
        hashtags,
        package_name: selectedPackageName,
      }),
    });

    const result = await response.json();
    hideProgressBar();

    if (result.success) {
      notifier.success(`Instagram 업로드 완료: ${result.media_id}`);
      document.getElementById('instagramUploadForm').classList.add('hidden');
      document.getElementById('instagramStatus').textContent = '업로드됨';
      document.getElementById('instagramStatus').classList.add('success');
    } else {
      notifier.error(`Instagram 업로드 실패: ${result.error}`);
    }
  } catch (error) {
    hideProgressBar();
    notifier.error(`Instagram 업로드 오류: ${error.message}`);
  }
}

function showProgressBar() {
  document.getElementById('uploadProgress').classList.remove('hidden');
  let progress = 0;
  const interval = setInterval(() => {
    progress += Math.random() * 30;
    if (progress > 90) progress = 90;
    updateProgressBar(progress);
    if (progress >= 90) clearInterval(interval);
  }, 500);
}

function hideProgressBar() {
  updateProgressBar(100);
  setTimeout(() => {
    document.getElementById('uploadProgress').classList.add('hidden');
  }, 1000);
}

function updateProgressBar(percent) {
  const bar = document.getElementById('uploadProgressBar');
  const text = document.getElementById('uploadPercent');
  bar.style.width = `${percent}%`;
  text.textContent = `${Math.round(percent)}%`;
}

// Initialize Feather Icons
if (typeof feather !== 'undefined') {
  feather.replace();
}

// Mobile menu toggle
function setupMobileMenu() {
  const toggle = document.getElementById("mobileMenuToggle");
  const wizardNav = document.querySelector(".wizard-nav");

  function showMobileMenu() {
    if (window.innerWidth <= 640 && wizardNav) {
      toggle.style.display = "flex";
      toggle.addEventListener("click", () => {
        wizardNav.classList.toggle("mobile-menu-open");
      });
      document.addEventListener("click", (e) => {
        if (!e.target.closest(".wizard-nav") && !e.target.closest(".mobile-menu-toggle")) {
          wizardNav.classList.remove("mobile-menu-open");
        }
      });
    } else if (window.innerWidth > 640) {
      toggle.style.display = "none";
      if (wizardNav) wizardNav.classList.remove("mobile-menu-open");
    }
  }

  showMobileMenu();
  window.addEventListener("resize", showMobileMenu);
}

setupMobileMenu();

updateSubtitlePanels();
setWorkflowMode(currentWorkflowMode);
showStep("files");
loadAssets();
loadTurboEngineStatus();
loadTurboStatus();
loadPackages();
loadInstagramStatus();
startAutoRefresh();
document.addEventListener("visibilitychange", () => {
  if (document.hidden) {
    stopAutoRefresh();
  } else {
    startAutoRefresh();
    refreshStatus();
  }
});
