"""
입력 검증 유틸리티
=================

Spring Boot의 @Valid, @Validated와 유사한 역할

학습 포인트:
- 서버사이드 검증의 중요성
- 보안을 위한 입력 정제
- 재사용 가능한 검증 함수들
- 정규표현식을 이용한 패턴 매칭
"""

import re
from typing import Optional, List
from datetime import datetime
from app.config.settings import settings


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
    
    text_stripped = text.strip()
    
    if len(text_stripped) > max_length:
        return f"{field_name}은(는) {max_length}자 이하로 입력해주세요."
    
    # 금지어 검사
    if contains_banned_words(text_stripped):
        banned_word = get_banned_word(text_stripped)
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
    if not text:
        return ""
    
    # HTML 태그 제거 (간단한 버전)
    text = re.sub(r'<[^>]+>', '', text)
    
    # 스크립트 태그 특별 처리
    text = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', text, flags=re.IGNORECASE)
    
    # 위험한 속성 제거
    text = re.sub(r'on\w+\s*=\s*["\'][^"\']*["\']', '', text, flags=re.IGNORECASE)
    
    # 앞뒤 공백 제거
    return text.strip()


def contains_banned_words(text: str) -> bool:
    """
    금지어 포함 여부 확인
    
    Args:
        text (str): 검사할 텍스트
        
    Returns:
        bool: 금지어 포함 여부
    """
    if not text:
        return False
    
    text_lower = text.lower()
    return any(banned_word.lower() in text_lower for banned_word in settings.BANNED_WORDS)


def get_banned_word(text: str) -> Optional[str]:
    """
    포함된 금지어 반환
    
    Args:
        text (str): 검사할 텍스트
        
    Returns:
        Optional[str]: 발견된 첫 번째 금지어
    """
    if not text:
        return None
    
    text_lower = text.lower()
    for banned_word in settings.BANNED_WORDS:
        if banned_word.lower() in text_lower:
            return banned_word
    
    return None


def validate_room_name(room_name: str) -> Optional[str]:
    """
    방 이름 전용 검증
    
    Args:
        room_name (str): 방 이름
        
    Returns:
        Optional[str]: 에러 메시지
    """
    error = validate_input(room_name, settings.MAX_ROOM_NAME_LENGTH, "방 이름")
    if error:
        return error
    
    # 특수 문자 검사
    forbidden_chars = ['<', '>', '&', '"', "'", '/']
    for char in forbidden_chars:
        if char in room_name:
            return f"방 이름에 '{char}' 문자는 사용할 수 없습니다"
    
    return None


def validate_username(username: str) -> Optional[str]:
    """
    사용자명 전용 검증
    
    Args:
        username (str): 사용자명
        
    Returns:
        Optional[str]: 에러 메시지
    """
    error = validate_input(username, settings.MAX_USERNAME_LENGTH, "닉네임")
    if error:
        return error
    
    # 공백만으로 이루어진 이름 방지
    if not username.strip():
        return "닉네임은 공백만으로 구성할 수 없습니다"
    
    # 시스템 예약어 검사
    reserved_names = ['시스템', 'system', 'admin', '관리자', 'bot']
    if username.lower() in [name.lower() for name in reserved_names]:
        return "사용할 수 없는 닉네임입니다"
    
    return None


def validate_message(message: str) -> Optional[str]:
    """
    메시지 전용 검증
    
    Args:
        message (str): 메시지 내용
        
    Returns:
        Optional[str]: 에러 메시지
    """
    error = validate_input(message, settings.MAX_MESSAGE_LENGTH, "메시지")
    if error:
        return error
    
    # 연속된 공백 검사 (스팸 방지)
    if re.search(r'\s{10,}', message):
        return "과도한 공백은 사용할 수 없습니다"
    
    # 연속된 특수문자 검사 (스팸 방지)
    if re.search(r'[!@#$%^&*()]{5,}', message):
        return "과도한 특수문자는 사용할 수 없습니다"
    
    return None


def is_valid_socket_id(sid: str) -> bool:
    """
    Socket ID 유효성 검사
    
    Args:
        sid (str): Socket ID
        
    Returns:
        bool: 유효 여부
    """
    if not sid or not isinstance(sid, str):
        return False
    
    # Socket.IO의 일반적인 SID 패턴 (영숫자, 하이픈, 언더스코어)
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', sid))


def format_timestamp(timestamp: float = None) -> str:
    """
    타임스탬프를 ISO 형식으로 포맷
    
    Args:
        timestamp (float, optional): Unix 타임스탬프. None이면 현재 시간
        
    Returns:
        str: ISO 형식 문자열
    """
    if timestamp is None:
        return datetime.now().isoformat()
    
    try:
        return datetime.fromtimestamp(timestamp).isoformat()
    except (ValueError, OSError):
        return datetime.now().isoformat()


def extract_mentions(message: str) -> List[str]:
    """
    메시지에서 멘션 추출
    
    Args:
        message (str): 메시지 내용
        
    Returns:
        List[str]: 멘션된 사용자명 목록
    """
    if not message:
        return []
    
    # @username 패턴 찾기
    mentions = re.findall(r'@(\w+)', message)
    
    # 중복 제거 및 빈 문자열 제거
    return list(set(mention for mention in mentions if mention.strip()))


def limit_text_length(text: str, max_length: int, suffix: str = "...") -> str:
    """
    텍스트 길이 제한 (로그용)
    
    Args:
        text (str): 원본 텍스트
        max_length (int): 최대 길이
        suffix (str): 잘림 표시 문자열
        
    Returns:
        str: 제한된 텍스트
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


# =============================================================================
# 🔧 검증 함수 사용 예시
# =============================================================================
"""
사용 방법:

from app.utils.validators import validate_username, sanitize_text

# 사용자명 검증
error = validate_username("홍길동")
if error:
    print(f"검증 실패: {error}")

# 텍스트 정제
safe_text = sanitize_text("<script>alert('xss')</script>안녕하세요")
print(safe_text)  # "안녕하세요"

# 멘션 추출
mentions = extract_mentions("@홍길동 @김철수 안녕하세요!")
print(mentions)  # ["홍길동", "김철수"]
"""