"""
채팅 컨트롤러
============

Spring Boot의 @RestController와 동일한 역할
Socket.IO 이벤트를 처리하고 적절한 서비스를 호출합니다.

학습 포인트:
- 컨트롤러의 역할: 요청 받기 → 검증 → 서비스 호출 → 응답
- 이벤트 기반 컨트롤러 패턴
- 의존성 주입 활용
- 에러 처리 및 응답 관리
"""

import socketio
from typing import Dict, Any, Optional
from pydantic import ValidationError
from app.models.chat_models import (
    CreateRoomRequest, JoinRoomRequest, SendMessageRequest, 
    TypingRequest, UserListRequest, ErrorResponse
)
from app.services.chat_service import get_chat_service
from app.services.room_service import room_service


class ChatController:
    """
    채팅 컨트롤러 클래스
    
    Socket.IO 이벤트를 처리하고 비즈니스 로직을 서비스 계층에 위임합니다.
    Spring Boot의 @RestController와 동일한 패턴을 따릅니다.
    """
    
    def __init__(self, sio: socketio.AsyncServer):
        """
        컨트롤러 초기화
        
        Args:
            sio (socketio.AsyncServer): Socket.IO 서버 인스턴스
        """
        self._sio = sio
        self._register_events()
        print("🎮 ChatController 초기화 완료")
    
    def _register_events(self) -> None:
        """Socket.IO 이벤트 핸들러 등록"""
        # 연결 관련 이벤트
        self._sio.on("connect")(self.handle_connect)
        self._sio.on("disconnect")(self.handle_disconnect)
        
        # 방 관련 이벤트
        self._sio.on("get_rooms")(self.handle_get_rooms)
        self._sio.on("create_room")(self.handle_create_room)
        self._sio.on("join")(self.handle_join)
        self._sio.on("leave")(self.handle_leave)
        
        # 메시지 관련 이벤트
        self._sio.on("message")(self.handle_message)
        
        # 타이핑 관련 이벤트
        self._sio.on("typing_start")(self.handle_typing_start)
        self._sio.on("typing_stop")(self.handle_typing_stop)
        
        # 사용자 관련 이벤트
        self._sio.on("get_user_list")(self.handle_get_user_list)
        
        # 기타 이벤트
        self._sio.on("ping")(self.handle_ping)
    
    async def handle_connect(self, sid: str, environ: Dict[str, Any], auth: Optional[Dict[str, Any]]) -> None:
        """
        클라이언트 연결 이벤트 처리
        
        Args:
            sid (str): 소켓 ID
            environ (Dict[str, Any]): 환경 변수
            auth (Optional[Dict[str, Any]]): 인증 정보
        """
        client_ip = environ.get('REMOTE_ADDR', 'Unknown')
        user_agent = environ.get('HTTP_USER_AGENT', 'Unknown')
        
        print(f"🔗 클라이언트 연결: {sid}")
        print(f"   📍 IP: {client_ip}")
        print(f"   🌐 User-Agent: {user_agent[:50]}...")
        
        # 연결 성공 응답 (선택사항)
        await self._sio.emit("connect_success", {
            "message": "서버에 연결되었습니다",
            "sid": sid
        }, room=sid)
    
    async def handle_disconnect(self, sid: str) -> None:
        """
        클라이언트 연결 해제 이벤트 처리
        
        Args:
            sid (str): 소켓 ID
        """
        print(f"🔌 클라이언트 연결 해제: {sid}")
        
        try:
            chat_service = get_chat_service()
            await chat_service.handle_disconnect(sid)
        except Exception as e:
            print(f"❌ 연결 해제 처리 중 오류: {e}")
    
    async def handle_get_rooms(self, sid: str) -> None:
        """
        방 목록 요청 처리
        
        Args:
            sid (str): 요청한 클라이언트의 소켓 ID
        """
        print(f"📋 방 목록 요청: {sid}")
        
        try:
            rooms = await room_service.get_all_rooms()
            room_list = [room.dict() for room in rooms]
            
            await self._sio.emit("rooms_list", room_list, room=sid)
            print(f"   📤 {len(rooms)}개 방 정보 전송")
            
        except Exception as e:
            print(f"❌ 방 목록 조회 오류: {e}")
            await self._emit_error(sid, "방 목록을 조회할 수 없습니다.")
    
    async def handle_create_room(self, sid: str, data: Dict[str, Any]) -> None:
        """
        방 생성 요청 처리
        
        Args:
            sid (str): 요청한 클라이언트의 소켓 ID
            data (Dict[str, Any]): 요청 데이터
        """
        try:
            # 요청 데이터 검증
            request = CreateRoomRequest(**data)
            print(f"🏠 방 생성 요청: '{request.room_id}' (요청자: {sid})")
            
            # 비즈니스 로직 처리
            success, message = await room_service.create_room(request.room_id)
            
            if success:
                # 성공 응답
                await self._sio.emit("room_created", {"room_id": request.room_id}, room=sid)
                
                # 전체 방 목록 업데이트 (교착상태 방지를 위해 임시 제거)
                # chat_service = get_chat_service()
                # await chat_service.broadcast_room_list()
                
                print(f"   ✅ 방 생성 성공: {request.room_id}")
            else:
                # 실패 응답
                await self._emit_error(sid, message)
                print(f"   ❌ 방 생성 실패: {message}")
        
        except ValidationError as e:
            error_msg = "잘못된 요청 데이터입니다."
            await self._emit_error(sid, error_msg)
            print(f"   ❌ 검증 오류: {e}")
        
        except Exception as e:
            await self._emit_error(sid, "방 생성 중 오류가 발생했습니다.")
            print(f"❌ 방 생성 오류: {e}")
    
    async def handle_join(self, sid: str, data: Dict[str, Any]) -> None:
        """
        방 입장 요청 처리
        
        Args:
            sid (str): 클라이언트의 소켓 ID
            data (Dict[str, Any]): 요청 데이터
        """
        try:
            # 요청 데이터 검증
            request = JoinRoomRequest(**data)
            print(f"🚪 방 입장 요청: '{request.room}' / '{request.username}' (sid: {sid})")
            
            # 비즈니스 로직 처리
            chat_service = get_chat_service()
            success, error_msg = await chat_service.handle_user_join(
                sid, request.room, request.username
            )
            
            if success:
                # 성공 응답
                await self._sio.emit("join_success", {
                    "room": request.room,
                    "username": request.username
                }, room=sid)
                print(f"   ✅ 방 입장 성공: {request.username} → {request.room}")
            else:
                # 실패 응답
                await self._emit_error(sid, error_msg)
                print(f"   ❌ 방 입장 실패: {error_msg}")
        
        except ValidationError as e:
            error_msg = "잘못된 요청 데이터입니다."
            await self._emit_error(sid, error_msg)
            print(f"   ❌ 검증 오류: {e}")
        
        except Exception as e:
            await self._emit_error(sid, "방 입장 중 오류가 발생했습니다.")
            print(f"❌ 방 입장 오류: {e}")
    
    async def handle_leave(self, sid: str, data: Optional[Dict[str, Any]] = None) -> None:
        """
        방 나가기 요청 처리
        
        Args:
            sid (str): 클라이언트의 소켓 ID
            data (Optional[Dict[str, Any]]): 요청 데이터 (선택사항)
        """
        print(f"🚪 방 나가기 요청: {sid}")
        
        try:
            chat_service = get_chat_service()
            room = await chat_service.handle_user_leave(sid)
            
            if room:
                # 성공 응답
                await self._sio.emit("leave_success", room=sid)
                print(f"   ✅ 방 나가기 성공: {sid} ← {room}")
            else:
                print(f"   ⚠️ 방에 없는 사용자의 나가기 요청: {sid}")
        
        except Exception as e:
            print(f"❌ 방 나가기 오류: {e}")
    
    async def handle_message(self, sid: str, data: Dict[str, Any]) -> None:
        """
        메시지 전송 요청 처리
        
        Args:
            sid (str): 전송자의 소켓 ID
            data (Dict[str, Any]): 요청 데이터
        """
        try:
            # 요청 데이터 검증
            request = SendMessageRequest(**data)
            
            # 로그 (메시지 내용은 일부만)
            msg_preview = request.msg[:30] + "..." if len(request.msg) > 30 else request.msg
            print(f"💬 메시지 전송 요청: {request.username} in {request.room}: '{msg_preview}'")
            
            # 비즈니스 로직 처리
            chat_service = get_chat_service()
            success, error_msg = await chat_service.send_user_message(
                sid, request.room, request.username, request.msg
            )
            
            if not success:
                await self._emit_error(sid, error_msg)
                print(f"   ❌ 메시지 전송 실패: {error_msg}")
        
        except ValidationError as e:
            error_msg = "잘못된 메시지 데이터입니다."
            await self._emit_error(sid, error_msg)
            print(f"   ❌ 검증 오류: {e}")
        
        except Exception as e:
            await self._emit_error(sid, "메시지 전송 중 오류가 발생했습니다.")
            print(f"❌ 메시지 전송 오류: {e}")
    
    async def handle_typing_start(self, sid: str, data: Dict[str, Any]) -> None:
        """
        타이핑 시작 이벤트 처리
        
        Args:
            sid (str): 타이핑하는 사용자의 소켓 ID
            data (Dict[str, Any]): 요청 데이터
        """
        try:
            chat_service = get_chat_service()
            await chat_service.handle_typing_start(sid)
        
        except Exception as e:
            print(f"❌ 타이핑 시작 처리 오류: {e}")
    
    async def handle_typing_stop(self, sid: str, data: Dict[str, Any]) -> None:
        """
        타이핑 중지 이벤트 처리
        
        Args:
            sid (str): 타이핑을 중지한 사용자의 소켓 ID
            data (Dict[str, Any]): 요청 데이터
        """
        try:
            chat_service = get_chat_service()
            await chat_service.handle_typing_stop(sid)
        
        except Exception as e:
            print(f"❌ 타이핑 중지 처리 오류: {e}")
    
    async def handle_get_user_list(self, sid: str, data: Dict[str, Any]) -> None:
        """
        사용자 목록 요청 처리
        
        Args:
            sid (str): 요청한 클라이언트의 소켓 ID
            data (Dict[str, Any]): 요청 데이터
        """
        try:
            # 요청 데이터 검증
            request = UserListRequest(**data)
            print(f"👥 사용자 목록 요청: {request.room_id} (요청자: {sid})")
            
            # 방 존재 확인
            if await room_service.room_exists(request.room_id):
                chat_service = get_chat_service()
                await chat_service.broadcast_user_list(request.room_id)
            else:
                await self._emit_error(sid, "존재하지 않는 방입니다.")
                print(f"   ❌ 존재하지 않는 방: {request.room_id}")
        
        except ValidationError as e:
            error_msg = "잘못된 요청 데이터입니다."
            await self._emit_error(sid, error_msg)
            print(f"   ❌ 검증 오류: {e}")
        
        except Exception as e:
            await self._emit_error(sid, "사용자 목록 조회 중 오류가 발생했습니다.")
            print(f"❌ 사용자 목록 조회 오류: {e}")
    
    async def handle_ping(self, sid: str, data: Dict[str, Any]) -> None:
        """
        핑 이벤트 처리 (연결 상태 확인)
        
        Args:
            sid (str): 핑을 보낸 클라이언트의 소켓 ID
            data (Dict[str, Any]): 핑 데이터
        """
        print(f"🏓 핑 수신: {sid}")
        
        try:
            # 퐁 응답
            await self._sio.emit("pong", {
                "timestamp": data.get("timestamp"),
                "server_time": str(datetime.now().isoformat())
            }, room=sid)
        
        except Exception as e:
            print(f"❌ 핑 응답 오류: {e}")
    
    async def _emit_error(self, sid: str, message: str, error_code: str = None) -> None:
        """
        에러 응답 전송 (내부 함수)
        
        Args:
            sid (str): 클라이언트 소켓 ID
            message (str): 에러 메시지
            error_code (str, optional): 에러 코드
        """
        error_response = ErrorResponse(
            message=message,
            error_code=error_code
        )
        
        await self._sio.emit("error", error_response.dict(), room=sid)


# 컨트롤러 인스턴스는 main.py에서 생성됩니다
chat_controller: Optional[ChatController] = None


def initialize_chat_controller(sio: socketio.AsyncServer) -> ChatController:
    """
    채팅 컨트롤러 초기화
    
    Args:
        sio (socketio.AsyncServer): Socket.IO 서버 인스턴스
        
    Returns:
        ChatController: 초기화된 컨트롤러 인스턴스
    """
    global chat_controller
    chat_controller = ChatController(sio)
    return chat_controller


def get_chat_controller() -> ChatController:
    """
    채팅 컨트롤러 인스턴스 반환
    
    Returns:
        ChatController: 컨트롤러 인스턴스
        
    Raises:
        RuntimeError: 컨트롤러가 초기화되지 않은 경우
    """
    if chat_controller is None:
        raise RuntimeError("ChatController가 초기화되지 않았습니다.")
    return chat_controller


# =============================================================================
# 🔧 컨트롤러 사용 예시
# =============================================================================
"""
사용 방법 (main.py에서):

from app.controllers.chat_controller import initialize_chat_controller

# Socket.IO 서버 생성
sio = socketio.AsyncServer(...)

# 컨트롤러 초기화 (이벤트 핸들러 자동 등록)
controller = initialize_chat_controller(sio)

# 서버 시작
uvicorn.run(app, ...)

---

클라이언트에서 이벤트 발생 시:
1. socket.emit("create_room", {"room_id": "새방"})
2. ChatController.handle_create_room() 호출
3. 요청 검증 (CreateRoomRequest)
4. RoomService.create_room() 호출
5. 성공/실패 응답 전송

이런 식으로 MVC 패턴의 깔끔한 흐름이 완성됩니다!
"""