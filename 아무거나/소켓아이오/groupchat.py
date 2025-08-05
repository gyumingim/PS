"""
💬 BABA CHAT 서버 - 실시간 채팅 애플리케이션
==============================================

이 파일은 Socket.IO와 FastAPI를 사용한 실시간 채팅 서버입니다.

📚 학습 포인트:
- Socket.IO: 실시간 양방향 통신
- FastAPI: 현대적인 Python 웹 프레임워크  
- ASGI: 비동기 웹 서버 게이트웨이 인터페이스
- 메모리 기반 데이터 관리
- 이벤트 드리븐 아키텍처
"""

from fastapi import FastAPI
import socketio
import uvicorn
import time
import re
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any

# =============================================================================
# 📋 상수 정의 (Constants)
# =============================================================================
# 왜 상수를 사용하나? 
# 1. 매직넘버 방지 2. 유지보수 용이 3. 설정 중앙화

# 메시지 및 사용자명 길이 제한
MAX_MESSAGE_LENGTH = 500      # 메시지 최대 길이
MAX_USERNAME_LENGTH = 20      # 사용자명 최대 길이  
MAX_ROOM_NAME_LENGTH = 30     # 방 이름 최대 길이

# 금지어 목록 (실제 서비스에서는 DB나 외부 파일에서 관리)
BANNED_WORDS = ["스팸", "욕설예시", "광고"]

# 서버 설정
HOST = "0.0.0.0"              # 모든 IP에서 접근 허용
PORT = 8000                   # 서버 포트
ROOM_CLEANUP_DELAY = 5        # 빈 방 삭제 지연 시간(초)

# =============================================================================
# 🏗️ 서버 초기화 (Server Initialization)
# =============================================================================

# 1) Socket.IO 서버 생성
# async_mode="asgi": ASGI 서버와 연동
# cors_allowed_origins="*": 모든 도메인에서 접근 허용 (개발용, 실제론 제한 필요)
sio = socketio.AsyncServer(
    async_mode="asgi", 
    cors_allowed_origins="*",
    logger=True,           # Socket.IO 로그 활성화
    engineio_logger=True   # Engine.IO 로그 활성화 (하위 레벨 로깅)
)

# 2) FastAPI 앱 생성
# FastAPI: 타입 힌팅 기반의 현대적 웹 프레임워크
app = FastAPI(
    title="💬 BABA CHAT API",
    description="실시간 채팅 서버 API",
    version="1.0.0"
)

# 3) Socket.IO와 FastAPI 통합
# ASGIApp: Socket.IO를 ASGI 애플리케이션으로 래핑
app = socketio.ASGIApp(sio, app)

# =============================================================================
# 💾 데이터 구조 (Data Structures)
# =============================================================================
# 메모리 기반 데이터 저장 - 서버 재시작 시 모든 데이터 소실
# 실제 서비스에서는 Redis, MongoDB 등 외부 저장소 사용 권장

# 채팅방 정보 저장
# 구조: {room_id: {users: {socket_id: username}, created_at: timestamp}}
rooms: Dict[str, Dict[str, Any]] = {}

# 사용자별 현재 접속 정보
# 구조: {socket_id: {room: room_name, username: user_name}}
user_rooms: Dict[str, Dict[str, str]] = {}

# 타이핑 상태 관리 (누가 어느 방에서 타이핑 중인지)
# 구조: {room_id: {socket_id: username}}
typing_users: Dict[str, Dict[str, str]] = {}

# =============================================================================
# 🛠️ 유틸리티 함수들 (Utility Functions)
# =============================================================================

def get_timestamp() -> str:
    """
    현재 시간을 ISO 형식으로 반환
    
    Returns:
        str: ISO 형식 타임스탬프 (예: "2024-01-01T12:30:45.123456")
        
    학습 포인트:
        - datetime.now(): 현재 로컬 시간
        - isoformat(): ISO 8601 표준 형식으로 변환
        - 실제 서비스에서는 UTC 시간 사용 권장 (datetime.utcnow())
    """
    return datetime.now().isoformat()


def validate_input(text: str, max_length: int, field_name: str) -> Optional[str]:
    """
    사용자 입력값 검증 함수
    
    Args:
        text (str): 검증할 텍스트
        max_length (int): 최대 길이
        field_name (str): 필드명 (에러 메시지용)
        
    Returns:
        Optional[str]: 에러 메시지 (문제없으면 None)
        
    학습 포인트:
        - 입력 검증은 보안의 첫 번째 방어선
        - 클라이언트 검증만으론 불충분, 서버에서도 반드시 검증
        - Optional 타입: None 또는 str 반환 가능
    """
    if not text or not text.strip():
        return f"{field_name}을(를) 입력해주세요."
    
    if len(text.strip()) > max_length:
        return f"{field_name}은(는) {max_length}자 이하로 입력해주세요."
    
    # 금지어 검사
    text_lower = text.lower()
    for banned_word in BANNED_WORDS:
        if banned_word in text_lower:
            return f"부적절한 단어가 포함되어 있습니다: '{banned_word}'"
    
    return None


def sanitize_text(text: str) -> str:
    """
    텍스트 정제 함수 (XSS 방지 등)
    
    Args:
        text (str): 정제할 텍스트
        
    Returns:
        str: 정제된 텍스트
        
    학습 포인트:
        - XSS(Cross-Site Scripting) 공격 방지
        - HTML 태그 제거로 보안 강화
        - 실제로는 더 정교한 sanitization 라이브러리 사용 권장
    """
    # HTML 태그 제거 (간단한 버전)
    text = re.sub(r'<[^>]+>', '', text)
    # 앞뒤 공백 제거
    return text.strip()


async def broadcast_user_list(room_id: str) -> None:
    """
    특정 방의 모든 사용자에게 현재 사용자 목록을 전송
    
    Args:
        room_id (str): 방 ID
        
    학습 포인트:
        - broadcast: 특정 그룹의 모든 클라이언트에게 메시지 전송
        - room 개념: Socket.IO에서 클라이언트들을 그룹으로 관리
        - List comprehension: 파이썬의 효율적인 리스트 생성 방법
    """
    if room_id not in rooms:
        print(f"⚠️ 존재하지 않는 방에 사용자 목록 전송 시도: {room_id}")
        return
    
    # 방의 모든 사용자 정보를 리스트로 생성
    user_list = [
        {"sid": sid, "username": username} 
        for sid, username in rooms[room_id]["users"].items()
    ]
    
    print(f"👥 방 '{room_id}'에 사용자 목록 전송: {len(user_list)}명")
    await sio.emit("user_list", user_list, room=room_id)


async def broadcast_room_list() -> None:
    """
    모든 클라이언트에게 현재 방 목록 전송
    
    학습 포인트:
        - 전체 브로드캐스트: 모든 연결된 클라이언트에게 전송
        - 실시간 데이터 동기화: 방 생성/삭제 시 모든 클라이언트 업데이트
    """
    room_list = []
    for room_id, room_data in rooms.items():
        room_list.append({
            "id": room_id,
            "name": room_id,
            "user_count": len(room_data["users"]),
            "created_at": room_data["created_at"]
        })
    
    print(f"🏠 전체 방 목록 브로드캐스트: {len(room_list)}개 방")
    await sio.emit("rooms_list", room_list)


async def clear_typing_status(room_id: str, sid: str) -> None:
    """
    특정 사용자의 타이핑 상태를 제거하고 다른 사용자들에게 알림
    
    Args:
        room_id (str): 방 ID
        sid (str): 소켓 ID (사용자 식별자)
        
    학습 포인트:
        - 상태 관리: 사용자의 실시간 상태(타이핑) 추적
        - 메모리 관리: 불필요한 데이터 정리로 메모리 누수 방지
        - 연쇄 업데이트: 한 사용자 상태 변경 → 다른 사용자들에게 알림
    """
    if room_id in typing_users and sid in typing_users[room_id]:
        username = typing_users[room_id][sid]
        del typing_users[room_id][sid]
        
        print(f"⌨️ {username} 타이핑 중지 (방: {room_id})")
        
        # 방에 타이핑하는 사용자가 없으면 방 자체를 삭제
        if len(typing_users[room_id]) == 0:
            del typing_users[room_id]
        
        # 변경된 타이핑 상태를 다른 사용자들에게 알림
        await broadcast_typing_status(room_id)


async def broadcast_typing_status(room_id: str) -> None:
    """
    방의 현재 타이핑 상태를 모든 사용자에게 전송
    
    Args:
        room_id (str): 방 ID
        
    학습 포인트:
        - 실시간 피드백: 사용자가 타이핑 중임을 다른 사용자에게 실시간 표시
        - UX 향상: "누군가 입력중..." 표시로 채팅 경험 개선
    """
    typing_list = []
    if room_id in typing_users:
        typing_list = list(typing_users[room_id].values())
    
    await sio.emit("typing_status", {"users": typing_list}, room=room_id)


async def delayed_room_cleanup(room_id: str) -> None:
    """
    빈 방을 지연 삭제하는 함수
    
    Args:
        room_id (str): 삭제할 방 ID
        
    학습 포인트:
        - 지연 삭제: 사용자가 새로고침 등으로 잠시 연결이 끊어져도 바로 삭제하지 않음
        - 사용자 경험 개선: 네트워크 불안정 상황에서도 방이 유지됨
        - asyncio.sleep(): 비동기적으로 대기 (다른 작업 차단하지 않음)
    """
    print(f"⏰ 방 '{room_id}' 삭제 대기 중... ({ROOM_CLEANUP_DELAY}초)")
    await asyncio.sleep(ROOM_CLEANUP_DELAY)
    
    try:
        if room_id in rooms:
            if len(rooms[room_id]["users"]) == 0:
                print(f"🗑️ 빈 방 '{room_id}' 삭제됨")
                del rooms[room_id]
                await broadcast_room_list()
            else:
                print(f"👥 방 '{room_id}'에 사용자가 다시 들어와서 삭제 취소됨")
    except Exception as e:
        print(f"❌ 방 삭제 중 오류: {e}")


async def handle_reconnection_join(sid: str, room: str, username: str) -> None:
    """
    재연결 시 기존 연결을 정리하는 함수
    
    Args:
        sid (str): 새로운 소켓 ID
        room (str): 방 이름
        username (str): 사용자명
        
    학습 포인트:
        - 재연결 처리: 브라우저 새로고침, 네트워크 끊김 후 재접속 처리
        - 중복 연결 방지: 같은 사용자의 이전 연결 정리
        - 상태 일관성 유지: 데이터 정합성 보장
    """
    old_connections = []
    
    # 같은 사용자명으로 연결된 다른 소켓 찾기
    if room in rooms:
        for old_sid, old_username in rooms[room]["users"].items():
            if old_username == username and old_sid != sid:
                old_connections.append(old_sid)
    
    # 이전 연결들 정리
    for old_sid in old_connections:
        print(f"🔄 재연결 감지: {username}의 이전 연결 {old_sid} 정리")
        await leave(old_sid)


async def send_system_message(room: str, content: str) -> None:
    """
    시스템 메시지 전송 (입장/퇴장 알림 등)
    
    Args:
        room (str): 방 이름
        content (str): 메시지 내용
        
    학습 포인트:
        - 시스템 메시지: 일반 사용자 메시지와 구분되는 관리 메시지
        - 일관성: 시스템 메시지 형식을 표준화
    """
    message_data = {
        "id": None,
        "type": "system",
        "content": content,
        "timestamp": get_timestamp(),
        "username": "시스템"
    }
    await sio.emit("message", message_data, room=room)

# =============================================================================
# 🎯 Socket.IO 이벤트 핸들러들 (Event Handlers)
# =============================================================================

@sio.event
async def connect(sid: str, environ: dict, auth: dict) -> None:
    """
    클라이언트 연결 시 호출되는 이벤트
    
    Args:
        sid (str): 소켓 ID (클라이언트의 고유 식별자)
        environ (dict): 환경 변수 정보
        auth (dict): 인증 정보
        
    학습 포인트:
        - Socket.IO 이벤트: @sio.event 데코레이터로 이벤트 핸들러 정의
        - 자동 호출: 클라이언트가 서버에 연결할 때 자동으로 실행
        - sid: 각 클라이언트의 고유 식별자 (세션 ID)
    """
    print(f"🔗 클라이언트 연결됨: {sid}")
    print(f"   📍 IP: {environ.get('REMOTE_ADDR', 'Unknown')}")
    

@sio.event
async def get_rooms(sid: str) -> None:
    """
    클라이언트가 방 목록을 요청할 때 호출
    
    Args:
        sid (str): 요청한 클라이언트의 소켓 ID
        
    학습 포인트:
        - 요청-응답 패턴: 클라이언트 요청 → 서버 응답
        - 개별 전송: 특정 클라이언트에게만 데이터 전송 (room=sid)
        - 데이터 직렬화: Python dict → JSON 자동 변환
    """
    print(f"📋 방 목록 요청: {sid}")
    
    room_list = []
    for room_id, room_data in rooms.items():
        room_list.append({
            "id": room_id,
            "name": room_id, 
            "user_count": len(room_data["users"]),
            "created_at": room_data["created_at"]
        })
    
    print(f"   📤 {len(room_list)}개 방 정보 전송")
    await sio.emit("rooms_list", room_list, room=sid)


@sio.event
async def create_room(sid: str, data: dict) -> None:
    """
    새로운 채팅방 생성 요청 처리
    
    Args:
        sid (str): 요청한 클라이언트의 소켓 ID
        data (dict): 클라이언트가 전송한 데이터 {"room_id": "방이름"}
        
    학습 포인트:
        - 입력 검증: 서버에서 반드시 클라이언트 입력을 검증
        - 중복 확인: 동일한 방 이름 존재 여부 체크
        - 에러 처리: 문제 발생 시 클라이언트에게 적절한 메시지 전송
        - 원자적 연산: 방 생성은 성공 또는 실패, 중간 상태 없음
    """
    room_id = data.get("room_id", "").strip()
    print(f"🏠 방 생성 요청: '{room_id}' (요청자: {sid})")
    
    # 1단계: 입력값 검증
    error_msg = validate_input(room_id, MAX_ROOM_NAME_LENGTH, "방 이름")
    if error_msg:
        print(f"   ❌ 입력 검증 실패: {error_msg}")
        await sio.emit("error", error_msg, room=sid)
        return
    
    # 2단계: 중복 확인
    if room_id in rooms:
        error_msg = "이미 존재하는 방입니다."
        print(f"   ❌ 중복 방 이름: {room_id}")
        await sio.emit("error", error_msg, room=sid)
        return
    
    # 3단계: 방 생성
    rooms[room_id] = {
        "users": {},                    # 빈 사용자 딕셔너리
        "created_at": time.time()       # 생성 시간 (Unix timestamp)
    }
    
    print(f"   ✅ 방 '{room_id}' 생성 완료")
    
    # 4단계: 성공 응답 및 전체 방 목록 업데이트
    await sio.emit("room_created", {"room_id": room_id}, room=sid)
    await broadcast_room_list()  # 모든 클라이언트에게 새 방 목록 전송

@sio.event
async def join(sid: str, data: dict) -> None:
    """
    사용자가 채팅방에 입장할 때 호출되는 이벤트
    
    Args:
        sid (str): 클라이언트의 소켓 ID
        data (dict): {"room": "방이름", "username": "사용자명"}
        
    학습 포인트:
        - 복잡한 비즈니스 로직: 여러 단계의 검증과 처리
        - 데이터 일관성: 여러 데이터 구조를 동기화하여 일관성 유지
        - 실시간 알림: 다른 사용자들에게 입장 사실을 즉시 알림
        - 트랜잭션적 사고: 모든 단계가 성공해야만 최종 성공 처리
    """
    room = data.get("room", "").strip()
    username = data.get("username", "").strip()
    
    print(f"🚪 방 입장 요청: '{room}' / '{username}' (sid: {sid})")
    
    # 1단계: 입력값 검증
    room_error = validate_input(room, MAX_ROOM_NAME_LENGTH, "방 이름")
    if room_error:
        print(f"   ❌ 방 이름 검증 실패: {room_error}")
        await sio.emit("error", room_error, room=sid)
        return
    
    username_error = validate_input(username, MAX_USERNAME_LENGTH, "닉네임")
    if username_error:
        print(f"   ❌ 닉네임 검증 실패: {username_error}")
        await sio.emit("error", username_error, room=sid)
        return
    
    # 2단계: 텍스트 정제 (보안)
    room = sanitize_text(room)
    username = sanitize_text(username)
    
    # 3단계: 방이 존재하지 않으면 자동 생성
    if room not in rooms:
        print(f"   🏗️ 방 '{room}' 자동 생성")
        rooms[room] = {
            "users": {},
            "created_at": time.time()
        }
    
    # 4단계: 중복 닉네임 검사 (대소문자 구분 없음)
    for existing_username in rooms[room]["users"].values():
        if existing_username.lower() == username.lower():
            error_msg = f"'{username}'은(는) 이미 사용 중인 닉네임입니다."
            print(f"   ❌ 중복 닉네임: {username}")
            await sio.emit("error", error_msg, room=sid)
            return
    
    # 5단계: 재연결 처리 (같은 사용자의 이전 연결 정리)
    await handle_reconnection_join(sid, room, username)
    
    # 6단계: 사용자 정보 저장 (메모리 내 데이터 구조 업데이트)
    rooms[room]["users"][sid] = username
    user_rooms[sid] = {"room": room, "username": username}
    
    # 7단계: Socket.IO 방에 물리적으로 입장
    await sio.enter_room(sid, room)
    print(f"   ✅ '{username}' 방 '{room}' 입장 완료")
    
    # 8단계: 다른 사용자들에게 입장 알림
    await send_system_message(room, f"🔵 {username}님이 입장했습니다.")
    
    # 9단계: 입장한 사용자에게 성공 응답
    await sio.emit("join_success", {"room": room, "username": username}, room=sid)
    
    # 10단계: 모든 사용자에게 업데이트된 정보 전송
    await broadcast_user_list(room)
    await broadcast_room_list()

@sio.event
async def message(sid: str, data: dict) -> None:
    """
    사용자가 메시지를 전송할 때 호출되는 이벤트
    
    Args:
        sid (str): 메시지 전송자의 소켓 ID
        data (dict): {"room": "방이름", "username": "사용자명", "msg": "메시지내용"}
        
    학습 포인트:
        - 메시지 검증: 내용, 권한, 길이 등 다각도 검증
        - 보안 처리: XSS 방지를 위한 텍스트 정제
        - 상태 관리: 타이핑 상태 자동 해제
        - 실시간 브로드캐스트: 방의 모든 사용자에게 즉시 전송
    """
    room = data.get("room", "").strip()
    username = data.get("username", "").strip()
    msg = data.get("msg", "").strip()
    
    print(f"💬 메시지 전송: {username} in {room}: '{msg[:50]}...'")
    
    # 1단계: 메시지 내용 검증
    msg_error = validate_input(msg, MAX_MESSAGE_LENGTH, "메시지")
    if msg_error:
        print(f"   ❌ 메시지 검증 실패: {msg_error}")
        await sio.emit("error", msg_error, room=sid)
        return
    
    # 2단계: 사용자 권한 확인 (방에 실제로 입장해 있는지)
    if sid not in user_rooms:
        error_msg = "방에 입장하지 않은 상태입니다."
        print(f"   ❌ 권한 없음: {sid}")
        await sio.emit("error", error_msg, room=sid)
        return
    
    user_info = user_rooms[sid]
    if user_info["room"] != room or user_info["username"] != username:
        error_msg = "방 정보가 일치하지 않습니다."
        print(f"   ❌ 방 정보 불일치: {sid}")
        await sio.emit("error", error_msg, room=sid)
        return
    
    # 3단계: 메시지 내용 정제 (보안)
    msg = sanitize_text(msg)
    
    # 4단계: 타이핑 상태 자동 해제
    await clear_typing_status(room, sid)
    
    # 5단계: 메시지 데이터 구성
    message_data = {
        "id": None,                    # DB 사용 시 메시지 ID
        "type": "user",                # 메시지 타입 (user/system)
        "content": msg,                # 메시지 내용
        "username": username,          # 전송자명
        "timestamp": get_timestamp(),  # 전송 시간
        "user_id": sid                 # 전송자 소켓 ID
    }
    
    # 6단계: 방의 모든 사용자에게 메시지 브로드캐스트
    print(f"   ✅ 메시지 브로드캐스트 완료")
    await sio.emit("message", message_data, room=room)


@sio.event
async def leave(sid: str, data: dict = None) -> None:
    """
    사용자가 방에서 나갈 때 호출되는 이벤트
    
    Args:
        sid (str): 나가는 사용자의 소켓 ID
        data (dict, optional): 클라이언트 데이터 (일반적으로 사용 안함)
        
    학습 포인트:
        - 정리 작업: 여러 데이터 구조에서 사용자 정보 제거
        - 조건부 로직: 방이 비었는지 확인하여 삭제 여부 결정
        - 지연 삭제: 즉시 삭제하지 않고 일정 시간 후 삭제 (재연결 대비)
        - 알림 시스템: 다른 사용자들에게 퇴장 사실 알림
    """
    if sid not in user_rooms:
        print(f"⚠️ 방에 없는 사용자의 나가기 시도: {sid}")
        return
    
    user_info = user_rooms[sid]
    room = user_info["room"]
    username = user_info["username"]
    
    print(f"🚪 방 나가기: {username} from {room} (sid: {sid})")
    
    # 1단계: 타이핑 상태 정리
    await clear_typing_status(room, sid)
    
    # 2단계: Socket.IO 방에서 물리적으로 나가기
    await sio.leave_room(sid, room)
    
    # 3단계: 데이터 구조에서 사용자 제거
    if room in rooms and sid in rooms[room]["users"]:
        del rooms[room]["users"][sid]
        print(f"   🗑️ 사용자 데이터 제거: {username}")
        
        # 4단계: 방이 비었는지 확인
        if len(rooms[room]["users"]) == 0:
            print(f"   📭 방 '{room}'이 비었음 - 지연 삭제 예약")
            # 즉시 삭제하지 않고 지연 삭제 (재연결 대비)
            asyncio.create_task(delayed_room_cleanup(room))
            
            # 타이핑 사용자 목록도 정리
            if room in typing_users:
                del typing_users[room]
        else:
            # 5단계: 다른 사용자들에게 퇴장 알림
            await send_system_message(room, f"🔴 {username}님이 퇴장했습니다.")
            
            # 6단계: 업데이트된 사용자 목록 전송
            await broadcast_user_list(room)
    
    # 7단계: 사용자 세션 정보 제거
    del user_rooms[sid]
    
    # 8단계: 클라이언트에게 성공 응답
    print(f"   ✅ '{username}' 방 나가기 완료")
    await sio.emit("leave_success", room=sid)
    
    # 9단계: 전체 방 목록 업데이트
    await broadcast_room_list()


@sio.event
async def disconnect(sid: str) -> None:
    """
    클라이언트 연결이 끊어질 때 자동으로 호출되는 이벤트
    
    Args:
        sid (str): 연결 해제된 클라이언트의 소켓 ID
        
    학습 포인트:
        - 자동 정리: 연결 끊김 시 자동으로 방에서 제거
        - 예외 처리: 네트워크 문제로 인한 비정상 종료 처리
        - 리소스 관리: 메모리 누수 방지를 위한 데이터 정리
        - 사용자 경험: 다른 사용자들에게 퇴장 사실 알림
    """
    print(f"🔌 클라이언트 연결 해제: {sid}")
    
    # 사용자가 방에 있었다면 자동으로 나가기 처리
    try:
        await leave(sid)
    except Exception as e:
        print(f"❌ 연결 해제 시 정리 중 오류: {e}")
        # 오류가 발생해도 서버는 계속 동작해야 함

@sio.event
async def typing_start(sid: str, data: dict) -> None:
    """
    사용자가 타이핑을 시작할 때 호출되는 이벤트
    
    Args:
        sid (str): 타이핑하는 사용자의 소켓 ID
        data (dict): 클라이언트 데이터 (일반적으로 비어있음)
        
    학습 포인트:
        - 실시간 상태 표시: 사용자의 타이핑 상태를 다른 사용자에게 실시간 전달
        - 임시 상태 관리: 타이핑은 일시적 상태로 별도 데이터 구조로 관리
        - UX 개선: 상대방이 응답을 준비 중임을 시각적으로 표시
    """
    if sid not in user_rooms:
        print(f"⚠️ 방에 없는 사용자의 타이핑 시작: {sid}")
        return
    
    user_info = user_rooms[sid]
    room = user_info["room"]
    username = user_info["username"]
    
    print(f"⌨️ 타이핑 시작: {username} in {room}")
    
    # 방별 타이핑 사용자 딕셔너리에 추가
    if room not in typing_users:
        typing_users[room] = {}
    
    typing_users[room][sid] = username
    
    # 방의 다른 사용자들에게 타이핑 상태 알림
    await broadcast_typing_status(room)


@sio.event
async def typing_stop(sid: str, data: dict) -> None:
    """
    사용자가 타이핑을 중지할 때 호출되는 이벤트
    
    Args:
        sid (str): 타이핑을 중지한 사용자의 소켓 ID
        data (dict): 클라이언트 데이터 (일반적으로 비어있음)
        
    학습 포인트:
        - 상태 정리: 타이핑 상태 제거 및 다른 사용자들에게 알림
        - 자동 호출: 메시지 전송 시 자동으로 타이핑 상태 해제
        - 타임아웃: 클라이언트에서 일정 시간 후 자동 호출
    """
    if sid not in user_rooms:
        print(f"⚠️ 방에 없는 사용자의 타이핑 중지: {sid}")
        return
    
    user_info = user_rooms[sid]
    room = user_info["room"]
    username = user_info["username"]
    
    print(f"⌨️ 타이핑 중지: {username} in {room}")
    
    # 타이핑 상태 제거 및 브로드캐스트
    await clear_typing_status(room, sid)


@sio.event
async def get_user_list(sid: str, data: dict) -> None:
    """
    특정 방의 사용자 목록을 요청하는 이벤트
    
    Args:
        sid (str): 요청한 클라이언트의 소켓 ID
        data (dict): {"room_id": "방이름"}
        
    학습 포인트:
        - 온디맨드 데이터: 필요할 때만 데이터 전송 (대역폭 절약)
        - 동기화: 클라이언트와 서버 간 데이터 동기화
        - 입장 후 초기화: 방 입장 후 현재 사용자 목록 확인용
    """
    room_id = data.get("room_id", "").strip()
    
    print(f"👥 사용자 목록 요청: {room_id} (요청자: {sid})")
    
    if room_id and room_id in rooms:
        await broadcast_user_list(room_id)
    else:
        print(f"   ❌ 존재하지 않는 방: {room_id}")


@sio.event
async def ping(sid: str, data: dict) -> None:
    """
    클라이언트의 연결 상태 확인용 핑 이벤트
    
    Args:
        sid (str): 핑을 보낸 클라이언트의 소켓 ID
        data (dict): 핑 데이터 (타임스탬프 등)
        
    학습 포인트:
        - 헬스체크: 연결 상태 확인 및 응답 시간 측정
        - Keep-alive: 연결 유지 확인
        - 네트워크 품질: 왕복 시간(RTT) 측정 가능
    """
    print(f"🏓 핑 수신: {sid}")
    
    # 퐁(응답) 전송 - 현재 서버 시간 포함
    await sio.emit("pong", {"timestamp": get_timestamp()}, room=sid)


# =============================================================================
# 🚀 서버 시작 (Server Startup)
# =============================================================================

if __name__ == "__main__":
    """
    서버 시작점 - 스크립트가 직접 실행될 때만 동작
    
    학습 포인트:
        - uvicorn: ASGI 서버 (비동기 웹 서버)
        - host="0.0.0.0": 모든 네트워크 인터페이스에서 접근 허용
        - port=8000: HTTP 포트 (개발용 기본값)
        - __name__ == "__main__": 모듈이 직접 실행될 때만 서버 시작
    """
    print("=" * 50)
    print("💬 BABA CHAT 서버 시작")
    print("=" * 50)
    print(f"🌐 서버 주소: http://{HOST}:{PORT}")
    print(f"📊 최대 메시지 길이: {MAX_MESSAGE_LENGTH}자")
    print(f"👤 최대 사용자명 길이: {MAX_USERNAME_LENGTH}자")
    print(f"🏠 최대 방 이름 길이: {MAX_ROOM_NAME_LENGTH}자")
    print(f"⏰ 빈 방 삭제 지연시간: {ROOM_CLEANUP_DELAY}초")
    print("=" * 50)
    
    try:
        # ASGI 서버 시작
        uvicorn.run(
            app, 
            host=HOST, 
            port=PORT,
            log_level="info",          # 로그 레벨 설정
            access_log=True            # 접근 로그 활성화
        )
    except KeyboardInterrupt:
        print("\n👋 서버가 종료됩니다...")
    except Exception as e:
        print(f"❌ 서버 시작 실패: {e}")