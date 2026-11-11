"""負け犬の癒し：試しの場に普通でない形をぶつける（本物の記録には触らない）。使い方：python3 sougatari.py <道具の場所> <作業の場所>"""
import http.client, json, os, re, socket, sqlite3, subprocess, sys, threading, time
from collections import Counter
from urllib.parse import quote, urlencode

道具, 作業 = sys.argv[1], sys.argv[2]
os.makedirs(作業, exist_ok=True)
sys.path.insert(0, 道具)
import 決まり
from 台帳 import 台帳

港 = 8771
記録 = os.path.join(作業, "試し.db")
for 名 in (記録, 記録 + "-wal", 記録 + "-shm"):
    if os.path.exists(名):
        os.remove(名)
エラー記録 = os.path.join(作業, "場の記録.txt")
起動 = "import sys;sys.path.insert(0,sys.argv[1]);import 場;場.場を作る(sys.argv[2],sys.argv[3],int(sys.argv[4])).serve_forever()"
場 = subprocess.Popen([sys.executable, "-B", "-c", 起動, 道具, 記録, "mimawari-test", str(港)], stderr=open(エラー記録, "w"))
for _ in range(50):
    try:
        socket.create_connection(("127.0.0.1", 港), timeout=1).close()
        break
    except OSError:
        time.sleep(0.1)


def 生で(行, 見出し=(), 本体=b"", 待つ=5):
    """生のバイト列で頼む。(状態, 見出しと本文) か ("切れた", "")。"""
    s = socket.create_connection(("127.0.0.1", 港), timeout=待つ)
    s.sendall(行 + b"\r\n" + b"".join(h + b"\r\n" for h in 見出し) + b"\r\n" + 本体)
    b = b""
    try:
        while True:
            c = s.recv(65536)
            if not c:
                break
            b += c
    except socket.timeout:
        return "待ち切れ", ""
    finally:
        s.close()
    if not b:
        return "切れた", ""
    m = re.match(rb"HTTP/\d\.\d (\d+)", b)
    return int(m.group(1)) if m else "形が変", b.decode("utf-8", "replace")


class 人:
    def __init__(self, 鍵=None):
        self.鍵 = 鍵 or os.urandom(16).hex()

    def 頼む(self, 動き, 道, 中身=None, 見出し=None):
        h = [b"Host: tameshi", b"Connection: close", f"Cookie: makeinu_kagi={self.鍵}".encode()]
        for k, v in (見出し or {}).items():
            h.append(f"{k}: {v}".encode())
        本体 = b""
        if 中身 is not None:
            本体 = urlencode(中身).encode()
            h += [b"Content-Type: application/x-www-form-urlencoded", f"Content-Length: {len(本体)}".encode()]
        return 生で(f"{動き} {道} HTTP/1.1".encode(), h, 本体)


def 札(結果):
    return 結果[0]


def 例外の数():
    return Counter(re.findall(r"^(\w+(?:\.\w+)*Error|\w+Exception|\w*Error)\b.*$", open(エラー記録, encoding="utf-8", errors="replace").read(), re.M))


結果 = {}
A = 人()

# 1 動き
結果["1 動き"] = {m: 札(生で(f"{m} / HTTP/1.1".encode(), [b"Host: t", b"Connection: close"])) for m in ("GET", "HEAD", "OPTIONS", "PUT", "DELETE", "TRACE")}

# 2 クッキーの形
クッキーたち = {"区切りの字": "a/b=1", "和字の名前": "名前=1", "予約の語": "path=1", "角かっこ": "a[b]=1", "空": "", "カンマ": "a,b=1",
              "鍵が和字32字": "makeinu_kagi=" + "あ" * 32, "鍵が引用符": 'makeinu_kagi="x"', "とても長い": "x=" + "y" * 7000, "セミコロンだけ": ";;;;"}
結果["2 クッキー"] = {名: 札(生で(b"GET / HTTP/1.1", [b"Host: t", b"Connection: close", ("Cookie: " + 値).encode("utf-8")])) for 名, 値 in クッキーたち.items()}

# 3 道の数字の形
道たち = {"²（生のB2）": b"/heya/\xb2", "大きい25桁": ("/heya/" + "9" * 25).encode(), "5000桁": ("/heya/" + "9" * 5000).encode(), "マイナス": b"/heya/-1",
         "ヌル": b"/ita/shigoto%00", "上へ": b"/../../etc/passwd", "二重の/": b"//ita//shigoto", "知らない板": b"/ita/nai", "%形の和字": "/ita/" .encode() + quote("仕事").encode(),
         "長い道": b"/" + b"a" * 7000}
結果["3 GETの道"] = {名: 札(生で(b"GET " + 道 + b" HTTP/1.1", [b"Host: t", b"Connection: close"])) for 名, 道 in 道たち.items()}
問いたち = {"知らせ²": "/shiraseru?bangou=%C2%B2", "知らせ①": "/shiraseru?bangou=%E2%91%A0", "知らせ大": "/shiraseru?bangou=" + "9" * 25, "知らせ5000桁": "/shiraseru?bangou=" + "9" * 5000,
           "そっと": "/?sotto=<script>", "名乗り無効": "/nanori?n=%FF%FE", "名乗りタグ": "/nanori?n=%3Cscript%3Ealert(1)%3C/script%3E", "名乗り長": "/nanori?n=" + "a" * 5000}
out = {}
for 名, 道 in 問いたち.items():
    r = 生で(f"GET {道} HTTP/1.1".encode(), [b"Host: t", b"Connection: close"])
    out[名] = r[0] if "<script>" not in r[1] else f"{r[0]} ★生のタグ"
結果["3 問い"] = out

# 4 POST の形
投げ = {"知らせ番号²": ("/shiraseru", {"bangou": "²", "honbun": "x"}), "知らせ番号大": ("/shiraseru", {"bangou": "9" * 25, "honbun": "x"}), "知らせ番号5000桁": ("/shiraseru", {"bangou": "9" * 5000, "honbun": "x"}),
       "部屋番号²": ("/heya/hiraku", {"bangou": "²"}), "部屋番号大": ("/heya/hiraku", {"bangou": "9" * 25}), "返事大": ("/henji/" + "9" * 25, {"honbun": "x"}), "わかる大": ("/wakaru/" + "9" * 25, {}),
       "結び大": ("/musubu/" + "9" * 25, {"musubi": "yatta"}), "部屋に書く大": ("/heya/" + "9" * 25 + "/kaku", {"honbun": "x"}), "知らない道": ("/nai", {"a": "b"})}
結果["4 POSTの番号"] = {名: 札(人().頼む("POST", 道, 中身)) for 名, (道, 中身) in 投げ.items()}
結果["4 送信の長さ"] = {名: 札(生で(b"POST /nanori HTTP/1.1", [b"Host: t", b"Connection: close", ("Content-Length: " + 値).encode()], b"nanori=a"))
                     for 名, 値 in {"字": "abc", "マイナス": "-1", "空": "", "大きい": "99999999999"}.items() if 名 != "大きい"}

# 5 本文の形（置けてしまうか）
形たち = {"ゼロ幅だけ": "​​​", "BOMだけ": "﻿", "ハングルの空き字": "ㅤㅤ", "点字の空き": "⠀⠀", "結合文字だけ": "́́", "右から左": "abc‮def", "行区切り": "a b", "ヌル入り": "a\x00b",
         "タグ": "<script>alert(1)</script>", "1000字": "あ" * 1000, "1001字": "あ" * 1001, "絵文字4000": "😀" * 1000}
out = {}
for 名, 文 in 形たち.items():
    B = 人()
    r = B.頼む("POST", "/ita/sonota/kaku", {"honbun": 文})
    out[名] = "置けた" if r[0] == 303 else f"断った{r[0]}"
結果["5 本文の形"] = out
見る = 人().頼む("GET", "/ita/sonota")
結果["5 タグがそのまま出ないか"] = "<script>alert(1)" not in 見る[1]

# 6 止める言葉をすり抜けるか（語は出さない）
語たち = [行.strip() for 行 in open(os.path.join(道具, "中身", "止める言葉.txt"), encoding="utf-8") if 行.strip() and not 行.startswith("#")]
語 = next(w for w in 語たち if len(w) >= 2)
すり抜け = {"そのまま": 語, "ゼロ幅を挟む": "​".join(語), "幅なし結合子": "‍".join(語), "BOMを挟む": "﻿".join(語), "異体字セレクタ": "️".join(語), "ソフトハイフン": "­".join(語), "空白を挟む": " ".join(語), "記号を挟む": "・".join(語), "点を挟む": ".".join(語)}
out = {}
for 名, 文 in すり抜け.items():
    r = 人().頼む("POST", "/ita/sonota/kaku", {"honbun": "試し" + 文})
    out[名] = "すり抜けた" if r[0] == 303 else "止めた"
結果["6 止める言葉"] = out

# 7 聞き役のなりすまし
なりすまし = {"そのまま": "聞き役（AI）", "ゼロ幅": "聞​き役（AI）", "別の字": "聴き役（AI）", "ひらがな": "ききやく（AI）", "全角": "聞き役（ＡＩ）", "空白": "聞 き 役（AI）"}
out = {}
for 名, 文 in なりすまし.items():
    r = 人().頼む("POST", "/nanori", {"nanori": 文})
    out[名] = "名乗れた" if r[0] == 303 else "断った"
結果["7 聞き役の名乗り"] = out

# 8 ほかのサイトからの送信
B = 人()
r = 生で(b"POST /ita/sonota/kaku HTTP/1.1", [b"Host: t", b"Connection: close", b"Origin: https://evil.example", b"Sec-Fetch-Site: cross-site", b"Content-Type: application/x-www-form-urlencoded", b"Content-Length: 26"], b"honbun=" + b"x" * 19)
結果["8 ほかのサイトから書く"] = "置けた（来た人の番地で記録に入る）" if r[0] == 303 else f"断った{r[0]}"

# 9 消した書き込みへの返事が残るか
帳 = 台帳(記録)
親 = 帳.書く("sonota", "消される親", "a" * 32, None, None, None)
C = 人("c" * 32)
C.頼む("POST", "/nanori", {"nanori": "試しの人"})
C.頼む("POST", f"/henji/{親}", {"honbun": "親を引用した返事"})
帳.消す(親)
頁 = 人().頼む("GET", "/nanori?n=" + quote("試しの人"))
結果["9 親を消した後、名乗りの頁に返事が残るか"] = "残る" if "親を引用した返事" in 頁[1] else "出ない"
結果["9 親を消した後、はじめの画面に返事が出るか"] = "出る" if "親を引用した返事" in 人().頼む("GET", "/")[1] else "出ない"

# 10 小部屋の番号が漏れるか
部屋 = 帳.小部屋を開く("試し", "a" * 32, "b" * 32)
部屋の話 = 帳.書く(決まり.小部屋の置き場(部屋), "2人だけの話", "a" * 32)
D = 人()
r1 = 生で(b"POST /wakaru/%d HTTP/1.1" % 部屋の話, [b"Host: t", b"Connection: close", b"Content-Length: 0"])
loc = re.search(r"Location: (\S+)", r1[1])
r2 = D.頼む("GET", f"/shiraseru?bangou={部屋の話}")
結果["10 ほかの人に小部屋の場所が出るか"] = {"わかるの移り先": loc.group(1) if loc else "なし", "知らせる欄に番号": f"#{部屋の話}" in r2[1], "本文": "2人だけの話" in r2[1]}

# 11 量
for i in range(260):
    帳.書く("okane", f"量の話{i}", "d" * 32)
板 = 人().頼む("GET", "/ita/okane")[1]
入 = 人().頼む("POST", "/kanri/hairu", {"aikotoba": "mimawari-test"})
札字 = re.search(r"makeinu_mimawari=([0-9a-f]+)", 入[1]).group(1)
s = socket.create_connection(("127.0.0.1", 港))
s.sendall(f"GET /kanri HTTP/1.1\r\nHost: t\r\nConnection: close\r\nCookie: makeinu_mimawari={札字}\r\n\r\n".encode())
b = b""
while True:
    c = s.recv(65536)
    if not c:
        break
    b += c
見回り = b.decode("utf-8", "replace")
結果["11 量"] = {"板に出る数(260書いた)": 板.count('class="書き込み"'), "前の話へ行く道": ("前へ" in 板 or "もっと" in 板 or "page=" in 板), "見回りに出る数": len(re.findall(r'id="m\d+"', 見回り)), "見回りの前へ": ("前へ" in 見回り or "もっと" in 見回り), "古い話の場所": 人().頼む("GET", "/ita/okane#k1")[1].count("量の話0<")}

# 12 速さと残り物
def 住人():
    with open(f"/proc/{場.pid}/status") as f:
        t = f.read()
    return {"糸": int(re.search(r"Threads:\s+(\d+)", t).group(1)), "RSS_MB": int(re.search(r"VmRSS:\s+(\d+)", t).group(1)) // 1024, "fd": len(os.listdir(f"/proc/{場.pid}/fd"))}


前 = 住人()
失敗 = Counter()
時間たち = []


def 流す(回):
    for i in range(回):
        t = time.time()
        try:
            r = 生で(b"GET /ita/okane HTTP/1.1", [b"Host: t", b"Connection: close", b"Cookie: makeinu_kagi=" + b"e" * 32], 待つ=30)
            失敗[r[0]] += 1
        except Exception as e:
            失敗[type(e).__name__] += 1
        時間たち.append(time.time() - t)


始 = time.time()
糸たち = [threading.Thread(target=流す, args=(100,)) for _ in range(30)]
[t.start() for t in 糸たち]
[t.join() for t in 糸たち]
時間たち.sort()
time.sleep(2)
結果["12 同時30人×100回"] = {"結果": dict(失敗), "秒": round(time.time() - 始 - 2, 1), "中央値ms": round(時間たち[len(時間たち) // 2] * 1000), "最大ms": round(時間たち[-1] * 1000), "前": 前, "後": 住人()}

# 13 記録が塞がっている時の書き込み
塞ぐ = sqlite3.connect(記録, timeout=1, isolation_level=None)
塞ぐ.execute("BEGIN IMMEDIATE")
t = time.time()
r = 人().頼む("POST", "/ita/sonota/kaku", {"honbun": "塞がっている時の話"})
秒 = round(time.time() - t, 1)
塞ぐ.execute("ROLLBACK")
塞ぐ.close()
結果["13 記録が12秒以上塞がった時"] = {"返り": r[0], "秒": 秒}

# 14 控えから戻せるか
控え = 帳.控えを取る(os.path.join(作業, "控え"))
戻し先 = os.path.join(作業, "戻し先.db")
open(戻し先, "wb").write(open(控え, "rb").read())
戻し = 台帳(戻し先)
件数 = 戻し.つなぎ.execute("select count(*) from 書き込み").fetchone()[0]
新番号 = 戻し.書く("sonota", "戻した後の話", "f" * 32)
結果["14 控えから戻す"] = {"書き込み": 件数, "書いた人の記録": 戻し.つなぎ.execute("select count(*) from 書いた人の記録").fetchone()[0], "戻した後に書ける番号": 新番号, "本物の最後の番号": 帳.つなぎ.execute("select max(番号) from 書き込み").fetchone()[0]}

# 15 書く道のうち数えの上限が無い物（番地を偽らず、じかに。loopback は数えないので受け口越しの形で見る）
上限 = {}
for 名, 道, 中身 in (("わかる", f"/wakaru/{親 + 1}", {}), ("名乗り", "/nanori", {"nanori": "数の試し"}), ("小部屋を受けない", "/heya/ukenai", {})):
    回 = Counter()
    for i in range(30):
        r = 生で(f"POST {道} HTTP/1.1".encode(), [b"Host: t", b"Connection: close", b"X-Real-IP: 203.0.113.50", b"X-Real-Port: 1000", b"Content-Type: application/x-www-form-urlencoded", f"Content-Length: {len(urlencode(中身))}".encode()], urlencode(中身).encode())
        回[r[0]] += 1
    上限[名] = dict(回)
結果["15 同じ番地から30回（クッキーなし）"] = 上限
つなぎ = sqlite3.connect(記録)
結果["15 増えた行"] = {"名乗り": つなぎ.execute("select count(*) from 名乗り").fetchone()[0], "小部屋を受けない": つなぎ.execute("select count(*) from 小部屋を受けない").fetchone()[0], "わかる": つなぎ.execute("select count(*) from わかる").fetchone()[0]}

場.terminate()
場.wait(timeout=10)
結果["場の例外"] = dict(例外の数())
print(json.dumps(結果, ensure_ascii=False, indent=0))
