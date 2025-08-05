"""
채팅 관련 데이터 모델
===================

Spring Boot의 Entity, DTO와 동일한 역할을 하는 Pydantic 모델들

학습 포인트:
- Pydantic: 타입 힌팅 기반 데이터 검증
- BaseModel: 모든 모델의 기본 클래스
- Field: 필드 검증 및 메타데이터 정의
- validator: 커스텀 검증 로직
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


# =============================================================================
# 🏷️ 열거형 정의 (Enums)
# =============================================================================

class MessageType(str, Enum):
    """메시지 타입 열거형"""
    USER = "user"           # 사용자 메시지
    SYSTEM = "system"       # 시스템 메시지
    TYPING = "typing"       # 타이핑 상태


class ConnectionStatus(str, Enum):
    """연결 상태 열거형"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"


# =============================================================================
# 📨 요청 모델들 (Request DTOs)
# =============================================================================

class CreateRoomRequest(BaseModel):
    """방 생성 요청 모델"""
    room_id: str = Field(..., min_length=1, max_length=30, description="방 이름")
    
    @validator('room_id')
    def validate_room_id(cls, v):
        """방 이름 검증"""
        v = v.strip()
        if not v:
            raise ValueError('방 이름을 입력해주세요')
        
        # 특수문자 제한 (선택사항)
        forbidden_chars = ['<', '>', '&', '"', "'"]
        for char in forbidden_chars:
            if char in v:
                raise ValueError(f'방 이름에 {char} 문자는 사용할 수 없습니다')
        
        return v


class JoinRoomRequest(BaseModel):
    """방 입장 요청 모델"""
    room: str = Field(..., min_length=1, max_length=30, description="방 이름")
    username: str = Field(..., min_length=1, max_length=20, description="사용자명")
    
    @validator('room', 'username')
    def validate_text_fields(cls, v):
        """텍스트 필드 공통 검증"""
        v = v.strip()
        if not v:
            raise ValueError('값을 입력해주세요')
        return v


class SendMessageRequest(BaseModel):
    """메시지 전송 요청 모델"""
    room: str = Field(..., description="방 이름")
    username: str = Field(..., description="사용자명")
    msg: str = Field(..., min_length=1, max_length=500, description="메시지 내용")
    
    @validator('msg')
    def validate_message(cls, v):
        """메시지 내용 검증"""
        v = v.strip()
        if not v:
            raise ValueError('메시지를 입력해주세요')
        return v


class TypingRequest(BaseModel):
    """타이핑 상태 요청 모델"""
    room: Optional[str] = Field(None, description="방 이름")


class UserListRequest(BaseModel):
    """사용자 목록 요청 모델"""
    room_id: str = Field(..., description="방 ID")


# =============================================================================
# 📤 응답 모델들 (Response DTOs)
# =============================================================================

class BaseResponse(BaseModel):
    """기본 응답 모델"""
    success: bool = Field(default=True, description="성공 여부")
    message: Optional[str] = Field(None, description="응답 메시지")
    timestamp: datetime = Field(default_factory=datetime.now, description="응답 시간")


class ErrorResponse(BaseResponse):
    """에러 응답 모델"""
    success: bool = Field(default=False)
    error_code: Optional[str] = Field(None, description="에러 코드")


class RoomInfo(BaseModel):
    """방 정보 모델"""
    id: str = Field(..., description="방 ID")
    name: str = Field(..., description="방 이름")
    user_count: int = Field(..., ge=0, description="사용자 수")
    created_at: float = Field(..., description="생성 시간 (Unix timestamp)")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "자유채팅",
                "name": "자유채팅",
                "user_count": 3,
                "created_at": 1640995200.0
            }
        }


class RoomListResponse(BaseResponse):
    """방 목록 응답 모델"""
    rooms: List[RoomInfo] = Field(default=[], description="방 목록")


class UserInfo(BaseModel):
    """사용자 정보 모델"""
    sid: str = Field(..., description="소켓 ID")
    username: str = Field(..., description="사용자명")
    joined_at: Optional[datetime] = Field(None, description="입장 시간")
    
    class Config:
        schema_extra = {
            "example": {
                "sid": "abc123",
                "username": "홍길동",
                "joined_at": "2024-01-01T12:00:00"
            }
        }


class UserListResponse(BaseResponse):
    """사용자 목록 응답 모델"""
    users: List[UserInfo] = Field(default=[], description="사용자 목록")


class MessageData(BaseModel):
    """메시지 데이터 모델"""
    id: Optional[str] = Field(None, description="메시지 ID")
    type: MessageType = Field(..., description="메시지 타입")
    content: str = Field(..., description="메시지 내용")
    username: str = Field(..., description="전송자명")
    timestamp: str = Field(..., description="전송 시간")
    user_id: Optional[str] = Field(None, description="전송자 소켓 ID")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "msg_123",
                "type": "user",
                "content": "안녕하세요!",
                "username": "홍길동",
                "timestamp": "2024-01-01T12:00:00",
                "user_id": "abc123"
            }
        }


class TypingStatusData(BaseModel):
    """타이핑 상태 데이터 모델"""
    users: List[str] = Field(default=[], description="타이핑 중인 사용자 목록")


class JoinSuccessResponse(BaseResponse):
    """방 입장 성공 응답 모델"""
    room: str = Field(..., description="방 이름")
    username: str = Field(..., description="사용자명")


class ConnectionStatusData(BaseModel):
    """연결 상태 데이터 모델"""
    status: ConnectionStatus = Field(..., description="연결 상태")
    timestamp: str = Field(..., description="상태 변경 시간")
    user_count: Optional[int] = Field(None, description="현재 접속자 수")


# =============================================================================
# 🗄️ 내부 데이터 모델들 (Domain Models)
# =============================================================================

class Room(BaseModel):
    """방 도메인 모델 (내부 사용)"""
    users: Dict[str, str] = Field(default_factory=dict, description="사용자 목록 {sid: username}")
    created_at: float = Field(..., description="생성 시간")
    
    def add_user(self, sid: str, username: str) -> None:
        """사용자 추가"""
        self.users[sid] = username
    
    def remove_user(self, sid: str) -> bool:
        """사용자 제거, 성공 여부 반환"""
        if sid in self.users:
            del self.users[sid]
            return True
        return False
    
    def get_user_count(self) -> int:
        """사용자 수 반환"""
        return len(self.users)
    
    def is_empty(self) -> bool:
        """빈 방인지 확인"""
        return len(self.users) == 0
    
    def has_user(self, username: str) -> bool:
        """특정 사용자명이 있는지 확인"""
        return username.lower() in [u.lower() for u in self.users.values()]


class UserSession(BaseModel):
    """사용자 세션 도메인 모델 (내부 사용)"""
    room: str = Field(..., description="현재 방")
    username: str = Field(..., description="사용자명")
    joined_at: datetime = Field(default_factory=datetime.now, description="입장 시간")
    last_activity: datetime = Field(default_factory=datetime.now, description="마지막 활동 시간")
    
    def update_activity(self) -> None:
        """마지막 활동 시간 업데이트"""
        self.last_activity = datetime.now()


# =============================================================================
# 🔧 모델 사용 예시
# =============================================================================
"""
사용 방법:

# 요청 검증
try:
    request = CreateRoomRequest(room_id="  자유채팅  ")
    print(request.room_id)  # "자유채팅" (자동으로 trim됨)
except ValidationError as e:
    print(f"검증 실패: {e}")

# 응답 생성
response = RoomListResponse(
    success=True,
    message="방 목록 조회 성공",
    rooms=[
        RoomInfo(id="방1", name="방1", user_count=3, created_at=time.time())
    ]
)

# 도메인 모델 사용
room = Room(created_at=time.time())
room.add_user("sid123", "홍길동")
if room.has_user("홍길동"):
    print("사용자가 방에 있습니다")
"""