"""
채팅 서비스
==========

Spring Boot의 @Service와 동일한 역할
메시지 처리, 브로드캐스트, 알림 등의 비즈니스 로직을 처리합니다.

학습 포인트:
- 메시지 처리 파이프라인
- 실시간 브로드캐스트 패턴
- 이벤트 기반 아키텍처
- 의존성 주입과 서비스 간 협력
"""

import socketio
from typing import Dict, List, Optional
from datetime import datetime
from app.models.chat_models import MessageData, MessageType, TypingStatusData
from app.services.room_service import room_service
from app.services.user_service import user_service
from app.utils.validators import validate_message, sanitize_text, extract_mentions


class ChatService:
    """
    채팅 서비스 클래스
    
    메시지 전송, 브로드캐스트, 특수 기능 등을 담당합니다.
    """
    
    def __init__(self, sio: socketio.AsyncServer):
        """
        서비스 초기화
        
        Args:
            sio (socketio.AsyncServer): Socket.IO 서버 인스턴스
        """
        self._sio = sio
        print("💬 ChatService 초기화 완료")
    
    async def send_user_message(self, user_sid: str, room: str, username: str, message: str) -> tuple[bool, str]:
        """
        사용자 메시지 전송 처리
        
        Args:
            user_sid (str): 전송자 소켓 ID
            room (str): 방 이름
            username (str): 사용자명
            message (str): 메시지 내용
            
        Returns:
            tuple[bool, str]: (성공 여부, 에러 메시지)
        """
        # 1단계: 메시지 검증
        error_msg = validate_message(message)
        if error_msg:
            return False, error_msg
        
        # 2단계: 사용자 권한 확인
        if not await user_service.is_user_in_room(user_sid, room):
            return False, "방에 입장하지 않은 상태입니다."
        
        # 3단계: 메시지 정제
        clean_message = sanitize_text(message)
        
        # 4단계: 타이핑 상태 자동 해제
        await user_service.stop_typing(user_sid)
        
        # 5단계: 메시지 데이터 구성
        message_data = MessageData(
            id=None,
            type=MessageType.USER,
            content=clean_message,
            username=username,
            timestamp=datetime.now().isoformat(),
            user_id=user_sid
        )
        
        # 6단계: 멘션 처리
        mentions = extract_mentions(clean_message)
        if mentions:
            await self._handle_mentions(room, username, mentions, clean_message)
        
        # 7단계: 메시지 브로드캐스트
        await self._sio.emit("message", message_data.dict(), room=room)
        
        print(f"💬 메시지 전송: {username} in {room}: '{clean_message[:50]}...'")
        return True, ""
    
    async def send_system_message(self, room: str, content: str) -> None:
        """
        시스템 메시지 전송
        
        Args:
            room (str): 방 이름
            content (str): 메시지 내용
        """
        message_data = MessageData(
            id=None,
            type=MessageType.SYSTEM,
            content=content,
            username="시스템",
            timestamp=datetime.now().isoformat(),
            user_id=None
        )
        
        await self._sio.emit("message", message_data.dict(), room=room)
        print(f"🔔 시스템 메시지: {room} → {content}")
    
    async def broadcast_user_list(self, room_id: str) -> None:
        """
        특정 방의 사용자 목록 브로드캐스트
        
        Args:
            room_id (str): 방 ID
        """
        users = await user_service.get_room_users(room_id)
        user_list = [user.dict() for user in users]
        
        await self._sio.emit("user_list", user_list, room=room_id)
        print(f"👥 사용자 목록 브로드캐스트: {room_id} ({len(users)}명)")
    
    async def broadcast_room_list(self) -> None:
        """
        전체 방 목록 브로드캐스트
        """
        rooms = await room_service.get_all_rooms()
        room_list = [room.dict() for room in rooms]
        
        await self._sio.emit("rooms_list", room_list)
        print(f"🏠 방 목록 브로드캐스트: {len(rooms)}개 방")
    
    async def broadcast_typing_status(self, room_id: str) -> None:
        """
        타이핑 상태 브로드캐스트
        
        Args:
            room_id (str): 방 ID
        """
        typing_users = await user_service.get_typing_users(room_id)
        typing_data = TypingStatusData(users=typing_users)
        
        await self._sio.emit("typing_status", typing_data.dict(), room=room_id)
        
        if typing_users:
            print(f"⌨️ 타이핑 상태 브로드캐스트: {room_id} → {typing_users}")
    
    async def handle_user_join(self, user_sid: str, room: str, username: str) -> tuple[bool, str]:
        """
        사용자 방 입장 처리
        
        Args:
            user_sid (str): 소켓 ID
            room (str): 방 이름
            username (str): 사용자명
            
        Returns:
            tuple[bool, str]: (성공 여부, 에러 메시지)
        """
        # 1단계: 재연결 처리
        await user_service.handle_reconnection(user_sid, room, username)
        
        # 2단계: 방에 사용자 추가
        success, message = await room_service.add_user_to_room(room, user_sid, username)
        if not success:
            return False, message
        
        # 3단계: 사용자 세션 생성
        success, session_msg = await user_service.create_session(user_sid, room, username)
        if not success:
            return False, session_msg
        
        # 4단계: Socket.IO 방에 입장
        await self._sio.enter_room(user_sid, room)
        
        # 5단계: 입장 알림
        await self.send_system_message(room, f"🔵 {username}님이 입장했습니다.")
        
        # 6단계: 실시간 정보 업데이트 (교착상태 방지를 위해 임시 제거)
        # await self.broadcast_user_list(room)
        # await self.broadcast_room_list()
        
        print(f"✅ 방 입장 완료: {username} → {room}")
        return True, ""
    
    async def handle_user_leave(self, user_sid: str) -> Optional[str]:
        """
        사용자 방 퇴장 처리
        
        Args:
            user_sid (str): 소켓 ID
            
        Returns:
            Optional[str]: 퇴장한 방 이름 (세션이 없으면 None)
        """
        # 1단계: 사용자 세션 정보 조회
        session = await user_service.get_session(user_sid)
        if not session:
            return None
        
        room = session.room
        username = session.username
        
        # 2단계: 타이핑 상태 정리
        await user_service.stop_typing(user_sid)
        
        # 3단계: Socket.IO 방에서 나가기
        await self._sio.leave_room(user_sid, room)
        
        # 4단계: 방에서 사용자 제거
        removed, removed_username, is_empty = await room_service.remove_user_from_room(room, user_sid)
        
        # 5단계: 사용자 세션 정리
        await user_service.cleanup_session(user_sid)
        
        if removed:
            # 6단계: 퇴장 알림 (방이 비지 않았을 때만)
            if not is_empty:
                await self.send_system_message(room, f"🔴 {username}님이 퇴장했습니다.")
                await self.broadcast_user_list(room)
            
            # 7단계: 방 목록 업데이트
            await self.broadcast_room_list()
            
            print(f"✅ 방 퇴장 완료: {username} ← {room}")
        
        return room
    
    async def handle_typing_start(self, user_sid: str) -> None:
        """
        타이핑 시작 처리
        
        Args:
            user_sid (str): 소켓 ID
        """
        room_id = await user_service.start_typing(user_sid)
        if room_id:
            await self.broadcast_typing_status(room_id)
    
    async def handle_typing_stop(self, user_sid: str) -> None:
        """
        타이핑 중지 처리
        
        Args:
            user_sid (str): 소켓 ID
        """
        room_id = await user_service.stop_typing(user_sid)
        if room_id:
            await self.broadcast_typing_status(room_id)
    
    async def handle_disconnect(self, user_sid: str) -> None:
        """
        연결 끊김 처리
        
        Args:
            user_sid (str): 소켓 ID
        """
        try:
            # 모든 방에서 사용자 제거
            removed_rooms = await room_service.cleanup_user_from_all_rooms(user_sid)
            
            # 사용자 세션 정리
            username = await user_service.cleanup_session(user_sid)
            
            # 퇴장 알림 및 업데이트
            for room in removed_rooms:
                # 방이 아직 존재하고 사용자가 있는지 확인
                if await room_service.room_exists(room):
                    user_count = await room_service.get_room_user_count(room)
                    if user_count > 0:  # 방에 다른 사용자가 있을 때만 알림
                        if username:
                            await self.send_system_message(room, f"🔴 {username}님이 퇴장했습니다.")
                        await self.broadcast_user_list(room)
            
            # 전체 방 목록 업데이트
            await self.broadcast_room_list()
            
            if username:
                print(f"✅ 연결 해제 정리 완료: {username} (sid: {user_sid})")
            
        except Exception as e:
            print(f"❌ 연결 해제 시 정리 중 오류: {e}")
    
    async def _handle_mentions(self, room: str, sender: str, mentions: List[str], message: str) -> None:
        """
        멘션 처리 (내부 함수)
        
        Args:
            room (str): 방 이름
            sender (str): 전송자명
            mentions (List[str]): 멘션된 사용자명 목록
            message (str): 원본 메시지
        """
        # 방의 사용자 목록 조회
        room_users = await user_service.get_room_users(room)
        room_usernames = [user.username.lower() for user in room_users]
        
        # 실제 존재하는 사용자만 필터링
        valid_mentions = []
        for mention in mentions:
            if mention.lower() in room_usernames:
                valid_mentions.append(mention)
        
        if valid_mentions:
            print(f"📢 멘션 발생: {sender} → {valid_mentions} in {room}")
            
            # TODO: 향후 멘션 알림 기능 구현
            # - 개별 알림 전송
            # - 사운드 알림
            # - 푸시 알림 등
    
    def get_stats(self) -> Dict[str, int]:
        """
        채팅 서비스 통계 조회
        
        Returns:
            Dict[str, int]: 통계 정보
        """
        user_stats = user_service.get_stats()
        room_stats = room_service.get_stats()
        
        return {
            **user_stats,
            **room_stats,
            "total_connections": len(self._sio.manager.rooms.get("/", {}))
        }


# 서비스 인스턴스는 main.py에서 생성됩니다
chat_service: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    """
    채팅 서비스 인스턴스 반환
    
    Returns:
        ChatService: 채팅 서비스 인스턴스
        
    Raises:
        RuntimeError: 서비스가 초기화되지 않은 경우
    """
    if chat_service is None:
        raise RuntimeError("ChatService가 초기화되지 않았습니다. main.py에서 초기화하세요.")
    return chat_service


# =============================================================================
# 🔧 서비스 사용 예시
# =============================================================================
"""
사용 방법:

from app.services.chat_service import get_chat_service

# 메시지 전송
chat = get_chat_service()
success, error = await chat.send_user_message(
    "socket123", "자유채팅", "홍길동", "안녕하세요!"
)

# 시스템 메시지
await chat.send_system_message("자유채팅", "서버 점검이 시작됩니다.")

# 사용자 입장 처리
success, error = await chat.handle_user_join(
    "socket123", "자유채팅", "홍길동"
)

# 통계 조회
stats = chat.get_stats()
print(f"전체 연결: {stats['total_connections']}개")
"""