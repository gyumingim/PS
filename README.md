# 💬 BABA CHAT - 실시간 채팅 애플리케이션

Spring Boot 스타일의 구조화된 FastAPI + Socket.IO 채팅 서비스

## 🏗️ **프로젝트 구조**

```
baba-chat/
├── 📁 backend/                 # 백엔드 (Python FastAPI + Socket.IO)
│   ├── app/
│   │   ├── main.py            # 🚀 애플리케이션 진입점
│   │   ├── config/            # ⚙️ 설정 관리
│   │   │   ├── __init__.py
│   │   │   └── settings.py    # 환경변수, 상수 정의
│   │   ├── controllers/       # 🎮 요청 처리 (Spring @Controller)
│   │   │   ├── __init__.py
│   │   │   └── chat_controller.py
│   │   ├── services/          # 🔧 비즈니스 로직 (Spring @Service)
│   │   │   ├── __init__.py
│   │   │   ├── room_service.py
│   │   │   ├── user_service.py
│   │   │   └── chat_service.py
│   │   ├── models/            # 📊 데이터 모델 (Spring @Entity/@DTO)
│   │   │   ├── __init__.py
│   │   │   └── chat_models.py
│   │   └── utils/             # 🛠️ 유틸리티 함수
│   │       ├── __init__.py
│   │       └── validators.py
│   └── requirements.txt       # 📦 Python 패키지 의존성
├── 📁 frontend/               # 프론트엔드 (HTML + CSS + JS)
│   ├── pages/                 # 📄 HTML 페이지들
│   │   ├── rooms.html         # 방 선택 페이지
│   │   ├── join.html          # 닉네임 입력 페이지
│   │   └── chat.html          # 채팅 페이지
│   └── static/                # 📁 정적 파일들
│       ├── css/
│       │   └── style.css      # 🎨 통합 스타일시트
│       └── js/                # (향후 JavaScript 모듈화 시 사용)
└── README.md                  # 📖 이 파일
```

## 🎯 **핵심 특징**

### 🏛️ **Spring Boot 스타일 아키텍처**
- **Controller**: HTTP/Socket.IO 요청 처리
- **Service**: 비즈니스 로직 구현  
- **Model**: 데이터 구조 정의
- **Config**: 중앙화된 설정 관리

### 🚀 **현대적 기술 스택**
- **Backend**: FastAPI + Socket.IO + Pydantic
- **Frontend**: HTML5 + CSS3 + Vanilla JavaScript
- **실시간 통신**: WebSocket (Socket.IO)
- **타입 안정성**: Python Type Hints + Pydantic 검증

### 🌈 **사용자 경험**
- **"Baba is You" 스타일 UI**: 단순하고 귀여운 디자인
- **페이지별 분리**: 깔끔한 네비게이션
- **실시간 기능**: 타이핑 표시, 사용자 목록, 즉시 메시지 전달

## 🚀 **빠른 시작**

### 1️⃣ **환경 설정**

```bash
# Python 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate     # Windows

# 의존성 설치
cd backend
pip install -r requirements.txt
```

### 2️⃣ **서버 실행**

```bash
# 개발 환경 (자동 리로드)
cd backend
python -m app.main

# 또는 uvicorn 직접 사용
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3️⃣ **브라우저 접속**

```
🌐 http://localhost:8000/
```

## 📡 **API 엔드포인트**

### 🌐 **HTTP API**
- `GET /` → 방 선택 페이지로 리다이렉트
- `GET /health` → 서버 상태 확인
- `GET /stats` → 실시간 통계 조회
- `GET /pages/*` → HTML 페이지 서빙
- `GET /static/*` → CSS, JS 파일 서빙

### 🔌 **Socket.IO 이벤트**

#### 📤 **클라이언트 → 서버**
| 이벤트 | 데이터 | 설명 |
|--------|--------|------|
| `get_rooms` | - | 방 목록 요청 |
| `create_room` | `{room_id}` | 새 방 생성 |
| `join` | `{room, username}` | 방 입장 |
| `leave` | - | 방 나가기 |
| `message` | `{room, username, msg}` | 메시지 전송 |
| `typing_start` | - | 타이핑 시작 |
| `typing_stop` | - | 타이핑 중지 |
| `get_user_list` | `{room_id}` | 사용자 목록 요청 |
| `ping` | `{timestamp}` | 연결 상태 확인 |

#### 📥 **서버 → 클라이언트**
| 이벤트 | 데이터 | 설명 |
|--------|--------|------|
| `rooms_list` | `[{id, name, user_count, created_at}]` | 방 목록 |
| `room_created` | `{room_id}` | 방 생성 완료 |
| `join_success` | `{room, username}` | 입장 성공 |
| `leave_success` | - | 퇴장 성공 |
| `message` | `{type, content, username, timestamp, user_id}` | 메시지 수신 |
| `user_list` | `[{sid, username, joined_at}]` | 사용자 목록 |
| `typing_status` | `{users: [username]}` | 타이핑 상태 |
| `error` | `{message, error_code}` | 에러 발생 |
| `pong` | `{timestamp, server_time}` | 핑 응답 |

## ⚙️ **환경 설정**

### 🔧 **환경변수**

```bash
# 서버 설정
ENVIRONMENT=development    # development | production
DEBUG=true
HOST=0.0.0.0
PORT=8000

# 기능 제한
MAX_MESSAGE_LENGTH=500
MAX_USERNAME_LENGTH=20
MAX_ROOM_NAME_LENGTH=30

# 보안 설정
CORS_ORIGINS=*                    # 개발용, 운영시 도메인 지정
BANNED_WORDS="스팸,욕설,광고"

# 시간 설정
ROOM_CLEANUP_DELAY=5      # 빈 방 삭제 지연시간(초)
TYPING_TIMEOUT=3          # 타이핑 자동 해제시간(초)

# 로그 설정
LOG_LEVEL=INFO            # DEBUG | INFO | WARNING | ERROR
```

### 📁 **.env 파일 예시**

```env
# 개발 환경 설정
ENVIRONMENT=development
DEBUG=true
HOST=localhost
PORT=8000
MAX_MESSAGE_LENGTH=1000
BANNED_WORDS=스팸,욕설,광고,도배
```

## 🛠️ **개발 가이드**

### 📊 **코드 구조 이해하기**

#### 🎮 **Controller 계층**
```python
# app/controllers/chat_controller.py
class ChatController:
    async def handle_join(self, sid: str, data: dict):
        # 1. 요청 검증 (Pydantic)
        request = JoinRoomRequest(**data)
        
        # 2. 서비스 호출
        success, error = await chat_service.handle_user_join(...)
        
        # 3. 응답 전송
        await self._sio.emit("join_success", ...)
```

#### 🔧 **Service 계층**
```python
# app/services/chat_service.py
class ChatService:
    async def handle_user_join(self, sid, room, username):
        # 비즈니스 로직 구현
        # - 재연결 처리
        # - 방에 사용자 추가
        # - 세션 생성
        # - 알림 브로드캐스트
```

#### 📊 **Model 계층**
```python
# app/models/chat_models.py
class JoinRoomRequest(BaseModel):
    room: str = Field(..., max_length=30)
    username: str = Field(..., max_length=20)
    
    @validator('username')
    def validate_username(cls, v):
        # 커스텀 검증 로직
```

### 🧪 **새 기능 추가하기**

1. **Model 정의** (`models/chat_models.py`)
2. **Service 로직** (`services/*.py`)  
3. **Controller 핸들러** (`controllers/chat_controller.py`)
4. **프론트엔드 연동** (`frontend/pages/*.html`)

### 🔧 **확장 가능성**

#### 🗄️ **데이터베이스 연동**
```python
# SQLAlchemy + PostgreSQL
# Redis (세션 스토어)
# MongoDB (메시지 히스토리)
```

#### 🔐 **인증 시스템**
```python
# JWT 토큰 기반 인증
# OAuth2 (Google, GitHub)
# 사용자 프로필 시스템
```

#### 📱 **추가 기능**
```python
# 파일 업로드/다운로드
# 이미지 미리보기
# 메시지 검색
# @멘션 시스템
# 이모지 반응
# 방 설정 (비밀번호, 최대 인원)
```

## 🐛 **문제 해결**

### ❌ **일반적인 오류들**

#### 1. **포트 충돌**
```bash
❌ OSError: [Errno 48] Address already in use
✅ 해결: 다른 포트 사용하거나 기존 프로세스 종료
```

#### 2. **모듈 인식 안됨**
```bash
❌ ModuleNotFoundError: No module named 'app'
✅ 해결: backend 폴더에서 python -m app.main 실행
```

#### 3. **Socket.IO 연결 실패**
```bash
❌ Connection failed
✅ 해결: CORS 설정 확인, 방화벽 설정 확인
```

### 🔍 **디버깅 팁**

```bash
# 디버그 모드로 실행
DEBUG=true python -m app.main

# 상세 로그 확인
LOG_LEVEL=DEBUG uvicorn app.main:app --reload

# 헬스체크
curl http://localhost:8000/health

# 실시간 통계
curl http://localhost:8000/stats
```

## 🤝 **기여하기**

1. **Fork** 프로젝트
2. **Feature Branch** 생성 (`git checkout -b feature/amazing-feature`)
3. **Commit** 변경사항 (`git commit -m 'Add amazing feature'`)
4. **Push** to Branch (`git push origin feature/amazing-feature`)
5. **Pull Request** 오픈

## 📄 **라이선스**

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 👨‍💻 **개발자**

**BABA CHAT Team** - 학습용 프로젝트

---

### 🎓 **학습 포인트**

이 프로젝트를 통해 배울 수 있는 개념들:

- **MVC 아키텍처 패턴**
- **의존성 주입 (Dependency Injection)**
- **실시간 웹 애플리케이션**
- **RESTful API 설계**
- **Socket.IO 이벤트 기반 통신**
- **Pydantic 데이터 검증**
- **FastAPI 고급 기능**
- **비동기 프로그래밍 (async/await)**
- **에러 처리 및 로깅**
- **환경별 설정 관리**

**Happy Coding! 🚀**