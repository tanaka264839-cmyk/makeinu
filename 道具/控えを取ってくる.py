"""負け犬の癒し：自宅PCが、サーバーの一番新しい毎日の控えを取ってきて、鍵をかけて置く（公開前に要るもの 順9）。

サーバーごと失くした時に、書き込みを戻せるように。お金をかけずに、持ち主の自宅のパソコンにだけ写しを置く（作業用のパソコンには置かない）。
鍵は Windows の仕組み（DPAPI）で、このパソコンのこの利用者でしか外せない。新しい4つだけ残す。
取りに行く鍵は、サーバーで控えを出すこと（控えを出す.py）しかできない専用の鍵。

使い方（自宅PC・Windows の Python。入れる物は無い）：
  取ってくる：pythonw 控えを取ってくる.py
  戻す時    ：python 控えを取ってくる.py 開く <写し.鍵付き> <書き出す先.db>
"""
import base64
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime

残す数 = 4
相手 = "ubuntu@203.0.113.10"
鍵の場所 = os.path.join(os.path.expanduser("~"), ".ssh", "makeinu_hikae")
ssh = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "OpenSSH", "ssh.exe")
# 試しの記録と同じ「記録」の中に置く（記録は、自宅PCと作業用PCの間で運ぶ一式に入れない）
写しの置き場 = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "記録", "控えの写し")
毎日の控えの名前 = re.compile(r"\d{4}-\d{2}-\d{2}\.db")
写しの名前 = re.compile(r"\d{4}-\d{2}-\d{2}\.鍵付き")


class 受け取れない(Exception):
    pass


def 受け取る(出たもの):
    """サーバーの 控えを出す.py の出力から、控えの名前と中身を取り出す。欠け・違い・おかしな名前・控えでない物は受け取らない。"""
    見出し行, _, 本体 = 出たもの.partition(b"\n")
    try:
        見出し = json.loads(見出し行)
        中身 = base64.b64decode(本体)
    except ValueError:
        raise 受け取れない("見出しか中身が読めない")
    名前 = 見出し.get("名前") if isinstance(見出し, dict) else None
    if not isinstance(名前, str) or not 毎日の控えの名前.fullmatch(名前):
        raise 受け取れない(f"名前がおかしい（{名前!r}）")
    if len(中身) != 見出し.get("大きさ") or hashlib.sha256(中身).hexdigest() != 見出し.get("sha256"):
        raise 受け取れない(f"{名前} の中身が欠けたか違う")
    if not 中身.startswith(b"SQLite format 3\x00"):
        raise 受け取れない(f"{名前} が控えの形でない")
    return 名前, 中身


def 写しを置く(置き場, 名前, 中身, 鍵をかける, 残す数):
    """鍵をかけて置き、新しい 残す数 だけ残す。その日の写しが既にあれば置かない。置いたら True。"""
    os.makedirs(置き場, exist_ok=True)
    写し = os.path.join(置き場, 名前[: -len(".db")] + ".鍵付き")
    if os.path.exists(写し):
        return False
    鍵付き = 鍵をかける(中身)
    書きかけ = 写し + ".書きかけ"
    try:
        with open(書きかけ, "wb") as f:
            f.write(鍵付き)
        os.replace(書きかけ, 写し)  # 書き終えてから名前を付ける（途中で止まっても、欠けた写しを残さない）
    except OSError:
        if os.path.exists(書きかけ):
            os.remove(書きかけ)
        raise
    for 古い in sorted((n for n in os.listdir(置き場) if 写しの名前.fullmatch(n)), reverse=True)[残す数:]:
        os.remove(os.path.join(置き場, 古い))
    return True


def 記す(置き場, 文):
    os.makedirs(置き場, exist_ok=True)
    with open(os.path.join(置き場, "取ってきた記録.txt"), "a", encoding="utf-8", newline="\n") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M} | {文}\n")


def 取ってくる(ssh命令, 置き場, 鍵をかける, 残す数=残す数):
    """サーバーにつないで一番新しい控えを受け取り、鍵をかけて置く。うまくいけば 0、だめなら 1（前の写しはそのまま）。"""
    try:
        返り = subprocess.run(ssh命令, capture_output=True, timeout=300)
        if 返り.returncode != 0:
            raise 受け取れない(f"サーバーから受け取れない（{返り.returncode}）{返り.stderr.decode(errors='replace').strip()[:200]}")
        名前, 中身 = 受け取る(返り.stdout)
        置いた = 写しを置く(置き場, 名前, 中身, 鍵をかける, 残す数)
    except (受け取れない, OSError, subprocess.SubprocessError) as 訳:
        記す(置き場, f"うまくいかなかった：{訳}")
        return 1
    記す(置き場, f"取ってきた：{名前}（{len(中身)}バイト）" if 置いた else f"もうある：{名前}")
    return 0


def _DPAPI(関数名, 中身, 説明=None):
    import ctypes
    from ctypes import wintypes

    class 塊(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

    元 = ctypes.create_string_buffer(中身, len(中身))
    入れる = 塊(len(中身), ctypes.cast(元, ctypes.POINTER(ctypes.c_char)))
    出る = 塊()
    尋ねる画面を出さない = 0x1  # CRYPTPROTECT_UI_FORBIDDEN（決まった時刻に裏で動くので）
    関数 = getattr(ctypes.windll.crypt32, 関数名)
    if not 関数(ctypes.byref(入れる), 説明, None, None, None, 尋ねる画面を出さない, ctypes.byref(出る)):
        raise ctypes.WinError()
    try:
        return ctypes.string_at(出る.pbData, 出る.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(ctypes.cast(出る.pbData, ctypes.c_void_p))


def 鍵をかける(中身):
    """このパソコンのこの利用者でしか外せない鍵（Windows の DPAPI）。"""
    return _DPAPI("CryptProtectData", 中身, "負け犬の癒しの控え")


def 鍵を外す(中身):
    return _DPAPI("CryptUnprotectData", 中身)


def 開く(写し, 書き出す先):
    """戻す時に、写しの鍵を外して控え（.db）に書き出す。書き出す先が既にあれば上書きしない。"""
    with open(写し, "rb") as f:
        中身 = 鍵を外す(f.read())
    with open(書き出す先, "xb") as f:
        f.write(中身)


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "開く":
        開く(sys.argv[2], sys.argv[3])
        sys.exit(0)
    if len(sys.argv) > 1:
        sys.exit("使い方：控えを取ってくる.py（取ってくる）／控えを取ってくる.py 開く <写し.鍵付き> <書き出す先.db>")
    命令 = [ssh, "-i", 鍵の場所, "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=30", 相手]
    sys.exit(取ってくる(命令, 写しの置き場, 鍵をかける))
