"""
💬 BABA CHAT - 메인 애플리케이션
==============================

Spring Boot의 Application.java와 동일한 역할
모든 컴포넌트를 초기화하고 서버를 시작합니다.

학습 포인트:
- 애플리케이션 진입점 (@SpringBootApplication과 유사)
- 의존성 주입 및 컴포넌트 초기화
- ASGI 애플리케이션 구성
- 정적 파일 서빙
- 예외 처리 및 로깅
"""

import uvicorn
import socketio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
from typing import AsyncGenerator

# 설정 및 서비스 임포트
from app.config.settings import settings
from app.services.chat_service import ChatService
from app.controllers.chat_controller import initialize_chat_controller
import app.services.chat_service as chat_service_module


# =============================================================================
# 🚀 애플리케이션 라이프사이클 관리
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    애플리케이션 라이프사이클 관리
    
    Spring Boot의 @PostConstruct, @PreDestroy와 유사한 역할
    
    학습 포인트:
        - 애플리케이션 시작/종료 시 실행할 로직
        - 컨텍스트 매니저를 이용한 리소스 관리
        - 의존성 초기화 순서 관리
    """
    # ===== 애플리케이션 시작 시 초기화 =====
    print("=" * 60)
    print("🚀 BABA CHAT 서버 시작 중...")
    print("=" * 60)
    
    try:
        # 의존성 초기화 (Spring의 @Autowired와 유사)
        await initialize_dependencies()
        
        print("✅ 모든 컴포넌트 초기화 완료")
        print(f"🌐 서버 주소: http://{settings.HOST}:{settings.PORT}")
        print(f"📁 정적 파일: {settings.STATIC_DIR}")
        print(f"🎯 환경: {'개발' if settings.DEBUG else '운영'}")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 초기화 실패: {e}")
        raise
    
    # 애플리케이션 실행
    yield
    
    # ===== 애플리케이션 종료 시 정리 =====
    print("\n" + "=" * 60)
    print("👋 BABA CHAT 서버 종료 중...")
    print("=" * 60)
    
    try:
        await cleanup_dependencies()
        print("✅ 모든 리소스 정리 완료")
    except Exception as e:
        print(f"❌ 정리 중 오류: {e}")
    
    print("👋 서버가 종료되었습니다.")
    print("=" * 60)


async def initialize_dependencies() -> None:
    """
    의존성 초기화 함수
    
    Spring Boot의 의존성 주입과 유사한 패턴
    """
    print("🔧 의존성 초기화 중...")
    
    # 1. Socket.IO 서버 가져오기 (이미 생성됨)
    global sio
    
    # 2. 채팅 서비스 초기화
    global chat_service
    chat_service = ChatService(sio)
    chat_service_module.chat_service = chat_service
    print("   ✅ ChatService 초기화")
    
    # 3. 컨트롤러 초기화 (이벤트 핸들러 등록)
    initialize_chat_controller(sio)
    print("   ✅ ChatController 초기화")
    
    print("🎯 의존성 초기화 완료")


async def cleanup_dependencies() -> None:
    """
    애플리케이션 종료 시 리소스 정리
    """
    print("🧹 리소스 정리 중...")
    
    try:
        # Socket.IO 연결 정리
        if sio:
            # 모든 클라이언트 연결 종료
            await sio.disconnect()
            print("   ✅ Socket.IO 연결 정리")
        
        # 기타 정리 작업 (데이터베이스 연결 등)
        # TODO: 향후 데이터베이스 연결 정리 추가
        
    except Exception as e:
        print(f"   ❌ 리소스 정리 중 오류: {e}")


# =============================================================================
# 🏗️ Socket.IO 서버 생성
# =============================================================================

# Socket.IO 서버 초기화
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",  # 개발용으로 모든 origin 허용
    logger=settings.DEBUG,           # 개발 환경에서만 Socket.IO 로그 활성화
    engineio_logger=settings.DEBUG   # 개발 환경에서만 Engine.IO 로그 활성화
)

# 전역 변수 (의존성 주입용)
chat_service: ChatService = None


# =============================================================================
# 🌐 FastAPI 애플리케이션 생성
# =============================================================================

# FastAPI 앱 생성 (Spring Boot의 @SpringBootApplication과 유사)
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan
)


# =============================================================================
# 📁 정적 파일 서빙 설정
# =============================================================================

# 정적 파일 마운트 (CSS, JS, 이미지 등)
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")

# HTML 페이지 서빙
app.mount("/pages", StaticFiles(directory=settings.TEMPLATE_DIR), name="pages")


# =============================================================================
# 🛣️ HTTP 라우트 정의
# =============================================================================

@app.get("/")
async def redirect_to_rooms():
    """
    루트 경로 접속 시 방 선택 페이지로 리다이렉트
    
    학습 포인트:
        - RESTful API 설계
        - 리다이렉트 응답
        - 사용자 경험 개선
    """
    return RedirectResponse(url="/pages/rooms.html", status_code=302)


@app.get("/health")
async def health_check():
    """
    서버 헬스체크 엔드포인트
    
    Returns:
        dict: 서버 상태 정보
        
    학습 포인트:
        - 헬스체크 패턴
        - 모니터링 및 운영 지원
        - Spring Boot Actuator와 유사
    """
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.VERSION,
        "debug": settings.DEBUG
    }


@app.get("/stats")
async def get_server_stats():
    """
    서버 통계 조회 엔드포인트
    
    Returns:
        dict: 서버 통계 정보
    """
    try:
        if chat_service:
            stats = chat_service.get_stats()
            return {
                "status": "success",
                "data": stats
            }
        else:
            return {
                "status": "error",
                "message": "서비스가 초기화되지 않았습니다"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


# =============================================================================
# 🔌 Socket.IO 통합
# =============================================================================

# Socket.IO를 FastAPI와 통합 (ASGI 애플리케이션으로 래핑)
app = socketio.ASGIApp(sio, app)


# =============================================================================
# 🎯 애플리케이션 시작점
# =============================================================================

def main() -> None:
    """
    애플리케이션 메인 함수
    
    Spring Boot의 main() 메서드와 동일한 역할
    """
    try:
        # 서버 시작
        uvicorn.run(
            "app.main:app",                    # 애플리케이션 모듈 경로
            host=settings.HOST,                # 호스트 주소
            port=settings.PORT,                # 포트 번호
            log_level=settings.LOG_LEVEL.lower(),  # 로그 레벨
            reload=settings.DEBUG,             # 개발 환경에서 자동 리로드
            access_log=True                    # 액세스 로그 활성화
        )
    
    except KeyboardInterrupt:
        print("\n⚠️ 사용자에 의해 서버가 중단되었습니다.")
    
    except Exception as e:
        print(f"❌ 서버 시작 실패: {e}")
        raise


if __name__ == "__main__":
    """
    스크립트가 직접 실행될 때만 서버 시작
    
    학습 포인트:
        - 모듈 실행 패턴
        - 진입점 분리
        - 테스트 용이성
    """
    main()


# =============================================================================
# 🔧 개발/운영 가이드
# =============================================================================
"""
🚀 서버 실행 방법:

1. 개발 환경:
   python -m app.main
   또는
   uvicorn app.main:app --reload

2. 운영 환경:
   ENVIRONMENT=production uvicorn app.main:app --host 0.0.0.0 --port 8000

📁 디렉토리 구조:
backend/
├── app/
│   ├── main.py           ← 이 파일 (애플리케이션 진입점)
│   ├── config/           ← 설정 관리
│   ├── controllers/      ← 요청 처리
│   ├── services/         ← 비즈니스 로직
│   ├── models/           ← 데이터 모델
│   └── utils/            ← 유틸리티

🌐 접속 URL:
- 메인 페이지: http://localhost:8000/
- 방 선택: http://localhost:8000/pages/rooms.html
- 헬스체크: http://localhost:8000/health
- 통계: http://localhost:8000/stats

🔧 환경 변수 설정:
export ENVIRONMENT=development
export DEBUG=true
export HOST=0.0.0.0
export PORT=8000
export MAX_MESSAGE_LENGTH=1000

이런 방식으로 Spring Boot와 동일한 패턴의 
구조화된 웹 애플리케이션을 만들 수 있습니다! 🎉
"""