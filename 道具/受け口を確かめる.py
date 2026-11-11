"""負け犬の癒し：受け口（nginx）を通した時に、場へ何が届くかをサーバーの中で確かめる（本物の記録には触れない）。

使い方（サーバーで ubuntu として、道具の写しの中から）：python3 受け口を確かめる.py [本物の道具の場所。既定 /srv/makeinu/道具]
  1. 本物の入口（https・http・名前の無い頼み）を、書き込まずに確かめる
  2. 試しの場を 127.0.0.1:8766 に、空の試しの記録で立てる
  3. 本物と同じ受け口の決まり（snippets/makeinu-ukeguchi.conf）で試しの場へ渡す試しの入口を、このサーバーの番地の 8081 に足す
     （サーバーの壁は 8081 を外から通さないので、外からは届かない。始める前に壁を確かめる）
  4. このサーバーの番地から試しの入口へ頼み、場に届いた物と、受け口の記録を見る
  5. 試しの入口を外し、試しの場を止め、試しの記録を消す（途中で落ちても必ず）
すべて合っていれば 0、どれかが違えば 1 で終わる。テスト.py と同じく、サーバーの道具には置かない。
"""
import http.client
import os
import re
import shutil
import socket
import sqlite3
import ssl
import subprocess
import sys
import tempfile
import time
from urllib.parse import urlencode

本物の名前 = "makeinu.net"
この番地 = "203.0.113.10"  # 場が「外から来た人」と見る番地として、このサーバーの番地から頼む
試しの入口の港 = 8081
試しの場の港 = 8766
試しの合言葉 = "ukeguchi-tameshi"
試しの入口 = "/etc/nginx/sites-enabled/makeinu-tameshi"
受け口の記録の場所 = "/var/log/nginx"
にせの番地 = "203.0.113.99"
守りの見出し = {"X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY", "Referrer-Policy": "no-referrer",
               "X-Robots-Tag": "noindex, nofollow", "Server": "nginx"}

結果 = []


def 見る(名前, よいか, 見たもの=""):
    結果.append((名前, bool(よいか), str(見たもの)[:300]))


def sudo(*命令, 入力=None):
    return subprocess.run(["sudo", "-n", *命令], input=入力, capture_output=True, text=True, timeout=60)


def 頼む(動き, 道, 中身=None, 見出し=None, 港=0, 本体=None, 相手=(この番地, 試しの入口の港)):
    つなぎ = http.client.HTTPConnection(*相手, timeout=30, source_address=(この番地, 港) if 相手[0] == この番地 else None)
    見出し = dict(見出し or {})
    if 中身 is not None:
        本体 = urlencode(中身).encode()
    if 本体 is not None:
        見出し["Content-Type"] = "application/x-www-form-urlencoded"
    try:
        つなぎ.request(動き, 道, 本体, 見出し)
        返り = つなぎ.getresponse()
        return 返り, 返り.read().decode("utf-8", "replace")
    finally:
        つなぎ.close()


def 聞いている所():
    return subprocess.run(["ss", "-ltnH"], capture_output=True, text=True).stdout


def 待つ(できたか, 秒=10):
    いつまで = time.time() + 秒
    while time.time() < いつまで:
        if できたか():
            return True
        time.sleep(0.2)
    return False


def 受け口の記録():
    """受け口の記録のファイルごとの大きさと、番地が出てくる数。"""
    名前たち = sudo("ls", 受け口の記録の場所).stdout.split()
    大きさ = {名前: sudo("stat", "-c", "%s", os.path.join(受け口の記録の場所, 名前)).stdout.strip() for 名前 in 名前たち}
    番地の数 = sudo("grep", "-rc", "-e", この番地, "-e", にせの番地, 受け口の記録の場所).stdout
    return 大きさ, sum(int(行.rsplit(":", 1)[1]) for 行 in 番地の数.split() if ":" in 行)


def 試しの場で確かめる(記録の場所):
    # 来た人の番地と港。来た人が付けてきた同じ名前の見出しは、受け口が上書きする
    返り = None
    for 港 in range(45678, 45700):
        try:
            返り, _ = 頼む("POST", "/ita/shigoto/kaku", {"honbun": "受け口の確かめ"}, {"X-Real-IP": にせの番地, "X-Real-Port": "1"}, 港=港)
            break
        except OSError:
            continue
    つなぎ = sqlite3.connect(記録の場所)
    書いた人 = つなぎ.execute("SELECT 番地, 港 FROM 書いた人の記録").fetchall()
    つなぎ.close()
    見る("来た人の番地と港が書いた人の記録に入り、来た人が付けた見出しは使われない", 返り and 返り.status == 303 and 書いた人 == [(この番地, 港)], f"{返り and 返り.status} {書いた人}")

    # 荒らしへの備え：同じ番地から1分に10件まで（クッキーを受けない書き方でも）
    状態たち = [頼む("POST", "/ita/shigoto/kaku", {"honbun": f"受け口の確かめ{i}"})[0].status for i in range(9)]
    返り, 文 = 頼む("POST", "/ita/shigoto/kaku", {"honbun": "11件目"})
    見る("同じ番地から1分に11件目は、間をあけてもらう", 状態たち == [303] * 9 and 返り.status == 400 and "少し間をあけて" in 文, f"{状態たち} → {返り.status}")

    # 見回りの合言葉の間違いも、来た人の番地で数える
    状態たち = [頼む("POST", "/kanri/hairu", {"aikotoba": "chigau"})[0].status for _ in range(5)]
    返り, _ = 頼む("POST", "/kanri/hairu", {"aikotoba": 試しの合言葉})
    見る("同じ番地から合言葉を5回間違えると、6回目は待ってもらう", 状態たち == [403] * 5 and 返り.status == 429, f"{状態たち} → {返り.status}")

    # 場が1回に読む大きさを超える送信は、受け口で断る
    返り, _ = 頼む("POST", "/shiraseru", 本体=b"honbun=" + b"a" * (64 * 1024))
    ちょうど, _ = 頼む("POST", "/shiraseru", 本体=b"honbun=" + b"a" * (64 * 1024 - len(b"honbun=")))
    見る("64KB を超える送信は受け口で断り、64KB ちょうどは場へ渡す", 返り.status == 413 and ちょうど.status != 413, f"{返り.status} / {ちょうど.status}")

    # 守りの見出しと、受け口の版を見せないこと
    返り, _ = 頼む("GET", "/kimari")
    見出し = {名前: 返り.getheader(名前) for 名前 in 守りの見出し}
    見る("守りの見出しが付き、受け口の版は見せない", 見出し == 守りの見出し, 見出し)

    # 同じ番地から同時に受けるのは20まで（送り終えないまま止まったつなぎで確かめる）
    つなぎたち = []
    try:
        for _ in range(21):
            s = socket.create_connection((この番地, 試しの入口の港), timeout=10, source_address=(この番地, 0))
            s.sendall(b"POST /shiraseru HTTP/1.1\r\nHost: tameshi\r\nContent-Type: application/x-www-form-urlencoded\r\nContent-Length: 1000\r\n\r\n")
            つなぎたち.append(s)
            time.sleep(0.05)
        つなぎたち[-1].settimeout(5)
        try:
            最後の返り = つなぎたち[-1].recv(100)
        except socket.timeout:
            最後の返り = "(返りなし)".encode()
        見る("同じ番地から同時に21本目のつなぎは断る", 最後の返り.startswith(b"HTTP/1.1 503"), 最後の返り[:40])
    finally:
        for s in つなぎたち:
            s.close()

    全部 = [行.split()[3] for 行 in 聞いている所().splitlines()]
    聞く = [所 for 所 in 全部 if 所.endswith((f":{試しの入口の港}", ":80", ":443"))]
    見る("受け口は IPv4 だけで聞き、80 と 443 で聞き、サーバーの中だけの 8080 は残っていない",
         all(not 所.startswith("[") for 所 in 聞く) and {"0.0.0.0:80", "0.0.0.0:443"} <= set(全部) and not any(所.endswith(":8080") for 所 in 全部), 全部)


def https_で頼む(動き, 道):
    つなぎ = http.client.HTTPSConnection(本物の名前, 443, timeout=30, context=ssl.create_default_context())
    try:
        つなぎ.request(動き, 道)
        返り = つなぎ.getresponse()
        return 返り, 返り.read().decode("utf-8", "replace")
    finally:
        つなぎ.close()


def 本物の入口を確かめる():
    """読むだけ。本物の記録には何も足さない。"""
    # 証明書が名前と合わなければ、ここで落ちる
    返り, 文 = https_で頼む("GET", "/kimari")
    見出し = {名前: 返り.getheader(名前) for 名前 in 守りの見出し}
    見る("https で本物の場の画面が開き、証明書が名前と合う", 返り.status == 200 and "利用の決まり" in 文, 返り.status)
    見る("本物の入口にも守りの見出しが付き、https だけで来るよう知らせる",
         見出し == 守りの見出し and 返り.getheader("Strict-Transport-Security") == "max-age=31536000", (見出し, 返り.getheader("Strict-Transport-Security")))

    # 検索に出すのは、はじめの画面だけ
    はじめ, 文 = https_で頼む("GET", "/")
    ほかの見出し = {名前: 値 for 名前, 値 in 守りの見出し.items() if 名前 != "X-Robots-Tag"}
    見る("はじめの画面だけ検索に出してよく、ほかの守りの見出しは付いたまま",
         はじめ.status == 200 and "<title>負け犬の癒し｜" in 文 and '<meta name="description" content="' in 文
         and はじめ.getheader("X-Robots-Tag") is None
         and {名前: はじめ.getheader(名前) for 名前 in ほかの見出し} == ほかの見出し, はじめ.getheaders())
    道たち = {道: https_で頼む("GET", 道)[0].getheader("X-Robots-Tag") for 道 in ("/kojin", "/ita/shigoto", "/kachi", "/kanri", "/nai")}
    見る("はじめの画面のほかは、検索に出さない", set(道たち.values()) == {"noindex, nofollow"}, 道たち)

    つなぎ = http.client.HTTPConnection(本物の名前, 80, timeout=30)
    つなぎ.request("GET", "/kimari?x=1")
    移る = つなぎ.getresponse()
    移る先 = 移る.getheader("Location")
    移る.read()
    つなぎ.request("GET", "/.well-known/acme-challenge/nai")
    確かめの道 = つなぎ.getresponse()
    確かめの道.read()
    つなぎ.close()
    見る("http は https の同じ道へ移すだけで、証明書の確かめの道は場へ渡さない",
         移る.status == 301 and 移る先 == f"https://{本物の名前}/kimari?x=1" and 確かめの道.status == 404, (移る.status, 移る先, 確かめの道.status))

    # Google の持ち主の確かめの1行（名前は手元の入口の決まりから読む。2か所に書かない）
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "受け口", "makeinu.conf"), encoding="utf-8") as f:
        確かめの名前 = re.search(r"location = /(google[0-9a-f]+\.html)", f.read()).group(1)
    返り, 文 = https_で頼む("GET", "/" + 確かめの名前)
    見る("Google の持ち主の確かめの1行を返す", 返り.status == 200 and 文 == f"google-site-verification: {確かめの名前}", (返り.status, 文[:60]))

    # 名前を知らずに番地だけで来た頼み
    with socket.create_connection((この番地, 80), timeout=10) as s:
        s.sendall(b"GET / HTTP/1.1\r\nHost: tameshi.invalid\r\nConnection: close\r\n\r\n")
        返事 = s.recv(100)
    見る("http で知らない名前の頼みは、何も返さずに切る", 返事 == b"", 返事)
    道具箱 = ssl.create_default_context()
    道具箱.check_hostname = False
    道具箱.verify_mode = ssl.CERT_NONE
    try:
        with socket.create_connection((この番地, 443), timeout=10) as s, 道具箱.wrap_socket(s, server_hostname="tameshi.invalid"):
            断られた = False
    except (ssl.SSLError, ConnectionError):
        断られた = True
    見る("https で知らない名前の頼みは、証明書を見せずに断る", 断られた)

    # 期限が近いのに更新されていないと、来た人が入れなくなる
    with socket.create_connection((本物の名前, 443), timeout=10) as s, ssl.create_default_context().wrap_socket(s, server_hostname=本物の名前) as 暗号:
        残り日数 = (ssl.cert_time_to_seconds(暗号.getpeercert()["notAfter"]) - time.time()) / 86400
    見る(f"証明書の残りが30日を超えている（残り {残り日数:.0f} 日）", 残り日数 > 30, 残り日数)


def 確かめる(道具):
    壁 = sudo("ufw", "status", "verbose").stdout
    壁が閉じている = "Status: active" in 壁 and "deny (incoming)" in 壁 and str(試しの入口の港) not in 壁
    見る("サーバーの壁が、試しの入口の港を外から通さない", 壁が閉じている, 壁)
    if not 壁が閉じている:
        return
    最初の記録 = 受け口の記録()
    本物の入口を確かめる()
    見る("本物の入口へ頼んでも、受け口の記録に何も足されない", 受け口の記録() == 最初の記録, 最初の記録)
    置き場 = tempfile.mkdtemp(prefix="makeinu-ukeguchi-")
    記録の場所 = os.path.join(置き場, "試し.db")
    場 = subprocess.Popen([sys.executable, "-B", "-c",
                          "import sys; sys.path.insert(0, sys.argv[1]); import 場; 場.場を作る(sys.argv[2], sys.argv[3], int(sys.argv[4])).serve_forever()",
                          道具, 記録の場所, 試しの合言葉, str(試しの場の港)])
    try:
        見る("試しの場が立つ", 待つ(lambda: f"127.0.0.1:{試しの場の港}" in 聞いている所()))
        入口 = (f"server {{\n    listen {この番地}:{試しの入口の港};\n    server_name _;\n"
                f"    set $makeinu_ba 127.0.0.1:{試しの場の港};\n    include snippets/makeinu-ukeguchi.conf;\n}}\n")
        sudo("tee", 試しの入口, 入力=入口)
        通るか = sudo("nginx", "-t")
        見る("受け口の決まりが nginx に通る", 通るか.returncode == 0, 通るか.stderr)
        if 通るか.returncode != 0:
            return
        sudo("systemctl", "reload", "nginx")
        見る("試しの入口が立つ", 待つ(lambda: f"{この番地}:{試しの入口の港}" in 聞いている所()))
        前の記録 = 受け口の記録()
        試しの場で確かめる(記録の場所)
        # 別のサイトから送らせた時に、ブラウザの付ける見出しが場まで届いて断れる
        返り, 文 = 頼む("POST", "/ita/shigoto/kaku", {"honbun": "別のサイトから"}, {"Sec-Fetch-Site": "cross-site"})
        見る("別のサイトからの送信は、受け口を通っても断る", 返り.status == 403 and "このサイトの画面から" in 文, 返り.status)
        # 場が止まっていても、英語の画面でなく日本語の知らせを出す（書いた人が POST で来た時も）
        場.terminate()
        場.wait(timeout=10)
        返り, 文 = 頼む("GET", "/ita/shigoto")
        送り, 送りの文 = 頼む("POST", "/ita/shigoto/kaku", {"honbun": "止まっている時"})
        見る("場が止まっている時は、見る時も送る時も日本語の知らせを出す",
             返り.status == 502 and "少し待ってから" in 文 and 送り.status == 502 and "少し待ってから" in 送りの文, (返り.status, 送り.status))
        後の記録 = 受け口の記録()
        見る("受け口の記録に何も足されず、番地も出てこない", 前の記録 == 後の記録 and 後の記録[1] == 0, f"{前の記録} → {後の記録}")
    finally:
        sudo("rm", "-f", 試しの入口)
        sudo("systemctl", "reload", "nginx")
        場.terminate()
        場.wait(timeout=10)
        shutil.rmtree(置き場, ignore_errors=True)
    # 読み直した後も、前の働き手が残りのつなぎを片付け終えるまでは、試しの入口の港を持っている
    片付いた = 待つ(lambda: f":{試しの入口の港}" not in 聞いている所() and f":{試しの場の港}" not in 聞いている所(), 秒=90)
    見る("片付けた後は、試しの入口も試しの場も聞いていない", 片付いた and not os.path.exists(置き場), 聞いている所())


if __name__ == "__main__":
    確かめる(sys.argv[1] if len(sys.argv) > 1 else "/srv/makeinu/道具")
    for 名前, よいか, 見たもの in 結果:
        print(f"{'合格' if よいか else '不合格'}｜{名前}" + ("" if よいか else f"｜{見たもの}"))
    sys.exit(0 if 結果 and all(よいか for _, よいか, _ in 結果) else 1)
