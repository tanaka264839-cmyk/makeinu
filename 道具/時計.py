"""負け犬の癒し：いまの時刻。

時刻で動く決まり（独り言の24時間・夜の部屋・連投の間隔）は、みなここから「いま」を取る。
試しで時計を進めたり夜に合わせたりできるよう、1か所に置く。
"""
from datetime import datetime, timedelta, timezone

日本時間 = timezone(timedelta(hours=9))


def いま():
    return datetime.now(timezone.utc)
