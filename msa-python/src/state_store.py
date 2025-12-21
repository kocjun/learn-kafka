from collections import defaultdict
from datetime import datetime

# 상품별 주문 카운트
product_order_count = defaultdict(int)

# 분 단위 주문 카운트
orders_per_minute = defaultdict(int)


def minute_bucket(ts: str) -> str:
    dt = datetime.fromisoformat(ts)
    return dt.strftime("%Y-%m-%d %H:%M")



