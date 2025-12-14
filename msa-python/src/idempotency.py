import time


# Simple in-memory idempotency tracking
processed_event_ids: set[str] = set()


# 확인된 이벤트 ID인지 검사
# 이벤트 ID가 이미 처리된 적이 있으면 True 반환
def is_duplicate(event_id: str) -> bool:
    return event_id in processed_event_ids


# 이벤트 ID를 처리된 것으로 표시
def mark_processed(event_id: str):
    processed_event_ids.add(event_id)


# 재시도 로직을 포함한 함수 래퍼
def retry_with_backoff(func, retries=3, base_delay=1):
    for attempt in range(1, retries + 1):
        try:
            return func()
        except Exception as e:
            if attempt == retries:
                raise
            sleep = base_delay * (2 ** (attempt - 1))
            print(f"⏳ retry {attempt}/{retries}, sleep {sleep}s")
            time.sleep(sleep)
