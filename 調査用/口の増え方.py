"""負け犬の癒し：頼みの数でファイルの口とメモリがどう増えるかを、試しの場で測る。使い方：python3 kuchi_test.py <道具> <作業> <閉じる直しを当てるか 0/1> <同時> <1人の回数>"""
import os, re, socket, subprocess, sys, threading, time
from collections import Counter

道具, 作業, 直し, 同時, 回数 = sys.argv[1], sys.argv[2], sys.argv[3] == "1", int(sys.argv[4]), int(sys.argv[5])
os.makedirs(作業, exist_ok=True)
記録 = os.path.join(作業, f"口{int(直し)}.db")
for 名 in (記録, 記録 + "-wal", 記録 + "-shm"):
    if os.path.exists(名):
        os.remove(名)
港 = 8772 + int(直し)
当てる = "o=場.場の受け口.finish\ndef f(self):\n    o(self)\n    self.台帳.閉じる()\n場.場の受け口.finish=f\n" if 直し else ""
起動 = "import sys;sys.path.insert(0,sys.argv[1]);import 場\n" + 当てる + "場.場を作る(sys.argv[2],sys.argv[3],int(sys.argv[4])).serve_forever()"
エラー = os.path.join(作業, f"口{int(直し)}.txt")
# 本物の場と同じ上限（systemd の既定 1024）で動かす
場 = subprocess.Popen(["bash", "-c", 'ulimit -n 1024; exec "$@"', "_", sys.executable, "-B", "-c", 起動, 道具, 記録, "x", str(港)], stderr=open(エラー, "w"))
for _ in range(50):
    try:
        socket.create_connection(("127.0.0.1", 港), timeout=1).close()
        break
    except OSError:
        time.sleep(0.1)


def 見る():
    with open(f"/proc/{場.pid}/status") as f:
        t = f.read()
    return len(os.listdir(f"/proc/{場.pid}/fd")), int(re.search(r"VmRSS:\s+(\d+)", t).group(1)) // 1024


結果 = Counter()
最大 = [0, 0]
止める = threading.Event()


def 見張り():
    while not 止める.is_set():
        try:
            fd, rss = 見る()
            最大[0] = max(最大[0], fd)
            最大[1] = max(最大[1], rss)
        except Exception:
            pass
        time.sleep(0.05)


def 流す():
    for _ in range(回数):
        try:
            s = socket.create_connection(("127.0.0.1", 港), timeout=30)
            s.sendall(b"GET /kachi HTTP/1.1\r\nHost: t\r\nConnection: close\r\nCookie: makeinu_kagi=" + b"e" * 32 + b"\r\n\r\n")
            b = b""
            while True:
                c = s.recv(65536)
                if not c:
                    break
                b += c
            s.close()
            m = re.match(rb"HTTP/\d\.\d (\d+)", b)
            結果[int(m.group(1)) if m else "切れた"] += 1
        except Exception as e:
            結果[type(e).__name__] += 1


threading.Thread(target=見張り, daemon=True).start()
始 = time.time()
糸 = [threading.Thread(target=流す) for _ in range(同時)]
[t.start() for t in 糸]
[t.join() for t in 糸]
秒 = time.time() - 始
time.sleep(1)
止める.set()
fd, rss = 見る()
場.terminate()
try:
    場.wait(timeout=5)
except Exception:
    場.kill()
誤り = Counter(re.findall(r"^(\w+(?:\.\w+)*Error[^\n]{0,60})", open(エラー, encoding="utf-8", errors="replace").read(), re.M))
print(f"閉じる直し{'あり' if 直し else 'なし'}：{同時}人×{回数}回 {秒:.0f}秒 → 結果{dict(結果)}／口 最大{最大[0]}・終わり{fd}／メモリ 最大{最大[1]}MB・終わり{rss}MB／場の誤り{dict(誤り.most_common(4))}")
