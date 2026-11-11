"""負け犬の癒し：記録が塞がった時に、書いた人に何が返るかを試しの場で見る。"""
import os, re, socket, sqlite3, subprocess, sys, threading, time
from urllib.parse import urlencode

道具, 作業 = sys.argv[1], sys.argv[2]
os.makedirs(作業, exist_ok=True)
記録 = os.path.join(作業, "塞ぐ.db")
for 名 in (記録, 記録 + "-wal", 記録 + "-shm"):
    if os.path.exists(名):
        os.remove(名)
港 = 8775
エラー = os.path.join(作業, "塞ぐ.txt")
起動 = "import sys;sys.path.insert(0,sys.argv[1]);import 場;場.場を作る(sys.argv[2],sys.argv[3],int(sys.argv[4])).serve_forever()"
場 = subprocess.Popen([sys.executable, "-B", "-c", 起動, 道具, 記録, "x", str(港)], stderr=open(エラー, "w"))
for _ in range(50):
    try:
        socket.create_connection(("127.0.0.1", 港), timeout=1).close()
        break
    except OSError:
        time.sleep(0.1)


def 書く(本文, 待つ=25):
    本体 = urlencode({"honbun": 本文}).encode()
    s = socket.create_connection(("127.0.0.1", 港), timeout=待つ)
    s.sendall(b"POST /ita/sonota/kaku HTTP/1.1\r\nHost: t\r\nConnection: close\r\nCookie: makeinu_kagi=" + os.urandom(16).hex().encode() + b"\r\nContent-Type: application/x-www-form-urlencoded\r\nContent-Length: " + str(len(本体)).encode() + b"\r\n\r\n" + 本体)
    b = b""
    始 = time.time()
    try:
        while True:
            c = s.recv(65536)
            if not c:
                break
            b += c
    except socket.timeout:
        return "待ち切れ", round(time.time() - 始, 1)
    m = re.match(rb"HTTP/\d\.\d (\d+)", b)
    return (int(m.group(1)) if m else "何も返らず切れた"), round(time.time() - 始, 1)


塞ぐ = sqlite3.connect(記録, timeout=1, isolation_level=None)
塞ぐ.execute("BEGIN IMMEDIATE")
print("11秒より長く塞がった時の書き込み →", 書く("塞がっている時の話"))
塞ぐ.execute("ROLLBACK")
print("塞がりが解けた後の書き込み →", 書く("解けた後の話"))
読む = sqlite3.connect(記録)
print("置かれた書き込み", [r[0] for r in 読む.execute("select 本文 from 書き込み")])
場.terminate()
print("場の誤り", re.findall(r"^(\w+(?:\.\w+)*Error[^\n]{0,60})", open(エラー, encoding="utf-8", errors="replace").read(), re.M))
