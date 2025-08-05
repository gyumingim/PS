"""
방 관리 서비스
=============

Spring Boot의 @Service와 동일한 역할
채팅방 생성, 삭제, 조회 등의 비즈니스 로직을 처리합니다.

학습 포인트:
- 비즈니스 로직과 데이터 액세스 분리
- 서비스 계층의 역할과 책임
- 싱글톤 패턴 적용
- 의존성 주입 (Dependency Injection)
"""

import time
import asyncio
from typing import Dict, List, Optional
from app.models.chat_models import Room, RoomInfo
from app.config.settings import settings
from app.utils.validators import validate_room_name


class RoomService:
    """
    방 관리 서비스 클래스
    
    Spring Boot의 @Service와 동일한 역할
    싱글톤 패턴으로 구현되어 애플리케이션 전체에서 하나의 인스턴스만 사용
    """
    
    def __init__(self):
        """서비스 초기화"""
        # 메모리 기반 방 저장소 (실제 서비스에서는 DB 사용)
        self._rooms: Dict[str, Room] = {}
        print("🏠 RoomService 초기화 완료")
    
    async def create_room(self, room_id: str) -> tuple[bool, str]:
        """
        새로운 채팅방 생성
        
        Args:
            room_id (str): 생성할 방 ID
            
        Returns:
            tuple[bool, str]: (성공 여부, 메시지)
            
        학습 포인트:
            - 입력 검증 → 중복 확인 → 생성 → 결과 반환 순서
            - 비즈니스 로직의 단계적 처리
            - 명확한 반환값으로 호출자에게 결과 전달
        """
        # 1단계: 입력 검증
        error_msg = validate_room_name(room_id)
        if error_msg:
            return False, error_msg
        
        # 2단계: 중복 확인
        if room_id in self._rooms:
            return False, "이미 존재하는 방입니다."
        
        # 3단계: 방 생성
        new_room = Room(created_at=time.time())
        self._rooms[room_id] = new_room
        
        print(f"🏠 방 '{room_id}' 생성 완료")
        return True, f"방 '{room_id}'이(가) 생성되었습니다."
    
    async def get_room(self, room_id: str) -> Optional[Room]:
        """
        특정 방 정보 조회
        
        Args:
            room_id (str): 조회할 방 ID
            
        Returns:
            Optional[Room]: 방 객체 (없으면 None)
        """
        return self._rooms.get(room_id)
    
    async def get_all_rooms(self) -> List[RoomInfo]:
        """
        모든 방 목록 조회
        
        Returns:
            List[RoomInfo]: 방 정보 목록
            
        학습 포인트:
            - 내부 데이터 구조를 외부 응답 모델로 변환
            - 데이터 은닉: 내부 구조를 직접 노출하지 않음
        """
        room_list = []
        for room_id, room in self._rooms.items():
            room_info = RoomInfo(
                id=room_id,
                name=room_id,
                user_count=room.get_user_count(),
                created_at=room.created_at
            )
            room_list.append(room_info)
        
        # 생성 시간 순으로 정렬 (최신 순)
        room_list.sort(key=lambda x: x.created_at, reverse=True)
        return room_list
    
    async def delete_room(self, room_id: str) -> bool:
        """
        방 삭제
        
        Args:
            room_id (str): 삭제할 방 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        if room_id in self._rooms:
            del self._rooms[room_id]
            print(f"🗑️ 방 '{room_id}' 삭제 완료")
            return True
        return False
    
    async def add_user_to_room(self, room_id: str, user_sid: str, username: str) -> tuple[bool, str]:
        """
        사용자를 방에 추가
        
        Args:
            room_id (str): 방 ID
            user_sid (str): 사용자 소켓 ID
            username (str): 사용자명
            
        Returns:
            tuple[bool, str]: (성공 여부, 메시지)
        """
        # 방이 없으면 자동 생성
        if room_id not in self._rooms:
            success, msg = await self.create_room(room_id)
            if not success:
                return False, msg
        
        room = self._rooms[room_id]
        
        # 중복 닉네임 검사
        if room.has_user(username):
            return False, f"'{username}'은(는) 이미 사용 중인 닉네임입니다."
        
        # 사용자 추가
        room.add_user(user_sid, username)
        print(f"👤 '{username}' → '{room_id}' 입장")
        
        return True, f"'{username}'님이 '{room_id}' 방에 입장했습니다."
    
    async def remove_user_from_room(self, room_id: str, user_sid: str) -> tuple[bool, str, bool]:
        """
        사용자를 방에서 제거
        
        Args:
            room_id (str): 방 ID
            user_sid (str): 사용자 소켓 ID
            
        Returns:
            tuple[bool, str, bool]: (성공 여부, 사용자명, 방이 비었는지 여부)
        """
        if room_id not in self._rooms:
            return False, "", False
        
        room = self._rooms[room_id]
        username = room.users.get(user_sid, "")
        
        # 사용자 제거
        removed = room.remove_user(user_sid)
        if removed:
            print(f"👤 '{username}' ← '{room_id}' 퇴장")
            
            # 방이 비었는지 확인
            is_empty = room.is_empty()
            if is_empty:
                # 지연 삭제 스케줄링
                asyncio.create_task(self._delayed_room_cleanup(room_id))
            
            return True, username, is_empty
        
        return False, "", False
    
    async def _delayed_room_cleanup(self, room_id: str) -> None:
        """
        빈 방 지연 삭제
        
        Args:
            room_id (str): 삭제할 방 ID
            
        학습 포인트:
            - 지연 삭제: 사용자가 새로고침 등으로 잠시 나갔을 때 방을 바로 삭제하지 않음
            - 사용자 경험 개선: 네트워크 불안정 상황 대응
        """
        print(f"⏰ 방 '{room_id}' 삭제 대기 중... ({settings.ROOM_CLEANUP_DELAY}초)")
        await asyncio.sleep(settings.ROOM_CLEANUP_DELAY)
        
        try:
            if room_id in self._rooms:
                room = self._rooms[room_id]
                if room.is_empty():
                    await self.delete_room(room_id)
                else:
                    print(f"👥 방 '{room_id}'에 사용자가 다시 들어와서 삭제 취소됨")
        except Exception as e:
            print(f"❌ 방 삭제 중 오류: {e}")
    
    async def get_room_users(self, room_id: str) -> List[str]:
        """
        방의 사용자 목록 조회
        
        Args:
            room_id (str): 방 ID
            
        Returns:
            List[str]: 사용자명 목록
        """
        if room_id not in self._rooms:
            return []
        
        return list(self._rooms[room_id].users.values())
    
    async def get_room_user_count(self, room_id: str) -> int:
        """
        방의 사용자 수 조회
        
        Args:
            room_id (str): 방 ID
            
        Returns:
            int: 사용자 수
        """
        if room_id not in self._rooms:
            return 0
        
        return self._rooms[room_id].get_user_count()
    
    async def room_exists(self, room_id: str) -> bool:
        """
        방 존재 여부 확인
        
        Args:
            room_id (str): 방 ID
            
        Returns:
            bool: 존재 여부
        """
        return room_id in self._rooms
    
    async def cleanup_user_from_all_rooms(self, user_sid: str) -> List[str]:
        """
        모든 방에서 특정 사용자 제거 (연결 끊김 시 사용)
        
        Args:
            user_sid (str): 사용자 소켓 ID
            
        Returns:
            List[str]: 제거된 방 목록
        """
        removed_rooms = []
        
        for room_id, room in list(self._rooms.items()):
            if user_sid in room.users:
                username = room.users[user_sid]
                room.remove_user(user_sid)
                removed_rooms.append(room_id)
                print(f"🧹 '{username}' → '{room_id}' 자동 정리")
                
                # 방이 비었으면 지연 삭제
                if room.is_empty():
                    asyncio.create_task(self._delayed_room_cleanup(room_id))
        
        return removed_rooms
    
    def get_stats(self) -> Dict[str, int]:
        """
        방 통계 조회
        
        Returns:
            Dict[str, int]: 통계 정보
        """
        total_rooms = len(self._rooms)
        total_users = sum(room.get_user_count() for room in self._rooms.values())
        
        return {
            "total_rooms": total_rooms,
            "total_users": total_users,
            "empty_rooms": sum(1 for room in self._rooms.values() if room.is_empty())
        }


# 싱글톤 인스턴스 생성
room_service = RoomService()


# =============================================================================
# 🔧 서비스 사용 예시
# =============================================================================
"""
사용 방법:

from app.services.room_service import room_service

# 방 생성
success, message = await room_service.create_room("자유채팅")
if success:
    print(f"성공: {message}")

# 사용자 추가
success, message = await room_service.add_user_to_room(
    "자유채팅", "socket123", "홍길동"
)

# 방 목록 조회
rooms = await room_service.get_all_rooms()
for room in rooms:
    print(f"방: {room.name}, 사용자: {room.user_count}명")

# 통계 조회
stats = room_service.get_stats()
print(f"전체 방: {stats['total_rooms']}개, 전체 사용자: {stats['total_users']}명")
"""