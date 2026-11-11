"""負け犬の癒し：一番新しい毎日の控えを、サーバーの外へ写すために出す（自宅PCの 控えを取ってくる.py が取りに来る）。

自宅PCの控えを取ってくる専用の鍵は、サーバーでこれしか動かせない（authorized_keys の command= で決めてある）。
  command="sudo -n -u makeinu /usr/bin/python3 -I -B /srv/makeinu/道具/控えを出す.py",restrict ssh-ed25519 …
出すもの：1行目に {"名前", "大きさ", "sha256"} を JSON で。2行目から控えの中身を base64 で（Windows で字として受け取っても壊れないように）。
出せる控えが無ければ、何も出さずに 1 で終わる。
"""
import base64
import hashlib
import json
import os
import re
import sqlite3
import sys
from urllib.parse import quote

控えの置き場 = "/srv/makeinu/記録/控え"
毎日の控えの名前 = re.compile(r"\d{4}-\d{2}-\d{2}\.db")


def 出してよいか(場所):
    """壊れていない負け犬の控えで、書いた人の記録が1件も入っていないこと（番地をサーバーの外へ出さない）。"""
    try:
        つなぎ = sqlite3.connect(f"file:{quote(場所)}?mode=ro", uri=True)
        try:
            if つなぎ.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                return False
            台たち = {行[0] for 行 in つなぎ.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
            if "書き込み" not in 台たち:
                return False
            return "書いた人の記録" not in 台たち or つなぎ.execute("SELECT COUNT(*) FROM 書いた人の記録").fetchone()[0] == 0
        finally:
            つなぎ.close()
    except sqlite3.Error:
        return False


def 一番新しい出せる控え(置き場):
    if not os.path.isdir(置き場):
        return None
    名前たち = sorted((名前 for 名前 in os.listdir(置き場) if 毎日の控えの名前.fullmatch(名前)), reverse=True)
    return next((os.path.join(置き場, 名前) for 名前 in 名前たち if 出してよいか(os.path.join(置き場, 名前))), None)


def 出す(置き場, 出す先):
    場所 = 一番新しい出せる控え(置き場)
    if not 場所:
        return 1
    with open(場所, "rb") as f:
        中身 = f.read()
    見出し = {"名前": os.path.basename(場所), "大きさ": len(中身), "sha256": hashlib.sha256(中身).hexdigest()}
    出す先.write(json.dumps(見出し).encode("ascii") + b"\n" + base64.encodebytes(中身))
    出す先.flush()
    return 0


if __name__ == "__main__":
    sys.exit(出す(sys.argv[1] if len(sys.argv) > 1 else 控えの置き場, sys.stdout.buffer))
