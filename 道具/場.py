"""負け犬の癒し：試しの場（このパソコンの中だけで開く）。受け口（どの道が来たら何をするか）と、書く・押す・消す。

起動：python3 場.py   → http://127.0.0.1:8765/
持ち主の見回り：環境変数 MAKEINU_AIKOTOBA に合言葉を入れて起動し、/kanri の入口の欄に合言葉を入れて入る。入れなければ見回りの画面は閉じたまま。
見る画面は 画面.py、見た目は 見た目.py、置き場の名前と場所は 置き場.py。
"""
import ipaddress
import os
import re
import secrets
import sys
import threading
import traceback
from datetime import timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import 決まり
import 時計
from 台帳 import 台帳
from 置き場 import 置き場の場所
from 画面 import 画面たち, 今夜の始まり
from 見た目 import 頁

フォルダ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
鍵の名前 = "makeinu_kagi"
札の名前 = "makeinu_mimawari"  # 持ち主が見回りに入った時だけ渡す札（クッキー）


class 接続元ごとの数:
    """同じ接続元から短い間に来た数（荒らしの書き込み・見回りの合言葉の間違い）。番地は記録に残さず、その場で数えるだけ（起動し直せば消える）。
    じかに来た自分（127.0.0.1 など）は数えない。前に置く受け口が番地を渡さない時に、全員が同じ番地に見えて場ごと止まらないように。"""

    def __init__(self, 上限, 秒):
        self.上限, self.秒 = 上限, 秒
        self._時刻たち = {}
        self._錠 = threading.Lock()

    def _数えない(self, 番地):
        try:
            return ipaddress.ip_address(番地).is_loopback
        except ValueError:
            return False

    def _近いもの(self, 番地):
        いつから = 時計.いま() - timedelta(seconds=self.秒)
        近い = [時刻 for 時刻 in self._時刻たち.get(番地, []) if 時刻 > いつから]
        if 近い:
            self._時刻たち[番地] = 近い
        else:
            self._時刻たち.pop(番地, None)
        return 近い

    def まだ受けるか(self, 番地):
        if self._数えない(番地):
            return True
        with self._錠:
            return len(self._近いもの(番地)) < self.上限

    def 数える(self, 番地):
        if self._数えない(番地):
            return
        with self._錠:
            self._近いもの(番地)
            self._時刻たち.setdefault(番地, []).append(時計.いま())
            if len(self._時刻たち) > 10000:  # 来なくなった接続元を、ときどきまとめて忘れる
                for 古い in list(self._時刻たち):
                    self._近いもの(古い)


class 見回りの札:
    """持ち主が合言葉で見回りに入った時に渡す札（クッキー）。効く秒がたつと切れる。記録には残さず、起動し直せば消える。
    札ごとに合い札を1つ持たせ、見回りの画面の消す・戻す・出るの欄に入れる。札と合い札がそろった時だけ動かす
    （ほかのサイトに仕掛けた送る欄から、持ち主のブラウザに送らせても動かないように）。"""

    def __init__(self, 効く秒):
        self.効く秒 = 効く秒
        self._札たち = {}  # 札 → (切れる時刻, 合い札)
        self._錠 = threading.Lock()

    def 渡す(self):
        札 = secrets.token_hex(32)
        with self._錠:
            いま = 時計.いま()
            self._札たち = {k: v for k, v in self._札たち.items() if v[0] > いま}  # 切れた札は、ここでまとめて忘れる
            self._札たち[札] = (いま + timedelta(seconds=self.効く秒), secrets.token_hex(16))
        return 札

    def 合い札(self, 札):
        """効いている札なら、その合い札。切れている・知らない札なら空。"""
        with self._錠:
            中身 = self._札たち.get(札)
            if 中身 and 中身[0] > 時計.いま():
                return 中身[1]
            self._札たち.pop(札, None)
            return ""

    def 返す(self, 札):
        with self._錠:
            self._札たち.pop(札, None)


def 札の見出し(札, 秒):
    # 見回りの道だけに送らせ、ページの中の仕組みからは読めず、ほかのサイトからの移動や送信には付けさせない。https の時だけ送らせる
    return ("Set-Cookie", f"{札の名前}={札}; Path=/kanri; Max-Age={秒}; HttpOnly; SameSite=Strict; Secure")


class 場の受け口(画面たち, BaseHTTPRequestHandler):
    台帳 = None
    合言葉 = ""
    接続元の数 = None
    合言葉の間違い = None
    見回りの札 = None
    timeout = 20  # 送るのが遅い人が1人いても、ほかの人を待たせ続けないよう、黙ったままのつなぎは切る
    _頭だけ = False  # HEAD の時は本文を返さない
    _送った中身 = {}  # 思わぬ誤りの時に、書いた字を画面に戻すため

    # ---- 共通 ----
    def finish(self):
        """1人分を返し終えたら、その人の記録へのつなぎを閉じる。閉じないと、口（ファイルの数の上限）が尽きるまで増え、誰も開けなくなる。"""
        try:
            super().finish()
        finally:
            self.台帳.閉じる()

    def _誤りも受ける(self, 動き):
        """場の中で思わぬ誤りが起きても、黙って切らず知らせる（切ると、書いた字が消えたうえに英語の画面が出る）。訳は場の記録に残す。"""
        try:
            動き()
        except (ConnectionError, TimeoutError):
            raise  # 来た人が途中で閉じた・黙ったまま切れた（同時に受ける場.handle_error）
        except Exception:
            traceback.print_exc()
            self._うまくいかなかった()

    def _クッキー(self, 名前):
        """見出しから欲しい名前の値だけを読む。ほかの名前の形が変でも止まらないように。"""
        for 片 in self.headers.get("Cookie", "").split(";"):
            名, _, 値 = 片.strip().partition("=")
            if 名 == 名前:
                return 値
        return ""

    def _鍵(self):
        """匿名の鍵。名前の代わりに、ブラウザごとの乱数で「わかる」の二度押しと連投だけを見分ける。渡した形（16進32字）でなければ新しく渡す。"""
        鍵 = self._クッキー(鍵の名前)
        if re.fullmatch("[0-9a-f]{32}", 鍵):
            return 鍵, False
        return secrets.token_hex(16), True

    def _返す(self, 状態, 本文, 新しい鍵=None, 足す見出し=()):
        中身 = 本文.encode("utf-8")
        self.send_response(状態)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(中身)))
        self._鍵を渡す(新しい鍵)
        for 名前, 値 in 足す見出し:
            self.send_header(名前, 値)
        self.end_headers()
        if not self._頭だけ:
            self.wfile.write(中身)

    def _移る(self, 行き先, 新しい鍵=None, 足す見出し=()):
        self.send_response(303)
        self.send_header("Location", 行き先)
        self.send_header("Content-Length", "0")
        self._鍵を渡す(新しい鍵)
        for 名前, 値 in 足す見出し:
            self.send_header(名前, 値)
        self.end_headers()

    def _鍵を渡す(self, 新しい鍵):
        if 新しい鍵:
            self.send_header(
                # Secure：同じブラウザの見分けに使う鍵を、暗号なしの http で流さないため
                "Set-Cookie", f"{鍵の名前}={新しい鍵}; Path=/; Max-Age=31536000; HttpOnly; SameSite=Lax; Secure"
            )

    def _送られた中身(self):
        長さ = min(決まり.番号を読む(self.headers.get("Content-Length")) or 0, 決まり.送られた中身の上限)
        return {k: v[0] for k, v in parse_qs(self.rfile.read(長さ).decode("utf-8", "replace")).items()}

    def _板(self, 鍵):
        return next((板 for 板 in 決まり.板の一覧を読む() if 板.鍵 == 鍵), None)

    def _見つからない(self, 新しい鍵=None):
        self._返す(404, 頁("見つかりません", '<p>この場所は見つかりませんでした。</p><a href="/">はじめへ</a>'), 新しい鍵)

    def log_message(self, *args):
        pass

    # ---- 見る ----
    def do_GET(self):
        self._誤りも受ける(self._見る)

    def do_HEAD(self):
        # 同じ見出しで本文だけ返さない（死活を見る道具や、リンク先を確かめる取得が HEAD で来る）
        self._頭だけ = True
        self.do_GET()

    def _見る(self):
        鍵, 新しい = self._鍵()
        新しい鍵 = 鍵 if 新しい else None
        url = urlparse(self.path)
        段 = [s for s in url.path.split("/") if s]
        問い = {k: v[0] for k, v in parse_qs(url.query).items()}
        if not 段:
            return self._はじめ(鍵, 新しい鍵, 問い)
        if len(段) == 2 and 段[0] == "ita":
            return self._板を見せる(段[1], 鍵, 新しい鍵, 問い)
        if 段 == ["kachi"]:
            return self._勝ちを見せる(鍵, 新しい鍵, 問い)
        if 段 == ["hitori"]:
            return self._独り言を見せる(新しい鍵, 問い)
        if 段 == ["sonogo"]:
            return self._その後を見せる(鍵, 新しい鍵, 問い)
        if 段 == ["mouikkai"]:
            return self._宣言を見せる(鍵, 新しい鍵, 問い)
        if 段 == ["yoru"]:
            return self._夜を見せる(鍵, 新しい鍵, 問い)
        if 段 == ["heya"]:
            return self._小部屋の一覧(鍵, 新しい鍵)
        if len(段) == 2 and 段[0] == "heya" and (番号 := 決まり.番号を読む(段[1])) is not None:
            return self._小部屋を見せる(番号, 鍵, 新しい鍵, 問い)
        if 段 == ["nanori"]:
            return self._名乗りを見せる(問い.get("n", ""), 鍵, 新しい鍵)
        if 段 == ["kanri"]:
            return self._見回りを開く(新しい鍵)
        if 段 == ["kanri", "matome"]:
            return self._このブラウザの書き込みを開く(問い.get("bangou", ""), 新しい鍵)
        if 段 == ["shiraseru"]:
            return self._知らせる欄(鍵, 新しい鍵, 問い)
        if 段 == ["kimari"]:
            return self._文を見せる("利用の決まり.txt", "利用の決まり", 新しい鍵)
        if 段 == ["kojin"]:
            return self._文を見せる("個人情報の扱い.txt", "個人情報の扱い", 新しい鍵)
        return self._見つからない(新しい鍵)

    # ---- 書く・押す・消す ----
    def do_POST(self):
        self._誤りも受ける(self._受ける)

    def _受ける(self):
        # 別のサイトに仕掛けた欄から、来た人のブラウザに書かせない（書いた人の記録に、その人の番地が残ってしまう）。
        # 見分けるのはブラウザが付ける見出し。この場は Referrer-Policy: no-referrer なので Origin では見分けられない。見出しを送らない古いブラウザは受ける
        if self.headers.get("Sec-Fetch-Site") in ("cross-site", "same-site"):
            return self._返す(403, 頁("送れませんでした｜負け犬の癒し", '<p>このサイトの画面から送ってください。</p><a href="/">はじめへ</a>'))
        鍵, 新しい = self._鍵()
        新しい鍵 = 鍵 if 新しい else None
        段 = [s for s in urlparse(self.path).path.split("/") if s]
        送られた = self._送った中身 = self._送られた中身()
        if len(段) == 3 and 段[0] == "ita" and 段[2] == "kaku":
            return self._書く(段[1], 送られた.get("honbun", ""), 鍵, 新しい鍵)
        if 段 == ["nanori"]:
            return self._名乗る(送られた.get("nanori", ""), 鍵, 新しい鍵)
        if 段 in (["kachi", "kaku"], ["mouikkai", "kaku"]):
            # 1行で置く場所（勝ち・宣言）。改行が来ても1行にまとめる
            置き場 = 決まり.勝ちの置き場 if 段[0] == "kachi" else 決まり.宣言の置き場
            return self._確かめて置く(置き場, 決まり.名乗りを整える(送られた.get("honbun", "")), 鍵, 新しい鍵, None)
        if len(段) == 2 and 段[0] == "musubu" and (番号 := 決まり.番号を読む(段[1])) is not None:
            return self._結ぶ(番号, 送られた.get("musubi", ""), 鍵, 新しい鍵)
        if 段 == ["sonogo", "kaku"]:
            あの時 = 決まり.名乗りを整える(送られた.get("ano", ""))  # あの時は1行
            return self._確かめて置く(決まり.その後の置き場, 送られた.get("honbun", ""), 鍵, 新しい鍵, None, あの時)
        if 段 == ["heya", "hiraku"]:
            return self._小部屋を開く(送られた.get("bangou", ""), 鍵, 新しい鍵)
        if 段 in (["heya", "ukenai"], ["heya", "ukeru"]):
            self.台帳.小部屋の受け方を決める(鍵, 段[1] == "ukeru")
            return self._移る("/heya", 新しい鍵)
        if len(段) == 3 and 段[0] == "heya" and (番号 := 決まり.番号を読む(段[1])) is not None and 段[2] in ("kaku", "tojiru"):
            部屋 = self.台帳.小部屋(番号, 鍵)
            if not 部屋:
                return self._見つからない(新しい鍵)
            if 段[2] == "tojiru":
                self.台帳.小部屋を閉じる(部屋["番号"], 鍵)
                return self._移る(f"/heya/{部屋['番号']}", 新しい鍵)
            if 部屋["閉じた時刻"]:
                # 閉じた後に開いたままの画面から送った時。閉じたことは画面に出ている
                return self._小部屋を見せる(部屋["番号"], 鍵, 新しい鍵, {}, "閉じた部屋")
            return self._確かめて置く(決まり.小部屋の置き場(部屋["番号"]), 送られた.get("honbun", ""), 鍵, 新しい鍵, None)
        if 段 == ["yoru", "kaku"]:
            if not 今夜の始まり():
                # 朝になってから、開いたままの画面で送った時
                return self._夜を見せる(鍵, 新しい鍵, {}, "夜の部屋は閉まりました。また今夜。")
            return self._確かめて置く(決まり.夜の置き場, 送られた.get("honbun", ""), 鍵, 新しい鍵, None)
        if 段 == ["hitori", "kaku"]:
            return self._確かめて置く(決まり.独り言の置き場, 送られた.get("honbun", ""), 鍵, 新しい鍵, None)
        if len(段) == 2 and 段[0] == "henji" and (番号 := 決まり.番号を読む(段[1])) is not None:
            return self._返事する(番号, 送られた.get("honbun", ""), 鍵, 新しい鍵)
        if len(段) == 2 and 段[0] == "wakaru" and (番号 := 決まり.番号を読む(段[1])) is not None:
            return self._わかる(番号, 鍵, 新しい鍵)
        if 段 == ["kanri", "hairu"]:
            return self._見回りに入る(送られた.get("aikotoba", ""), 新しい鍵)
        if len(段) == 2 and 段[0] == "kanri" and 段[1] in ("kesu", "modosu", "deru", "matomete-kesu", "matomete-modosu"):
            return self._見回りで動く(段[1], 送られた, 新しい鍵)
        if 段 == ["shiraseru"]:
            return self._知らせる(送られた.get("bangou", ""), 送られた.get("honbun", ""), 鍵, 新しい鍵)
        return self._見つからない(新しい鍵)

    def _書く(self, 板の鍵, 本文, 鍵, 新しい鍵):
        if not self._板(板の鍵):
            return self._見つからない(新しい鍵)
        self._確かめて置く(板の鍵, 本文, 鍵, 新しい鍵, None)

    def _返事する(self, 親番号, 本文, 鍵, 新しい鍵):
        板の鍵 = self.台帳.返事できる親(親番号)
        if not 板の鍵 or not self._板(板の鍵):
            # 消された書き込み（開いたままの古い画面から）や返事への返事は置かず、その板へ戻す
            return self._移る(self._見られる場所(self.台帳.書き込みの板(親番号), 鍵), 新しい鍵)
        self._確かめて置く(板の鍵, 本文, 鍵, 新しい鍵, 親番号)

    def _見られる場所(self, 板の鍵, 鍵, 印=""):
        """その置き場の画面。無い置き場と、入れない小部屋は、はじめの画面（小部屋の番号を当てても、部屋があることを見せない）。"""
        部屋番号 = 決まり.小部屋の番号(板の鍵)
        if not 板の鍵 or (部屋番号 is not None and not self.台帳.小部屋(部屋番号, 鍵)):
            return "/"
        return 置き場の場所(板の鍵) + 印

    def _確かめて置く(self, 板の鍵, 本文, 鍵, 新しい鍵, 親番号, あの時=None):
        """書き込みも返事も同じ決まりで確かめる。止めた時は書きかけを、書いた場所に戻す。"""
        本文 = 決まり.本文を整える(本文)
        上限 = {決まり.勝ちの置き場: 決まり.勝ちの上限, 決まり.宣言の置き場: 決まり.宣言の上限}.get(板の鍵, 決まり.本文の上限)
        見立て = 決まり.見立てる(本文, 上限)
        断る訳 = 見立て.断る訳
        その後 = 板の鍵 == 決まり.その後の置き場
        if その後:
            あの時の見立て = 決まり.見立てる(あの時, 決まり.あの時の上限)
            if not あの時の見立て.通す:
                断る訳 = 断る訳 or ("「あの時」も書いてください。" if not あの時 else "「あの時」は" + あの時の見立て.断る訳)
                見立て = あの時の見立て
            elif あの時の見立て.相談先を出す:
                見立て = 決まり.見立て(見立て.通す, 見立て.断る訳, True)
        独り言 = 板の鍵 == 決まり.独り言の置き場
        部屋番号 = 決まり.小部屋の番号(板の鍵)
        番地, 港 = self._接続元()
        二度目 = False
        # 二度押しと連投の確かめから書くまでを1つの動きにする。同時に2つ送られても、両方が確かめを抜けて2件置かれないように
        with self.台帳.ひとりずつ():
            if 見立て.通す and not 断る訳 and self.台帳.同じ書き込みがあるか(板の鍵, 本文, 鍵, 決まり.二重送信とみなす秒, 親番号):
                二度目 = True
            else:
                最後 = self.台帳.最後に書いた時刻(鍵)
                if not 断る訳 and 最後 and 時計.いま() - 最後 < timedelta(seconds=決まり.連投の間隔秒):
                    断る訳 = "少し間をあけてから、もう一度送ってください。"
                if not 断る訳 and not self.接続元の数.まだ受けるか(番地):
                    断る訳 = "少し間をあけてから、もう一度送ってください。"
                if not 断る訳:
                    self._置く(板の鍵, 本文, 鍵, 親番号, 独り言, 部屋番号, あの時 if その後 else None, 番地, 港)
                    self.接続元の数.数える(番地)
        if 二度目:
            # 送るボタンの二度押し・戻って再送。同じものは2つ置かず、置いた所を見せる
            return self._移る(self._置いた所(板の鍵, 親番号), 新しい鍵)
        if 断る訳:
            # 止めた時は、書いた場所の画面に書きかけごと戻す
            if 部屋番号:
                return self._小部屋を見せる(部屋番号, 鍵, 新しい鍵, {}, 断る訳, 本文)
            戻す画面 = {
                決まり.勝ちの置き場: lambda: self._勝ちを見せる(鍵, 新しい鍵, {}, 断る訳, 本文),
                決まり.独り言の置き場: lambda: self._独り言を見せる(新しい鍵, {}, 断る訳, 本文),
                決まり.その後の置き場: lambda: self._その後を見せる(鍵, 新しい鍵, {}, 断る訳, 本文, あの時),
                決まり.宣言の置き場: lambda: self._宣言を見せる(鍵, 新しい鍵, {}, 断る訳, 本文),
                決まり.夜の置き場: lambda: self._夜を見せる(鍵, 新しい鍵, {}, 断る訳, 本文),
            }.get(板の鍵)
            if 戻す画面:
                return 戻す画面()
            if 親番号:
                return self._板を見せる(板の鍵, 鍵, 新しい鍵, {}, 返事の断り=(親番号, 断る訳, 本文))
            return self._板を見せる(板の鍵, 鍵, 新しい鍵, {}, 断る訳, 本文)
        self._移る(self._置いた所(板の鍵, 親番号, 見立て.相談先を出す), 新しい鍵)

    def _接続元(self):
        """(番地, 港)。前に置く https の受け口が、来た人の番地と港を X-Real-IP・X-Real-Port に入れて渡す。"""
        return 決まり.接続元を決める(*self.client_address[:2], self.headers.get("X-Real-IP"), self.headers.get("X-Real-Port"))

    def _置く(self, 板の鍵, 本文, 鍵, 親番号, 独り言, 部屋番号, あの時, 番地, 港):
        名乗り = "" if 独り言 else self.台帳.名乗りを読む(鍵)  # 独り言は名乗りを残さない（名乗りから辿れないように）
        # 夜の話はその夜だけのもの。名乗りは見せるが、名乗りの頁からは辿れないようにする
        # 小部屋の話は2人だけのもの。名乗りも残さない
        if 部屋番号:
            名乗り = ""
        名乗りの形 = None if 板の鍵 == 決まり.夜の置き場 or 部屋番号 else 決まり.そろえる(名乗り)
        self.台帳.書く(板の鍵, 本文, 鍵, 親番号, 名乗り, 名乗りの形, あの時, 番地, 港)  # 番地と港は書いた人の記録へ

    def _小部屋を開く(self, 番号, 鍵, 新しい鍵):
        """自分と同じ名乗りで書いた、ほかの人とだけ開ける。つきまといを防ぐ決まり（画面.py `_部屋を開けるか`）にも当てる。"""
        読んだ番号 = 決まり.番号を読む(番号)
        書いた人 = self.台帳.書いた人(読んだ番号) if 読んだ番号 is not None else None
        自分の名乗りの形 = 決まり.そろえる(self.台帳.名乗りを読む(鍵))
        if not 書いた人 or not 自分の名乗りの形 or 書いた人[1] != 自分の名乗りの形 or 書いた人[0] == 鍵:
            return self._移る("/heya", 新しい鍵)
        if not self._部屋を開けるか(鍵, 書いた人[0]):
            return self._移る("/heya", 新しい鍵)
        部屋番号 = self.台帳.小部屋を開く(自分の名乗りの形, 鍵, 書いた人[0])
        self._移る(f"/heya/{部屋番号}", 新しい鍵)

    def _結ぶ(self, 番号, 結び, 鍵, 新しい鍵):
        if 結び in 決まり.結びの言葉:
            self.台帳.結ぶ(番号, 鍵, 決まり.宣言の置き場, 結び)
        self._移る(f"/mouikkai#k{番号}", 新しい鍵)

    def _名乗る(self, 名乗り, 鍵, 新しい鍵):
        名乗り = 決まり.名乗りを整える(名乗り)
        if 名乗り:
            見立て = 決まり.名乗りを見立てる(名乗り)
            if not 見立て.通す:
                return self._はじめ(鍵, 新しい鍵, {}, 見立て.断る訳, 名乗り)
        self.台帳.名乗りを決める(鍵, 名乗り)
        self._移る("/?sotto=1#nanori" if 名乗り and 見立て.相談先を出す else "/#nanori", 新しい鍵)

    def _置いた所(self, 板の鍵, 親番号, 相談先を出す=False):
        印 = f"#k{親番号}" if 親番号 else {決まり.夜の置き場: "#yoru-kaku"}.get(板の鍵, "#heya-kaku" if 決まり.小部屋の番号(板の鍵) else "")
        return 置き場の場所(板の鍵) + ("?sotto=1" if 相談先を出す else "") + 印

    def _知らせる(self, 番号, 本文, 鍵, 新しい鍵):
        """持ち主への知らせ。無い番号は番号なしとして受ける。二度押し・連投は書き込みと同じ間で見分ける（知らせどうしで数える）。"""
        読んだ番号 = 決まり.番号を読む(番号)
        書き込み番号 = 読んだ番号 if 読んだ番号 is not None and self.台帳.書き込みの板(読んだ番号) else None
        本文 = 決まり.本文を整える(本文)
        見立て = 決まり.知らせを見立てる(本文, 書き込み番号 is not None)
        断る訳 = 見立て.断る訳
        番地, _ = self._接続元()
        with self.台帳.ひとりずつ():
            二度目 = not 断る訳 and self.台帳.同じ知らせがあるか(鍵, 書き込み番号, 本文, 決まり.二重送信とみなす秒)
            if not 断る訳 and not 二度目:
                最後 = self.台帳.最後に知らせた時刻(鍵)
                if (最後 and 時計.いま() - 最後 < timedelta(seconds=決まり.連投の間隔秒)) or not self.接続元の数.まだ受けるか(番地):
                    断る訳 = "少し間をあけてから、もう一度送ってください。"
                else:
                    self.台帳.知らせる(鍵, 書き込み番号, 本文)
                    self.接続元の数.数える(番地)
        if 断る訳:
            return self._知らせる欄(鍵, 新しい鍵, {"bangou": str(書き込み番号 or "")}, 断る訳, 本文)
        self._移る("/shiraseru?okutta=1" + ("&sotto=1" if 見立て.相談先を出す else ""), 新しい鍵)

    def _わかる(self, 番号, 鍵, 新しい鍵):
        板 = self.台帳.書き込みの板(番号)
        if 板 != 決まり.独り言の置き場 and not 決まり.小部屋の番号(板):  # 独り言・小部屋には何も返さない
            self.台帳.わかると押す(番号, 鍵)
        self._移る(self._見られる場所(板, 鍵, f"#k{番号}"), 新しい鍵)

    # ---- 見回り ----
    def _入っていれば合い札(self, 新しい鍵):
        """見回りに入っているブラウザなら、その札の合い札。入っていなければ入口を（合言葉の無い場は見つからないを）返して空。"""
        if not self.合言葉:
            self._見つからない(新しい鍵)
            return ""
        合い札 = self.見回りの札.合い札(self._クッキー(札の名前))
        if not 合い札:
            self._見回りの入口(新しい鍵)
        return 合い札

    def _見回りを開く(self, 新しい鍵):
        合い札 = self._入っていれば合い札(新しい鍵)
        if 合い札:
            self._見回り(合い札, 新しい鍵)

    def _このブラウザの書き込みを開く(self, 番号, 新しい鍵):
        """その番号を書いたブラウザの書き込みの一覧。まとめて消す・戻す前に、何が消えるかを持ち主が見る。"""
        合い札 = self._入っていれば合い札(新しい鍵)
        if not 合い札:
            return
        読んだ番号 = 決まり.番号を読む(番号)
        書き込みたち = self.台帳.同じブラウザの書き込み(読んだ番号) if 読んだ番号 is not None else []
        if not 書き込みたち:
            return self._見つからない(新しい鍵)
        self._このブラウザの書き込み(読んだ番号, 書き込みたち, 合い札, 新しい鍵)

    def _見回りに入る(self, 合言葉, 新しい鍵):
        """合言葉は入口の欄から送ってもらい、ページの場所（URL）に載せない。ブラウザの履歴や、前に置く受け口の記録に残らないように。"""
        if not self.合言葉:
            return self._見つからない(新しい鍵)  # 合言葉を入れずに起動した時は閉じたまま（空どうしを同じとみなさない）
        番地, _ = self._接続元()
        if not self.合言葉の間違い.まだ受けるか(番地):
            # 間違いが続いた接続元は、合言葉が正しくても確かめずに待ってもらう
            return self._見回りの入口(新しい鍵, f"間違いが続いたので、{決まり.合言葉の間違いを数える秒 // 60}分ほどたってから入れてください。", 429)
        # 貼り付けた時に付きやすい前後の空白は外す。比べるのは文字の並び（bytes）で、日本語が来ても止まらない
        if not secrets.compare_digest(合言葉.strip().encode("utf-8"), self.合言葉.encode("utf-8")):
            self.合言葉の間違い.数える(番地)
            return self._見回りの入口(新しい鍵, "合言葉が違います。", 403)
        self._移る("/kanri", 新しい鍵, [札の見出し(self.見回りの札.渡す(), 決まり.見回りの札が効く秒)])

    def _見回りで動く(self, 動き, 送られた, 新しい鍵):
        """消す・戻す・出るは、効いている札と、その札の合い札（見回りの画面の欄に入れてある）がそろった時だけ。"""
        if not self.合言葉:
            return self._見つからない(新しい鍵)
        札 = self._クッキー(札の名前)
        合い札 = self.見回りの札.合い札(札)
        if not 合い札 or not secrets.compare_digest(送られた.get("aifuda", "").encode("utf-8"), 合い札.encode("utf-8")):
            return self._見回りの入口(新しい鍵, "見回りの札が切れました。もう一度、合言葉を入れてください。", 403)
        if 動き == "deru":
            self.見回りの札.返す(札)
            return self._移る("/kanri", 新しい鍵, [札の見出し("", 0)])
        番号 = 決まり.番号を読む(送られた.get("bangou", ""))
        if 番号 is None:
            return self._見つからない(新しい鍵)
        if 動き in ("matomete-kesu", "matomete-modosu"):
            # ここまで＝一覧を見せた時の一番新しい番号。見せた後に書かれた物は、まとめて消さない
            ここまで = 決まり.番号を読む(送られた.get("made", ""))
            if ここまで is None or not self.台帳.同じブラウザの書き込み(番号):
                return self._見つからない(新しい鍵)
            (self.台帳.まとめて消す if 動き == "matomete-kesu" else self.台帳.まとめて戻す)(番号, ここまで)
            return self._移る(f"/kanri/matome?bangou={番号}", 新しい鍵)
        (self.台帳.消す if 動き == "kesu" else self.台帳.戻す)(番号)
        self._移る(f"/kanri#m{番号}", 新しい鍵)  # 消した・戻した行へ戻る


class 同時に受ける場(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 128  # 入口で待てる人数。元のままの5人だと、同時に来た6人目から断られる（Linux で起きた）

    def handle_error(self, request, client_address):
        # 来た人が途中で閉じた・黙ったまま切れたのは、場の不具合ではないので残さない
        if not isinstance(sys.exc_info()[1], (ConnectionError, TimeoutError)):
            super().handle_error(request, client_address)


def 場を作る(台帳の場所, 合言葉="", 港=8765):
    """同時に来た人を、それぞれ別に受ける。"""
    受け口 = type("受け口", (場の受け口,), {
        "台帳": 台帳(台帳の場所), "合言葉": 合言葉,
        "接続元の数": 接続元ごとの数(決まり.接続元ごとの上限, 決まり.接続元を数える秒),
        "合言葉の間違い": 接続元ごとの数(決まり.合言葉を間違えてよい回数, 決まり.合言葉の間違いを数える秒),
        "見回りの札": 見回りの札(決まり.見回りの札が効く秒)})
    return 同時に受ける場(("127.0.0.1", 港), 受け口)


if __name__ == "__main__":
    記録 = os.path.join(フォルダ, "記録")
    os.makedirs(記録, exist_ok=True)
    場 = 場を作る(os.path.join(記録, "場.db"), os.environ.get("MAKEINU_AIKOTOBA", ""), int(sys.argv[1]) if len(sys.argv) > 1 else 8765)
    場.RequestHandlerClass.台帳.毎日の手入れ(os.path.join(記録, "控え"))
    print(f"http://127.0.0.1:{場.server_port}/ で開いています（止めるときは Ctrl+C）")
    場.serve_forever()
