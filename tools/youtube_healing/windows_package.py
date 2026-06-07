from __future__ import annotations

import argparse
import shutil
from pathlib import Path


START_WINDOWS_BAT = """@echo off
cd /d "%~dp0"
python --version >nul 2>&1
if errorlevel 1 (
  echo Python is not installed. Install Python 3.11 or later from https://www.python.org/downloads/windows/
  pause
  exit /b 1
)
python -m tools.youtube_healing.dashboard_server --host 127.0.0.1 --port 8787 --multi-user-root data\\users
pause
"""


AUTHORIZE_YOUTUBE_BAT = """@echo off
cd /d "%~dp0"
if not exist "secrets\\client_secret.json" (
  echo Missing secrets\\client_secret.json
  echo Read YouTube-OAuth-Setup-KO.txt first.
  pause
  exit /b 1
)
python -m pip install google-api-python-client google-auth-oauthlib google-auth-httplib2
python -m tools.youtube_healing.publish_agent --authorize-youtube --client-secret-file "secrets\\client_secret.json" --token-file "secrets\\youtube_token.json"
echo.
echo YouTube authorization completed. Token saved to secrets\\youtube_token.json
pause
"""


BUILD_EXE_BAT = """@echo off
cd /d "%~dp0"
python -m pip install --upgrade pip
python -m pip install pyinstaller google-api-python-client google-auth-oauthlib google-auth-httplib2 requests
pyinstaller --name YoutubeBirdStudio --onefile --add-data "web;web" --add-data "config;config" tools\\youtube_healing\\windows_studio_launcher.py
echo.
echo Built executable: dist\\YoutubeBirdStudio.exe
pause
"""


README_FIRST_KO = """YouTube Bird Studio - Windows 처음 실행

1. 압축을 풉니다.
2. Start-Windows.bat 을 더블클릭합니다.
3. 브라우저에서 http://127.0.0.1:8787/ 이 열리면 사용합니다.

필요한 것:
- Windows 10/11
- Python 3.11 이상
- FFmpeg

실행파일 만들기:
- Build-Exe-Windows.bat 을 더블클릭합니다.
- 완료 후 dist\\YoutubeBirdStudio.exe 가 생성됩니다.

YouTube API 주의:
- 이 패키지에는 제작자의 OAuth 토큰이나 client secret을 넣지 않습니다.
- 각 사용자는 자기 Google Cloud OAuth client를 만들어야 합니다.
- 업로드는 승인한 사용자의 YouTube 채널로 올라갑니다.

YouTube 설정:
- YouTube-OAuth-Setup-KO.txt 를 먼저 읽으세요.
- Google Cloud에서 받은 OAuth 파일을 secrets\\client_secret.json 으로 저장합니다.
- Authorize-YouTube.bat 을 실행해 본인 계정으로 승인합니다.

Instagram 자동 업로드:
- Instagram Business/Creator 계정과 Meta Graph API 권한이 필요합니다.
- 로그인 버튼을 쓰려면 INSTAGRAM_APP_ID, INSTAGRAM_APP_SECRET, INSTAGRAM_REDIRECT_URI 환경변수를 설정합니다.
- 사용자는 대시보드에서 본인 Instagram 계정으로 로그인합니다.
- 실행 전에 INSTAGRAM_VIDEO_URL 환경변수를 설정합니다.
- INSTAGRAM_VIDEO_URL 은 Meta가 가져갈 수 있는 공개 HTTPS mp4 주소여야 합니다.
- 업로드 결과는 instagram_upload_report.json 으로 저장됩니다.
- instagram_token.json 은 절대 다른 사람에게 보내지 마세요.
"""


YOUTUBE_OAUTH_SETUP_KO = """YouTube OAuth 개인 설정 안내

목표:
- 각 사용자가 본인의 Google Cloud OAuth client를 사용합니다.
- 업로드는 승인한 본인의 YouTube 채널로 올라갑니다.
- 제작자/배포자의 토큰은 절대 포함하지 않습니다.

1. Google Cloud Console 접속
- https://console.cloud.google.com/
- 새 프로젝트를 만들거나 기존 프로젝트를 선택합니다.

2. YouTube Data API v3 활성화
- APIs & Services > Library
- YouTube Data API v3 검색
- Enable 클릭

3. OAuth 동의 화면 설정
- APIs & Services > OAuth consent screen
- User Type은 개인 사용이면 External
- 앱 이름, 이메일 입력
- Scope에 YouTube upload 권한을 추가합니다.
- 테스트 모드라면 본인 Google 계정을 Test user로 추가합니다.

4. OAuth Client 생성
- APIs & Services > Credentials
- Create Credentials > OAuth client ID
- Application type: Desktop app
- JSON 다운로드

5. 파일 저장
- 다운로드한 JSON 파일 이름을 client_secret.json 으로 바꿉니다.
- 이 폴더에 저장합니다:
  secrets\\client_secret.json

6. 승인
- Authorize-YouTube.bat 을 더블클릭합니다.
- 브라우저가 열리면 본인 Google/YouTube 계정으로 승인합니다.
- 완료되면 secrets\\youtube_token.json 이 생성됩니다.

주의:
- client_secret.json 과 youtube_token.json 은 절대 다른 사람에게 보내지 마세요.
- OAuth 앱이 검증되지 않은 상태면 Google 경고 화면이 나올 수 있습니다.
- 테스트 모드에서는 Test user로 등록된 계정만 사용할 수 있습니다.
- 외부 사용자에게 넓게 배포하려면 Google OAuth 앱 검증이 필요할 수 있습니다.
"""


def build_windows_package_plan() -> dict:
    return {
        "copy_dirs": ["tools", "web", "config"],
        "generated_files": [
            "Start-Windows.bat",
            "Authorize-YouTube.bat",
            "Build-Exe-Windows.bat",
            "README-FIRST-KO.txt",
            "YouTube-OAuth-Setup-KO.txt",
        ],
    }


def _copy_tree(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "youtube_token.json", ".DS_Store"),
    )


def write_windows_package(project_root: Path, package_dir: Path) -> Path:
    package_dir.mkdir(parents=True, exist_ok=True)
    for directory in build_windows_package_plan()["copy_dirs"]:
        source = project_root / directory
        if source.exists():
            _copy_tree(source, package_dir / directory)

    (package_dir / "Start-Windows.bat").write_text(START_WINDOWS_BAT, encoding="utf-8")
    (package_dir / "Authorize-YouTube.bat").write_text(AUTHORIZE_YOUTUBE_BAT, encoding="utf-8")
    (package_dir / "Build-Exe-Windows.bat").write_text(BUILD_EXE_BAT, encoding="utf-8")
    (package_dir / "README-FIRST-KO.txt").write_text(README_FIRST_KO, encoding="utf-8")
    (package_dir / "YouTube-OAuth-Setup-KO.txt").write_text(YOUTUBE_OAUTH_SETUP_KO, encoding="utf-8")
    (package_dir / "secrets").mkdir(exist_ok=True)
    return package_dir


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create a Windows-friendly source package.")
    parser.add_argument("--output", default="dist/YoutubeBirdStudio-Windows")
    return parser


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    args = build_parser().parse_args()
    package_dir = write_windows_package(project_root, Path(args.output).expanduser())
    print(f"Windows package written: {package_dir}")


if __name__ == "__main__":
    main()
