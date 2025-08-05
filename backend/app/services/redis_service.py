"""
Redis 서비스
============

Spring Boot의 Redis 템플릿과 동일한 역할
세션 관리, 캐싱, Pub/Sub 등의 Redis 기능을 제공합니다.

학습 포인트:
- Redis 비동기 클라이언트 사용
- 세션 데이터 관리
- 메시지 히스토리 캐싱
- 실시간 상태 관리
"""

import redis.asyncio as redis
import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from app.config.settings import settings


class RedisService:
    """
    Redis 서비스 클래스
    
    Spring Boot의 RedisTemplate과 동일한 패턴을 따릅니다.
    """
    
    def __init__(self):
        """Redis 클라이언트 초기화"""
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub_client: Optional[redis.Redis] = None
        print("🔴 RedisService 초기화 준비")
    
    async def connect(self):
        """Redis 서버에 연결"""
        try:
            # 메인 Redis 클라이언트
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Pub/Sub 전용 클라이언트
            self.pubsub_client = redis.Redis(
                host='localhost',
                port=6379,
                decode_responses=True
            )
            
            # 연결 테스트
            await self.redis_client.ping()
            print("✅ Redis 연결 성공")
            
        except Exception as e:
            print(f"❌ Redis 연결 실패: {e}")
            print("💡 Redis 서버가 실행 중인지 확인하세요: redis-server")
            # Redis 없이도 동작하도록 None으로 설정
            self.redis_client = None
            self.pubsub_client = None
    
    async def disconnect(self):
        """Redis 연결 종료"""
        try:
            if self.redis_client:
                await self.redis_client.close()
            if self.pubsub_client:
                await self.pubsub_client.close()
            print("✅ Redis 연결 종료")
        except Exception as e:
            print(f"❌ Redis 연결 종료 오류: {e}")
    
    # =============================================================================
    # 🔐 세션 관리
    # =============================================================================
    
    async def set_user_session(self, sid: str, room: str, username: str, ttl: int = 3600) -> bool:
        """
        사용자 세션 저장
        
        Args:
            sid (str): 소켓 ID
            room (str): 방 이름
            username (str): 사용자명
            ttl (int): 만료 시간(초, 기본 1시간)
            
        Returns:
            bool: 저장 성공 여부
        """
        if not self.redis_client:
            return False
            
        try:
            session_data = {
                "room": room,
                "username": username,
                "joined_at": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat()
            }
            
            await self.redis_client.setex(
                f"session:{sid}", 
                ttl, 
                json.dumps(session_data)
            )
            
            # 사용자별 세션 추적 (중복 로그인 방지용)
            await self.redis_client.setex(
                f"user:{username}:session", 
                ttl, 
                sid
            )
            
            print(f"💾 세션 저장: {username} → {room} (sid: {sid})")
            return True
            
        except Exception as e:
            print(f"❌ 세션 저장 실패: {e}")
            return False
    
    async def get_user_session(self, sid: str) -> Optional[Dict[str, Any]]:
        """
        사용자 세션 조회
        
        Args:
            sid (str): 소켓 ID
            
        Returns:
            Optional[Dict]: 세션 데이터
        """
        if not self.redis_client:
            return None
            
        try:
            data = await self.redis_client.get(f"session:{sid}")
            if data:
                session = json.loads(data)
                # 마지막 활동 시간 업데이트
                session["last_activity"] = datetime.now().isoformat()
                await self.redis_client.setex(
                    f"session:{sid}", 
                    3600, 
                    json.dumps(session)
                )
                return session
            return None
            
        except Exception as e:
            print(f"❌ 세션 조회 실패: {e}")
            return None
    
    async def remove_user_session(self, sid: str) -> bool:
        """
        사용자 세션 삭제
        
        Args:
            sid (str): 소켓 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        if not self.redis_client:
            return False
            
        try:
            # 세션 정보 먼저 조회
            session = await self.get_user_session(sid)
            if session:
                username = session.get("username")
                if username:
                    await self.redis_client.delete(f"user:{username}:session")
            
            # 세션 삭제
            result = await self.redis_client.delete(f"session:{sid}")
            print(f"🗑️ 세션 삭제: {sid}")
            return result > 0
            
        except Exception as e:
            print(f"❌ 세션 삭제 실패: {e}")
            return False
    
    # =============================================================================
    # 💬 메시지 히스토리 캐싱
    # =============================================================================
    
    async def save_message_to_history(self, room: str, message_data: Dict[str, Any], max_messages: int = 50) -> bool:
        """
        메시지 히스토리에 저장
        
        Args:
            room (str): 방 이름
            message_data (Dict): 메시지 데이터
            max_messages (int): 최대 보관할 메시지 수
            
        Returns:
            bool: 저장 성공 여부
        """
        if not self.redis_client:
            return False
            
        try:
            # 타임스탬프 추가
            message_data["timestamp"] = datetime.now().isoformat()
            
            # Redis LIST에 메시지 추가 (최신이 앞쪽)
            await self.redis_client.lpush(
                f"messages:{room}", 
                json.dumps(message_data)
            )
            
            # 최대 개수 제한
            await self.redis_client.ltrim(f"messages:{room}", 0, max_messages - 1)
            
            # 메시지 히스토리 만료 시간 설정 (7일)
            await self.redis_client.expire(f"messages:{room}", 604800)
            
            print(f"📝 메시지 히스토리 저장: {room}")
            return True
            
        except Exception as e:
            print(f"❌ 메시지 히스토리 저장 실패: {e}")
            return False
    
    async def get_message_history(self, room: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        메시지 히스토리 조회
        
        Args:
            room (str): 방 이름
            limit (int): 가져올 메시지 개수
            
        Returns:
            List[Dict]: 메시지 리스트 (시간순)
        """
        if not self.redis_client:
            return []
            
        try:
            # Redis LIST에서 메시지 조회 (최신부터)
            messages = await self.redis_client.lrange(f"messages:{room}", 0, limit - 1)
            
            # JSON 파싱 및 시간순 정렬 (오래된 것부터)
            result = []
            for msg in reversed(messages):  # reversed로 시간순 정렬
                try:
                    result.append(json.loads(msg))
                except json.JSONDecodeError:
                    continue
            
            print(f"📖 메시지 히스토리 조회: {room} ({len(result)}개)")
            return result
            
        except Exception as e:
            print(f"❌ 메시지 히스토리 조회 실패: {e}")
            return []
    
    # =============================================================================
    # 👥 사용자 상태 관리
    # =============================================================================
    
    async def set_user_online(self, username: str, room: str, ttl: int = 300) -> bool:
        """
        사용자 온라인 상태 설정
        
        Args:
            username (str): 사용자명
            room (str): 방 이름
            ttl (int): 만료 시간(초, 기본 5분)
            
        Returns:
            bool: 설정 성공 여부
        """
        if not self.redis_client:
            return False
            
        try:
            # 전체 온라인 사용자
            await self.redis_client.setex(f"online:{username}", ttl, room)
            
            # 방별 온라인 사용자
            await self.redis_client.sadd(f"room_users:{room}", username)
            await self.redis_client.expire(f"room_users:{room}", ttl)
            
            return True
            
        except Exception as e:
            print(f"❌ 온라인 상태 설정 실패: {e}")
            return False
    
    async def set_user_offline(self, username: str, room: str) -> bool:
        """
        사용자 오프라인 상태 설정
        
        Args:
            username (str): 사용자명
            room (str): 방 이름
            
        Returns:
            bool: 설정 성공 여부
        """
        if not self.redis_client:
            return False
            
        try:
            # 온라인 상태 제거
            await self.redis_client.delete(f"online:{username}")
            
            # 방에서 사용자 제거
            await self.redis_client.srem(f"room_users:{room}", username)
            
            return True
            
        except Exception as e:
            print(f"❌ 오프라인 상태 설정 실패: {e}")
            return False
    
    async def get_online_users_in_room(self, room: str) -> List[str]:
        """
        방의 온라인 사용자 목록 조회
        
        Args:
            room (str): 방 이름
            
        Returns:
            List[str]: 온라인 사용자 목록
        """
        if not self.redis_client:
            return []
            
        try:
            users = await self.redis_client.smembers(f"room_users:{room}")
            return list(users) if users else []
            
        except Exception as e:
            print(f"❌ 온라인 사용자 조회 실패: {e}")
            return []
    
    # =============================================================================
    # 🏠 방 상태 영구 저장
    # =============================================================================
    
    async def save_room_info(self, room_id: str, room_data: Dict[str, Any]) -> bool:
        """
        방 정보 영구 저장
        
        Args:
            room_id (str): 방 ID
            room_data (Dict): 방 데이터
            
        Returns:
            bool: 저장 성공 여부
        """
        if not self.redis_client:
            return False
            
        try:
            # 방 생성 시간 추가
            if "created_at" not in room_data:
                room_data["created_at"] = datetime.now().isoformat()
            
            room_data["last_updated"] = datetime.now().isoformat()
            
            await self.redis_client.hset(
                f"room:{room_id}",
                mapping=room_data
            )
            
            # 방 목록에 추가
            await self.redis_client.sadd("rooms:all", room_id)
            
            print(f"🏠 방 정보 저장: {room_id}")
            return True
            
        except Exception as e:
            print(f"❌ 방 정보 저장 실패: {e}")
            return False
    
    async def get_room_info(self, room_id: str) -> Optional[Dict[str, Any]]:
        """
        방 정보 조회
        
        Args:
            room_id (str): 방 ID
            
        Returns:
            Optional[Dict]: 방 데이터
        """
        if not self.redis_client:
            return None
            
        try:
            data = await self.redis_client.hgetall(f"room:{room_id}")
            return dict(data) if data else None
            
        except Exception as e:
            print(f"❌ 방 정보 조회 실패: {e}")
            return None
    
    async def get_all_rooms(self) -> List[str]:
        """
        모든 방 목록 조회
        
        Returns:
            List[str]: 방 ID 목록
        """
        if not self.redis_client:
            return []
            
        try:
            rooms = await self.redis_client.smembers("rooms:all")
            return list(rooms) if rooms else []
            
        except Exception as e:
            print(f"❌ 방 목록 조회 실패: {e}")
            return []


# =============================================================================
# 🌐 Redis 서비스 싱글톤 인스턴스
# =============================================================================

redis_service: Optional[RedisService] = None


def get_redis_service() -> RedisService:
    """
    Redis 서비스 인스턴스 반환
    
    Returns:
        RedisService: Redis 서비스 인스턴스
        
    Raises:
        RuntimeError: 서비스가 초기화되지 않은 경우
    """
    if redis_service is None:
        raise RuntimeError("RedisService가 초기화되지 않았습니다. main.py에서 초기화하세요.")
    return redis_service