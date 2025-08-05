"""
애플리케이션 설정
===============

Spring Boot의 application.properties와 @ConfigurationProperties 역할

학습 포인트:
- 환경별 설정 관리 (개발/운영)
- 타입 힌팅으로 설정값 검증
- 중앙화된 설정 관리
"""

import os
from typing import List, Optional
from pydantic import validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    애플리케이션 설정 클래스
    
    Spring Boot의 @ConfigurationProperties와 유사
    환경변수나 .env 파일에서 자동으로 값을 읽어옵니다.
    """
    
    # =============================================================================
    # 🌐 서버 설정
    # =============================================================================
    APP_NAME: str = "💬 BABA CHAT"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # =============================================================================
    # 🔒 CORS 설정
    # =============================================================================
    CORS_ORIGINS: List[str] = ["*"]  # 개발용, 운영에서는 구체적 도메인 설정
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # =============================================================================
    # 📏 데이터 제한 설정
    # =============================================================================
    MAX_MESSAGE_LENGTH: int = 500
    MAX_USERNAME_LENGTH: int = 20
    MAX_ROOM_NAME_LENGTH: int = 30
    
    # =============================================================================
    # 🛡️ 보안 설정
    # =============================================================================
    BANNED_WORDS: List[str] = ["스팸", "욕설예시", "광고"]
    
    # =============================================================================
    # ⏰ 시간 설정
    # =============================================================================
    ROOM_CLEANUP_DELAY: int = 5  # 빈 방 삭제 지연시간(초)
    TYPING_TIMEOUT: int = 3       # 타이핑 상태 자동 해제 시간(초)
    
    # =============================================================================
    # 📁 정적 파일 설정
    # =============================================================================
    STATIC_DIR: str = "../아무거나/baba-chat/frontend/static"
    TEMPLATE_DIR: str = "../아무거나/baba-chat/frontend/pages"
    
    # =============================================================================
    # 📊 로그 설정
    # =============================================================================
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @validator('CORS_ORIGINS', pre=True)
    def parse_cors_origins(cls, v):
        """CORS origins를 환경변수에서 읽을 때 문자열을 리스트로 변환"""
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @validator('BANNED_WORDS', pre=True) 
    def parse_banned_words(cls, v):
        """금지어를 환경변수에서 읽을 때 문자열을 리스트로 변환"""
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    class Config:
        """Pydantic 설정"""
        env_file = ".env"                    # .env 파일 자동 로드
        env_file_encoding = "utf-8"         # 한글 지원
        case_sensitive = True               # 대소문자 구분


class DevelopmentSettings(Settings):
    """개발환경 설정"""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"


class ProductionSettings(Settings):
    """운영환경 설정"""
    DEBUG: bool = False
    LOG_LEVEL: str = "WARNING"
    CORS_ORIGINS: List[str] = ["https://yourdomain.com"]  # 실제 도메인으로 변경


def get_settings() -> Settings:
    """
    환경에 따른 설정 반환
    
    Returns:
        Settings: 환경별 설정 객체
        
    학습 포인트:
        - 환경변수 ENVIRONMENT에 따라 다른 설정 반환
        - Factory Pattern 적용
        - 싱글톤 패턴으로 성능 최적화 가능
    """
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    if environment == "production":
        return ProductionSettings()
    else:
        return DevelopmentSettings()


# 전역 설정 객체 (싱글톤)
settings = get_settings()


# =============================================================================
# 🔧 설정 사용 예시
# =============================================================================
"""
사용 방법:

from app.config.settings import settings

# 서버 시작
uvicorn.run(app, host=settings.HOST, port=settings.PORT)

# 메시지 길이 검증
if len(message) > settings.MAX_MESSAGE_LENGTH:
    raise ValueError("메시지가 너무 깁니다")

# 환경변수로 설정 변경:
# export MAX_MESSAGE_LENGTH=1000
# export BANNED_WORDS="욕설1,욕설2,욕설3"
"""