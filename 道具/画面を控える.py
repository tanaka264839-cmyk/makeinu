"""整える前後で画面の文字が1字も変わらないかを比べるため、決まった手順で全画面を書き出す。"""
import http.client, os, re, sys, tempfile, threading
from datetime import datetime, timedelta
from urllib.parse import urlencode, quote
道具, 出す先 = sys.argv[1], sys.argv[2]
sys.path.insert(0, 道具)
import 場, 台帳
mods = [場, 台帳]
for 名 in ("時計", "画面"):
    if 名 in sys.modules or os.path.exists(os.path.join(道具, 名 + ".py")):
        mods.append(__import__(名))
時 = [datetime.fromisoformat("2026-10-23T20:00:00+09:00")]
for m in mods:
    if hasattr(m, "いま"):
        setattr(m, "いま", lambda: 時[0])
置き場 = tempfile.mkdtemp()
s = 場.場を作る(os.path.join(置き場, "x.db"), "aiko", 0)
threading.Thread(target=s.serve_forever, daemon=True).start()
鍵 = {"A": "a" * 32, "B": "b" * 32, "C": "c" * 32}
os.makedirs(出す先, exist_ok=True)
n = [0]
札 = {}  # 見回りに入った人の札（クッキー）
def 頼む(動き, 道, 中身=None, 人="A", 控える=True):
    if 控える:
        時[0] += timedelta(seconds=30)
    c = http.client.HTTPConnection("127.0.0.1", s.server_port)
    h = {"Cookie": f"makeinu_kagi={鍵[人]}" + (f"; makeinu_mimawari={札[人]}" if 人 in 札 else "")}
    b = None
    if 中身 is not None:
        b = urlencode(中身); h["Content-Type"] = "application/x-www-form-urlencoded"
    c.request(動き, 道, b, h)
    r = c.getresponse(); 文 = r.read().decode()
    for 渡された in r.msg.get_all("Set-Cookie") or []:
        if 渡された.startswith("makeinu_mimawari="):
            札[人] = 渡された.split(";")[0].split("=", 1)[1]
    if not 控える:
        return
    n[0] += 1
    文 = re.sub(r'name="aifuda" value="[0-9a-f]+"', 'name="aifuda" value="…"', 文)  # 合い札は入るたびに変わるので、比べられるようにそろえる
    with open(os.path.join(出す先, f"{n[0]:03d}.txt"), "w", encoding="utf-8") as f:
        f.write(f"{動き} {道} {人} -> {r.status} {r.getheader('Location')}\n{文}")
def 見回りに入る(人):
    # 合言葉は入口の欄から送る。控えには数えず時計も進めない（前の作りの手順と、番号と時刻をそろえて比べるため）
    頼む("POST", "/kanri/hairu", {"aikotoba": "aiko"}, 人, 控える=False)
頼む("POST", "/nanori", {"nanori": "バツイチ"}, "A")
頼む("POST", "/nanori", {"nanori": "ﾊﾞﾂｲﾁ"}, "B")
頼む("POST", "/ita/kazoku/kaku", {"honbun": "離婚した\n3年たつ"}, "B")
頼む("POST", "/henji/1", {"honbun": "ひとりも悪くない"}, "A")
頼む("POST", "/wakaru/2", {}, "C")
頼む("POST", "/wakaru/1", {}, "A")
頼む("POST", "/kachi/kaku", {"honbun": "布団から出た"}, "A")
頼む("POST", "/sonogo/kaku", {"ano": "受験に落ちた", "honbun": "今は楽しい"}, "B")
頼む("POST", "/mouikkai/kaku", {"honbun": "面接を受ける"}, "A")
頼む("POST", "/wakaru/6", {}, "B")
頼む("POST", "/musubu/6", {"musubi": "yatta"}, "A")
頼む("POST", "/hitori/kaku", {"honbun": "疲れた"}, "C")
頼む("POST", "/ita/shigoto/kaku", {"honbun": "上司は死ね"}, "C")
頼む("POST", "/ita/shigoto/kaku", {"honbun": "消えたい"}, "C")
頼む("POST", "/sonogo/kaku", {"ano": "", "honbun": "x"}, "A")
# 部屋を開けるのは書き始めて1日たったブラウザからだけなので、Aの最初の書き込み（#2 の返事）を前の日に書いたことにする
s.RequestHandlerClass.台帳.つなぎ.execute("UPDATE 書き込み SET 書いた時刻 = '2026-10-22T20:00:00+09:00' WHERE 番号 = 2")
頼む("POST", "/heya/hiraku", {"bangou": "1"}, "A")
頼む("POST", "/heya/1/kaku", {"honbun": "はじめまして"}, "A")
頼む("POST", "/heya/1/kaku", {"honbun": "死ね"}, "B")
時[0] = datetime.fromisoformat("2026-10-23T23:30:00+09:00")
頼む("POST", "/yoru/kaku", {"honbun": "眠れない"}, "A")
頼む("POST", "/yoru/kaku", {"honbun": "自分も"}, "B")
見回りに入る("A")  # B と C は入らずに、見回りの入口を見る
for 人 in "ABC":
    for 道 in ["/", "/ita/kazoku", "/ita/shigoto", "/ita/shigoto?sotto=1", "/kachi", "/sonogo", "/mouikkai", "/yoru", "/hitori", "/heya", "/heya/1", "/nanori?n=" + quote("バツイチ"), "/kanri", "/nai"]:
        頼む("GET", 道, None, 人)
頼む("POST", "/heya/1/tojiru", {}, "B")
頼む("POST", "/heya/1/kaku", {"honbun": "まだ"}, "A")
頼む("GET", "/heya", None, "A")
時[0] = datetime.fromisoformat("2026-10-24T12:00:00+09:00")
頼む("GET", "/yoru", None, "A")
頼む("POST", "/yoru/kaku", {"honbun": "昼"}, "A")
見回りに入る("A")  # 前の晩の札は3時間で切れている
頼む("POST", "/kanri/kesu", {"aifuda": s.RequestHandlerClass.見回りの札.合い札(札["A"]), "bangou": "1"}, "A")
頼む("GET", "/ita/kazoku", None, "A")
頼む("GET", "/kanri/matome?bangou=2", None, "A")  # 見回りの「このブラウザの書き込み」（A が書いた物の一覧）
if os.path.exists(os.path.join(道具, "聞き役.py")):
    # 聞き役（AI）：人の返事が無いまま10分たった板の書き込みに返す。AIの代わりに決まった文を返す（前の作りには無いので最後に足す）
    import 聞き役
    頼む("POST", "/ita/okane/kaku", {"honbun": "貯金が尽きた"}, "C")
    時[0] += timedelta(minutes=11)
    聞き役.ひと回り(s.RequestHandlerClass.台帳, lambda 本文: "尽きるまで、よく持たせたね。")
    for 道 in ["/ita/okane", "/", "/kanri"]:
        頼む("GET", 道, None, "A" if 道 == "/kanri" else "B")
print("書き出した", n[0])
