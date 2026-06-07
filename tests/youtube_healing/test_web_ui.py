import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class WebUiTests(unittest.TestCase):
    def test_dashboard_uses_wizard_steps(self):
        html = (PROJECT_ROOT / "web" / "index.html").read_text(encoding="utf-8")

        self.assertIn("workflow-step", html)
        self.assertIn("1. 영상과 음악", html)
        self.assertIn("2. 작업 영상", html)
        self.assertIn("3. 자막", html)
        self.assertIn("4. 확인과 업로드", html)

    def test_dashboard_has_guided_next_actions(self):
        html = (PROJECT_ROOT / "web" / "index.html").read_text(encoding="utf-8")
        js = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")

        self.assertIn("renderNextAction", js)
        self.assertIn("다음 작업", html)

    def test_dashboard_exposes_make_package_after_import(self):
        html = (PROJECT_ROOT / "web" / "index.html").read_text(encoding="utf-8")
        js = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")

        self.assertIn("assetSummaryText", html)
        self.assertIn("clearAssetsButton", html)
        self.assertIn("영상 가져오기", html)
        self.assertIn("사진 가져오기", html)
        self.assertIn("음악 가져오기", html)
        self.assertIn("imageForm", html)
        self.assertIn("작업하기", html)
        self.assertIn("workDurationSelect", html)
        self.assertIn("30분", html)
        self.assertIn("1시간", html)
        self.assertIn("createWorkPackage", js)
        self.assertIn("/api/assets/delete", js)
        self.assertIn("/api/assets/clear", js)
        self.assertIn("이미 불러온 파일입니다.", js)
        self.assertIn("먼저 영상 또는 사진을 가져오세요.", js)
        self.assertIn("duration_seconds", js)
        self.assertIn("/api/packages/create", js)

    def test_dashboard_allows_append_media_and_music_sequences(self):
        html = (PROJECT_ROOT / "web" / "index.html").read_text(encoding="utf-8")
        js = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")

        self.assertIn("영상/사진 이어 붙이기", html)
        self.assertIn('id="workMediaSelect" multiple', html)
        self.assertIn('id="workMusicSelect" multiple', html)
        self.assertIn("편집 중에도 새로 가져오기", html)
        self.assertIn("selectedOptions", js)
        self.assertIn("media_items", js)
        self.assertIn("music_items", js)

    def test_file_and_work_step_is_compact_and_has_clear_work_status(self):
        html = (PROJECT_ROOT / "web" / "index.html").read_text(encoding="utf-8")
        css = (PROJECT_ROOT / "web" / "styles.css").read_text(encoding="utf-8")
        js = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")

        self.assertIn("file-workbench", html)
        self.assertIn("import-strip", html)
        self.assertIn("asset-summary-row", html)
        self.assertIn("workStatus", html)
        self.assertIn(".file-workbench", css)
        self.assertIn(".import-strip", css)
        self.assertIn("작업 영상 생성 중", js)
        self.assertIn("작업 영상 생성 완료", js)
        self.assertIn("workSubmitButton.disabled = true", js)
        self.assertIn("const data = await response.json()", js)
        self.assertIn("selectedPackageName = data.package.name", js)
        self.assertIn('showStep("packages")', js)

    def test_dashboard_previews_finished_video_before_upload_steps(self):
        html = (PROJECT_ROOT / "web" / "index.html").read_text(encoding="utf-8")
        css = (PROJECT_ROOT / "web" / "styles.css").read_text(encoding="utf-8")
        js = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")

        self.assertIn("finalPreviewPanel", html)
        self.assertIn("합성 영상 프리뷰", html)
        self.assertIn("finalPreviewVideo", html)
        self.assertIn("approveFinalPreviewButton", html)
        self.assertIn("renderFinalPreview", js)
        self.assertIn("youtubeBirdPreviewApproved", js)
        self.assertIn("/api/package-file", js)
        self.assertIn("final_video.mp4", js)
        self.assertIn("프리뷰 확인 후 업로드", js)
        self.assertIn("!isFinalPreviewApproved(item.name)", js)
        self.assertIn(".final-preview-panel", css)

    def test_dashboard_exposes_moneyprinter_turbo_import(self):
        html = (PROJECT_ROOT / "web" / "index.html").read_text(encoding="utf-8")
        js = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")

        self.assertIn("MoneyPrinter Turbo", html)
        self.assertIn("turboStatus", html)
        self.assertIn("turboEngineStatus", html)
        self.assertIn("turboTopicInput", html)
        self.assertIn("runTurboButton", html)
        self.assertIn("turboVideoSelect", html)
        self.assertIn("importTurboButton", html)
        self.assertIn("/api/turbo/status", js)
        self.assertIn("/api/turbo/engine-status", js)
        self.assertIn("/api/turbo/run", js)
        self.assertIn("/api/turbo/import", js)
        self.assertIn("loadTurboEngineStatus", js)
        self.assertIn("runTurboEngine", js)
        self.assertIn("loadTurboStatus", js)
        self.assertIn("importTurboVideo", js)

    def test_dashboard_orchestrates_between_bird_and_turbo_modes(self):
        html = (PROJECT_ROOT / "web" / "index.html").read_text(encoding="utf-8")
        css = (PROJECT_ROOT / "web" / "styles.css").read_text(encoding="utf-8")
        js = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")

        self.assertIn("workflow-orchestrator", html)
        self.assertIn("편집 방식 선택", html)
        self.assertIn("일반 자동 작업", html)
        self.assertIn("MoneyPrinterTurbo 연동", html)
        self.assertIn("파일을 확인한 뒤 자동 편집 방식만 고르세요.", html)
        self.assertIn('data-workflow-mode-target="bird"', html)
        self.assertIn('data-workflow-mode-target="turbo"', html)
        self.assertIn('data-workflow-panel="bird"', html)
        self.assertIn('data-workflow-panel="turbo"', html)
        self.assertIn('<body data-workflow-mode="bird">', html)
        self.assertNotIn('class="workflow-orchestrator hidden"', html)
        self.assertNotIn('class="work-package-panel hidden"', html)
        self.assertIn('id="videoForm"', html)
        self.assertIn('id="imageForm"', html)
        self.assertIn("setWorkflowMode", js)
        self.assertIn("youtubeBirdWorkflowMode", js)
        self.assertIn("data-workflow-mode", js)
        self.assertNotIn('workflowOrchestrator.classList.toggle("hidden"', js)
        self.assertNotIn('workPackageForm.classList.toggle("hidden"', js)
        self.assertIn("가져온 파일로 일반 자동 작업을 진행합니다.", js)
        self.assertIn("직접 촬영한 영상/사진을 함께 가져올 수 있습니다.", js)
        self.assertIn('body[data-workflow-mode="bird"] [data-workflow-panel="turbo"]', css)
        self.assertIn('body[data-workflow-mode="turbo"] [data-workflow-panel="bird"]', css)

    def test_import_buttons_show_loading_state(self):
        js = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")

        self.assertIn('submitButton.textContent = "불러오는 중..."', js)
        self.assertIn("submitButton.disabled = true", js)
        self.assertIn("submitButton.textContent = originalText", js)
        self.assertIn("submitButton.disabled = originallyDisabled", js)
        self.assertIn('importTurboButton.textContent = "불러오는 중..."', js)
        self.assertIn("importTurboButton.textContent = originalText", js)
        self.assertIn("await loadTurboStatus()", js)
        self.assertIn('turboEngineStatus.textContent = "실행 중"', js)
        self.assertIn("runTurboButton.disabled = true", js)
        self.assertIn("let turboRunInProgress = false", js)
        self.assertIn("let turboImportInProgress = false", js)
        self.assertIn("if (turboRunInProgress) return", js)
        self.assertIn("if (turboImportInProgress) return", js)
        self.assertIn("runTurboButton.disabled = turboRunInProgress || !turboEngineCanRun", js)
        self.assertIn("importTurboButton.disabled = turboImportInProgress || !turboImportAvailable", js)
        self.assertIn("turboRunInProgress = true", js)
        self.assertIn("turboRunInProgress = false", js)
        self.assertIn("turboImportInProgress = true", js)
        self.assertIn("turboImportInProgress = false", js)
        self.assertIn("turboStatus.textContent = finalStatus", js)

    def test_dashboard_exposes_instagram_upload_action(self):
        html = (PROJECT_ROOT / "web" / "index.html").read_text(encoding="utf-8")
        js = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")

        self.assertIn("instagramAuthStatus", html)
        self.assertIn("connectInstagram", js)
        self.assertIn("/api/instagram/auth-url", js)
        self.assertIn("/api/instagram/status", js)
        self.assertIn("uploadInstagramPackage", js)
        self.assertIn("/api/instagram/upload", js)
        self.assertIn("Instagram 자동 업로드", js)

    def test_dashboard_exposes_music_volume_preview_gate(self):
        js = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")

        self.assertIn("renderMusicVolumeControls", js)
        self.assertIn("/api/music-volume/preview", js)
        self.assertIn("/api/music-volume/approve", js)
        self.assertIn("배경음악 볼륨 프리뷰", js)
        self.assertIn("이 볼륨으로 승인", js)

    def test_dashboard_has_interactive_studio_design_hooks(self):
        html = (PROJECT_ROOT / "web" / "index.html").read_text(encoding="utf-8")
        css = (PROJECT_ROOT / "web" / "styles.css").read_text(encoding="utf-8")
        js = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")

        self.assertIn("immersive-shell", html)
        self.assertIn("progress-track", html)
        self.assertIn("data-step-index", html)
        self.assertIn("--motion-smooth", css)
        self.assertIn(".wizard-tab.is-complete", css)
        self.assertIn("translateY", css)
        self.assertIn("setWizardProgress", js)


if __name__ == "__main__":
    unittest.main()
