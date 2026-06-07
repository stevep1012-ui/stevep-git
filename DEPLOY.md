# YouTube Bird Studio - 클라우드 배포 가이드

YouTube Bird Studio를 Render에 배포하는 단계별 가이드입니다.

## 📋 사전 준비

- GitHub 계정 (코드 저장소)
- Render 계정 (무료: https://render.com)
- Sentry 계정 (무료: https://sentry.io) - 선택사항

## 🚀 배포 단계

### 1단계: GitHub 저장소 설정

```bash
# 저장소 클론
git clone https://github.com/YOUR_USERNAME/youtube-bird.git
cd youtube-bird

# 또는 기존 저장소에 추가
git remote add origin https://github.com/YOUR_USERNAME/youtube-bird.git
git push -u origin main
```

### 2단계: Render 계정 설정

1. **Render 접속**: https://dashboard.render.com
2. **GitHub 연결**: Settings > GitHub 인증
3. **저장소 선택**: youtube-bird 저장소 선택

### 3단계: render.yaml 배포

Render은 render.yaml을 자동으로 감지합니다.

```bash
# render.yaml이 있는지 확인
ls -la render.yaml

# GitHub에 푸시
git add render.yaml
git commit -m "Add Render deployment configuration"
git push origin main
```

### 4단계: 환경 변수 설정

Render 대시보드에서:

1. **Web Service 생성 후**
2. **Environment** 탭에서 다음 변수 추가:

```bash
# 필수 환경 변수
SECRET_KEY=python3 -c "import secrets; print(secrets.token_hex(32))" # 실행 후 복사

# Sentry (선택사항)
SENTRY_DSN=https://your-key@sentry.io/your-project-id
SENTRY_ENVIRONMENT=production

# OAuth (선택사항)
GOOGLE_OAUTH_CLIENT_ID=your-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret

# 기타
DEBUG=false
```

### 5단계: 데이터베이스 생성

Render 대시보드:

1. **PostgreSQL** 생성: `youtube-bird-db`
2. **Redis** 생성: `youtube-bird-cache`

### 6단계: 배포

```bash
git push origin main  # 자동 배포 시작
```

## 🔍 배포 후 확인

```bash
# 헬스체크
curl https://your-domain.onrender.com/api/health

# 웹 UI
open https://your-domain.onrender.com
```

## 📊 모니터링

- **Sentry**: https://sentry.io (에러 추적)
- **Render Dashboard**: 성능 메트릭
- **로그**: Render > Logs 탭

## ✅ 배포 완료 체크리스트

- [ ] render.yaml 배포
- [ ] PostgreSQL + Redis 생성
- [ ] 환경 변수 설정
- [ ] 헬스체크 통과 (200 OK)
- [ ] 웹 UI 접근 가능
- [ ] HTTPS 자동 활성화
- [ ] 로그 정상

---

**상세 가이드**: 각 단계별 문제 해결은 이 파일의 후반부 참고
