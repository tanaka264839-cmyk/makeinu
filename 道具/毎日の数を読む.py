"""負け犬の癒し：毎朝の数字のために、きのう（日本時間）の数とサーバーの様子を読み、本人に伝えることがあれば言う。

本文も番地も鍵も出さない。数は AI が読むが、本文を読むのは持ち主の見回りだけ（AI が本文を読むと、外の会社へ送ることになるため。決定メモ「AIは本物の書き込みの本文を読まない」）。
記録は読むだけで、何も書かない。
使い方（サーバーで makeinu として）：python3 -I -B /srv/makeinu/道具/毎日の数を読む.py [記録の場所。既定 /srv/makeinu/記録/場.db]
"""
import os
import re
import shutil
import socket
import sqlite3
import ssl
import sys
import time
from datetime import date, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # -I で動かすので、同じ場所の決まりと時計を読めるようにする
import 決まり  # noqa: E402
import 時計  # noqa: E402

本物の記録 = "/srv/makeinu/記録/場.db"
本物の名前 = "makeinu.net"

# ここを超えた日だけ本人に伝える
空きの下限GB = 30  # いまは43GB。控えは消さずに溜まるので、少なくなる前に相談する
証明書の残りの下限日 = 25  # 残り30日で自動で更新する。25日を切っていれば、更新が動いていない
控えの遅れの上限日 = 1  # 毎日0:05に取る。朝に見て、きのうの分までは普通
見回りに届く件数 = 150  # 見回りは新しい200件まで、板は100件まで。届かなくなる前に直す
急に増えた行 = 1000  # わかる・名乗り・受けない に回数の上限が無いので、荒らしの目安
聞き役の失敗の上限 = 3  # 1回の失敗は一時の止まりで起きる。続いていれば鍵か窓口を疑う


def 記録を開く(記録の場所):
    return sqlite3.connect(f"file:{記録の場所}?mode=ro", uri=True, timeout=10)


def きのうの範囲(いま):
    """日本時間のきのうの始まりと終わり（世界標準時の字。記録の時刻と字のまま比べられる形）。"""
    今日 = いま.astimezone(時計.日本時間).replace(hour=0, minute=0, second=0, microsecond=0)
    return tuple(時.astimezone(timezone.utc).isoformat() for 時 in (今日 - timedelta(days=1), 今日))


def 数を読む(記録の場所, いま=None):
    範囲 = きのうの範囲(いま or 時計.いま())
    つなぎ = 記録を開く(記録の場所)
    try:
        def 数(文, *値):
            return つなぎ.execute(文, 値).fetchone()[0]

        人の = "書いた人の鍵 != ?"
        きのう = "書いた時刻 >= ? AND 書いた時刻 < ?"
        聞き役 = 決まり.聞き役の鍵
        つらい = sum(
            1 for 本文, あの時 in つなぎ.execute(f"SELECT 本文, あの時 FROM 書き込み WHERE {人の} AND {きのう}", (聞き役, *範囲))
            if 決まり.見立てる(本文).相談先を出す or (あの時 and 決まり.見立てる(あの時).相談先を出す)
        )
        増えた = sum(数(f"SELECT COUNT(*) FROM {台} WHERE {列} >= ? AND {列} < ?", *範囲)
                  for 台, 列 in (("わかる", "押した時刻"), ("名乗り", "変えた時刻"), ("小部屋を受けない", "決めた時刻")))
        聞き役の結果 = "SELECT COUNT(*) FROM 聞き役の記録 WHERE 結果 = ? AND 最後に試した時刻 >= ? AND 最後に試した時刻 < ?"
        return {
            "きのうの人の書き込み": 数(f"SELECT COUNT(*) FROM 書き込み WHERE {人の} AND {きのう}", 聞き役, *範囲),
            "うち消した": 数(f"SELECT COUNT(*) FROM 書き込み WHERE {人の} AND {きのう} AND 消した時刻 IS NOT NULL", 聞き役, *範囲),
            "きのうの聞き役の返事": 数(f"SELECT COUNT(*) FROM 書き込み WHERE 書いた人の鍵 = ? AND {きのう}", 聞き役, *範囲),
            "人の書き込みの累計": 数(f"SELECT COUNT(*) FROM 書き込み WHERE {人の}", 聞き役),
            "きのうの知らせ": 数("SELECT COUNT(*) FROM 知らせ WHERE 送った時刻 >= ? AND 送った時刻 < ?", *範囲),
            "知らせの累計": 数("SELECT COUNT(*) FROM 知らせ"),
            "きのうのつらすぎる言葉": つらい,
            "きのうの聞き役の失敗": 数(聞き役の結果, "失敗", *範囲),
            "きのうの聞き役の止めた": 数(聞き役の結果, "止めた", *範囲),
            "きのう増えた行": 増えた,
        }
    finally:
        つなぎ.close()


def 控えの遅れ日(記録の場所, いま=None):
    """一番新しい毎日の控えが何日前か。控えが無ければ None。作りかけや別の形のファイルは見ない。"""
    控えの場所 = os.path.join(os.path.dirname(記録の場所), "控え")
    if not os.path.isdir(控えの場所):
        return None
    日付たち = [名前[:10] for 名前 in os.listdir(控えの場所) if re.fullmatch(r"\d{4}-\d{2}-\d{2}\.db", 名前)]
    if not 日付たち:
        return None
    return ((いま or 時計.いま()).astimezone(時計.日本時間).date() - date.fromisoformat(max(日付たち))).days


def 証明書の残り日(名前=本物の名前):
    """本物の入口へつないで証明書の残りの日数を読む。つながらない・証明書が正しくない時は None（https で開けないおそれがある）。"""
    try:
        with socket.create_connection((名前, 443), timeout=10) as つなぎ, ssl.create_default_context().wrap_socket(つなぎ, server_hostname=名前) as 暗号:
            return int((ssl.cert_time_to_seconds(暗号.getpeercert()["notAfter"]) - time.time()) // 86400)
    except (OSError, ssl.SSLError, KeyError, ValueError):
        return None


def 様子を読む(記録の場所, いま=None):
    return {"空きGB": shutil.disk_usage(os.path.dirname(記録の場所)).free // 1024 ** 3, "証明書の残り日": 証明書の残り日(), "控えの遅れ日": 控えの遅れ日(記録の場所, いま)}


def 伝えること(数, 様子):
    """本人に伝えることだけを返す（何もない日は空）。"""
    伝える = []
    if 数["きのうの知らせ"] > 0:
        伝える.append(f"新しい知らせが{数['きのうの知らせ']}件あります。見回りを開いてください。")
    if 数["きのうのつらすぎる言葉"] > 0:
        伝える.append(f"つらすぎる言葉の書き込みが{数['きのうのつらすぎる言葉']}件ありました。見回りを開いてください。")
    if 数["きのうの人の書き込み"] > 0 and 数["人の書き込みの累計"] == 数["きのうの人の書き込み"]:
        伝える.append(f"初めて人の書き込みが付きました（{数['きのうの人の書き込み']}件）。見回りを開いてください。")
    if 数["人の書き込みの累計"] > 見回りに届く件数:
        伝える.append(f"書き込みが{見回りに届く件数}件を超えました。古い書き込みに届かなくなる前に直します。")
    if 数["きのう増えた行"] > 急に増えた行:
        伝える.append(f"「わかる」や名乗りの行がきのう{数['きのう増えた行']}行増えました。荒らしかもしれません。")
    if 数["きのうの聞き役の失敗"] >= 聞き役の失敗の上限:
        伝える.append(f"聞き役がきのう{数['きのうの聞き役の失敗']}回うまくいきませんでした。AIの鍵か窓口を確かめます。")
    if 様子["空きGB"] < 空きの下限GB:
        伝える.append(f"サーバーの空きが{様子['空きGB']}GBです。")
    if 様子["証明書の残り日"] is None:
        伝える.append("証明書を読めませんでした。https で開けないかもしれません。")
    elif 様子["証明書の残り日"] < 証明書の残りの下限日:
        伝える.append(f"証明書の残りが{様子['証明書の残り日']}日です。自動の更新が動いていないかもしれません。")
    if 様子["控えの遅れ日"] is None:
        伝える.append("毎日の控えがありません。")
    elif 様子["控えの遅れ日"] > 控えの遅れの上限日:
        伝える.append(f"毎日の控えが{様子['控えの遅れ日']}日止まっています。")
    return 伝える


def 字にする(数, 様子):
    行たち = [f"{名前} {値}" for 名前, 値 in {**数, **様子}.items()]
    伝える = 伝えること(数, 様子)
    return "\n".join(行たち + (["伝えること：" + 文 for 文 in 伝える] or ["伝えること：なし"]))


if __name__ == "__main__":
    場所 = sys.argv[1] if len(sys.argv) > 1 else 本物の記録
    print(字にする(数を読む(場所), 様子を読む(場所)))
