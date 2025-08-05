"""
사용자 관리 서비스
================

Spring Boot의 @Service와 동일한 역할
사용자 세션 관리, 인증, 타이핑 상태 등을 처리합니다.

학습 포인트:
- 세션 관리 패턴
- 사용자 상태 추적
- 실시간 상태 동기화
- 메모리 기반 캐싱
"""

from typing import Dict, List, Optional, Set
from datetime import datetime
from app.models.chat_models import UserSession, UserInfo
from app.utils.validators import validate_username
from app.services.redis_service import get_redis_service


class UserService:
    """
    사용자 관리 서비스 클래스
    
    사용자 세션, 타이핑 상태, 온라인 상태 등을 관리합니다.
    """
    
    def __init__(self):
        """서비스 초기화"""
        # 사용자 세션 저장소 {socket_id: UserSession}
        self._user_sessions: Dict[str, UserSession] = {}
        
        # 타이핑 상태 저장소 {room_id: {socket_id: username}}
        self._typing_users: Dict[str, Dict[str, str]] = {}
        
        print("👤 UserService 초기화 완료")
    
    async def create_session(self, user_sid: str, room: str, username: str) -> tuple[bool, str]:
        """
        사용자 세션 생성 (Redis 기반)
        
        Args:
            user_sid (str): 소켓 ID
            room (str): 방 이름
            username (str): 사용자명
            
        Returns:
            tuple[bool, str]: (성공 여부, 메시지)
        """
        # 사용자명 검증
        error_msg = validate_username(username)
        if error_msg:
            return False, error_msg
        
        # 기존 세션이 있으면 정리
        await self.cleanup_session(user_sid)
        
        # Redis에 세션 저장
        try:
            redis_service = get_redis_service()
            success = await redis_service.set_user_session(user_sid, room, username)
            
            # 메모리에도 백업 저장 (Redis 실패 시 대체용)
            session = UserSession(room=room, username=username)
            self._user_sessions[user_sid] = session
            
            # 온라인 상태 설정
            await redis_service.set_user_online(username, room)
            
            print(f"👤 세션 생성: {username} (sid: {user_sid}) → {room} {'(Redis)' if success else '(Memory)'}")
            return True, f"'{username}' 세션이 생성되었습니다."
            
        except Exception as e:
            print(f"❌ Redis 세션 생성 실패: {e}, 메모리 사용")
            # Redis 실패 시 메모리만 사용
            session = UserSession(room=room, username=username)
            self._user_sessions[user_sid] = session
            return True, f"'{username}' 세션이 생성되었습니다."
    
    async def get_session(self, user_sid: str) -> Optional[UserSession]:
        """
        사용자 세션 조회 (Redis 우선, 메모리 백업)
        
        Args:
            user_sid (str): 소켓 ID
            
        Returns:
            Optional[UserSession]: 세션 객체 (없으면 None)
        """
        try:
            # Redis에서 세션 조회
            redis_service = get_redis_service()
            redis_session = await redis_service.get_user_session(user_sid)
            
            if redis_session:
                # Redis 데이터를 UserSession 객체로 변환
                session = UserSession(
                    room=redis_session["room"],
                    username=redis_session["username"],
                    joined_at=redis_session.get("joined_at"),
                    last_activity=redis_session.get("last_activity")
                )
                
                # 메모리에도 동기화
                self._user_sessions[user_sid] = session
                return session
                
        except Exception as e:
            print(f"❌ Redis 세션 조회 실패: {e}, 메모리에서 조회")
        
        # Redis 실패 시 메모리에서 조회
        session = self._user_sessions.get(user_sid)
        if session:
            # 활동 시간 업데이트
            session.update_activity()
        return session
    
    async def cleanup_session(self, user_sid: str) -> Optional[str]:
        """
        사용자 세션 정리 (Redis + 메모리)
        
        Args:
            user_sid (str): 소켓 ID
            
        Returns:
            Optional[str]: 정리된 사용자명 (없으면 None)
        """
        username = None
        room = None
        
        # Redis에서 세션 정보 가져오기
        try:
            redis_service = get_redis_service()
            redis_session = await redis_service.get_user_session(user_sid)
            if redis_session:
                username = redis_session["username"]
                room = redis_session["room"]
                
                # Redis에서 세션 삭제
                await redis_service.remove_user_session(user_sid)
                # 오프라인 상태 설정
                await redis_service.set_user_offline(username, room)
                
        except Exception as e:
            print(f"❌ Redis 세션 정리 실패: {e}")
        
        # 메모리에서도 세션 정리
        session = self._user_sessions.get(user_sid)
        if session:
            if not username:  # Redis에서 가져오지 못한 경우
                username = session.username
                room = session.room
            
            # 메모리 세션 제거
            del self._user_sessions[user_sid]
        
        if username:
            # 타이핑 상태도 정리
            await self.stop_typing(user_sid)
            
            print(f"👤 세션 정리: {username} (sid: {user_sid}) ← {room}")
            return username
        
        return None
    
    async def get_room_users(self, room_id: str) -> List[UserInfo]:
        """
        특정 방의 사용자 목록 조회
        
        Args:
            room_id (str): 방 ID
            
        Returns:
            List[UserInfo]: 사용자 정보 목록
        """
        users = []
        for sid, session in self._user_sessions.items():
            if session.room == room_id:
                user_info = UserInfo(
                    sid=sid,
                    username=session.username,
                    joined_at=session.joined_at
                )
                users.append(user_info)
        
        # 입장 시간 순으로 정렬
        users.sort(key=lambda x: x.joined_at if x.joined_at else datetime.min)
        return users
    
    async def get_online_users(self) -> List[UserInfo]:
        """
        전체 온라인 사용자 목록 조회
        
        Returns:
            List[UserInfo]: 온라인 사용자 목록
        """
        users = []
        for sid, session in self._user_sessions.items():
            user_info = UserInfo(
                sid=sid,
                username=session.username,
                joined_at=session.joined_at
            )
            users.append(user_info)
        
        return users
    
    async def start_typing(self, user_sid: str) -> Optional[str]:
        """
        타이핑 상태 시작
        
        Args:
            user_sid (str): 소켓 ID
            
        Returns:
            Optional[str]: 방 ID (세션이 없으면 None)
        """
        session = await self.get_session(user_sid)
        if not session:
            return None
        
        room_id = session.room
        username = session.username
        
        # 방별 타이핑 사용자 딕셔너리에 추가
        if room_id not in self._typing_users:
            self._typing_users[room_id] = {}
        
        self._typing_users[room_id][user_sid] = username
        print(f"⌨️ 타이핑 시작: {username} in {room_id}")
        
        return room_id
    
    async def stop_typing(self, user_sid: str) -> Optional[str]:
        """
        타이핑 상태 중지
        
        Args:
            user_sid (str): 소켓 ID
            
        Returns:
            Optional[str]: 방 ID (타이핑 중이 아니면 None)
        """
        # 모든 방에서 해당 사용자의 타이핑 상태 제거
        room_id = None
        username = ""
        
        for rid, typing_users in list(self._typing_users.items()):
            if user_sid in typing_users:
                username = typing_users[user_sid]
                del typing_users[user_sid]
                room_id = rid
                
                # 방에 타이핑하는 사용자가 없으면 방 자체를 삭제
                if len(typing_users) == 0:
                    del self._typing_users[rid]
                
                print(f"⌨️ 타이핑 중지: {username} in {rid}")
                break
        
        return room_id
    
    async def get_typing_users(self, room_id: str) -> List[str]:
        """
        특정 방의 타이핑 중인 사용자 목록 조회
        
        Args:
            room_id (str): 방 ID
            
        Returns:
            List[str]: 타이핑 중인 사용자명 목록
        """
        if room_id not in self._typing_users:
            return []
        
        return list(self._typing_users[room_id].values())
    
    async def is_user_in_room(self, user_sid: str, room_id: str) -> bool:
        """
        사용자가 특정 방에 있는지 확인
        
        Args:
            user_sid (str): 소켓 ID
            room_id (str): 방 ID
            
        Returns:
            bool: 방에 있는지 여부
        """
        session = self._user_sessions.get(user_sid)
        return session is not None and session.room == room_id
    
    async def get_user_room(self, user_sid: str) -> Optional[str]:
        """
        사용자가 현재 있는 방 조회
        
        Args:
            user_sid (str): 소켓 ID
            
        Returns:
            Optional[str]: 방 ID (세션이 없으면 None)
        """
        session = self._user_sessions.get(user_sid)
        return session.room if session else None
    
    async def get_username(self, user_sid: str) -> Optional[str]:
        """
        사용자명 조회
        
        Args:
            user_sid (str): 소켓 ID
            
        Returns:
            Optional[str]: 사용자명 (세션이 없으면 None)
        """
        session = self._user_sessions.get(user_sid)
        return session.username if session else None
    
    async def cleanup_old_sessions(self, max_inactive_minutes: int = 30) -> int:
        """
        비활성 세션 정리
        
        Args:
            max_inactive_minutes (int): 최대 비활성 시간(분)
            
        Returns:
            int: 정리된 세션 수
        """
        now = datetime.now()
        inactive_sids = []
        
        for sid, session in self._user_sessions.items():
            inactive_time = (now - session.last_activity).total_seconds() / 60
            if inactive_time > max_inactive_minutes:
                inactive_sids.append(sid)
        
        # 비활성 세션 정리
        cleaned_count = 0
        for sid in inactive_sids:
            await self.cleanup_session(sid)
            cleaned_count += 1
        
        if cleaned_count > 0:
            print(f"🧹 {cleaned_count}개의 비활성 세션 정리 완료")
        
        return cleaned_count
    
    async def handle_reconnection(self, new_sid: str, room: str, username: str) -> List[str]:
        """
        재연결 처리 (같은 사용자의 이전 연결 정리)
        
        Args:
            new_sid (str): 새로운 소켓 ID
            room (str): 방 이름
            username (str): 사용자명
            
        Returns:
            List[str]: 정리된 이전 소켓 ID 목록
        """
        old_sids = []
        
        # 같은 방에서 같은 사용자명을 가진 다른 세션 찾기
        for sid, session in list(self._user_sessions.items()):
            if (sid != new_sid and 
                session.room == room and 
                session.username.lower() == username.lower()):
                old_sids.append(sid)
        
        # 이전 세션들 정리
        for old_sid in old_sids:
            await self.cleanup_session(old_sid)
            print(f"🔄 재연결 감지: {username}의 이전 세션 {old_sid} 정리")
        
        return old_sids
    
    def get_stats(self) -> Dict[str, int]:
        """
        사용자 통계 조회
        
        Returns:
            Dict[str, int]: 통계 정보
        """
        total_users = len(self._user_sessions)
        typing_users = sum(len(users) for users in self._typing_users.values())
        
        # 방별 사용자 수 계산
        room_user_counts = {}
        for session in self._user_sessions.values():
            room = session.room
            room_user_counts[room] = room_user_counts.get(room, 0) + 1
        
        return {
            "total_online_users": total_users,
            "typing_users": typing_users,
            "rooms_with_users": len(room_user_counts),
            "max_users_in_room": max(room_user_counts.values()) if room_user_counts else 0
        }


# 싱글톤 인스턴스 생성
user_service = UserService()


# =============================================================================
# 🔧 서비스 사용 예시
# =============================================================================
"""
사용 방법:

from app.services.user_service import user_service

# 세션 생성
success, message = await user_service.create_session(
    "socket123", "자유채팅", "홍길동"
)

# 타이핑 시작
room_id = await user_service.start_typing("socket123")
if room_id:
    typing_users = await user_service.get_typing_users(room_id)
    print(f"타이핑 중: {typing_users}")

# 방의 사용자 목록 조회
users = await user_service.get_room_users("자유채팅")
for user in users:
    print(f"사용자: {user.username}, 입장: {user.joined_at}")

# 통계 조회
stats = user_service.get_stats()
print(f"온라인 사용자: {stats['total_online_users']}명")
"""