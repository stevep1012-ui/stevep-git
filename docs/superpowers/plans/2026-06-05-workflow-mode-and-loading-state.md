# Workflow Mode And Loading State Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 선택한 편집 방식의 작업 메뉴만 표시하고 파일 불러오기 버튼에 처리 상태를 표시한다.

**Architecture:** 기존 `body[data-workflow-mode]`와 패널 속성을 이용해 CSS로 메뉴를 전환한다. 비동기 불러오기 함수는 제출 버튼의 원래 상태를 저장하고 `finally`에서 복원한다.

**Tech Stack:** HTML, CSS, JavaScript, Python `unittest`

---

### Task 1: 편집 방식별 패널 표시

**Files:**
- Modify: `web/index.html`
- Modify: `web/styles.css`
- Test: `tests/youtube_healing/test_web_ui.py`

- [ ] **Step 1: 실패 테스트 작성**

`test_dashboard_orchestrates_between_bird_and_turbo_modes`에 다음 검증을 추가한다.

```python
self.assertIn('data-workflow-panel="bird"', html)
self.assertIn('body[data-workflow-mode="turbo"] [data-workflow-panel="bird"]', css)
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `python3 -m unittest tests.youtube_healing.test_web_ui.WebUiTests.test_dashboard_orchestrates_between_bird_and_turbo_modes -v`

Expected: 일반 작업 패널 속성과 Turbo 모드 CSS가 없어 FAIL.

- [ ] **Step 3: 최소 구현**

`web/index.html`의 `workPackageForm`에 일반 모드 패널 속성을 추가한다.

```html
<form id="workPackageForm" class="work-package-panel hidden" data-workflow-panel="bird">
```

`web/styles.css`에 반대 모드 패널 숨김 규칙을 추가한다.

```css
body[data-workflow-mode="turbo"] [data-workflow-panel="bird"] {
  display: none;
}
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `python3 -m unittest tests.youtube_healing.test_web_ui.WebUiTests.test_dashboard_orchestrates_between_bird_and_turbo_modes -v`

Expected: PASS.

### Task 2: 파일 불러오기 버튼 상태

**Files:**
- Modify: `web/app.js`
- Test: `tests/youtube_healing/test_web_ui.py`

- [ ] **Step 1: 실패 테스트 작성**

새 테스트에서 로딩 문구와 버튼 복원 코드가 있는지 확인한다.

```python
def test_import_buttons_show_loading_state(self):
    js = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")

    self.assertIn('submitButton.textContent = "불러오는 중..."', js)
    self.assertIn("submitButton.disabled = true", js)
    self.assertIn("submitButton.textContent = originalText", js)
    self.assertIn('importTurboButton.textContent = "불러오는 중..."', js)
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `python3 -m unittest tests.youtube_healing.test_web_ui.WebUiTests.test_import_buttons_show_loading_state -v`

Expected: 로딩 버튼 처리가 없어 FAIL.

- [ ] **Step 3: 최소 구현**

`importFile`에서 제출 버튼 상태를 요청 전후로 관리한다.

```javascript
const submitButton = form.querySelector("button[type='submit']");
const originalText = submitButton.textContent;
const originallyDisabled = submitButton.disabled;
submitButton.textContent = "불러오는 중...";
submitButton.disabled = true;
try {
  // 기존 업로드 요청
} finally {
  submitButton.textContent = originalText;
  submitButton.disabled = originallyDisabled;
}
```

`importTurboVideo`에서도 동일하게 원래 문구를 저장하고 `finally`에서 복원한다.

- [ ] **Step 4: 테스트 통과 확인**

Run: `python3 -m unittest tests.youtube_healing.test_web_ui.WebUiTests.test_import_buttons_show_loading_state -v`

Expected: PASS.

### Task 3: 회귀 검증 및 실행 반영

**Files:**
- Verify: `web/index.html`
- Verify: `web/styles.css`
- Verify: `web/app.js`

- [ ] **Step 1: UI 테스트 실행**

Run: `python3 -m unittest tests.youtube_healing.test_web_ui -v`

Expected: 모든 UI 테스트 PASS.

- [ ] **Step 2: 전체 테스트 실행**

Run: `python3 -m unittest discover -s tests -v`

Expected: 모든 테스트 PASS.

- [ ] **Step 3: 대시보드 재시작**

실행 중인 대시보드를 종료하고 `./scripts/run_dashboard.sh`로 다시 실행한다.

- [ ] **Step 4: 정적 파일과 상태 API 확인**

Run: `curl -fsS http://127.0.0.1:8787/app.js`

Expected: `불러오는 중...` 버튼 코드가 제공됨.

Run: `curl -fsS http://127.0.0.1:8787/api/turbo/engine-status`

Expected: `"installed": true`, `"command_configured": true`.

> 이 작업 폴더에는 `.git`이 없어 커밋 단계는 생략한다.
