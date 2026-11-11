"""負け犬の癒し：守る動作のテスト。番号は テスト結果.md の「守る動作」の番号と同じ。

動かし方：python3 テスト.py
"""
import base64
import contextlib
import gc
import hashlib
import http.client
import io
import json
import os
import re
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from datetime import datetime, timedelta
from unittest import mock
from urllib.parse import quote, urlencode

import 控えを取ってくる
import 毎日の数を読む
import 決まり
import 場
import 時計
import 聞き役
import 見た目
from 台帳 import 台帳


class 決まりのテスト(unittest.TestCase):
    def setUp(self):
        self.止める = 決まり.言葉を読む("止める言葉.txt")
        self.相談 = 決まり.言葉を読む("相談先の言葉.txt")

    def 見立て(self, 文):
        return 決まり.書き込みを見立てる(決まり.本文を整える(文), self.止める, self.相談)

    def test_01_空や空白だけは置かない(self):
        for 文 in ["", "   ", "　　", "\n\n", None]:
            self.assertFalse(self.見立て(文).通す, repr(文))

    def test_02_上限ちょうどは通し_超えたら断る(self):
        self.assertTrue(self.見立て("あ" * 決まり.本文の上限).通す)
        超え = self.見立て("あ" * (決まり.本文の上限 + 1))
        self.assertFalse(超え.通す)
        self.assertIn("1001字", 超え.断る訳)

    def test_03_人を叩く言葉は止める(self):
        self.assertFalse(self.見立て("お前なんか死ね").通す)

    def test_04_書き方を変えても止める(self):
        for 文 in ["死 ね", "死　ね", "ｷｴﾛ", "キエロ", "消　え　ろ", "ｺﾛｽｿﾞ"]:
            self.assertFalse(self.見立て(文).通す, 文)

    def test_134_見えない字や記号を挟んでも止める(self):
        for 挟む字 in ["​", "‍", "﻿", "️", "­", "⁠", "・", ".", "-", "*"]:
            self.assertFalse(self.見立て(挟む字.join("死ね")).通す, repr(挟む字))
            self.assertTrue(self.見立て(挟む字.join("死にたい")).相談先を出す, repr(挟む字))

    def test_135_見えない字だけは置かず_記号や絵文字だけは置く(self):
        for 文 in ["​​", "﻿", "ㅤㅤ", "⠀⠀", "́́", "­", "⁠", "‍️", "ᅟᅠﾠ"]:
            self.assertFalse(self.見立て(決まり.本文を整える(文)).通す, repr(文))
        for 文 in ["……", "！", "😀", "👨‍👩‍👧"]:
            self.assertTrue(self.見立て(決まり.本文を整える(文)).通す, repr(文))

    def test_136_本文の見えない字のうち_向きを変える字と幅のない字は残さず_絵文字のつなぎは残す(self):
        self.assertEqual(決まり.本文を整える("abc‮def⁦g⁩"), "abcdefg")
        self.assertEqual(決まり.本文を整える("あ​い﻿う⁠え­お"), "あいうえお")
        self.assertEqual(決まり.本文を整える("👨‍👩‍👧"), "👨‍👩‍👧")
        self.assertEqual(決まり.本文を整える("☺️"), "☺️")

    def test_137_聞き役に似せた名乗りは使えない(self):
        for 名乗り in ["聞き役", "聞き役（AI）", "聞​き役（AI）", "聞‍き役", "聴き役（AI）", "ききやく", "キキヤク", "きき役", "聞きやく", "聞・き・役", "相談員（AI）", "店長(ai)", "店長（ＡＩ）"]:
            self.assertFalse(決まり.名乗りを見立てる(決まり.名乗りを整える(名乗り)).通す, repr(名乗り))
        for 名乗り in ["元・店長", "mai", "AI好き", "元・聞き上手"]:
            self.assertTrue(決まり.名乗りを見立てる(決まり.名乗りを整える(名乗り)).通す, repr(名乗り))

    def test_138_AIの断りの文と日本語でない文は_聞き役の返事に出さない(self):
        for 返事 in ["I'm sorry, but I can't help with that.", "I’m sorry, but I can’t comply with that request.", "ごめん、対応できません。",
                   "ごめんね、このリクエストには応えられない", "申し訳ありませんが、お答えできません。", "お手伝いできかねます。", "OK", "12345"]:
            self.assertFalse(決まり.聞き役の返事を出せるか(返事), 返事)
        for 返事 in ["そのまま置いていっていいよ。", "クビになって、すべてが嫌になる気持ち、伝わってくるよ。"]:
            self.assertTrue(決まり.聞き役の返事を出せるか(返事), 返事)

    def test_139_番号は半角の数字で桁が収まる時だけ読む(self):
        for 文, 番号 in [("12", 12), ("0", 0), ("9" * 18, int("9" * 18))]:
            self.assertEqual(決まり.番号を読む(文), 番号)
        for 文 in ["", None, "²", "①", "٣", "１２", "-1", "1.5", " 1", "1 ", "a", "9" * 19, "9" * 5000]:
            self.assertIsNone(決まり.番号を読む(文), repr(文)[:20])

    def test_05_自分を責める言葉は止めない(self):
        for 文 in ["自分はクズだ", "無能な俺", "負け犬です", "負け組のまま40歳", "やる気しねぇ"]:
            見立て = self.見立て(文)
            self.assertTrue(見立て.通す, 文)
            self.assertFalse(見立て.相談先を出す, 文)

    def test_06_つらすぎる言葉は通して相談先を出す(self):
        for 文 in ["もう死にたい", "ｷｴﾀｲ", "消えたい…", "生きて いたくない"]:
            見立て = self.見立て(文)
            self.assertTrue(見立て.通す, 文)
            self.assertTrue(見立て.相談先を出す, 文)

    def test_51_夜の部屋は23時から朝5時まで_日付をまたいでも同じ夜(self):
        def 始まり(文):
            return 決まり.今夜の始まり(datetime.fromisoformat(文 + "+09:00"))
        self.assertIsNone(始まり("2026-10-23T22:59:59"))
        self.assertEqual(始まり("2026-10-23T23:00:00").isoformat(), "2026-10-23T23:00:00+09:00")
        self.assertEqual(始まり("2026-10-24T02:30:00").isoformat(), "2026-10-23T23:00:00+09:00")
        self.assertEqual(始まり("2026-10-24T04:59:59").isoformat(), "2026-10-23T23:00:00+09:00")
        self.assertIsNone(始まり("2026-10-24T05:00:00"))
        self.assertEqual(始まり("2027-01-01T01:00:00").isoformat(), "2026-12-31T23:00:00+09:00")

    def test_75_受け口から来た時だけ見出しの接続元を使い_おかしな見出しは使わない(self):
        決める = 決まり.接続元を決める
        # 前に置く https の受け口（同じサーバーの中から来る）が、来た人の番地と港を見出しに入れて渡す
        self.assertEqual(決める("127.0.0.1", 50001, "203.0.113.7", "54321"), ("203.0.113.7", 54321))
        self.assertEqual(決める("127.0.0.1", 50001, "2001:DB8::1", "443"), ("2001:db8::1", 443))
        self.assertEqual(決める("127.0.0.1", 50001, " 203.0.113.7 ", " 54321 "), ("203.0.113.7", 54321))
        # 見出しが無い・番地の形でない時は、じかの相手
        self.assertEqual(決める("127.0.0.1", 50001, None, None), ("127.0.0.1", 50001))
        self.assertEqual(決める("127.0.0.1", 50001, "203.0.113.7, 198.51.100.1", "54321"), ("127.0.0.1", 50001))
        self.assertEqual(決める("127.0.0.1", 50001, "not-an-ip", "54321"), ("127.0.0.1", 50001))
        # 番地は正しく港がおかしい時は、番地だけ使い港は空にする
        for 港 in ("99999", "0", "abc", None):
            self.assertEqual(決める("127.0.0.1", 50001, "203.0.113.7", 港), ("203.0.113.7", None), 港)
        # 受け口を通らずに来た相手（サーバーの外）が見出しを付けてきても信じない
        self.assertEqual(決める("198.51.100.9", 40000, "203.0.113.7", "54321"), ("198.51.100.9", 40000))

    def test_14_制御文字を落とし改行をそろえる(self):
        self.assertEqual(決まり.本文を整える("　あ\r\nい\x00\x07\rう \n"), "あ\nい\nう")

    def test_13_板の一覧と相談先を中身から読む(self):
        板たち = 決まり.板の一覧を読む()
        self.assertGreaterEqual(len(板たち), 5)
        self.assertEqual(len({板.鍵 for 板 in 板たち}), len(板たち), "板の鍵が重なっている")
        self.assertTrue(all(re.fullmatch(r"[a-z]+", 板.鍵) for 板 in 板たち))
        板でない = {決まり.勝ちの置き場, 決まり.独り言の置き場, 決まり.その後の置き場, 決まり.宣言の置き場}
        self.assertFalse(板でない & {板.鍵 for 板 in 板たち}, "板の鍵が、板でない置き場と重なっている")
        相談先たち = 決まり.相談先を読む()
        self.assertTrue(all(先.番号 for 先 in 相談先たち))
        # 夜にも出すので、24時間の窓口が2つとも読めていること（名前が # で始まる窓口を読み飛ばさない）
        self.assertEqual([先.番号 for 先 in 相談先たち][:2], ["0120-279-338", "0120-061-338"])


class 見た目のテスト(unittest.TestCase):
    def test_91_中身の文の印を画面の形に直し_記号は文字のまま_道はこの場の中だけ(self):
        文 = ("# メモは出さない\nはじめの段落<b>\n\n■ 見出し\n▼ 小見出し\n・箇条1\n・箇条2 [知らせる](/shiraseru)\n{相談先}\n"
             "おわり [外](javascript:alert(1)) [外2](https://example.com) [外3](//example.com)\n")
        self.assertEqual(
            見た目.中身を見せる(文, {"{相談先}": "<ul><li>窓口</li></ul>"}),
            '<p>はじめの段落&lt;b&gt;</p><h2>見出し</h2><h3>小見出し</h3>'
            '<ul><li>箇条1</li><li>箇条2 <a href="/shiraseru">知らせる</a></li></ul><ul><li>窓口</li></ul>'
            '<p>おわり [外](javascript:alert(1)) [外2](https://example.com) [外3](//example.com)</p>',
        )

    def test_160_検索の説明は字のまま属性に入れ_渡さない画面には付けない(self):
        文 = 見た目.頁("題", "", 説明='「"引用"」<b>&')
        self.assertEqual(文.count('name="description"'), 1)
        self.assertIn('<meta name="description" content="「&quot;引用&quot;」&lt;b&gt;&amp;">', 文)
        self.assertNotIn('name="description"', 見た目.頁("題", ""))


class 場のテスト(unittest.TestCase):
    合言葉 = "tameshi-aikotoba"

    def setUp(self):
        self.置き場 = tempfile.mkdtemp()
        self.場 = 場.場を作る(os.path.join(self.置き場, "場.db"), self.合言葉, 0)
        self.台帳 = self.場.RequestHandlerClass.台帳
        threading.Thread(target=self.場.serve_forever, daemon=True).start()
        self.クッキー = {}

    def tearDown(self):
        self.場.shutdown()
        self.場.server_close()
        self.台帳.つなぎ.close()
        shutil.rmtree(self.置き場, ignore_errors=True)

    def 頼む(self, 動き, 道, 中身=None, 人="A", 足す見出し=None):
        """人ごとのブラウザとして頼む。渡されたクッキーは人ごとに持ち、次から送る（人=None はクッキーを受けないブラウザ）。"""
        つなぎ = http.client.HTTPConnection("127.0.0.1", self.場.server_port)
        見出し = dict(足す見出し or {})
        クッキー = self.クッキー.setdefault(人, {}) if 人 is not None else {}
        if クッキー:
            見出し["Cookie"] = "; ".join(f"{名}={値}" for 名, 値 in クッキー.items())
        本体 = None
        if 中身 is not None:
            本体 = urlencode(中身)
            見出し["Content-Type"] = "application/x-www-form-urlencoded"
        つなぎ.request(動き, 道, 本体, 見出し)
        返り = つなぎ.getresponse()
        文 = 返り.read().decode("utf-8")
        つなぎ.close()
        self.返りの見出し = 返り.msg
        for 渡された in 返り.msg.get_all("Set-Cookie") or []:
            名, _, 値 = 渡された.split(";")[0].partition("=")
            if "Max-Age=0" in 渡された:
                クッキー.pop(名, None)
            else:
                クッキー[名] = 値
        return 返り.status, 返り.getheader("Location"), 文

    def 鍵(self, 人):
        """その人のブラウザの匿名の鍵。"""
        return self.クッキー[人][場.鍵の名前]

    def 書く(self, 本文, 板="shigoto", 人="A"):
        return self.頼む("POST", f"/ita/{板}/kaku", {"honbun": 本文}, 人)

    def 板の件数(self, 板="shigoto"):
        return self.台帳.つなぎ.execute("SELECT COUNT(*) FROM 書き込み WHERE 板 = ? AND 消した時刻 IS NULL", (板,)).fetchone()[0]

    def 時計を戻す(self):
        self.台帳.つなぎ.execute("UPDATE 書き込み SET 書いた時刻 = '2000-01-01T00:00:00+00:00'")

    # 見回りは、持ち主のブラウザが入口の欄から合言葉を送って入る（札のクッキーを受け取る）
    def 見回りに入る(self, 合言葉=None, 人="持ち主", 番地=None):
        見出し = {"X-Real-IP": 番地, "X-Real-Port": "1000"} if 番地 else None  # 番地を付けると、受け口を通って来た形
        return self.頼む("POST", "/kanri/hairu", {"aikotoba": self.合言葉 if 合言葉 is None else 合言葉}, 人, 見出し)

    def 見回りの画面(self, 人="持ち主"):
        if 場.札の名前 not in self.クッキー.get(人, {}):
            self.見回りに入る(人=人)
        return self.頼む("GET", "/kanri", 人=人)[2]

    def 合い札(self, 人="持ち主"):
        """見回りの画面の、消す・戻す・出るの欄に入っている合い札。"""
        return re.search(r'name="aifuda" value="([0-9a-f]+)"', self.見回りの画面(人)).group(1)

    def 見回りで(self, 動き, 番号=None, 人="持ち主"):
        中身 = {"aifuda": self.合い札(人)}
        if 番号 is not None:
            中身["bangou"] = 番号
        return self.頼む("POST", f"/kanri/{動き}", 中身, 人)

    def 消す(self, 番号):
        return self.見回りで("kesu", 番号)

    def 戻す(self, 番号):
        return self.見回りで("modosu", 番号)

    def このブラウザの書き込み(self, 番号, 人="持ち主"):
        """見回りの「このブラウザの書き込み」（その番号を書いたブラウザの書き込みの一覧）。"""
        if 場.札の名前 not in self.クッキー.get(人, {}):
            self.見回りに入る(人=人)
        return self.頼む("GET", f"/kanri/matome?bangou={番号}", 人=人)

    def 欄を読む(self, 文, 動き):
        """画面の、まとめて消す・戻すの欄に入っているもの（合い札・番号・ここまで）。"""
        欄 = re.search(rf'<form method="post" action="/kanri/matomete-{動き}">(.*?)</form>', 文, re.S).group(1)
        return dict(re.findall(r'<input type="hidden" name="(\w+)" value="([^"]*)">', 欄))

    def まとめて(self, 動き, 番号, 人="持ち主"):
        """一覧を開いて、その欄のまま、まとめて消す（kesu）・戻す（modosu）を送る。"""
        return self.頼む("POST", f"/kanri/matomete-{動き}", self.欄を読む(self.このブラウザの書き込み(番号, 人)[2], 動き), 人)

    def 消したか(self):
        return dict(self.台帳.つなぎ.execute("SELECT 番号, 消した時刻 IS NOT NULL FROM 書き込み").fetchall())

    def test_00_はじめの画面に板が並ぶ(self):
        状態, _, 文 = self.頼む("GET", "/")
        self.assertEqual(状態, 200)
        for 板 in 決まり.板の一覧を読む():
            self.assertIn(f'href="/ita/{板.鍵}"', 文)

    def test_63_はじめの画面は板が一番上で_名乗りの欄は一番下(self):
        文 = self.頼む("GET", "/")[2]
        板の位置 = [文.index(f'href="/ita/{板.鍵}"') for 板 in 決まり.板の一覧を読む()]
        self.assertLess(max(板の位置), 文.index('class="場所へ'))
        self.assertLess(文.index('href="/hitori"'), 文.index('id="nanori"'))
        # 止められて画面を返す時も、名乗りの欄へ飛ぶ
        self.assertIn('action="/nanori#nanori"', 文)

    def test_07_書いた物が板に出て_ほかの板には出ない(self):
        状態, 行き先, _ = self.書く("会社をクビになった")
        self.assertEqual((状態, 行き先), (303, "/ita/shigoto"))
        self.assertIn("会社をクビになった", self.頼む("GET", "/ita/shigoto")[2])
        self.assertNotIn("会社をクビになった", self.頼む("GET", "/ita/okane")[2])

    def test_03_止めた時は書きかけを残して理由を出す(self):
        状態, _, 文 = self.書く("上司は死ね<b>")
        self.assertEqual(状態, 400)
        self.assertIn("人を傷つける言葉", 文)
        self.assertIn("上司は死ね&lt;b&gt;</textarea>", 文)
        self.assertEqual(self.板の件数(), 0)

    def test_06_つらすぎる書き込みは置いて_書いた人にだけ相談先を出す(self):
        状態, 行き先, _ = self.書く("もう消えたい")
        self.assertEqual(行き先, "/ita/shigoto?sotto=1")
        self.assertEqual(self.板の件数(), 1)
        self.assertIn("よりそいホットライン", self.頼む("GET", 行き先)[2])
        self.assertNotIn("よりそいホットライン", self.頼む("GET", "/ita/shigoto", 人="B")[2])

    def test_08_二度押しでも1件だけ(self):
        self.書く("同じ話")
        状態, 行き先, _ = self.書く("同じ話")
        self.assertEqual((状態, 行き先), (303, "/ita/shigoto"))
        self.assertEqual(self.板の件数(), 1)

    def test_09_続けて書くと間をあけてもらい_時間がたてば書ける(self):
        self.書く("ひとつめ")
        状態, _, 文 = self.書く("ふたつめ")
        self.assertEqual(状態, 400)
        self.assertIn("少し間をあけて", 文)
        self.assertIn("ふたつめ</textarea>", 文)
        self.時計を戻す()
        self.assertEqual(self.書く("ふたつめ")[0], 303)
        self.assertEqual(self.板の件数(), 2)

    def test_10_わかるは1人1回で_数は出さない(self):
        self.書く("ふられた", 板="renai", 人="A")
        番号 = self.台帳.つなぎ.execute("SELECT MAX(番号) FROM 書き込み").fetchone()[0]
        self.頼む("GET", "/", 人="B")
        self.頼む("POST", f"/wakaru/{番号}", {}, 人="B")
        self.頼む("POST", f"/wakaru/{番号}", {}, 人="B")
        self.assertEqual(self.台帳.つなぎ.execute("SELECT COUNT(*) FROM わかる").fetchone()[0], 1)
        Bの画面 = self.頼む("GET", "/ita/renai", 人="B")[2]
        self.assertIn("わかった", Bの画面)
        Aの画面 = self.頼む("GET", "/ita/renai", 人="A")[2]
        self.assertIn("わかる、と言った人がいます", Aの画面)
        self.assertNotRegex(Aの画面, r"\d+\s*人")

    def test_11_消した書き込みは出ず_わかるも押せず_戻せる(self):
        self.書く("消される話")
        番号 = self.台帳.つなぎ.execute("SELECT MAX(番号) FROM 書き込み").fetchone()[0]
        self.消す(番号)
        self.assertNotIn("消される話", self.頼む("GET", "/ita/shigoto")[2])
        self.assertFalse(self.台帳.わかると押す(番号, "b" * 32))
        self.戻す(番号)
        self.assertIn("消される話", self.頼む("GET", "/ita/shigoto")[2])

    def test_12_見回りは合言葉が無いと開かず_消せない(self):
        self.書く("残る話")
        self.assertNotIn("残る話", self.頼む("GET", "/kanri")[2])
        self.assertEqual(self.見回りに入る("chigau", 人="A")[0], 403)
        self.assertNotIn("残る話", self.頼む("GET", "/kanri")[2])
        self.assertEqual(self.頼む("POST", "/kanri/kesu", {"aikotoba": "chigau", "bangou": 1})[0], 403)
        self.assertEqual(self.板の件数(), 1)
        self.assertIn("残る話", self.見回りの画面())

    def test_12b_合言葉を入れずに起動したら見回りは閉じたまま(self):
        閉じた場 = 場.場を作る(os.path.join(self.置き場, "閉.db"), "", 0)
        threading.Thread(target=閉じた場.serve_forever, daemon=True).start()
        try:
            # 空の合言葉を送っても入れない（空どうしを同じとみなさない）
            for 動き, 道, 本体 in (("GET", "/kanri", None), ("POST", "/kanri/hairu", "aikotoba="),
                                   ("POST", "/kanri/kesu", "aifuda=&bangou=1")):
                つなぎ = http.client.HTTPConnection("127.0.0.1", 閉じた場.server_port)
                つなぎ.request(動き, 道, 本体, {"Content-Type": "application/x-www-form-urlencoded"} if 本体 else {})
                返り = つなぎ.getresponse()
                返り.read()
                つなぎ.close()
                self.assertEqual(返り.status, 404, 道)
                self.assertNotIn(f"{場.札の名前}=", 返り.getheader("Set-Cookie") or "", 道)
        finally:
            閉じた場.shutdown()
            閉じた場.server_close()
            閉じた場.RequestHandlerClass.台帳.つなぎ.close()

    def test_15_書いた文字はそのまま文字として出る(self):
        self.書く('<script>alert("x")</script>\n2行目')
        文 = self.頼む("GET", "/ita/shigoto")[2]
        self.assertNotIn("<script>alert", 文)
        self.assertIn("&lt;script&gt;", 文)
        self.assertIn("<br>2行目", 文)

    def test_16_無い板や知らない場所は見つからない(self):
        self.assertEqual(self.頼む("GET", "/ita/nai")[0], 404)
        self.assertEqual(self.書く("どこへ", 板="nai")[0], 404)
        self.assertEqual(self.頼む("POST", "/wakaru/99999", {})[1], "/")

    def test_17_クッキーを受け取らないブラウザでも書ける(self):
        self.assertEqual(self.書く("鍵なしで書く", 人=None)[0], 303)
        self.assertEqual(self.板の件数(), 1)

    def test_18_控えは1日に1つ(self):
        self.書く("控えに残る話")
        控えの場所 = os.path.join(self.置き場, "控え")
        一回目 = self.台帳.控えを取る(控えの場所)
        二回目 = self.台帳.控えを取る(控えの場所)
        self.assertEqual(一回目, 二回目)
        self.assertEqual(len(os.listdir(控えの場所)), 1)
        控え = 台帳(一回目)
        self.assertEqual(控え.つなぎ.execute("SELECT 本文 FROM 書き込み").fetchone()[0], "控えに残る話")
        控え.つなぎ.close()


    # ---- 返事（案1 見方を変える返事） ----
    def 最後の番号(self):
        return self.台帳.つなぎ.execute("SELECT MAX(番号) FROM 書き込み").fetchone()[0]

    def 返す(self, 番号, 本文, 人="B"):
        return self.頼む("POST", f"/henji/{番号}", {"honbun": 本文}, 人)

    def test_20_返事は書き込みの下に古い順で出て_単独では並ばない(self):
        self.書く("40歳で無職になった")
        親 = self.最後の番号()
        状態, 行き先, _ = self.返す(親, "休めると見たら勝ちじゃない？")
        self.assertEqual((状態, 行き先), (303, f"/ita/shigoto#k{親}"))
        self.時計を戻す()
        self.返す(親, "わかる、自分もだった", 人="C")
        文 = self.頼む("GET", "/ita/shigoto")[2]
        self.assertLess(文.index("休めると見たら"), 文.index("自分もだった"))
        self.assertEqual(文.count('class="書き込み"'), 1)
        self.assertEqual(self.板の件数(), 3)

    def test_21_返事も人を叩く言葉は止め_書きかけをその返事欄に戻す(self):
        self.書く("ふられた")
        親 = self.最後の番号()
        状態, _, 文 = self.返す(親, "そんな奴は消えろ")
        self.assertEqual(状態, 400)
        self.assertIn("<details open>", 文)
        self.assertIn("そんな奴は消えろ</textarea>", 文)
        self.assertEqual(self.台帳.つなぎ.execute("SELECT COUNT(*) FROM 書き込み WHERE 親番号 IS NOT NULL").fetchone()[0], 0)

    def test_22_返事でつらすぎる言葉なら_書いた人に相談先を出す(self):
        self.書く("仕事がない")
        親 = self.最後の番号()
        self.assertEqual(self.返す(親, "自分も死にたい")[1], f"/ita/shigoto?sotto=1#k{親}")

    def test_23_消された書き込みや返事には返事を置かない(self):
        self.書く("消される話")
        親 = self.最後の番号()
        self.返す(親, "返事")
        返事 = self.最後の番号()
        self.時計を戻す()
        self.assertEqual(self.返す(返事, "返事への返事", 人="C")[1], "/ita/shigoto")
        self.台帳.消す(親)
        self.assertEqual(self.返す(親, "古い画面から", 人="D")[1], "/ita/shigoto")
        self.assertEqual(self.台帳.つなぎ.execute("SELECT COUNT(*) FROM 書き込み").fetchone()[0], 2)

    def test_24_返事を消すと出なくなり_見回りには返事先が出る(self):
        self.書く("話")
        親 = self.最後の番号()
        self.返す(親, "消される返事")
        返事 = self.最後の番号()
        self.assertIn(f"#{親}への返事", self.見回りの画面())
        self.消す(返事)
        self.assertNotIn("消される返事", self.頼む("GET", "/ita/shigoto")[2])

    def test_25_返事の二度押しでも1件(self):
        self.書く("話")
        親 = self.最後の番号()
        self.返す(親, "同じ返事")
        self.assertEqual(self.返す(親, "同じ返事")[0], 303)
        self.assertEqual(self.台帳.つなぎ.execute("SELECT COUNT(*) FROM 書き込み WHERE 親番号 = ?", (親,)).fetchone()[0], 1)

    def test_26_返事の列が無い前の版の台帳もそのまま開ける(self):
        import sqlite3
        前の場所 = os.path.join(self.置き場, "前の版.db")
        前 = sqlite3.connect(前の場所)
        前.executescript("""CREATE TABLE 書き込み (番号 INTEGER PRIMARY KEY AUTOINCREMENT, 板 TEXT NOT NULL, 本文 TEXT NOT NULL,
            書いた人の鍵 TEXT NOT NULL, 書いた時刻 TEXT NOT NULL, 消した時刻 TEXT);
            INSERT INTO 書き込み (板, 本文, 書いた人の鍵, 書いた時刻) VALUES ('shigoto', '前の書き込み', 'a', '2026-10-23T00:00:00+00:00');""")
        前.commit()
        前.close()
        開いた = 台帳(前の場所)
        self.assertEqual([行["本文"] for 行 in 開いた.板の書き込み("shigoto", "x")], ["前の書き込み"])
        開いた.つなぎ.close()

    def test_27_返事にもわかるが押せて_1人1回で数は出さない(self):
        self.書く("話")
        親 = self.最後の番号()
        self.返す(親, "わかるよ")
        返事 = self.最後の番号()
        状態, 行き先, _ = self.頼む("POST", f"/wakaru/{返事}", {}, 人="C")
        self.assertEqual(行き先, f"/ita/shigoto#k{返事}")
        self.頼む("POST", f"/wakaru/{返事}", {}, 人="C")
        self.assertEqual(self.台帳.つなぎ.execute("SELECT COUNT(*) FROM わかる WHERE 書き込み番号 = ?", (返事,)).fetchone()[0], 1)
        Cの画面 = self.頼む("GET", "/ita/shigoto", 人="C")[2]
        返事の所 = Cの画面[Cの画面.index(f'id="k{返事}"'):]
        self.assertIn("わかった", 返事の所)
        親の所 = Cの画面[Cの画面.index(f'id="k{親}"'):Cの画面.index(f'id="k{返事}"')]
        self.assertNotIn("わかった", 親の所)

    # ---- 今日の小さな勝ち（案3） ----
    def 勝ちを置く(self, 本文, 人="A"):
        return self.頼む("POST", "/kachi/kaku", {"honbun": 本文}, 人)

    def test_28_勝ちは勝ちの場所にだけ出て_はじめの画面から行ける(self):
        self.assertIn('href="/kachi"', self.頼む("GET", "/")[2])
        状態, 行き先, _ = self.勝ちを置く("今日は布団から出た")
        self.assertEqual((状態, 行き先), (303, "/kachi"))
        self.assertIn("今日は布団から出た", self.頼む("GET", "/kachi")[2])
        for 板 in 決まり.板の一覧を読む():
            self.assertNotIn("今日は布団から出た", self.頼む("GET", f"/ita/{板.鍵}")[2])
        self.assertNotIn(決まり.勝ちの置き場, [板.鍵 for 板 in 決まり.板の一覧を読む()])

    def test_29_勝ちは100字までの1行(self):
        self.assertEqual(self.勝ちを置く("あ" * 101)[0], 400)
        self.assertEqual(self.勝ちを置く("あ" * 100)[0], 303)
        self.時計を戻す()
        self.勝ちを置く("ご飯を\n作った")
        self.assertEqual(self.台帳.つなぎ.execute("SELECT 本文 FROM 書き込み ORDER BY 番号 DESC").fetchone()[0], "ご飯を 作った")

    def test_30_勝ちにも守りが効き_止めた時は書きかけを残す(self):
        状態, _, 文 = self.勝ちを置く("上司に死ねと言えた")
        self.assertEqual(状態, 400)
        self.assertIn('value="上司に死ねと言えた"', 文)
        self.assertEqual(self.勝ちを置く("消えたいけど起きた", 人="B")[1], "/kachi?sotto=1")

    def test_31_勝ちには_それ勝ち_と押せて数は出さない(self):
        self.勝ちを置く("歯をみがいた")
        番号 = self.最後の番号()
        self.assertIn("それ、勝ち", self.頼む("GET", "/kachi", 人="B")[2])
        self.assertEqual(self.頼む("POST", f"/wakaru/{番号}", {}, 人="B")[1], f"/kachi#k{番号}")
        self.assertIn("勝ちと言った", self.頼む("GET", "/kachi", 人="B")[2])
        Aの画面 = self.頼む("GET", "/kachi", 人="A")[2]
        self.assertIn("勝ち、と言った人がいます", Aの画面)
        self.assertNotRegex(Aの画面, r"\d+\s*人")

    def test_32_勝ちに返事は置かず_見回りには勝ちと出る(self):
        self.勝ちを置く("散歩した")
        番号 = self.最後の番号()
        self.assertEqual(self.返す(番号, "えらい")[1], "/kachi")
        self.assertEqual(self.台帳.つなぎ.execute("SELECT COUNT(*) FROM 書き込み").fetchone()[0], 1)
        self.assertIn("今日の小さな勝ち", self.見回りの画面())

    # ---- ゆるい名乗り（案5） ----
    def 名乗る(self, 名乗り, 人="A"):
        return self.頼む("POST", "/nanori", {"nanori": 名乗り}, 人)

    def test_33_名乗ると_その後の書き込みと返事と勝ちに出て_無ければ名無し(self):
        self.書く("名乗る前", 人="A")
        self.時計を戻す()
        self.assertEqual(self.名乗る("元・就活全落ち")[1], "/#nanori")
        self.assertIn('value="元・就活全落ち"', self.頼む("GET", "/")[2])
        self.書く("名乗った後")
        親 = self.最後の番号()
        self.時計を戻す()
        self.返す(親, "返事も名乗る", 人="A")
        self.時計を戻す()
        self.勝ちを置く("勝ちも名乗る")
        板 = self.頼む("GET", "/ita/shigoto")[2]
        self.assertIn("元・就活全落ち</a>", 板)
        self.assertIn("名無し", 板)
        self.assertIn("元・就活全落ち として書きます", 板)
        self.assertIn("元・就活全落ち</a>", self.頼む("GET", "/kachi")[2])
        self.assertEqual(self.台帳.つなぎ.execute("SELECT COUNT(*) FROM 書き込み WHERE 名乗り = '元・就活全落ち'").fetchone()[0], 3)

    def test_34_名乗りを変えても_前の書き込みは書いた時のまま(self):
        self.名乗る("元・営業")
        self.書く("前の話")
        self.名乗る("元・営業、いま無職")
        文 = self.頼む("GET", "/ita/shigoto")[2]
        self.assertIn("元・営業</a>", 文)
        self.assertNotIn("元・営業、いま無職</a>", 文)

    def test_35_名乗りを空にすると名無しに戻る(self):
        self.名乗る("元・受験生")
        self.名乗る("\u3000 ")
        self.書く("名無しで書く")
        self.assertIsNone(self.台帳.つなぎ.execute("SELECT 名乗り FROM 書き込み").fetchone()[0])
        self.assertIn("名無し として書きます", self.頼む("GET", "/ita/shigoto")[2])

    def test_36_同じ名乗りの書き込みを_書き方の違いもそろえて見られる(self):
        self.名乗る("バツイチ", 人="A")
        self.書く("離婚した", 板="kazoku", 人="A")
        self.名乗る("ﾊﾞﾂｲﾁ", 人="B")
        self.書く("自分もです", 板="renai", 人="B")
        self.名乗る("バツイチ", 人="C")
        self.書く("消される話", 板="renai", 人="C")
        self.台帳.消す(self.最後の番号())
        状態, _, 文 = self.頼む("GET", "/nanori?n=" + quote("バツイチ"))
        self.assertEqual(状態, 200)
        self.assertIn("離婚した", 文)
        self.assertIn("自分もです", 文)
        self.assertNotIn("消される話", 文)
        self.assertIn('href="/ita/kazoku#k', 文)
        self.assertEqual(self.頼む("GET", "/nanori?n=")[1], "/")

    def test_37_名乗りにも守りと20字までが効く(self):
        状態, _, 文 = self.名乗る("上司は死ね")
        self.assertEqual(状態, 400)
        self.assertIn('value="上司は死ね"', 文)
        self.assertEqual(self.名乗る("あ" * 21)[0], 400)
        self.assertEqual(self.台帳.名乗りを読む(self.鍵("A")), "")
        self.assertEqual(self.名乗る("あ" * 20)[0], 303)

    def test_38_名乗りの記号はそのまま文字として出る(self):
        self.名乗る('<b>"x"&')
        self.書く("話")
        文 = self.頼む("GET", "/ita/shigoto")[2]
        self.assertIn("&lt;b&gt;&quot;x&quot;&amp;</a>", 文)
        self.assertIn('href="/nanori?n=%3Cb%3E%22x%22%26"', 文)

    def test_64_名乗りを止めた時も相談先を出す時も_名乗りの欄のそばに出る(self):
        状態, _, 文 = self.名乗る("上司は死ね")
        self.assertEqual(状態, 400)
        self.assertLess(文.index('id="nanori"'), 文.index('class="断り"'))
        self.assertEqual(self.名乗る("消えたい")[1], "/?sotto=1#nanori")
        文 = self.頼む("GET", "/?sotto=1")[2]
        self.assertLess(文.index('id="nanori"'), 文.index('class="そっと"'))

    def test_68_表に出すのは禅の言葉で_負けを問う言葉は出さない(self):
        はじめ = self.頼む("GET", "/")[2]
        self.assertLess(はじめ.index('class="禅語"'), はじめ.index('href="/ita/'))
        self.書く("会社をクビになった")
        for 場所 in ["/", "/ita/shigoto", "/ita/sonota", "/sonogo", "/kimari", "/kojin", "/shiraseru"]:
            文 = self.頼む("GET", 場所)[2]
            for 言葉 in ["本当に負け", "負けじゃなく", "「負け」"]:
                self.assertNotIn(言葉, 文, 場所)

    def 生で(self, 動き, 道, 見出したち=(), 本体=b""):
        """道や見出しを、そのままのバイト列で頼む（http.client では送れない形のため）。(状態, 全部の返り) か (None, "")。"""
        with socket.create_connection(("127.0.0.1", self.場.server_port), timeout=15) as s:
            s.sendall(動き + b" " + 道 + b" HTTP/1.1\r\nHost: t\r\nConnection: close\r\n" + b"".join(行 + b"\r\n" for 行 in 見出したち) + b"\r\n" + 本体)
            返り = b""
            while True:
                片 = s.recv(65536)
                if not 片:
                    break
                返り += 片
        合う = re.match(rb"HTTP/\d\.\d (\d+)", 返り)
        return (int(合う.group(1)) if 合う else None), 返り.decode("utf-8", "replace")

    @unittest.skipUnless(os.path.isdir("/proc/self/fd"), "ファイルの口を数えるのは Linux だけ")
    def test_140_1人分を返すたびに_記録へのつなぎを閉じる(self):
        def 口の数():
            数 = 0
            for 名 in os.listdir("/proc/self/fd"):
                try:
                    数 += os.readlink(f"/proc/self/fd/{名}").startswith(self.置き場)
                except OSError:
                    pass
            return 数
        gc.disable()  # 片付けの巡回に頼らず、返すたびに閉じていることを見る
        self.addCleanup(gc.enable)
        self.頼む("GET", "/")
        始め = 口の数()
        for _ in range(30):
            self.頼む("GET", "/ita/shigoto")
        # 閉じないと 30回×3つの口 が増える。SQLite は同じファイルの口を少しの間だけ持ち越すことがあるので、数個の揺れは許す
        for _ in range(40):
            if 口の数() <= 始め + 5:
                break
            time.sleep(0.05)
        self.assertLessEqual(口の数(), 始め + 5, "返した後もつなぎが開いたまま残っている")

    def test_141_記録が塞がって置けない時は_黙って切らず_書いた字を残して日本語で知らせる(self):
        self.台帳.待つ秒 = 0.1
        塞ぐ = sqlite3.connect(self.台帳.場所, timeout=1, isolation_level=None)
        self.addCleanup(塞ぐ.close)
        塞ぐ.execute("BEGIN IMMEDIATE")
        with contextlib.redirect_stderr(io.StringIO()) as 記録:
            状態, _, 文 = self.書く("塞がっている時の<話>")
        塞ぐ.execute("ROLLBACK")
        self.assertEqual(状態, 503)
        self.assertIn("置けませんでした", 文)
        self.assertIn("database is locked", 記録.getvalue())  # 場の記録には訳を残す
        self.assertNotIn("塞がっている時の", 記録.getvalue())  # 書いた字は場の記録に出さない
        self.assertIn("塞がっている時の&lt;話&gt;", 文)  # 字は戻すが、タグのまま出さない
        self.assertNotIn("塞がっている時の<話>", 文)
        self.assertIn('action="/ita/shigoto/kaku"', 文)
        self.assertIn('<textarea name="honbun"', 文)
        self.assertEqual(self.返りの見出し.get("Cache-Control"), "no-store")
        self.assertEqual(self.板の件数(), 0)
        # 同じ欄からもう一度送ると置ける
        self.assertEqual(self.書く("塞がっている時の<話>")[0], 303)
        self.assertEqual(self.板の件数(), 1)

    def test_141b_思わぬ誤りの時も_その後の話は両方の欄を戻し_合言葉や合い札は画面に戻さず_見る画面は日本語で知らせる(self):
        self.台帳.待つ秒 = 0.1
        塞ぐ = sqlite3.connect(self.台帳.場所, timeout=1, isolation_level=None)
        self.addCleanup(塞ぐ.close)
        塞ぐ.execute("BEGIN IMMEDIATE")
        with contextlib.redirect_stderr(io.StringIO()):
            文 = self.頼む("POST", "/sonogo/kaku", {"ano": "あの時の字", "honbun": "その後の字"})[2]
            入口 = self.頼む("POST", "/kanri/hairu", {"aikotoba": "ひみつの合言葉の試し"})
        塞ぐ.execute("ROLLBACK")
        self.assertIn('name="ano"', 文)
        self.assertIn("あの時の字", 文)
        self.assertIn("その後の字", 文)
        self.assertNotIn("ひみつの合言葉の試し", 入口[2])
        with mock.patch.object(self.台帳, "板の書き込み", side_effect=sqlite3.OperationalError("disk I/O error")), contextlib.redirect_stderr(io.StringIO()):
            状態, _, 文 = self.頼む("GET", "/ita/shigoto")
        self.assertEqual(状態, 503)
        self.assertIn("うまくいきませんでした", 文)
        # 見回りの動きは、札と合い札を欄に戻さない
        合い札 = self.合い札()
        self.書く("見回りの試し")
        番号 = self.最後の番号()
        with mock.patch.object(self.台帳, "消す", side_effect=sqlite3.OperationalError("disk I/O error")), contextlib.redirect_stderr(io.StringIO()):
            状態, _, 文 = self.頼む("POST", "/kanri/kesu", {"aifuda": 合い札, "bangou": 番号}, "持ち主")
        self.assertEqual(状態, 503)
        self.assertNotIn(合い札, 文)
        self.assertIn('href="/kanri"', 文)

    def test_142_別のサイトからの送信は_置かずに断る(self):
        self.書く("押される話")
        番号 = self.最後の番号()
        for 値 in ("cross-site", "same-site"):
            for 道, 中身 in [("/ita/shigoto/kaku", {"honbun": "仕掛けられた話"}), ("/nanori", {"nanori": "仕掛け"}), (f"/wakaru/{番号}", {}), (f"/henji/{番号}", {"honbun": "仕掛け"}),
                            ("/shiraseru", {"honbun": "仕掛け"}), ("/heya/ukenai", {}), ("/kachi/kaku", {"honbun": "仕掛け"}), ("/kanri/hairu", {"aikotoba": self.合言葉})]:
                状態, _, 文 = self.頼む("POST", 道, 中身, "よそ", {"Sec-Fetch-Site": 値})
                self.assertEqual(状態, 403, f"{道} {値}")
                self.assertIn("このサイトの画面から", 文)
        読む = self.台帳.つなぎ
        self.assertEqual(読む.execute("SELECT COUNT(*) FROM 書き込み").fetchone()[0], 1)
        self.assertEqual(読む.execute("SELECT COUNT(*) FROM 知らせ").fetchone()[0], 0)
        self.assertEqual(読む.execute("SELECT COUNT(*) FROM わかる").fetchone()[0], 0)
        self.assertEqual(読む.execute("SELECT COUNT(*) FROM 名乗り").fetchone()[0], 0)
        self.assertEqual(読む.execute("SELECT COUNT(*) FROM 小部屋を受けない").fetchone()[0], 0)
        # このサイトの画面から（same-origin）と、見出しを送らない古いブラウザや道具は受ける
        self.assertEqual(self.頼む("POST", "/ita/shigoto/kaku", {"honbun": "同じサイトの話"}, "B", {"Sec-Fetch-Site": "same-origin"})[0], 303)
        self.assertEqual(self.頼む("POST", "/ita/shigoto/kaku", {"honbun": "見出しなしの話"}, "C")[0], 303)

    def test_143_親を消した返事は_名乗りの頁に出さず_親を戻すとまた出る(self):
        self.名乗る("試しの人", 人="B")
        self.書く("親の話", 人="A")
        親 = self.最後の番号()
        self.返す(親, "親を引用した返事", 人="B")
        道 = "/nanori?n=" + quote("試しの人")
        self.assertIn("親を引用した返事", self.頼む("GET", 道, 人="C")[2])
        self.消す(親)
        self.assertNotIn("親を引用した返事", self.頼む("GET", 道, 人="C")[2])
        self.戻す(親)
        self.assertIn("親を引用した返事", self.頼む("GET", 道, 人="C")[2])

    def test_144_番号の形が違っても黙って切らず_無い物として扱う(self):
        self.見回りに入る()
        札 = self.クッキー["持ち主"][場.札の名前]
        大 = b"9" * 25
        長 = b"9" * 5000
        with contextlib.redirect_stderr(io.StringIO()) as 記録:
            for 道 in [b"/heya/\xb2", b"/heya/" + 大, b"/heya/" + 長]:
                self.assertEqual(self.生で(b"GET", 道)[0], 404, 道[:20])
            for 道 in [b"/shiraseru?bangou=%C2%B2", b"/shiraseru?bangou=%E2%91%A0", b"/shiraseru?bangou=" + 大, b"/shiraseru?bangou=" + 長]:
                self.assertEqual(self.生で(b"GET", 道)[0], 200, 道[:30])
            for 道 in [b"/henji/" + 大, b"/wakaru/" + 大, b"/musubu/" + 大, b"/heya/" + 大 + b"/kaku", b"/wakaru/\xb2"]:
                self.assertEqual(self.生で(b"POST", 道, [b"Content-Length: 0"])[0], 404, 道[:20])
            for 中身, 期待 in [({"bangou": "²", "honbun": "x"}, 303), ({"bangou": "9" * 25, "honbun": "y"}, 303), ({"bangou": "9" * 5000, "honbun": "z"}, 303)]:
                self.assertEqual(self.頼む("POST", "/shiraseru", 中身, 中身["honbun"])[0], 期待)
            for 値 in ["²", "9" * 25]:
                self.assertEqual(self.頼む("POST", "/heya/hiraku", {"bangou": 値})[0], 303)
                self.assertEqual(self.頼む("POST", "/kanri/kesu", {"aifuda": self.合い札(), "bangou": 値}, "持ち主")[0], 404)
                self.assertEqual(self.頼む("GET", f"/kanri/matome?bangou={quote(値)}", 人="持ち主")[0], 404)
                self.assertEqual(self.頼む("POST", "/kanri/matomete-kesu", {"aifuda": self.合い札(), "bangou": 値, "made": 値}, "持ち主")[0], 404)
            # 送信の長さの見出しが壊れていても、待たせず切らず、空の送信として扱う
            for 長さ in [b"abc", b"-1", b"9" * 25]:
                self.assertEqual(self.生で(b"POST", b"/nanori", [b"Content-Length: " + 長さ])[0], 303, 長さ[:10])
        self.assertEqual(記録.getvalue(), "")  # 場の誤りとして残らない
        self.assertTrue(札)

    def test_145_変な名前のクッキーが混ざっても開け_鍵は読め_形の違う鍵には新しい鍵を渡す(self):
        self.書く("鍵の試し")
        鍵 = self.鍵("A")
        with contextlib.redirect_stderr(io.StringIO()) as 記録:
            for 混ざる in ["a/b=1", "a,b=1", "名前=1", "path=1", "a[b]=1", "x", ";;;", '"="']:
                状態, 文 = self.生で(b"GET", b"/", [f"Cookie: {混ざる}; {場.鍵の名前}={鍵}; z=1".encode("utf-8")])
                self.assertEqual(状態, 200, 混ざる)
                self.assertNotIn("Set-Cookie", 文, 混ざる)  # 鍵は読めたので、新しい鍵を渡さない
            for 形の違う鍵 in ["あ" * 32, "g" * 32, "A" * 32, "a" * 31, "a" * 33, '"' + "a" * 30 + '"']:
                状態, 文 = self.生で(b"GET", b"/", [f"Cookie: {場.鍵の名前}={形の違う鍵}".encode("utf-8")])
                self.assertEqual(状態, 200, 形の違う鍵)
                self.assertIn("Set-Cookie: " + 場.鍵の名前, 文, 形の違う鍵)
        self.assertEqual(記録.getvalue(), "")

    def test_146_HEADは同じ見出しで本文を返さない(self):
        for 道, 期待 in [(b"/", 200), (b"/ita/shigoto", 200), (b"/kimari", 200), (b"/nai", 404)]:
            状態, 文 = self.生で(b"HEAD", 道)
            self.assertEqual(状態, 期待, 道)
            self.assertEqual(文.split("\r\n\r\n", 1)[1], "", 道)
            self.assertIn("Content-Type: text/html", 文, 道)

    def test_147_小部屋の場所は_入れない人には出さない(self):
        部屋 = self.台帳.小部屋を開く("試し", "a" * 32, "b" * 32)
        話 = self.台帳.書く(決まり.小部屋の置き場(部屋), "2人だけの話", "a" * 32)
        for 動き, 道, 中身 in [("POST", f"/wakaru/{話}", {}), ("POST", f"/henji/{話}", {"honbun": "のぞき"})]:
            状態, 行き先, _ = self.頼む(動き, 道, 中身, "よそ")
            self.assertEqual((状態, 行き先), (303, "/"), 道)
        self.assertEqual(self.台帳.つなぎ.execute("SELECT COUNT(*) FROM わかる").fetchone()[0], 0)
        # 部屋の2人には今までどおり部屋へ戻す
        状態, 行き先, _ = self.頼む("POST", f"/wakaru/{話}", {}, None, {"Cookie": f"{場.鍵の名前}={'a' * 32}"})
        self.assertEqual((状態, 行き先), (303, f"/heya/{部屋}#k{話}"))

    def test_133_さっきの話の段に_検索の文に出さない印が付く(self):
        self.書く("検索の文に出さない話", 人="A")
        self.assertIn('<div class="いまの話たち" data-nosnippet>', self.頼む("GET", "/", 人="B")[2])

    def test_159_はじめの画面の題と説明は_探す人の言葉と持ち主の文で_ほかの画面は今までどおり(self):
        文 = self.頼む("GET", "/")[2]
        self.assertIn("<title>負け犬の癒し｜匿名で愚痴を吐き出せる掲示板</title>", 文)
        self.assertEqual(re.findall(r'<meta name="description" content="([^"]*)">', 文),
                         ["ポジティブでいろ。前向きな言葉を使おう。元気出していこう。・・・うるせーな。わかってんだよ。"
                          "いいじゃねえかよネガティブにいたってよ。無理に前を向かなくていいんだよ。"])
        for 道, 題 in (("/ita/shigoto", "仕事の板"), ("/kachi", "今日の小さな勝ち"), ("/kimari", "利用の決まり")):
            文 = self.頼む("GET", 道)[2]
            self.assertIn(f"<title>{題}｜負け犬の癒し</title>", 文, 道)
            self.assertNotIn('name="description"', 文, 道)  # 検索に出さない画面には付けない

    def test_69_はじめの画面に板の新しい話が3つだけ出て_名乗りも消した話も板の外も出ない(self):
        self.assertNotIn("さっきの話", self.頼む("GET", "/")[2])  # まだ何も無い時は、段ごと出さない
        self.名乗る("元・店長", 人="A")
        self.書く("一つ目の話", 人="A")
        self.書く("二つ目の話", 板="okane", 人="B")
        親 = self.最後の番号()
        self.返す(親, "三つ目は返事", 人="C")
        self.書く("四つ目の話" + "あ" * 60, 板="renai", 人="D")
        self.つぶやく("独り言は出ない", 人="E")
        文 = self.頼む("GET", "/", 人="F")[2]  # 名乗ったAの画面には、A自身の名乗りの欄があるので、別の人で見る
        self.assertIn("さっきの話", 文)
        self.assertNotIn("一つ目の話", 文)  # 新しい3つだけ
        self.assertIn(f'href="/ita/okane#k{親}"', 文)
        self.assertIn("お金への返事", 文)
        self.assertIn("四つ目の話" + "あ" * 35 + "…", 文)  # 長い話は40字で切る
        self.assertNotIn("独り言は出ない", 文)
        self.assertNotIn("元・店長", 文)
        self.消す(親)
        文 = self.頼む("GET", "/")[2]
        self.assertNotIn("二つ目の話", 文)
        self.assertNotIn("三つ目は返事", 文)  # 消した話への返事も出さない
        self.assertLess(文.index('class="板たち"'), 文.index("さっきの話"))  # 板はその上のまま

    # ---- 同時に来た時（公開の前に） ----
    def 一斉に(self, 動きたち):
        """動きたちを、できるだけ同じ瞬間に始める。返りは動きの順。"""
        合図 = threading.Barrier(len(動きたち))
        返りたち = [None] * len(動きたち)

        def 走る(i, 動き):
            合図.wait()
            try:
                返りたち[i] = 動き()
            except Exception as 例外:  # 失敗した動きは、何で失敗したかを残して比べる
                返りたち[i] = (type(例外).__name__, None, str(例外))

        糸たち = [threading.Thread(target=走る, args=(i, 動き)) for i, 動き in enumerate(動きたち)]
        for 糸 in 糸たち:
            糸.start()
        for 糸 in 糸たち:
            糸.join(30)
        return 返りたち

    def test_70_20人が同時に書いても_全部が1件ずつ残る(self):
        人たち = [f"人{i}" for i in range(20)]
        for 人 in 人たち:
            self.頼む("GET", "/", 人=人)
        返りたち = self.一斉に([lambda 人=人: self.書く(f"{人}の話", 人=人) for 人 in 人たち])
        self.assertEqual([返り[0] for 返り in 返りたち], [303] * 20)
        self.assertEqual(self.板の件数(), 20)
        文 = self.頼む("GET", "/ita/shigoto")[2]
        for 人 in 人たち:
            self.assertIn(f"{人}の話", 文)

    def test_71_同じ人が同時に何度送っても_1件だけ置く(self):
        self.頼む("GET", "/")
        # 送るボタンを何度も押した（同じ文）
        返りたち = self.一斉に([lambda: self.書く("同時の二度押し")] * 5)
        self.assertEqual([返り[0] for 返り in 返りたち], [303] * 5)
        self.assertEqual(self.板の件数(), 1)
        # 別々の文を同時に（連投）。1件だけ置き、ほかは間をあけてもらう
        self.時計を戻す()
        返りたち = self.一斉に([lambda i=i: self.書く(f"連投{i}") for i in range(5)])
        self.assertEqual(sorted(返り[0] for 返り in 返りたち), [303] + [400] * 4)
        self.assertEqual(self.板の件数(), 2)

    def test_72_送るのが遅い人がいても_ほかの人はすぐ見られる(self):
        import socket
        import time

        遅い人 = socket.create_connection(("127.0.0.1", self.場.server_port))
        try:
            遅い人.sendall(b"POST /ita/shigoto/kaku HTTP/1.1\r\nHost: x\r\n")  # 途中で止まったまま
            始め = time.monotonic()
            self.assertEqual(self.頼む("GET", "/ita/shigoto", 人="B")[0], 200)
            self.assertLess(time.monotonic() - 始め, 3)
        finally:
            遅い人.close()

    def test_73_書いている最中に取った控えも_欠けずに開ける(self):
        self.頼む("GET", "/")
        self.書く("控えの前の話")
        控えの場所 = os.path.join(self.置き場, "控え")
        返りたち = self.一斉に(
            [lambda 人=f"人{i}": self.書く(f"{人}の話", 人=人) for i in range(5)] + [lambda: self.台帳.控えを取る(控えの場所)]
        )
        控え = 台帳(返りたち[-1])
        try:
            self.assertEqual(控え.つなぎ.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertIn("控えの前の話", [行[0] for 行 in 控え.つなぎ.execute("SELECT 本文 FROM 書き込み")])
        finally:
            控え.閉じる()

    # ---- 返事のいらない独り言（案8） ----
    def つぶやく(self, 本文, 人="A"):
        return self.頼む("POST", "/hitori/kaku", {"honbun": 本文}, 人)

    def test_39_独り言はその場所にだけ出て_名乗りもわかるも返事も無い(self):
        self.assertIn('href="/hitori"', self.頼む("GET", "/")[2])
        self.名乗る("元・店長")
        状態, 行き先, _ = self.つぶやく("もう何もしたくない")
        self.assertEqual((状態, 行き先), (303, "/hitori"))
        文 = self.頼む("GET", "/hitori", 人="B")[2]
        self.assertIn("もう何もしたくない", 文)
        for 出ない物 in ("元・店長", "名無し", "/wakaru/", "/henji/", "<details"):
            self.assertNotIn(出ない物, 文)
        self.assertIsNone(self.台帳.つなぎ.execute("SELECT 名乗り FROM 書き込み").fetchone()[0])
        self.assertNotIn("もう何もしたくない", self.頼む("GET", "/nanori?n=" + quote("元・店長"))[2])
        for 板 in 決まり.板の一覧を読む():
            self.assertNotIn("もう何もしたくない", self.頼む("GET", f"/ita/{板.鍵}")[2])

    def test_40_独り言は24時間で画面から消え_見回りには残る(self):
        self.つぶやく("消える話")
        # 書いた時刻を1分前に決めてから見る（Windows の時計は粗く、書いてすぐ読むと経った時間が0になり「あと24時間」と出ることがある）
        self.台帳.つなぎ.execute("UPDATE 書き込み SET 書いた時刻 = ?", ((時計.いま() - timedelta(minutes=1)).isoformat(),))
        self.assertIn("あと23時間で消えます", self.頼む("GET", "/hitori")[2])
        self.台帳.つなぎ.execute("UPDATE 書き込み SET 書いた時刻 = ?", ((時計.いま() - timedelta(hours=23, minutes=30)).isoformat(),))
        self.assertIn("もうすぐ消えます", self.頼む("GET", "/hitori")[2])
        self.台帳.つなぎ.execute("UPDATE 書き込み SET 書いた時刻 = ?", ((時計.いま() - timedelta(hours=24, seconds=1)).isoformat(),))
        self.assertNotIn("消える話", self.頼む("GET", "/hitori")[2])
        self.assertIn("消える話", self.見回りの画面())

    def test_41_独り言にわかるや返事を送っても何も置かない(self):
        self.つぶやく("ひとりごと")
        番号 = self.最後の番号()
        self.assertEqual(self.頼む("POST", f"/wakaru/{番号}", {}, 人="B")[1], f"/hitori#k{番号}")
        self.assertEqual(self.返す(番号, "返事")[1], "/hitori")
        self.assertEqual(self.台帳.つなぎ.execute("SELECT COUNT(*) FROM わかる").fetchone()[0], 0)
        self.assertEqual(self.台帳.つなぎ.execute("SELECT COUNT(*) FROM 書き込み").fetchone()[0], 1)

    def test_42_独り言にも守りが効き_つらすぎる時は相談先(self):
        状態, _, 文 = self.つぶやく("あいつは死ね")
        self.assertEqual(状態, 400)
        self.assertIn("あいつは死ね</textarea>", 文)
        self.assertEqual(self.つぶやく("消えたい", 人="B")[1], "/hitori?sotto=1")
        self.assertIn("よりそいホットライン", self.頼む("GET", "/hitori?sotto=1", 人="B")[2])

    # ---- その後の話の棚（案6） ----
    def 棚に置く(self, あの時, その後, 人="A"):
        return self.頼む("POST", "/sonogo/kaku", {"ano": あの時, "honbun": その後}, 人)

    def test_43_棚に置くと_あの時とその後が並び_その場所にだけ出る(self):
        self.assertIn('href="/sonogo"', self.頼む("GET", "/")[2])
        self.名乗る("元・浪人")
        状態, 行き先, _ = self.棚に置く("受験に全部落ちた", "働きながら資格を取って、今は好きな仕事をしてる")
        self.assertEqual((状態, 行き先), (303, "/sonogo"))
        文 = self.頼む("GET", "/sonogo")[2]
        self.assertLess(文.index("受験に全部落ちた"), 文.index("働きながら資格を取って"))
        self.assertIn("元・浪人</a>", 文)
        for 板 in 決まり.板の一覧を読む():
            self.assertNotIn("受験に全部落ちた", self.頼む("GET", f"/ita/{板.鍵}")[2])
        self.assertIn("受験に全部落ちた", self.頼む("GET", "/nanori?n=" + quote("元・浪人"))[2])

    def test_44_あの時かその後が欠けたら断り_両方の書きかけを残す(self):
        状態, _, 文 = self.棚に置く("", "その後だけ書いた")
        self.assertEqual(状態, 400)
        self.assertIn("「あの時」も書いてください", 文)
        self.assertIn("その後だけ書いた</textarea>", 文)
        状態, _, 文 = self.棚に置く("あの時だけ書いた", "")
        self.assertEqual(状態, 400)
        self.assertIn('value="あの時だけ書いた"', 文)
        self.assertEqual(self.棚に置く("あ" * 201, "その後")[0], 400)
        self.assertEqual(self.棚に置く("あ" * 200, "その後")[0], 303)

    def test_45_あの時にも守りが効き_つらすぎる言葉なら相談先(self):
        状態, _, 文 = self.棚に置く("上司に死ねと言われた", "辞めて正解だった")
        self.assertEqual(状態, 400)
        self.assertIn("「あの時」は人を傷つける言葉", 文)
        self.assertEqual(self.棚に置く("死にたいと思った", "今は生きててよかった", 人="B")[1], "/sonogo?sotto=1")

    def test_46_棚の話には_沁みた_と押せて数は出さない(self):
        self.棚に置く("離婚した", "ひとりの暮らしが気に入ってる")
        番号 = self.最後の番号()
        self.assertEqual(self.頼む("POST", f"/wakaru/{番号}", {}, 人="B")[1], f"/sonogo#k{番号}")
        self.assertIn("沁みた、と言った人がいます", self.頼む("GET", "/sonogo", 人="A")[2])
        self.assertNotRegex(self.頼む("GET", "/sonogo", 人="A")[2], r"\d+\s*人")

    # ---- もう一回の宣言（案12） ----
    def 宣言する(self, 本文, 人="A"):
        return self.頼む("POST", "/mouikkai/kaku", {"honbun": 本文}, 人)

    def test_47_宣言は1行で置け_もう一回_を頭に付けて出る(self):
        self.assertIn('href="/mouikkai"', self.頼む("GET", "/")[2])
        self.名乗る("元・picker")
        self.assertEqual(self.宣言する("来月、面接を\n受けてみる")[1], "/mouikkai")
        文 = self.頼む("GET", "/mouikkai", 人="B")[2]
        self.assertIn("もう一回、来月、面接を 受けてみる", 文)
        self.assertIn("元・picker</a>", 文)
        self.時計を戻す()
        self.assertEqual(self.宣言する("あ" * 101)[0], 400)
        self.assertEqual(self.宣言する("あ" * 100)[0], 303)

    def test_48_宣言には_見守る_だけ押せて数は出さず_返事は置かない(self):
        self.宣言する("資格の試験をもう一回")
        番号 = self.最後の番号()
        self.assertEqual(self.頼む("POST", f"/wakaru/{番号}", {}, 人="B")[1], f"/mouikkai#k{番号}")
        self.assertIn("見守ってる", self.頼む("GET", "/mouikkai", 人="B")[2])
        Aの画面 = self.頼む("GET", "/mouikkai", 人="A")[2]
        self.assertIn("見守っている人がいます", Aの画面)
        self.assertNotRegex(Aの画面, r"\d+\s*人")
        self.assertEqual(self.返す(番号, "がんばれ")[1], "/mouikkai")
        self.assertEqual(self.台帳.つなぎ.execute("SELECT COUNT(*) FROM 書き込み").fetchone()[0], 1)

    def test_49_結びは宣言した本人だけが1回だけ付けられる(self):
        self.宣言する("もう一回、絵を描く")
        番号 = self.最後の番号()
        self.assertIn(f'action="/musubu/{番号}"', self.頼む("GET", "/mouikkai", 人="A")[2])
        self.頼む("GET", "/", 人="B")
        self.assertNotIn("/musubu/", self.頼む("GET", "/mouikkai", 人="B")[2])
        self.頼む("POST", f"/musubu/{番号}", {"musubi": "yatta"}, 人="B")
        self.頼む("POST", f"/musubu/{番号}", {"musubi": "warui"}, 人="A")
        self.assertIsNone(self.台帳.つなぎ.execute("SELECT 結び FROM 書き込み").fetchone()[0])
        self.assertEqual(self.頼む("POST", f"/musubu/{番号}", {"musubi": "yameta"}, 人="A")[1], f"/mouikkai#k{番号}")
        self.頼む("POST", f"/musubu/{番号}", {"musubi": "yatta"}, 人="A")
        文 = self.頼む("GET", "/mouikkai", 人="B")[2]
        self.assertIn("今回はやめた。それでいい", 文)
        self.assertNotIn("/musubu/", self.頼む("GET", "/mouikkai", 人="A")[2])

    def test_50_宣言にも守りが効き_書きかけを残す(self):
        状態, _, 文 = self.宣言する("あいつを殺してやる")
        self.assertEqual(状態, 400)
        self.assertIn('value="あいつを殺してやる"', 文)
        self.assertEqual(self.宣言する("死にたいけど、もう一回だけ", 人="B")[1], "/mouikkai?sotto=1")

    # ---- 夜の部屋（案4） ----
    def 時刻を決める(self, 日本の時刻):
        """この先の「いま」を日本時間の決まった時刻にする（夜の部屋は時刻で開け閉めするため）。"""
        固定 = datetime.fromisoformat(日本の時刻 + "+09:00")
        当て = mock.patch.object(時計, "いま", lambda: 固定)
        当て.start()
        self.addCleanup(当て.stop)

    def 夜に話す(self, 本文, 人="A"):
        return self.頼む("POST", "/yoru/kaku", {"honbun": 本文}, 人)

    def test_52_閉まっている時は何も見せず_書いても置かない(self):
        self.時刻を決める("2026-10-23T12:00:00")
        self.assertNotIn("いま開いています", self.頼む("GET", "/")[2])
        self.assertIn("いまは閉まっています", self.頼む("GET", "/yoru")[2])
        状態, _, 文 = self.夜に話す("昼に送る")
        self.assertEqual(状態, 400)
        self.assertIn("閉まりました", 文)
        self.assertEqual(self.台帳.つなぎ.execute("SELECT COUNT(*) FROM 書き込み").fetchone()[0], 0)

    def test_53_開いている時は今夜の話が古い順に並ぶ(self):
        self.時刻を決める("2026-10-23T23:30:00")
        self.assertIn("いま開いています", self.頼む("GET", "/")[2])
        self.assertEqual(self.夜に話す("眠れない")[1], "/yoru#yoru-kaku")
        self.時刻を決める("2026-10-24T01:00:00")
        self.夜に話す("自分も", 人="B")
        文 = self.頼む("GET", "/yoru")[2]
        self.assertLess(文.index("眠れない"), 文.index("自分も"))

    def test_54_前の夜の話は今夜は見えない(self):
        self.時刻を決める("2026-10-23T23:30:00")
        self.夜に話す("ゆうべの話")
        self.時刻を決める("2026-10-24T23:10:00")
        self.夜に話す("今夜の話", 人="B")
        文 = self.頼む("GET", "/yoru")[2]
        self.assertNotIn("ゆうべの話", 文)
        self.assertIn("今夜の話", 文)
        self.assertIn("ゆうべの話", self.見回りの画面())

    def test_55_夜は名乗りが出るが_名乗りの頁からは辿れない(self):
        self.時刻を決める("2026-10-23T23:30:00")
        self.名乗る("夜勤明け")
        self.時計を戻す()
        self.夜に話す("夜の話")
        self.assertIn("夜勤明け</a>", self.頼む("GET", "/yoru")[2])
        self.assertNotIn("夜の話", self.頼む("GET", "/nanori?n=" + quote("夜勤明け"))[2])

    def test_56_夜にも守りが効き_書きかけを残す(self):
        self.時刻を決める("2026-10-23T23:30:00")
        状態, _, 文 = self.夜に話す("隣のやつ消えろ")
        self.assertEqual(状態, 400)
        self.assertIn("隣のやつ消えろ</textarea>", 文)
        self.assertEqual(self.夜に話す("消えたい", 人="B")[1], "/yoru?sotto=1#yoru-kaku")

    # ---- 1対1の小部屋（案11） ----
    def 部屋を用意する(self, 名乗り="バツイチ"):
        """AとBが同じ名乗りで、Bの書き込みからAが部屋を開く。部屋番号を返す。
        部屋を開けるのは書き始めて1日たった人だけなので、Aは名乗る前に1つ書いて、前に書いたことにしておく。"""
        self.書く("Aの前の話", 板="shigoto", 人="A")
        self.時計を戻す()
        self.名乗る(名乗り, 人="A")
        self.名乗る(名乗り, 人="B")
        self.書く("離婚した", 板="kazoku", 人="B")
        番号 = self.最後の番号()
        行き先 = self.頼む("POST", "/heya/hiraku", {"bangou": 番号}, 人="A")[1]
        return int(行き先.rsplit("/", 1)[1])

    def 部屋で話す(self, 部屋, 本文, 人):
        return self.頼む("POST", f"/heya/{部屋}/kaku", {"honbun": 本文}, 人)

    def test_57_同じ名乗りのほかの人とだけ部屋を開け_同じ2人なら同じ部屋(self):
        self.assertIn('href="/heya"', self.頼む("GET", "/")[2])
        部屋 = self.部屋を用意する()
        Bの番号 = self.台帳.つなぎ.execute("SELECT 番号 FROM 書き込み WHERE 本文 = '離婚した'").fetchone()[0]
        self.assertIn("この人と2人で話す", self.頼む("GET", "/nanori?n=" + quote("バツイチ"), 人="A")[2])
        self.assertNotIn("この人と2人で話す", self.頼む("GET", "/nanori?n=" + quote("バツイチ"), 人="B")[2])
        self.assertEqual(self.頼む("POST", "/heya/hiraku", {"bangou": Bの番号}, 人="A")[1], f"/heya/{部屋}")
        self.名乗る("元・店長", 人="C")
        self.assertEqual(self.頼む("POST", "/heya/hiraku", {"bangou": Bの番号}, 人="C")[1], "/heya")
        self.assertEqual(self.頼む("POST", "/heya/hiraku", {"bangou": Bの番号}, 人="B")[1], "/heya")
        self.assertEqual(self.頼む("POST", "/heya/hiraku", {"bangou": "x"}, 人="A")[1], "/heya")
        self.assertEqual(self.台帳.つなぎ.execute("SELECT COUNT(*) FROM 小部屋").fetchone()[0], 1)

    def test_58_部屋は2人だけが入れ_ほかの人には見つからない(self):
        部屋 = self.部屋を用意する()
        self.部屋で話す(部屋, "はじめまして", "A")
        self.assertIn("はじめまして", self.頼む("GET", f"/heya/{部屋}", 人="B")[2])
        self.頼む("GET", "/", 人="C")
        self.assertEqual(self.頼む("GET", f"/heya/{部屋}", 人="C")[0], 404)
        self.assertEqual(self.部屋で話す(部屋, "のぞき", "C")[0], 404)
        self.assertEqual(self.頼む("POST", f"/heya/{部屋}/tojiru", {}, 人="C")[0], 404)
        self.assertNotIn("はじめまして", self.頼む("GET", "/heya", 人="C")[2])

    def test_59_部屋の話はあなたと相手で出て_ほかの場所には出ず_わかるも返事も置かない(self):
        部屋 = self.部屋を用意する()
        self.assertEqual(self.部屋で話す(部屋, "ひみつの話", "A")[1], f"/heya/{部屋}#heya-kaku")
        番号 = self.最後の番号()
        Aの画面 = self.頼む("GET", f"/heya/{部屋}", 人="A")[2]
        Bの画面 = self.頼む("GET", f"/heya/{部屋}", 人="B")[2]
        self.assertIn(">あなた</span>", Aの画面)
        self.assertIn(">相手</span>", Bの画面)
        self.assertNotIn("ひみつの話", self.頼む("GET", "/nanori?n=" + quote("バツイチ"), 人="B")[2])
        for 板 in 決まり.板の一覧を読む():
            self.assertNotIn("ひみつの話", self.頼む("GET", f"/ita/{板.鍵}")[2])
        self.頼む("POST", f"/wakaru/{番号}", {}, 人="B")
        self.時計を戻す()
        self.返す(番号, "外から返事", 人="C")
        self.assertEqual(self.台帳.つなぎ.execute("SELECT COUNT(*) FROM わかる").fetchone()[0], 0)
        self.assertEqual(self.台帳.つなぎ.execute("SELECT COUNT(*) FROM 書き込み WHERE 親番号 IS NOT NULL").fetchone()[0], 0)

    def test_60_閉じると2人とも書けず_一覧に閉じたと出る(self):
        部屋 = self.部屋を用意する()
        self.頼む("POST", f"/heya/{部屋}/tojiru", {}, 人="B")
        状態, _, 文 = self.部屋で話す(部屋, "まだ話したい", "A")
        self.assertEqual(状態, 400)
        self.assertIn("相手が閉じました。もう書けません", 文)
        self.assertEqual(self.台帳.つなぎ.execute("SELECT COUNT(*) FROM 書き込み WHERE 板 LIKE 'heya-%'").fetchone()[0], 0)
        self.assertIn("相手が閉じました", self.頼む("GET", f"/heya/{部屋}", 人="A")[2])
        self.assertIn("あなたが閉じました", self.頼む("GET", f"/heya/{部屋}", 人="B")[2])
        self.assertIn("閉じられました", self.頼む("GET", "/heya", 人="A")[2])

    def test_61_一覧には相手から話が来ていると出る(self):
        部屋 = self.部屋を用意する()
        self.時計を戻す()
        self.部屋で話す(部屋, "こんばんは", "A")
        self.assertIn("相手から話が来ています", self.頼む("GET", "/heya", 人="B")[2])
        self.assertNotIn("相手から話が来ています", self.頼む("GET", "/heya", 人="A")[2])

    def 書き始めを前にする(self, 人, 時間):
        """その人の書き込みを、時間（時間の数）だけ前に書いたことにする。"""
        鍵 = self.鍵(人)
        self.台帳.つなぎ.execute(
            "UPDATE 書き込み SET 書いた時刻 = ? WHERE 書いた人の鍵 = ?", ((時計.いま() - timedelta(hours=時間)).isoformat(), 鍵))

    def test_93_一度部屋を閉じた2人は_名乗りを変えても_もう部屋を開けない(self):
        部屋 = self.部屋を用意する()
        self.頼む("POST", f"/heya/{部屋}/tojiru", {}, 人="B")
        self.時計を戻す()  # Bも書き始めて1日たったことにする
        self.名乗る("元・店長", 人="A")
        self.名乗る("元・店長", 人="B")
        self.書く("店をたたんだ", 板="shigoto", 人="B")
        Bの番号 = self.最後の番号()
        self.書く("自分も店をたたんだ", 板="shigoto", 人="A")
        Aの番号 = self.最後の番号()
        # 閉じたのはBだが、どちらからも、もう開けない
        self.assertEqual(self.頼む("POST", "/heya/hiraku", {"bangou": Bの番号}, 人="A")[1], "/heya")
        self.assertEqual(self.頼む("POST", "/heya/hiraku", {"bangou": Aの番号}, 人="B")[1], "/heya")
        self.assertEqual(self.台帳.つなぎ.execute("SELECT COUNT(*) FROM 小部屋").fetchone()[0], 1)
        self.assertNotIn("この人と2人で話す", self.頼む("GET", "/nanori?n=" + quote("元・店長"), 人="A")[2])

    def test_94_書き始めて1日たたないブラウザからは部屋を開けず_案内が出て_1日たてば開ける(self):
        self.名乗る("夜勤", 人="A")
        self.名乗る("夜勤", 人="B")
        self.書く("夜勤明け", 板="shigoto", 人="B")
        Bの番号 = self.最後の番号()
        # Aはまだ何も書いていない（クッキーを消して別人になったばかりの人と同じ）
        self.assertEqual(self.頼む("POST", "/heya/hiraku", {"bangou": Bの番号}, 人="A")[1], "/heya")
        文 = self.頼む("GET", "/nanori?n=" + quote("夜勤"), 人="A")[2]
        self.assertNotIn("この人と2人で話す", 文)
        self.assertIn("書き始めて1日たってから", 文)
        self.書く("Aの話", 板="okane", 人="A")
        self.書き始めを前にする("A", 23)
        self.assertEqual(self.頼む("POST", "/heya/hiraku", {"bangou": Bの番号}, 人="A")[1], "/heya")
        self.書き始めを前にする("A", 25)
        self.assertTrue(self.頼む("POST", "/heya/hiraku", {"bangou": Bの番号}, 人="A")[1].startswith("/heya/"))
        self.assertEqual(self.台帳.つなぎ.execute("SELECT COUNT(*) FROM 小部屋").fetchone()[0], 1)

    def test_95_小部屋を受けないにした人とは部屋を開けず_戻すとまた開ける_いまある部屋はそのまま(self):
        部屋 = self.部屋を用意する()
        self.時計を戻す()
        self.名乗る("バツイチ", 人="C")
        self.書く("Cの話", 板="renai", 人="C")
        self.書き始めを前にする("C", 48)
        状態, 行き先, _ = self.頼む("POST", "/heya/ukenai", {}, 人="B")
        self.assertEqual((状態, 行き先), (303, "/heya"))
        self.assertIn("いまは小部屋を受けていません", self.頼む("GET", "/heya", 人="B")[2])
        Bの番号 = self.台帳.つなぎ.execute("SELECT 番号 FROM 書き込み WHERE 本文 = '離婚した'").fetchone()[0]
        self.assertEqual(self.頼む("POST", "/heya/hiraku", {"bangou": Bの番号}, 人="C")[1], "/heya")
        self.assertNotIn("この人と2人で話す", self.頼む("GET", "/nanori?n=" + quote("バツイチ"), 人="C")[2])
        # いまある部屋は、そのまま話せる（閉じるのは、それぞれの部屋で）
        self.assertEqual(self.部屋で話す(部屋, "まだ話せる", "A")[1], f"/heya/{部屋}#heya-kaku")
        # 戻すと、また開ける
        self.assertEqual(self.頼む("POST", "/heya/ukeru", {}, 人="B")[1], "/heya")
        self.assertTrue(self.頼む("POST", "/heya/hiraku", {"bangou": Bの番号}, 人="C")[1].startswith("/heya/"))

    # ---- 荒らしへの備え（公開前に要るもの 順7） ----
    def test_96_同じ接続元から1分に10件までで_11件目は間をあけてもらう_知らせも合わせて数える(self):
        self.時刻を決める("2026-10-26T12:00:00")
        for i in range(9):  # クッキーを受けないブラウザ（毎回別人に見える）からでも
            self.assertEqual(self.受け口から("/ita/shigoto/kaku", {"honbun": f"荒らし{i}"}, None, "203.0.113.50", "1000")[0], 303, i)
        self.assertEqual(self.受け口から("/shiraseru", {"honbun": "知らせ"}, None, "203.0.113.50", "1000")[0], 303)
        状態, _, 文 = self.受け口から("/ita/shigoto/kaku", {"honbun": "11件目"}, None, "203.0.113.50", "1000")
        self.assertEqual(状態, 400)
        self.assertIn("少し間をあけて", 文)
        self.assertIn("11件目</textarea>", 文)
        self.assertEqual(self.板の件数(), 9)

    def test_97_別の接続元なら止まらず_1分たてばまた書ける(self):
        self.時刻を決める("2026-10-26T12:00:00")
        for i in range(10):
            self.受け口から("/ita/shigoto/kaku", {"honbun": f"話{i}"}, None, "203.0.113.51", "1000")
        self.assertEqual(self.受け口から("/ita/shigoto/kaku", {"honbun": "まだ"}, None, "203.0.113.51", "1000")[0], 400)
        self.assertEqual(self.受け口から("/ita/shigoto/kaku", {"honbun": "別の人"}, None, "203.0.113.52", "1000")[0], 303)
        self.時刻を決める("2026-10-26T12:01:01")
        self.assertEqual(self.受け口から("/ita/shigoto/kaku", {"honbun": "1分たった"}, None, "203.0.113.51", "1000")[0], 303)

    def test_98_止めた書き込みと二度押しは数えず_じかに来た自分は数えない(self):
        self.時刻を決める("2026-10-26T12:00:00")
        for i in range(12):
            self.assertEqual(self.受け口から("/ita/shigoto/kaku", {"honbun": f"死ね{i}"}, None, "203.0.113.53", "1000")[0], 400)
        for _ in range(12):
            self.受け口から("/ita/shigoto/kaku", {"honbun": "同じ話"}, "A", "203.0.113.53", "1000")
        self.assertEqual(self.受け口から("/ita/shigoto/kaku", {"honbun": "止めた分は数えない"}, None, "203.0.113.53", "1000")[0], 303)
        # 前に置く受け口が番地を渡さない時（じかに来た 127.0.0.1）は、全員が同じに見えるので数えない（場ごと止まらないように）
        for i in range(12):
            self.assertEqual(self.頼む("POST", "/ita/okane/kaku", {"honbun": f"じかの話{i}"}, None)[0], 303, i)

    def test_62_部屋にも守りが効き_書きかけを残す(self):
        部屋 = self.部屋を用意する()
        self.時計を戻す()
        状態, _, 文 = self.部屋で話す(部屋, "お前なんか死ね", "A")
        self.assertEqual(状態, 400)
        self.assertIn("お前なんか死ね</textarea>", 文)
        self.assertEqual(self.部屋で話す(部屋, "消えたい", "A")[1], f"/heya/{部屋}?sotto=1#heya-kaku")
        self.assertIn(f"小部屋#{部屋}", self.見回りの画面())

    # ---- 書いた人の記録（公開前に要るもの 順3） ----
    def 受け口から(self, 道, 中身, 人="A", 番地="203.0.113.7", 港="54321"):
        """前に置く https の受け口を通って来た形。来た人の番地と港は、受け口が見出しに入れて渡す。"""
        return self.頼む("POST", 道, 中身, 人, {"X-Real-IP": 番地, "X-Real-Port": 港})

    def 書いた人の記録(self):
        return [tuple(行) for 行 in self.台帳.つなぎ.execute(
            "SELECT 書き込み番号, 番地, 港, 書いた時刻 FROM 書いた人の記録 ORDER BY 書き込み番号")]

    def 年をとらせる(self, 番地, 日数):
        """その番地の記録を、日数だけ前に書いたことにする。"""
        self.台帳.つなぎ.execute(
            "UPDATE 書いた人の記録 SET 書いた時刻 = ? WHERE 番地 = ?", ((時計.いま() - timedelta(days=日数)).isoformat(), 番地))

    def test_74_書くと_接続元の番地と港と時刻が_書き込みとは別に1件ずつ残る(self):
        self.受け口から("/ita/shigoto/kaku", {"honbun": "板の話"}, "A", "203.0.113.7", "54321")
        板の番号 = self.最後の番号()
        self.受け口から(f"/henji/{板の番号}", {"honbun": "返事の話"}, "B", "2001:DB8::1", "40000")
        返事の番号 = self.最後の番号()
        self.受け口から("/hitori/kaku", {"honbun": "独り言"}, "C", "198.51.100.20", "1")
        独り言の番号 = self.最後の番号()
        記録 = self.書いた人の記録()
        self.assertEqual([行[:3] for 行 in 記録], [
            (板の番号, "203.0.113.7", 54321), (返事の番号, "2001:db8::1", 40000), (独り言の番号, "198.51.100.20", 1)])
        書いた時刻 = dict(self.台帳.つなぎ.execute("SELECT 番号, 書いた時刻 FROM 書き込み").fetchall())
        self.assertEqual([行[3] for 行 in 記録], [書いた時刻[板の番号], 書いた時刻[返事の番号], 書いた時刻[独り言の番号]])
        # 2人だけの小部屋の話も残す（つきまといの訴えに応えるため）
        self.時計を戻す()  # AとBが続けて書けるように
        部屋 = self.部屋を用意する()
        self.受け口から(f"/heya/{部屋}/kaku", {"honbun": "部屋の話"}, "A", "203.0.113.8", "60000")
        self.assertEqual(self.書いた人の記録()[-1][:3], (self.最後の番号(), "203.0.113.8", 60000))

    def test_76_書いた人の記録は_どの画面にも出ない(self):
        self.名乗る("元・営業")
        self.受け口から("/ita/shigoto/kaku", {"honbun": "番地は出ない話"}, "A", "203.0.113.77", "61234")
        番号 = self.最後の番号()
        self.assertEqual(self.書いた人の記録()[0][:3], (番号, "203.0.113.77", 61234))
        画面たち = [(道, self.頼む("GET", 道)[2]) for 道 in ("/", "/ita/shigoto", "/nanori?n=" + quote("元・営業"))]
        for 道, 文 in 画面たち + [("見回り", self.見回りの画面())]:
            self.assertIn("番地は出ない話", 文, 道)
            self.assertNotIn("203.0.113.77", 文, 道)
            self.assertNotIn("61234", 文, 道)

    def test_77_止めた書き込み_二度押し_連投では_記録を残さない(self):
        self.assertEqual(self.受け口から("/ita/shigoto/kaku", {"honbun": "上司は死ね"})[0], 400)
        self.assertEqual(self.受け口から("/ita/shigoto/kaku", {"honbun": "置かれる話"})[0], 303)
        self.assertEqual(self.受け口から("/ita/shigoto/kaku", {"honbun": "置かれる話"})[0], 303)  # 二度押し
        self.assertEqual(self.受け口から("/ita/shigoto/kaku", {"honbun": "すぐ次の話"})[0], 400)  # 連投
        self.assertEqual([行[0] for 行 in self.書いた人の記録()], [self.最後の番号()])
        self.assertEqual(self.板の件数(), 1)
        # 消された書き込みに、開いたままの古い画面から返事しても、置かないので残さない
        self.消す(self.最後の番号())
        self.受け口から(f"/henji/{self.最後の番号()}", {"honbun": "古い画面からの返事"}, "B")
        self.assertEqual(len(self.書いた人の記録()), 1)

    def test_78_半年を過ぎた記録だけ消え_書き込みは残り_消した番地はファイルにも残らない(self):
        self.受け口から("/ita/shigoto/kaku", {"honbun": "古い話"}, "A", "203.0.113.81", "1111")
        self.受け口から("/ita/shigoto/kaku", {"honbun": "新しい話"}, "B", "203.0.113.82", "2222")
        self.年をとらせる("203.0.113.81", 184)
        self.年をとらせる("203.0.113.82", 182)
        self.台帳.毎日の手入れ(os.path.join(self.置き場, "控え"))
        self.assertEqual([行[1] for 行 in self.書いた人の記録()], ["203.0.113.82"])
        self.assertEqual(self.板の件数(), 2)
        for 名前 in os.listdir(self.置き場):
            if 名前.startswith("場.db"):
                with open(os.path.join(self.置き場, 名前), "rb") as f:
                    self.assertFalse(b"203.0.113.81" in f.read(), f"消した番地が {名前} に残っている")

    def test_79_控えには_書いた人の記録を入れない(self):
        self.受け口から("/ita/shigoto/kaku", {"honbun": "控えに残る話"}, "A", "203.0.113.91", "3333")
        self.assertEqual(len(self.書いた人の記録()), 1)
        控えの場所 = os.path.join(self.置き場, "控え")
        控え = self.台帳.控えを取る(控えの場所)
        self.assertEqual(os.listdir(控えの場所), [os.path.basename(控え)])
        with open(控え, "rb") as f:
            self.assertFalse(b"203.0.113.91" in f.read(), "控えに番地が残っている")
        控えの台帳 = 台帳(控え)
        try:
            self.assertEqual(控えの台帳.つなぎ.execute("SELECT 本文 FROM 書き込み").fetchone()[0], "控えに残る話")
        finally:
            控えの台帳.閉じる()
        self.assertEqual(len(self.書いた人の記録()), 1)  # 元の記録はそのまま

    def test_80_求められた時に_書き込み番号から取り出せ_消した書き込みでも取り出せる(self):
        self.時刻を決める("2026-10-26T09:12:34")
        self.受け口から("/ita/shigoto/kaku", {"honbun": "問われた話"}, "A", "203.0.113.100", "50000")
        番号 = self.最後の番号()
        self.消す(番号)
        道具 = os.path.dirname(os.path.abspath(__file__))

        def 取り出す(番号):
            return subprocess.run(
                # 子は -X utf8 で動かす（Windows の Python は、子の出力を既定で cp932 にするので utf-8 で読めない）
                [sys.executable, "-X", "utf8", "-B", os.path.join(道具, "書いた人を取り出す.py"), os.path.join(self.置き場, "場.db"), str(番号)],
                capture_output=True, text=True, encoding="utf-8", timeout=30)

        返り = 取り出す(番号)
        self.assertEqual(返り.returncode, 0, 返り.stderr)
        for 出る物 in ("203.0.113.100", "50000", "2026-10-26 09:12:34", "2026-10-26 00:12:34", "問われた話", "消した書き込み"):
            self.assertIn(出る物, 返り.stdout)
        返り = 取り出す(番号 + 1)
        self.assertEqual(返り.returncode, 1)
        self.assertIn("記録はありません", 返り.stdout)

    def test_81_同時に書いても_書き込みと書いた人の記録が1対1でそろう(self):
        人たち = [f"人{i}" for i in range(10)]
        for 人 in 人たち:
            self.頼む("GET", "/", 人=人)
        self.一斉に([lambda i=i, 人=人: self.受け口から("/ita/shigoto/kaku", {"honbun": f"{人}の話"}, 人, f"203.0.113.{i + 1}", str(40000 + i))
                    for i, 人 in enumerate(人たち)])
        書き込み = dict(self.台帳.つなぎ.execute("SELECT 本文, 番号 FROM 書き込み").fetchall())
        記録 = {行[0]: (行[1], 行[2]) for 行 in self.書いた人の記録()}
        self.assertEqual(len(書き込み), 10)
        for i, 人 in enumerate(人たち):
            self.assertEqual(記録[書き込み[f"{人}の話"]], (f"203.0.113.{i + 1}", 40000 + i), 人)

    # ---- 持ち主へ知らせる（公開前に要るもの 順5 通報ボタン・順4 の連絡先） ----
    def 知らせる(self, 本文, 番号=None, 人="B"):
        中身 = {"honbun": 本文}
        if 番号 is not None:
            中身["bangou"] = 番号
        return self.頼む("POST", "/shiraseru", 中身, 人)

    def 見回りの知らせ(self):
        """見回りの画面の、知らせ1件ずつのかたまり。"""
        return re.findall(r'<div class="知らせ".*?</div>', self.見回りの画面(), re.S)

    def 知らせの件数(self):
        return self.台帳.つなぎ.execute("SELECT COUNT(*) FROM 知らせ").fetchone()[0]

    def test_82_書き込みの知らせるから持ち主へ知らせると_見回りに届き_理由は無くてよい(self):
        self.書く("まずい話")
        番号 = self.最後の番号()
        self.assertIn(f'href="/shiraseru?bangou={番号}"', self.頼む("GET", "/ita/shigoto", 人="B")[2])
        self.assertIn(f'name="bangou" value="{番号}"', self.頼む("GET", f"/shiraseru?bangou={番号}", 人="B")[2])
        状態, 行き先, _ = self.知らせる("", 番号)
        self.assertEqual((状態, 行き先), (303, "/shiraseru?okutta=1"))
        self.assertIn("持ち主に届きました", self.頼む("GET", 行き先, 人="B")[2])
        [知らせ] = self.見回りの知らせ()
        self.assertIn(f"#{番号}（仕事）への知らせ", 知らせ)
        self.assertIn("（理由なし）", 知らせ)

    def test_83_はじめの画面の下から番号なしで知らせられ_空は断り_長すぎれば書きかけを残す(self):
        self.assertIn('href="/shiraseru"', self.頼む("GET", "/")[2])
        self.assertEqual(self.知らせる("消し方を<b>教えて</b>")[0], 303)
        [知らせ] = self.見回りの知らせ()
        self.assertIn("消し方を&lt;b&gt;教えて&lt;/b&gt;", 知らせ)
        状態, _, 文 = self.知らせる("", 人="C")
        self.assertEqual(状態, 400)
        self.assertIn("何を知らせたいか", 文)
        状態, _, 文 = self.知らせる("あ" * 1001, 人="D")
        self.assertEqual(状態, 400)
        self.assertIn("あ" * 1001 + "</textarea>", 文)
        self.assertEqual(self.知らせの件数(), 1)

    def test_84_知らせは見回りにだけ出て_知らせる欄にも書き込みの中身は出さない(self):
        部屋 = self.部屋を用意する()
        self.部屋で話す(部屋, "ふたりだけの話", "A")
        部屋の話 = self.最後の番号()
        self.頼む("GET", "/", 人="C")
        # 小部屋や消した書き込みの番号を当てても、知らせる欄にその中身は出ない
        self.assertNotIn("ふたりだけの話", self.頼む("GET", f"/shiraseru?bangou={部屋の話}", 人="C")[2])
        self.知らせる("ひみつの知らせ", 人="C")
        for 道 in ("/", "/ita/shigoto", "/ita/kazoku", "/nanori?n=" + quote("バツイチ"), f"/heya/{部屋}", "/shiraseru"):
            self.assertNotIn("ひみつの知らせ", self.頼む("GET", 道, 人="A")[2], 道)
        self.assertIn("ひみつの知らせ", self.見回りの画面())

    def test_85_書いた時と同じブラウザから知らせると_見回りに本人からと出る(self):
        self.書く("消してほしい話", 人="A")
        番号 = self.最後の番号()
        self.知らせる("自分で書いたけど消してほしい", 番号, 人="A")
        self.知らせる("ほかの人の話です", 番号, 人="B")
        知らせたち = self.見回りの知らせ()
        本人から = [知らせ for 知らせ in 知らせたち if "自分で書いたけど消してほしい" in 知らせ]
        ほかの人 = [知らせ for 知らせ in 知らせたち if "ほかの人の話です" in 知らせ]
        self.assertIn("書いた人と同じブラウザから", 本人から[0])
        self.assertNotIn("書いた人と同じブラウザから", ほかの人[0])
        # 番号なしの知らせには、そのブラウザで書いた書き込みの番号が出る（どれのことかを持ち主が探せるように）
        self.知らせる("前に書いたものを消したい", 人="C")
        self.書く("Cの話", 人="C")
        Cの番号 = self.最後の番号()
        [Cの知らせ] = [知らせ for 知らせ in self.見回りの知らせ() if "前に書いたものを消したい" in 知らせ]
        self.assertIn(f"このブラウザで書いたもの：#{Cの番号}", Cの知らせ)
        self.assertNotIn(f"#{番号}", Cの知らせ)

    def test_86_知らせには止める言葉を効かせず_つらすぎる言葉なら相談先を出す(self):
        self.assertEqual(self.知らせる("この書き込みに「死ね」と書かれています")[1], "/shiraseru?okutta=1")
        self.assertIn("「死ね」と書かれています", self.見回りの画面())
        self.assertEqual(self.知らせる("もう消えたい", 人="C")[1], "/shiraseru?okutta=1&sotto=1")
        self.assertIn("よりそいホットライン", self.頼む("GET", "/shiraseru?okutta=1&sotto=1", 人="C")[2])

    def test_87_知らせの二度押しは1件_続けて送ると間をあけてもらい_無い番号は番号なしで受ける(self):
        self.知らせる("同じ知らせ")
        self.知らせる("同じ知らせ")
        self.assertEqual(self.知らせの件数(), 1)
        状態, _, 文 = self.知らせる("すぐ次の知らせ")
        self.assertEqual(状態, 400)
        self.assertIn("少し間をあけて", 文)
        self.assertIn("すぐ次の知らせ</textarea>", 文)
        self.assertEqual(self.知らせる("番号違い", 99999, 人="C")[0], 303)
        self.assertIsNone(self.台帳.つなぎ.execute("SELECT 書き込み番号 FROM 知らせ WHERE 本文 = '番号違い'").fetchone()[0])

    def test_88_どの場所の書き込みにも_知らせるがある(self):
        self.名乗る("元・店長")
        self.書く("板の話", 人="A")
        板の話 = self.最後の番号()
        self.返す(板の話, "返事の話", 人="B")
        返事 = self.最後の番号()
        self.頼む("POST", "/kachi/kaku", {"honbun": "起きた"}, 人="C")
        勝ち = self.最後の番号()
        self.棚に置く("落ちた", "働いている", 人="D")
        棚 = self.最後の番号()
        self.宣言する("面接を受ける", 人="E")
        宣言 = self.最後の番号()
        self.つぶやく("ひとり", 人="F")
        独り言 = self.最後の番号()
        for 道, 番号 in (("/ita/shigoto", 板の話), ("/ita/shigoto", 返事), ("/kachi", 勝ち), ("/sonogo", 棚),
                         ("/mouikkai", 宣言), ("/hitori", 独り言), ("/nanori?n=" + quote("元・店長"), 板の話)):
            self.assertIn(f'href="/shiraseru?bangou={番号}"', self.頼む("GET", 道, 人="G")[2], 道)
        self.時計を戻す()
        部屋 = self.部屋を用意する()
        self.部屋で話す(部屋, "部屋の話", "A")
        self.assertIn(f'href="/shiraseru?bangou={self.最後の番号()}"', self.頼む("GET", f"/heya/{部屋}", 人="B")[2])
        self.時刻を決める("2026-10-23T23:30:00")
        self.夜に話す("夜の話", 人="H")
        self.assertIn(f'href="/shiraseru?bangou={self.最後の番号()}"', self.頼む("GET", "/yoru", 人="G")[2])

    # ---- 利用の決まり・個人情報の扱い（公開前に要るもの 順4） ----
    def test_89_はじめの画面の下から_利用の決まりと個人情報の扱いへ行ける(self):
        はじめ = self.頼む("GET", "/")[2]
        下の道 = はじめ[はじめ.index('class="下の道"'):]
        for 道 in ('href="/kimari"', 'href="/kojin"', 'href="/shiraseru"'):
            self.assertIn(道, 下の道)
        状態, _, 決まりの頁 = self.頼む("GET", "/kimari")
        self.assertEqual(状態, 200)
        for 出る物 in ("書かないでほしいこと", "18歳以上の方の場所です", "半年のあいだ残します", 'href="/kojin"', 'href="/shiraseru"'):
            self.assertIn(出る物, 決まりの頁)
        状態, _, 個人の頁 = self.頼む("GET", "/kojin")
        self.assertEqual(状態, 200)
        for 出る物 in ("聞かないもの", "求められたら遅れずにお答えします", "持ち主への知らせ", 'href="/shiraseru"'):
            self.assertIn(出る物, 個人の頁)
        # 運営者が答えるための届け先は、知らせる人が書き添えた時だけ
        self.assertIn("返事が要る時だけ", self.頼む("GET", "/shiraseru")[2])

    def test_90_利用の決まりの相談先は_相談先の一覧から出る(self):
        試しの窓口 = [決まり.相談先("試しの窓口", "0000-11-2222", "試しの時間")]
        with mock.patch.object(決まり, "相談先を読む", lambda: 試しの窓口):
            文 = self.頼む("GET", "/kimari")[2]
        self.assertIn("試しの窓口", 文)
        self.assertIn("0000-11-2222", 文)
        self.assertNotIn("0120-279-338", 文)  # 番号を決まりの文に書き写していない（変わった時に直し漏れる）

    def test_128_鍵のクッキーは_httpsの時だけ送る(self):
        つなぎ = http.client.HTTPConnection("127.0.0.1", self.場.server_port)
        つなぎ.request("GET", "/")
        クッキー = つなぎ.getresponse().getheader("Set-Cookie")
        つなぎ.close()
        self.assertTrue(クッキー.startswith(f"{場.鍵の名前}="))
        for 印 in ("Path=/", "HttpOnly", "SameSite=Lax", "Secure"):
            self.assertIn(印, クッキー)

    def test_132_利用の決まりと個人情報の扱いに_公開の日の空きを残さない(self):
        for 道 in ("/kimari", "/kojin"):
            文 = self.頼む("GET", 道)[2]
            self.assertNotIn("公開の日", 文, 道)
            self.assertRegex(文, r"\d{4}年\d{1,2}月\d{1,2}日から", 道)

    def test_92_個人情報の扱いの中身が_いまの作りと合っている(self):
        文 = self.頼む("GET", "/kojin")[2]
        つなぎ = http.client.HTTPConnection("127.0.0.1", self.場.server_port)
        つなぎ.request("GET", "/")
        クッキー = つなぎ.getresponse().getheader("Set-Cookie")
        self.assertIn(f"クッキー「{場.鍵の名前}」", 文)
        self.assertTrue(クッキー.startswith(f"{場.鍵の名前}="))
        self.assertIn("Max-Age=31536000", クッキー)  # 1年。変えたら個人情報の扱いの「1年」も直す
        self.assertIn("いつまで：1年", 文)
        self.assertTrue(181 <= 決まり.書いた人の記録を残す日数 <= 184)  # 半年。変えたら「半年で消します」も直す
        self.assertIn("半年で消します", 文)
        self.assertEqual(決まり.聞き役が待つ秒, 10 * 60)  # 10分。変えたら「10分ほどたつと」も直す
        self.assertIn(f"10分ほどたつと「{決まり.聞き役の名乗り}」が", 文)
        self.assertIn("本文だけを、さくらインターネットの「さくらのAI Engine」に送ります", 文)

    # ---- 見回りの入り方（公開前に要るもの 順8） ----
    def test_99_見回りは入口の欄から合言葉を送って入り_合言葉はページの場所にも画面にも出ない(self):
        self.書く("見回りで読む話")
        番号 = self.最後の番号()
        状態, _, 入口 = self.頼む("GET", "/kanri", 人="持ち主")
        self.assertEqual(状態, 200)
        self.assertIn('<form method="post" action="/kanri/hairu">', 入口)
        self.assertIn('type="password" name="aikotoba"', 入口)
        self.assertNotIn("見回りで読む話", 入口)
        # 入ると、数時間で切れる見回りの札を渡し、行き先は /kanri だけ（合言葉を載せない）
        self.assertEqual(self.見回りに入る()[:2], (303, "/kanri"))
        [札] = [渡された for 渡された in self.返りの見出し.get_all("Set-Cookie") if 渡された.startswith(場.札の名前 + "=")]
        for 印 in ("Path=/kanri", f"Max-Age={決まり.見回りの札が効く秒}", "HttpOnly", "SameSite=Strict", "Secure"):
            self.assertIn(印, 札)
        状態, _, 見回り = self.頼む("GET", "/kanri", 人="持ち主")
        self.assertEqual(状態, 200)
        self.assertIn("見回りで読む話", 見回り)
        self.assertNotIn(self.合言葉, 見回り)
        self.assertEqual(self.返りの見出し.get("Cache-Control"), "no-store")  # 出た後に「戻る」で見回りの画面が出ないように
        self.assertEqual(self.消す(番号)[:2], (303, f"/kanri#m{番号}"))
        # 前の入り方（ページの場所に合言葉）では、もう入れない
        文 = self.頼む("GET", f"/kanri?aikotoba={self.合言葉}", 人="ほかの人")[2]
        self.assertNotIn("見回りで読む話", 文)
        self.assertNotIn(場.札の名前, self.クッキー["ほかの人"])

    def test_100_合言葉が違えば入れず_5回間違えた接続元は10分たつまで試せず_ほかの接続元と書き込みは止まらない(self):
        self.時刻を決める("2026-10-26T12:00:00")
        for 違う in ("chigau", "", "あいことば", "ｔａｍｅｓｈｉ－ａｉｋｏｔｏｂａ", self.合言葉 + "x"):
            状態, _, 文 = self.見回りに入る(違う, 人="荒らし", 番地="203.0.113.60")
            self.assertEqual(状態, 403, 違う)
            self.assertIn("合言葉が違います", 文)
        # 6回目は、正しい合言葉でも確かめずに待ってもらう
        self.時刻を決める("2026-10-26T12:09:59")
        状態, _, 文 = self.見回りに入る(人="荒らし", 番地="203.0.113.60")
        self.assertEqual(状態, 429)
        self.assertIn("10分ほど", 文)
        self.assertNotIn(場.札の名前, self.クッキー["荒らし"])
        # ほかの接続元からは入れる。同じ接続元からも書ける（書き込みの数とは別に数える）
        self.assertEqual(self.見回りに入る(人="持ち主", 番地="203.0.113.61")[1], "/kanri")
        self.assertEqual(self.受け口から("/ita/shigoto/kaku", {"honbun": "書ける"}, "荒らし", "203.0.113.60", "1000")[0], 303)
        # 10分たてば、また試せる。前後の空白は外して比べる（貼り付けた時に付きやすい）
        self.時刻を決める("2026-10-26T12:10:01")
        self.assertEqual(self.見回りに入る(f" {self.合言葉}　", 人="荒らし", 番地="203.0.113.60")[1], "/kanri")

    def test_101_見回りの札は3時間で切れ_出ると切れ_切れた後の開いたままの画面からは消せない(self):
        self.時刻を決める("2026-10-26T12:00:00")
        self.書く("残る話")
        番号 = self.最後の番号()
        古い合い札 = self.合い札()
        self.時刻を決める("2026-10-26T14:59:59")
        self.assertIn("残る話", self.頼む("GET", "/kanri", 人="持ち主")[2])
        self.時刻を決める("2026-10-26T15:00:01")
        文 = self.頼む("GET", "/kanri", 人="持ち主")[2]
        self.assertNotIn("残る話", 文)
        self.assertIn('action="/kanri/hairu"', 文)
        # 札が切れた後に、開いたままの見回りの画面から消そうとしても消えず、入り直すよう出る
        状態, _, 文 = self.頼む("POST", "/kanri/kesu", {"aifuda": 古い合い札, "bangou": 番号}, 人="持ち主")
        self.assertEqual(状態, 403)
        self.assertIn("もう一度、合言葉を入れてください", 文)
        self.assertEqual(self.板の件数(), 1)
        # 入り直して「見回りを出る」と、ブラウザから札が消え、同じ札をもう一度見せても入れない
        self.見回りに入る()
        札 = self.クッキー["持ち主"][場.札の名前]
        self.assertIn('action="/kanri/deru"', self.見回りの画面())
        self.assertEqual(self.見回りで("deru")[:2], (303, "/kanri"))
        self.assertNotIn(場.札の名前, self.クッキー["持ち主"])
        self.クッキー["持ち主"][場.札の名前] = 札
        self.assertNotIn("残る話", self.頼む("GET", "/kanri", 人="持ち主")[2])

    def test_102_消す戻すは_札と_その札の見回りの画面の合い札がそろった時だけ(self):
        self.書く("消されない話")
        番号 = self.最後の番号()
        合い札 = self.合い札()
        # 札はあるが合い札が無い・違う（ほかのサイトに仕掛けた送る欄から、持ち主のブラウザに送らせた時）
        for 中身 in ({"bangou": 番号}, {"aifuda": "0" * len(合い札), "bangou": 番号}):
            self.assertEqual(self.頼む("POST", "/kanri/kesu", 中身, 人="持ち主")[0], 403)
        # 合い札はあるが札が無い／前の入り方で合言葉を送る
        for 中身 in ({"aifuda": 合い札, "bangou": 番号}, {"aikotoba": self.合言葉, "bangou": 番号}):
            self.assertEqual(self.頼む("POST", "/kanri/kesu", 中身, 人="ほかの人")[0], 403)
        # 別の札の合い札では動かない（合い札は札ごとに違う）
        self.見回りに入る(人="2つ目のブラウザ")
        self.assertEqual(self.頼む("POST", "/kanri/kesu", {"aifuda": 合い札, "bangou": 番号}, 人="2つ目のブラウザ")[0], 403)
        self.assertEqual(self.板の件数(), 1)
        # そろえば消え、戻せる
        self.assertEqual(self.頼む("POST", "/kanri/kesu", {"aifuda": 合い札, "bangou": 番号}, 人="持ち主")[0], 303)
        self.assertEqual(self.板の件数(), 0)
        self.assertEqual(self.戻す(番号)[0], 303)
        self.assertEqual(self.板の件数(), 1)

    # ---- 見回りで、同じブラウザの書き込みをまとめて消す ----
    def 荒らしが書く(self, 本文たち, 親=None):
        """同じブラウザ（荒らし）が板・返事・独り言に書く。書いた番号を返す。"""
        道たち = [("/ita/shigoto/kaku", {}), (f"/henji/{親}", {}), ("/hitori/kaku", {})]
        番号たち = []
        for (道, _), 本文 in zip(道たち if 親 else 道たち[::2], 本文たち):
            self.時計を戻す()  # 連投の間をあける
            self.頼む("POST", 道, {"honbun": 本文}, 人="荒らし")
            番号たち.append(self.最後の番号())
        return 番号たち

    def test_110_同じブラウザの書き込みを一覧で見てから_まとめて消すと_そのブラウザの物だけ消える(self):
        self.書く("ほかの人の話", 人="B")
        ほかの人 = self.最後の番号()
        荒らし = self.荒らしが書く(["荒らしの一つ目", "荒らしの返事", "荒らしの独り言"], 親=ほかの人)
        状態, _, 一覧 = self.このブラウザの書き込み(荒らし[0])
        self.assertEqual(状態, 200)
        self.assertEqual(self.返りの見出し.get("Cache-Control"), "no-store")
        for 本文 in ("荒らしの一つ目", "荒らしの返事", "荒らしの独り言"):
            self.assertIn(本文, 一覧)
        self.assertNotIn("ほかの人の話", 一覧)
        self.assertIn("出ている3件をまとめて消す", 一覧)
        self.assertEqual(self.まとめて("kesu", 荒らし[0])[:2], (303, f"/kanri/matome?bangou={荒らし[0]}"))
        消したか = self.消したか()
        self.assertEqual([消したか[番号] for 番号 in 荒らし], [1, 1, 1])
        self.assertEqual(消したか[ほかの人], 0)
        板 = self.頼む("GET", "/ita/shigoto", 人="C")[2]
        self.assertIn("ほかの人の話", 板)
        self.assertNotIn("荒らしの一つ目", 板)
        self.assertNotIn("荒らしの返事", 板)
        self.assertIn("消した3件をまとめて戻す", self.このブラウザの書き込み(荒らし[0])[2])

    def test_111_まとめて戻すと消した物が戻り_一覧を開いた後に書かれた物はまとめて消さない(self):
        荒らし = self.荒らしが書く(["荒らしの一つ目", "荒らしの独り言"])
        self.まとめて("kesu", 荒らし[0])
        self.assertEqual(self.まとめて("modosu", 荒らし[0])[:2], (303, f"/kanri/matome?bangou={荒らし[0]}"))
        self.assertEqual([self.消したか()[番号] for 番号 in 荒らし], [0, 0])
        # 開いたままの古い一覧から送る：一覧を開いた後に同じブラウザで書かれた物は、見ていないので消さない
        古い一覧 = self.このブラウザの書き込み(荒らし[0])[2]
        self.時計を戻す()
        self.頼む("POST", "/ita/shigoto/kaku", {"honbun": "一覧の後の話"}, 人="荒らし")
        後 = self.最後の番号()
        self.頼む("POST", "/kanri/matomete-kesu", self.欄を読む(古い一覧, "kesu"), 人="持ち主")
        消したか = self.消したか()
        self.assertEqual([消したか[番号] for 番号 in 荒らし], [1, 1])
        self.assertEqual(消したか[後], 0)
        # 2つの画面から続けて送っても、2回目は何も変えない
        self.assertEqual(self.頼む("POST", "/kanri/matomete-kesu", self.欄を読む(古い一覧, "kesu"), 人="持ち主")[0], 303)
        self.assertEqual(self.消したか()[後], 0)

    def test_112_一覧とまとめて消す戻すは_札と合い札が無いと見えず動かず_無い番号は見つからない(self):
        self.書く("残る話")
        番号 = self.最後の番号()
        状態, _, 文 = self.頼む("GET", f"/kanri/matome?bangou={番号}", 人="ほかの人")
        self.assertNotIn("残る話", 文)
        self.assertIn('action="/kanri/hairu"', 文)
        self.見回りに入る()
        for 中身 in ({"bangou": 番号, "made": 番号}, {"aifuda": "0" * 32, "bangou": 番号, "made": 番号}):
            self.assertEqual(self.頼む("POST", "/kanri/matomete-kesu", 中身, 人="持ち主")[0], 403)
        self.assertEqual(self.板の件数(), 1)
        for 道 in ("/kanri/matome?bangou=99999", "/kanri/matome?bangou=abc", "/kanri/matome"):
            self.assertEqual(self.頼む("GET", 道, 人="持ち主")[0], 404, 道)
        合い札 = self.合い札()
        for 中身 in ({"bangou": "99999", "made": "99999"}, {"bangou": 番号, "made": "x"}, {"bangou": 番号}):
            self.assertEqual(self.頼む("POST", "/kanri/matomete-kesu", {"aifuda": 合い札, **中身}, 人="持ち主")[0], 404, 中身)
        self.assertEqual(self.板の件数(), 1)

    def test_113_見回りの行には_2件以上書いたブラウザにだけ件数つきの入口が出て_ブラウザの乱数は画面に出ない(self):
        self.書く("一度だけの人", 人="B")
        一度 = self.最後の番号()
        self.書く("一つ目", 人="A")
        一つ目 = self.最後の番号()
        self.時計を戻す()
        self.書く("二つ目", 人="A")
        二つ目 = self.最後の番号()
        文 = self.見回りの画面()
        for 番号 in (一つ目, 二つ目):
            self.assertIn(f'href="/kanri/matome?bangou={番号}">このブラウザの書き込み（2件）</a>', 文)
        self.assertNotIn(f"/kanri/matome?bangou={一度}", 文)
        一覧 = self.このブラウザの書き込み(一つ目)[2]
        for 人 in ("A", "B"):
            self.assertNotIn(self.鍵(人), 文)
            self.assertNotIn(self.鍵(人), 一覧)

    # ---- AIの聞き役（案9） ----
    def 偽のAI(self, 返事="そう思うのも、自然なことだと思う。"):
        """本物のAIの代わり。尋ねられた本文を覚え、決まった返事を返す。"""
        聞いた = []

        def 尋ねる(本文):
            聞いた.append(本文)
            return 返事
        return 尋ねる, 聞いた

    def 聞き役が回る(self, 尋ねる=None):
        return 聞き役.ひと回り(self.台帳, 尋ねる or self.偽のAI()[0])

    def 前に書いたことにする(self, 番号, 分):
        self.台帳.つなぎ.execute(
            "UPDATE 書き込み SET 書いた時刻 = ? WHERE 番号 = ?", ((時計.いま() - timedelta(minutes=分)).isoformat(), 番号))

    def 板に置く(self, 本文, 板="shigoto", 鍵="a" * 32, 分=11):
        """画面を通さずに台帳へじかに置き、分だけ前に書いたことにする。"""
        番号 = self.台帳.書く(板, 本文, 鍵)
        self.前に書いたことにする(番号, 分)
        return 番号

    def 聞き役の返事(self, 番号=None):
        """聞き役が置いた返事の (親番号, 本文)。番号を渡せば、その書き込みへの返事だけ。"""
        return [tuple(行) for 行 in self.台帳.つなぎ.execute(
            "SELECT 親番号, 本文 FROM 書き込み WHERE 書いた人の鍵 = ? AND (? IS NULL OR 親番号 = ?) ORDER BY 番号",
            (決まり.聞き役の鍵, 番号, 番号))]

    def 聞き役の記録(self, 番号):
        行 = self.台帳.つなぎ.execute("SELECT 結果, 試した回数 FROM 聞き役の記録 WHERE 書き込み番号 = ?", (番号,)).fetchone()
        return tuple(行) if 行 else None

    def test_114_人の返事が無いまま10分たった板の書き込みに_聞き役が一度だけ返し_名乗りの道は付かない(self):
        self.書く("40歳で会社をクビになった")
        番号 = self.最後の番号()
        尋ねる, 聞いた = self.偽のAI("突然だと、胸が苦しくなるよね。")
        self.前に書いたことにする(番号, 9)
        self.聞き役が回る(尋ねる)
        self.assertEqual(聞いた, [])  # 10分たつ前は尋ねない
        self.前に書いたことにする(番号, 11)
        self.聞き役が回る(尋ねる)
        self.聞き役が回る(尋ねる)  # もう一度回っても、二度は返さない
        self.assertEqual(聞いた, ["40歳で会社をクビになった"])
        self.assertEqual(self.聞き役の返事(), [(番号, "突然だと、胸が苦しくなるよね。")])
        文 = self.頼む("GET", "/ita/shigoto", 人="B")[2]
        self.assertIn("突然だと、胸が苦しくなるよね。", 文)
        self.assertIn(f'<span class="名乗り 聞き役">{決まり.聞き役の名乗り}</span>', 文)
        self.assertNotIn("/nanori?n=" + quote(決まり.聞き役の名乗り), 文)  # 聞き役の返事を1か所に集めて見せない
        self.消す(self.台帳.つなぎ.execute("SELECT 番号 FROM 書き込み WHERE 書いた人の鍵 = ?", (決まり.聞き役の鍵,)).fetchone()[0])
        self.聞き役が回る(尋ねる)  # 持ち主が聞き役の返事を消しても、もう一度は返さない
        self.assertEqual(聞いた, ["40歳で会社をクビになった"])

    def test_115_人の返事があれば返さず_書いた本人の返事と消された返事は人の返事に数えない(self):
        返された = self.板に置く("離婚して3年", 鍵="a" * 32)
        self.台帳.書く("shigoto", "わかる", "b" * 32, 返された)
        自分で足した = self.板に置く("休みの日が長い", 鍵="c" * 32)
        self.台帳.書く("shigoto", "自分で書き足す", "c" * 32, 自分で足した)
        消された = self.板に置く("受験に落ちた", 鍵="d" * 32)
        self.台帳.消す(self.台帳.書く("shigoto", "ひどい返事", "e" * 32, 消された))
        尋ねる, 聞いた = self.偽のAI()
        self.聞き役が回る(尋ねる)
        self.assertEqual(聞いた, ["休みの日が長い", "受験に落ちた"])
        self.assertEqual(self.聞き役の返事(返された), [])

    def test_116_返事_板でない置き場_消した書き込み_6時間より前の書き込みには返さない(self):
        親 = self.板に置く("親の書き込み")
        self.前に書いたことにする(self.台帳.書く("shigoto", "書いた本人の返事", "a" * 32, 親), 11)
        for 置き場 in (決まり.勝ちの置き場, 決まり.その後の置き場, 決まり.宣言の置き場, 決まり.独り言の置き場,
                     決まり.夜の置き場, 決まり.小部屋の置き場(1)):
            self.板に置く(f"{置き場}の書き込み", 置き場)
        self.台帳.消す(self.板に置く("消した書き込み"))
        self.板に置く("古い書き込み", 分=決まり.聞き役が返す期限の秒 // 60 + 1)
        尋ねる, 聞いた = self.偽のAI()
        self.聞き役が回る(尋ねる)
        self.assertEqual(聞いた, ["親の書き込み"])
        self.assertEqual([親番号 for 親番号, _ in self.聞き役の返事()], [親])

    def test_117_つらすぎる言葉のある書き込みには返さず_AIにも送らない(self):
        番号 = self.板に置く("もう消えたい")
        尋ねる, 聞いた = self.偽のAI()
        self.聞き役が回る(尋ねる)
        self.聞き役が回る(尋ねる)
        self.assertEqual(聞いた, [])
        self.assertEqual(self.聞き役の返事(), [])
        self.assertEqual(self.聞き役の記録(番号), ("見送った", 1))  # 見送ったことを残し、次の回は見直さない

    def test_118_AIに送るのは頼みと本文だけで_名乗りもブラウザの乱数も接続元の番号も送らない(self):
        self.名乗る("元・店長")
        self.受け口から("/ita/shigoto/kaku", {"honbun": "店を畳んだ"})
        番号 = self.最後の番号()
        self.前に書いたことにする(番号, 11)
        送った = []

        class 偽の返り:
            def __enter__(self):
                return self

            def __exit__(self, *引数):
                return False

            def read(self, *引数):
                return json.dumps({"choices": [{"message": {"content": json.dumps({"henji": "畳むまで、よく持たせたね。"})}}]}).encode("utf-8")

        def 偽の頼み先(頼み, timeout=None):
            送った.append(頼み)
            return 偽の返り()
        with mock.patch.object(聞き役.urllib.request, "urlopen", 偽の頼み先):
            self.聞き役が回る(lambda 本文: 聞き役.さくらに尋ねる(本文, "tameshi-kagi", "頼みの文"))
        self.assertEqual(len(送った), 1)
        頼み = 送った[0]
        self.assertEqual(頼み.full_url, 聞き役.窓口)
        self.assertEqual(頼み.get_header("Authorization"), "Bearer tameshi-kagi")
        中身 = json.loads(頼み.data)
        self.assertEqual([言葉["content"] for 言葉 in 中身["messages"]], ["頼みの文", "店を畳んだ"])
        for 送らない物 in ("元・店長", self.鍵("A"), "203.0.113.7", "54321"):
            self.assertNotIn(送らない物, 頼み.data.decode("utf-8"))
        self.assertEqual(self.聞き役の返事(番号), [(番号, "畳むまで、よく持たせたね。")])

    def test_119_AIの文も守りを通し_止める言葉_つらすぎる言葉_外への道_使わない言葉_長すぎる文は出さない(self):
        for i, 返事 in enumerate(("上司は死ね", "消えたいよね", "https://example.com を見て", "www.example.com を見て",
                                 "前向きにいこう", "ガンバって", "それは本当に負けなのかな", "あ" * (決まり.聞き役の返事の上限 + 1), "  ")):
            番号 = self.板に置く(f"書き込み{i}")
            self.聞き役が回る(self.偽のAI(返事)[0])
            self.assertEqual(self.聞き役の返事(番号), [], 返事)
            self.assertEqual(self.聞き役の記録(番号), ("止めた", 1), 返事)
        番号 = self.板に置く("改行の書き込み")
        self.聞き役が回る(self.偽のAI("一行目です。\\n二行目です。")[0])  # AIは改行を「\n」の字で返すことがある
        self.assertEqual(self.聞き役の返事(番号), [(番号, "一行目です。\n二行目です。")])

    def test_120_AIに尋ねるのがうまくいかなければ置かず次の回にもう一度_決まった回数でやめ_ほかの書き込みは続ける(self):
        すぐ返る = self.板に置く("一つ目")
        いつも失敗 = self.板に置く("二つ目")
        二度目で返る = self.板に置く("三つ目")
        回数 = {"二つ目": 0, "三つ目": 0}

        def 尋ねる(本文):
            if 本文 in 回数:
                回数[本文] += 1
                if 本文 == "二つ目" or 回数[本文] == 1:
                    raise TimeoutError("返事が来ない")
            return "そうだったんだね。"
        for _ in range(決まり.聞き役が試す回数 + 1):
            self.聞き役が回る(尋ねる)
        self.assertEqual(回数, {"二つ目": 決まり.聞き役が試す回数, "三つ目": 2})
        self.assertEqual(self.聞き役の記録(いつも失敗), ("失敗", 決まり.聞き役が試す回数))
        self.assertEqual(self.聞き役の記録(二度目で返る), ("返した", 2))
        self.assertEqual(len(self.聞き役の返事(すぐ返る)), 1)
        self.assertEqual(self.聞き役の返事(いつも失敗), [])

    def test_121_AIに尋ねるのは24時間に決まった件数まで_やり直しは数に入っていて続け_1回に回るのも決まった件数まで(self):
        番号たち = [self.板に置く(f"書き込み{i}") for i in range(3)]
        聞いた = []

        def 尋ねる(本文):
            聞いた.append(本文)
            if 本文 == "書き込み0" and 聞いた.count(本文) == 1:
                raise TimeoutError("返事が来ない")
            return "そうだったんだね。"
        with mock.patch.object(決まり, "聞き役の1日の上限", 2):
            self.聞き役が回る(尋ねる)
            self.聞き役が回る(尋ねる)  # 書き込み0 のやり直しは、もう数に入っているので尋ねる
        self.assertEqual(聞いた, ["書き込み0", "書き込み1", "書き込み0"])
        self.assertIsNone(self.聞き役の記録(番号たち[2]))
        self.台帳.つなぎ.execute("UPDATE 聞き役の記録 SET 最初に試した時刻 = ?", ((時計.いま() - timedelta(days=1, minutes=1)).isoformat(),))
        with mock.patch.object(決まり, "聞き役の1日の上限", 2):
            self.聞き役が回る(尋ねる)  # 24時間たてば、また尋ねる
        self.assertEqual(聞いた[3:], ["書き込み2"])
        聞いた.clear()
        for i in range(決まり.聞き役の1回の数 + 2):
            self.板に置く(f"多い{i}")
        self.聞き役が回る(尋ねる)
        self.assertEqual(len(聞いた), 決まり.聞き役の1回の数)  # 残りは次の回

    def test_122_AIに尋ねている間に人が返したり持ち主が消したりしたら_聞き役の返事は置かない(self):
        人が返す = self.板に置く("一つ目")
        持ち主が消す = self.板に置く("二つ目")

        def 尋ねる(本文):
            if 本文 == "一つ目":
                self.台帳.書く("shigoto", "人の返事", "b" * 32, 人が返す)
            else:
                self.台帳.消す(持ち主が消す)
            return "そうだったんだね。"
        self.聞き役が回る(尋ねる)
        self.assertEqual(self.聞き役の返事(), [])
        self.assertEqual(self.聞き役の記録(人が返す), ("置かなかった", 1))
        self.assertEqual(self.聞き役の記録(持ち主が消す), ("置かなかった", 1))

    def test_123_人は_聞き役_を含む名乗りを使えない(self):
        for 名乗り in (決まり.聞き役の名乗り, "聞き役", "ＡＩの聞き役です", "聞き役(ai)"):
            状態, _, 文 = self.名乗る(名乗り)
            self.assertEqual(状態, 400, 名乗り)
            self.assertIn("「聞き役」は", 文)
        self.assertEqual(self.台帳.名乗りを読む(self.鍵("A")), "")
        self.assertEqual(self.名乗る("聞く役")[0], 303)

    def test_124_聞き役の返事は_さっきの話に出ず_書いた人の記録を残さず_見回りでは聞き役の返事としてまとまり_決まりに書いてある(self):
        self.板に置く("一つ目の話")
        self.板に置く("二つ目の話", 板="okane")
        self.聞き役が回る(self.偽のAI("聞き役のひとこと。")[0])
        返事たち = [行[0] for 行 in self.台帳.つなぎ.execute("SELECT 番号 FROM 書き込み WHERE 書いた人の鍵 = ? ORDER BY 番号", (決まり.聞き役の鍵,))]
        self.assertEqual(len(返事たち), 2)
        はじめ = self.頼む("GET", "/", 人="B")[2]
        self.assertIn("二つ目の話", はじめ)
        self.assertNotIn("聞き役のひとこと", はじめ)
        self.assertNotIn("への返事", はじめ)
        self.assertEqual(self.書いた人の記録(), [])
        見回り = self.見回りの画面()
        self.assertIn(f'<a href="/kanri/matome?bangou={返事たち[-1]}">聞き役の返事（2件）</a>', 見回り)
        一覧 = self.このブラウザの書き込み(返事たち[-1])[2]
        self.assertIn("<h1>聞き役の返事</h1>", 一覧)
        self.assertNotIn("を書いたブラウザ", 一覧)
        self.assertIn(f"「{決まり.聞き役の名乗り}」が一度だけ短く返す", self.頼む("GET", "/kimari")[2])


class 聞き役の動かし方のテスト(unittest.TestCase):
    """サーバーで聞き役を決まった時刻に動かす決まり（道具/動かし方/）と、聞き役.py をそのまま動かした時。"""
    道具 = os.path.dirname(os.path.abspath(__file__))

    def 読む(self, 名前):
        """書き添え（# から後）を除いた、決まりの行。"""
        with open(os.path.join(self.道具, "動かし方", 名前), encoding="utf-8") as f:
            return [行.split("#", 1)[0].strip() for 行 in f]

    def test_125_聞き役は2分ごとに_makeinuとして動き_書けるのは記録だけで_読む鍵は聞き役の分だけ(self):
        決まりの行 = self.読む("makeinu-kikiyaku.service")
        for 行 in ("Type=oneshot", "User=makeinu", "Group=makeinu", "EnvironmentFile=/etc/makeinu/kikiyaku.env",
                   "ExecStart=/usr/bin/python3 /srv/makeinu/道具/聞き役.py /srv/makeinu/記録/場.db",
                   "NoNewPrivileges=yes", "ProtectSystem=strict", "ProtectHome=yes", "PrivateTmp=yes", "ReadWritePaths=/srv/makeinu/記録"):
            self.assertIn(行, 決まりの行)
        self.assertNotIn("EnvironmentFile=/etc/makeinu/env", 決まりの行)  # 見回りの合言葉は読ませない
        時刻の行 = self.読む("makeinu-kikiyaku.timer")
        self.assertIn("OnUnitActiveSec=2min", 時刻の行)
        self.assertIn("Unit=makeinu-kikiyaku.service", 時刻の行)

    def _古い書き込みで聞き役を動かす(self, 環境):
        """10分より前の板の書き込みが1件だけある記録で、聞き役.py をそのまま動かす。
        終わり方と、[書き込みの数, 聞き役の記録の数] を返す。"""
        置き場 = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, 置き場, True)
        場所 = os.path.join(置き場, "場.db")
        帳 = 台帳(場所)
        番号 = 帳.書く("shigoto", "鍵を確かめる時の書き込み", "a" * 32)
        帳.つなぎ.execute("UPDATE 書き込み SET 書いた時刻 = ? WHERE 番号 = ?", ((時計.いま() - timedelta(minutes=11)).isoformat(), 番号))
        帳.閉じる()
        返り = subprocess.run([sys.executable, "-B", os.path.join(self.道具, "聞き役.py"), 場所],
                            capture_output=True, encoding="utf-8", errors="replace", env=環境, timeout=60)
        帳 = 台帳(場所)
        数 = [帳.つなぎ.execute(f"SELECT COUNT(*) FROM {表}").fetchone()[0] for 表 in ("書き込み", "聞き役の記録")]
        帳.閉じる()
        return 返り, 数

    def test_126_鍵が無ければ_聞き役はAIに尋ねず何も置かず_鍵の名前を知らせて止まる(self):
        環境 = {名前: 値 for 名前, 値 in os.environ.items() if 名前 != "MAKEINU_SAKURA_AI_TOKEN"}
        返り, 数 = self._古い書き込みで聞き役を動かす(環境)
        self.assertNotEqual(返り.returncode, 0)
        self.assertIn("MAKEINU_SAKURA_AI_TOKEN", 返り.stderr)
        self.assertEqual(数, [1, 0])

    def test_127_家計簿の件の鍵しか無ければ_聞き役はそれを使わずAIに尋ねずに止まる(self):
        環境 = {名前: 値 for 名前, 値 in os.environ.items() if 名前 not in ("MAKEINU_SAKURA_AI_TOKEN", "no_proxy", "NO_PROXY")}
        環境["SAKURA_AI_TOKEN"] = "00000000-0000-0000-0000-000000000000:tsukurimono"  # 作り物の家計簿の件の鍵
        環境["https_proxy"] = 環境["HTTPS_PROXY"] = "http://127.0.0.1:9"  # 間違えて尋ねても、外へは出ずにしくじる
        返り, 数 = self._古い書き込みで聞き役を動かす(環境)
        self.assertNotEqual(返り.returncode, 0)
        self.assertIn("MAKEINU_SAKURA_AI_TOKEN", 返り.stderr)
        self.assertNotIn("tsukurimono", 返り.stdout + 返り.stderr)
        self.assertEqual(数, [1, 0])


class 毎日の数のテスト(unittest.TestCase):
    """毎朝の数字で AI が読む数（毎日の数を読む.py）。本文も番地も出さない。何かあった日だけ本人に伝える。"""
    いま = datetime.fromisoformat("2026-11-03T08:00:00+09:00")
    きのう = "2026-11-02T12:00:00+09:00"
    おととい = "2026-11-01T12:00:00+09:00"
    何もない様子 = {"空きGB": 43, "証明書の残り日": 89, "控えの遅れ日": 0}
    何もない数 = {"きのうの人の書き込み": 0, "うち消した": 0, "きのうの聞き役の返事": 0, "人の書き込みの累計": 5, "きのうの知らせ": 0, "知らせの累計": 0,
               "きのうのつらすぎる言葉": 0, "きのうの聞き役の失敗": 0, "きのうの聞き役の止めた": 0, "きのう増えた行": 0}

    def setUp(self):
        self.置き場 = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.置き場, True)
        self.記録 = os.path.join(self.置き場, "場.db")
        self.帳 = 台帳(self.記録)
        self.addCleanup(self.帳.閉じる)

    def 時刻に(self, 時刻):
        return mock.patch.object(時計, "いま", lambda: datetime.fromisoformat(時刻))

    def 書く(self, 時刻, 本文, 鍵="a" * 32, 親番号=None, 名乗り=None, あの時=None):
        with self.時刻に(時刻):
            return self.帳.書く("shigoto", 本文, 鍵, 親番号, 名乗り, None, あの時, "203.0.113.77", 4242)

    def test_149_きのうの数だけを数え_聞き役は人の書き込みに入れない(self):
        self.書く(self.おととい, "おとといの話")
        self.書く(self.きのう, "きのうの話1")
        親 = self.書く(self.きのう, "きのうの話2")
        消す = self.書く(self.きのう, "消された話")
        with self.時刻に(self.きのう):
            self.帳.消す(消す)
            self.帳.聞き役が返す(親, "shigoto", "聞き役の返事です。")
            self.帳.知らせる("b" * 32, 親, "知らせの本文")
            self.帳.聞き役の記録をつける(親, "返した", 99)
            self.帳.聞き役の記録をつける(消す, "失敗")
            self.帳.わかると押す(親, "c" * 32)
            self.帳.名乗りを決める("c" * 32, "名乗りの本文")
            self.帳.小部屋の受け方を決める("c" * 32, False)
        with self.時刻に(self.おととい):
            self.帳.知らせる("b" * 32, None, "おとといの知らせ")
        数 = 毎日の数を読む.数を読む(self.記録, self.いま)
        self.assertEqual(数["きのうの人の書き込み"], 3)
        self.assertEqual(数["うち消した"], 1)
        self.assertEqual(数["きのうの聞き役の返事"], 1)
        self.assertEqual(数["人の書き込みの累計"], 4)
        self.assertEqual(数["きのうの知らせ"], 1)
        self.assertEqual(数["知らせの累計"], 2)
        self.assertEqual(数["きのうの聞き役の失敗"], 1)
        self.assertEqual(数["きのう増えた行"], 3)

    def test_150_日本時間の日付で分ける(self):
        self.書く("2026-11-01T23:59:59+09:00", "前の日の終わり")
        self.書く("2026-11-02T00:00:00+09:00", "きのうの始まり")
        self.書く("2026-11-02T23:59:59+09:00", "きのうの終わり")
        self.書く("2026-11-03T00:00:00+09:00", "今日の始まり")
        self.assertEqual(毎日の数を読む.数を読む(self.記録, self.いま)["きのうの人の書き込み"], 2)

    def test_151_つらすぎる言葉は_本文とあの時を数え_聞き役の文は数えない(self):
        self.書く(self.きのう, "もう死にたい")
        self.書く(self.きのう, "その後は働いた", あの時="消えたいと思った")
        self.書く(self.きのう, "ふつうの話")
        self.書く(self.おととい, "おとといも死にたい")
        self.書く(self.きのう, "死にたいと言う聞き役", 決まり.聞き役の鍵)
        self.assertEqual(毎日の数を読む.数を読む(self.記録, self.いま)["きのうのつらすぎる言葉"], 2)

    def test_152_出す字に本文も番地も鍵も入れない(self):
        self.書く(self.きのう, "ひみつの本文もう死にたい", 名乗り="ひみつの名乗り", あの時="ひみつのあの時")
        with self.時刻に(self.きのう):
            self.帳.知らせる("b" * 32, None, "ひみつの知らせ")
        字 = 毎日の数を読む.字にする(毎日の数を読む.数を読む(self.記録, self.いま), self.何もない様子)
        for 出さない字 in ("ひみつ", "203.0.113.77", "4242", "a" * 32, "b" * 32):
            self.assertNotIn(出さない字, 字)
        self.assertIn("きのうの人の書き込み 1", 字)

    def test_153_記録を読むだけで何も変えない(self):
        self.書く(self.きのう, "読むだけの話")
        self.帳.閉じる()  # 閉じると書き足しの帳面が本体へまとまるので、その後で比べる
        前 = hashlib.sha256(open(self.記録, "rb").read()).hexdigest()
        毎日の数を読む.数を読む(self.記録, self.いま)
        self.assertEqual(hashlib.sha256(open(self.記録, "rb").read()).hexdigest(), 前)
        with self.assertRaises(sqlite3.OperationalError):
            毎日の数を読む.記録を開く(self.記録).execute("DELETE FROM 書き込み")

    def test_154_何もない日は何も伝えない(self):
        self.assertEqual(毎日の数を読む.伝えること(self.何もない数, self.何もない様子), [])

    def test_155_本人に伝えるのは決めた時だけ(self):
        数 = self.何もない数
        様子 = self.何もない様子
        for 足す数, 足す様子, 言葉 in [
            ({"きのうの知らせ": 2}, {}, "新しい知らせ"),
            ({"きのうのつらすぎる言葉": 1}, {}, "つらすぎる言葉"),
            ({"きのうの人の書き込み": 3, "人の書き込みの累計": 3}, {}, "初めて"),
            ({"人の書き込みの累計": 151}, {}, "古い書き込み"),
            ({"きのう増えた行": 1001}, {}, "荒らし"),
            ({"きのうの聞き役の失敗": 3}, {}, "聞き役"),
            ({}, {"空きGB": 29}, "空き"),
            ({}, {"証明書の残り日": 24}, "証明書"),
            ({}, {"証明書の残り日": None}, "証明書"),
            ({}, {"控えの遅れ日": 2}, "控え"),
            ({}, {"控えの遅れ日": None}, "控え"),
        ]:
            伝える = 毎日の数を読む.伝えること({**数, **足す数}, {**様子, **足す様子})
            self.assertEqual(len(伝える), 1, (足す数, 足す様子, 伝える))
            self.assertIn(言葉, 伝える[0])
        # 境目は伝えない
        for 足す数, 足す様子 in [({"人の書き込みの累計": 150}, {}), ({"きのう増えた行": 1000}, {}), ({"きのうの聞き役の失敗": 2}, {}), ({}, {"空きGB": 30}), ({}, {"証明書の残り日": 25}), ({}, {"控えの遅れ日": 1})]:
            self.assertEqual(毎日の数を読む.伝えること({**数, **足す数}, {**様子, **足す様子}), [], (足す数, 足す様子))
        # 書き込みが前からある日は「初めて」と言わない
        self.assertEqual(毎日の数を読む.伝えること({**数, "きのうの人の書き込み": 3, "人の書き込みの累計": 8}, 様子), [])

    def test_156_控えの遅れは一番新しい控えの日付で数え_控えの形でない物は見ない(self):
        控え = os.path.join(self.置き場, "控え")
        self.assertIsNone(毎日の数を読む.控えの遅れ日(self.記録, self.いま))
        os.makedirs(控え)
        for 名前 in ("2026-10-31.db", "2026-11-02.db", "2026-11-03.db.書きかけ", "2026-11-09.txt", "めも.db"):
            open(os.path.join(控え, 名前), "w").close()
        self.assertEqual(毎日の数を読む.控えの遅れ日(self.記録, self.いま), 1)

    def test_157_証明書を読めない時は分からないとして伝える(self):
        with mock.patch.object(毎日の数を読む.socket, "create_connection", side_effect=OSError("つながらない")):
            self.assertIsNone(毎日の数を読む.証明書の残り日())


class 受け口のテスト(unittest.TestCase):
    """前に置く受け口（nginx）の決まりの書き漏れを見る。受け口を通した動きは、サーバーの中で 受け口を確かめる.py が確かめる。"""
    場所 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "受け口")

    def 読む(self, 名前):
        """書き添え（# から後）を除いた、決まりの行。"""
        with open(os.path.join(self.場所, 名前), encoding="utf-8") as f:
            return [行.split("#", 1)[0].strip() for 行 in f]

    def 入口ごと(self):
        """makeinu.conf の server の塊ごとの行。"""
        塊たち, いま = [], None
        for 行 in self.読む("makeinu.conf"):
            if 行 == "server {":
                いま = []
                塊たち.append(いま)
            elif いま is not None and 行:
                いま.append(行)
        return 塊たち

    def test_129_どの入口も_来た人の番地を受け口の記録に残さず_版を見せない(self):
        塊たち = self.入口ごと()
        self.assertEqual(len(塊たち), 3)
        for 塊 in 塊たち:
            if "include snippets/makeinu-ukeguchi.conf;" in 塊:
                continue  # 決まりの行は test_109 が見る
            for 行 in ("access_log off;", "error_log /dev/null;", "server_tokens off;"):
                self.assertIn(行, 塊, f"この入口に足りない：{塊}")

    def test_130_名前の無い頼みは切り_httpはhttpsへ移すだけで_httpsは名前と証明書で受ける(self):
        知らない, http, https = self.入口ごと()
        for 行 in ("listen 80 default_server;", "listen 443 ssl default_server;", "server_name _;", "ssl_reject_handshake on;", "return 444;"):
            self.assertIn(行, 知らない)
        for 行 in ("listen 80;", "server_name makeinu.net;", "root /var/www/makeinu-shoumei;", "return 301 https://makeinu.net$request_uri;"):
            self.assertIn(行, http)
        self.assertNotIn("include snippets/makeinu-ukeguchi.conf;", http, "http のままでは場へ渡さない")
        for 行 in ("listen 443 ssl;", "server_name makeinu.net;",
                   "ssl_certificate /etc/letsencrypt/live/makeinu.net/fullchain.pem;",
                   "ssl_certificate_key /etc/letsencrypt/live/makeinu.net/privkey.pem;",
                   'add_header Strict-Transport-Security "max-age=31536000" always;',
                   "include snippets/makeinu-ukeguchi.conf;"):
            self.assertIn(行, https)

    def test_158_Googleの持ち主の確かめは_httpsの入口だけで決まった1行を返す(self):
        知らない, http, https = self.入口ごと()
        道たち = [行 for 行 in https if re.fullmatch(r"location = /google[0-9a-f]+\.html \{", 行)]
        self.assertEqual(len(道たち), 1)
        名前 = 道たち[0].split("/")[1].split(" ")[0]
        self.assertIn(f'return 200 "google-site-verification: {名前}";', https)
        self.assertFalse([行 for 行 in 知らない + http if "google" in 行])

    def test_148_場が止まっている時は_入口が日本語の知らせを出す(self):
        行たち = self.読む("makeinu-ukeguchi.conf")
        for 行 in ("error_page 502 503 504 /yasumi.html;", "location = /yasumi.html {", "internal;", "root /var/www/makeinu-yasumi;", "charset utf-8;"):
            self.assertIn(行, 行たち)
        with open(os.path.join(self.場所, "yasumi.html"), encoding="utf-8") as f:
            文 = f.read()
        self.assertIn("少し待ってから", 文)
        self.assertIn('<meta charset="utf-8">', 文)
        self.assertNotIn("http", 文)  # 外のものを読み込まない
        self.assertNotIn("<script", 文)

    def test_131_検索に出すのははじめの画面だけで_ほかの画面には出さない見出しを付ける(self):
        self.assertIn("add_header X-Robots-Tag $makeinu_kensaku always;", self.読む("makeinu-ukeguchi.conf"))
        行たち = self.読む("makeinu-http.conf")
        for 行 in ("map $uri $makeinu_kensaku {", 'default "noindex, nofollow";', '/ "";'):
            self.assertIn(行, 行たち)

    def test_109_受け口は来た人の番地と港を上書きして渡し_記録を残さず_場の大きさの上限で断り_IPv6とサーバーの中だけの入口では聞かない(self):
        決まりの行 = self.読む("makeinu-ukeguchi.conf")
        for 行 in ("proxy_set_header X-Real-IP $remote_addr;", "proxy_set_header X-Real-Port $remote_port;",
                   "access_log off;", "error_log /dev/null;", "limit_conn makeinu_conn 20;", "server_tokens off;",
                   f"client_max_body_size {決まり.送られた中身の上限 // 1024}k;", "proxy_pass http://$makeinu_ba;"):
            self.assertIn(行, 決まりの行)
        self.assertIn("limit_conn_zone $binary_remote_addr zone=makeinu_conn:10m;", self.読む("makeinu-http.conf"))
        入口 = self.読む("makeinu.conf")
        self.assertIn("include snippets/makeinu-ukeguchi.conf;", 入口)
        self.assertIn("set $makeinu_ba 127.0.0.1:8765;", 入口)
        聞く所 = [行 for 行 in 入口 if 行.startswith("listen ")]
        self.assertTrue(聞く所)
        for 行 in 聞く所:
            self.assertNotIn("[", 行, "IPv6 では聞かない（書いた人の記録と荒らしの数えは IPv4 の番地で）")
            self.assertNotIn("127.0.0.1", 行, f"外に開いた形では、サーバーの中だけの入口を残さない：{行}")


class 控えの写しのテスト(unittest.TestCase):
    """公開前に要るもの 順9：サーバーは一番新しい毎日の控えを出し（控えを出す.py）、
    自宅PCがそれを取ってきて、鍵をかけて置く（控えを取ってくる.py）。"""
    道具 = os.path.dirname(os.path.abspath(__file__))

    def setUp(self):
        self.置き場 = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.置き場, True)
        self.控えの場所 = os.path.join(self.置き場, "控え")
        self.写しの場所 = os.path.join(self.置き場, "控えの写し")

    def 控えを作る(self, 日付, 本文="控えの話"):
        """その日の0:05に、本物の台帳から毎日の控えを作る（書いた人の記録は入らない）。控えの場所を返す。"""
        記録 = 台帳(os.path.join(self.置き場, f"場_{日付}.db"))
        try:
            記録.書く("shigoto", 本文, "a" * 32, 番地="203.0.113.5", 港=1000)
            with mock.patch.object(時計, "いま", lambda: datetime.fromisoformat(日付 + "T00:05:00+09:00")):
                return 記録.控えを取る(self.控えの場所)
        finally:
            記録.閉じる()

    def 番地の入った控えを作る(self, 日付):
        """控えを作っている最中（写した記録から書いた人の記録を消す前）の形。"""
        記録 = 台帳(os.path.join(self.置き場, f"場_{日付}.db"))
        try:
            記録.書く("shigoto", "最中の話", "a" * 32, 番地="203.0.113.9", 港=1000)
            os.makedirs(self.控えの場所, exist_ok=True)
            写し = sqlite3.connect(os.path.join(self.控えの場所, 日付 + ".db"))
            記録.つなぎ.backup(写し)
            写し.close()
        finally:
            記録.閉じる()

    def 控えを出す(self):
        返り = subprocess.run([sys.executable, "-B", os.path.join(self.道具, "控えを出す.py"), self.控えの場所],
                             capture_output=True, timeout=60)
        return 返り.returncode, 返り.stdout

    def 読む(self, 出たもの):
        見出し, _, 本体 = 出たもの.partition(b"\n")
        return json.loads(見出し), base64.b64decode(本体)

    def test_103_控えを出すは_一番新しい毎日の控えを_名前と大きさと印を付けて_字だけで出す(self):
        for 日付 in ("2026-10-24", "2026-10-25", "2026-10-26"):
            self.控えを作る(日付, f"{日付}の話")
        # 毎日の控えでない物は、読める控えの形でも出さない（置き直す時の退避・作りかけ・書き足しの帳面・メモ）
        with open(os.path.join(self.控えの場所, "2026-10-26.db"), "rb") as f:
            読める形 = f.read()
        for 名前 in ("退避_20261027-1336.db", "2026-10-27.db.書きかけ", "2026-10-27.db-wal", "メモ.txt"):
            with open(os.path.join(self.控えの場所, 名前), "wb") as f:
                f.write(読める形)
        os.utime(os.path.join(self.控えの場所, "2026-10-24.db"))  # 一番新しいのは、触った時刻でなく日付で決める
        番号, 出たもの = self.控えを出す()
        self.assertEqual(番号, 0)
        self.assertTrue(出たもの.isascii())  # Windows で字として受け取っても壊れない
        見出し, 中身 = self.読む(出たもの)
        with open(os.path.join(self.控えの場所, "2026-10-26.db"), "rb") as f:
            self.assertEqual(中身, f.read())
        self.assertEqual(見出し, {"名前": "2026-10-26.db", "大きさ": len(中身), "sha256": hashlib.sha256(中身).hexdigest()})

    def test_104_書いた人の記録が入った控えや壊れた控えは出さず_一つ前を出し_無ければ何も出さない(self):
        self.控えを作る("2026-10-24")
        self.番地の入った控えを作る("2026-10-25")
        with open(os.path.join(self.控えの場所, "2026-10-26.db"), "wb") as f:
            f.write(b"SQLite format 3\x00" + b"\x00" * 50)  # 開けない控え
        # 開けて台の一覧も読めるが、書き込みの台の1ページが壊れた控え
        中が壊れた = self.控えを作る("2026-10-27")
        つなぎ = sqlite3.connect(中が壊れた)
        根, ページの大きさ = つなぎ.execute("SELECT rootpage FROM sqlite_master WHERE name = '書き込み'").fetchone()[0], つなぎ.execute("PRAGMA page_size").fetchone()[0]
        つなぎ.close()
        with open(中が壊れた, "r+b") as f:
            f.seek((根 - 1) * ページの大きさ)
            f.write(b"\xff" * 16)
        番号, 出たもの = self.控えを出す()
        self.assertEqual(番号, 0)
        見出し, 中身 = self.読む(出たもの)
        self.assertEqual(見出し["名前"], "2026-10-24.db")
        self.assertNotIn(b"203.0.113", 中身)
        os.remove(os.path.join(self.控えの場所, "2026-10-24.db"))
        self.assertEqual(self.控えを出す(), (1, b""))

    def test_108_毎日の控えは作り終えてから名前を付け_作っている最中は控えの名前で見えない(self):
        記録 = 台帳(os.path.join(self.置き場, "場.db"))
        self.addCleanup(記録.閉じる)
        記録.書く("shigoto", "最中の話", "a" * 32, 番地="203.0.113.7", 港=1000)
        控え = os.path.join(self.控えの場所, 時計.いま().astimezone(時計.日本時間).strftime("%Y-%m-%d") + ".db")
        os.makedirs(self.控えの場所)
        with open(控え + ".書きかけ", "wb") as f:
            f.write("前に途中で止まった時の残り".encode())
        見えたか = []
        本物 = sqlite3.connect

        class 見張るつなぎ(sqlite3.Connection):
            def execute(self, sql, *引数):
                if sql.strip().upper() == "VACUUM":
                    見えたか.append(os.path.exists(控え))
                return super().execute(sql, *引数)

        def 見張って開く(場所, *引数, **名前つき):
            if os.path.dirname(os.path.abspath(str(場所))) == os.path.abspath(self.控えの場所):
                名前つき["factory"] = 見張るつなぎ
            return 本物(場所, *引数, **名前つき)

        with mock.patch("sqlite3.connect", 見張って開く):
            self.assertEqual(記録.控えを取る(self.控えの場所), 控え)
        # 書いた人の記録を消して詰め直している間は、まだ控えの名前のファイルは無い（取りに来ても出さない）
        self.assertEqual(見えたか, [False])
        self.assertEqual(os.listdir(self.控えの場所), [os.path.basename(控え)])

    # ---- 自宅PCの側 ----
    def 試しの鍵(self, 中身):
        """試しの鍵（本物は Windows の仕組み）。かけても外しても同じ形で、中の字は見えなくなる。"""
        return bytes(字 ^ 0x5A for 字 in 中身)

    def 偽のssh(self, 出たもの, 終わりの番号=0):
        """サーバーにつなぐ代わりに、決まった出力を返す命令。"""
        出力 = os.path.join(self.置き場, f"出力_{len(os.listdir(self.置き場))}.txt")
        with open(出力, "wb") as f:
            f.write(出たもの)
        偽 = os.path.join(self.置き場, "偽のssh.py")
        with open(偽, "w", encoding="utf-8") as f:
            f.write("import sys\nsys.stdout.buffer.write(open(sys.argv[1], 'rb').read())\nsys.exit(int(sys.argv[2]))\n")
        return [sys.executable, 偽, 出力, str(終わりの番号)]

    def 取ってくる(self, ssh命令):
        return 控えを取ってくる.取ってくる(ssh命令, self.写しの場所, self.試しの鍵, 4)

    def 写したち(self):
        return sorted(名前 for 名前 in os.listdir(self.写しの場所) if 名前.endswith(".鍵付き"))

    def 取ってきた記録(self):
        with open(os.path.join(self.写しの場所, "取ってきた記録.txt"), encoding="utf-8") as f:
            return f.read()

    def test_105_自宅PCは_取ってきた控えに鍵をかけて置き_同じ日は1つだけ_新しい4つを残す(self):
        元たち = {}
        for 日 in range(21, 27):
            日付 = f"2026-10-{日}"
            with open(self.控えを作る(日付, f"{日付}の話"), "rb") as f:
                元たち[日付] = f.read()
            self.assertEqual(self.取ってくる(self.偽のssh(self.控えを出す()[1])), 0, 日付)
        self.assertEqual(self.写したち(), [f"2026-10-{日}.鍵付き" for 日 in range(23, 27)])
        for 名前 in self.写したち():
            with open(os.path.join(self.写しの場所, 名前), "rb") as f:
                写し = f.read()
            日付 = 名前.split(".")[0]
            self.assertNotIn(f"{日付}の話".encode(), 写し)  # 鍵がかかっていて、中の字は見えない
            self.assertEqual(self.試しの鍵(写し), 元たち[日付])  # 外すと元の控えに戻る
        # 同じ日にもう一度取りに行っても、2つは置かない
        self.assertEqual(self.取ってくる(self.偽のssh(self.控えを出す()[1])), 0)
        self.assertEqual(len(self.写したち()), 4)
        self.assertEqual(self.取ってきた記録().count("取ってきた："), 6)
        self.assertIn("もうある：2026-10-26.db", self.取ってきた記録())

    def test_106_中身が違う_欠けた_名前がおかしい_SQLiteでない_つながらない時は置かず_前の写しも消さない(self):
        self.控えを作る("2026-10-25")
        self.assertEqual(self.取ってくる(self.偽のssh(self.控えを出す()[1])), 0)
        self.控えを作る("2026-10-26")
        出たもの = self.控えを出す()[1]
        見出し, 中身 = self.読む(出たもの)

        def 出し直す(見出し=見出し, 中身=中身):
            return json.dumps(見出し).encode() + b"\n" + base64.encodebytes(中身)
        偽の中身 = b"x" * 100
        悪い出力たち = {
            "中身が違う": 出し直す(中身=中身[:-1] + bytes([中身[-1] ^ 1])),
            "欠けた": 出し直す(中身=中身[: len(中身) // 2]),
            "名前がおかしい": 出し直す(見出し={**見出し, "名前": "../../2026-10-26.db"}),
            "SQLiteでない": 出し直す({**見出し, "大きさ": len(偽の中身), "sha256": hashlib.sha256(偽の中身).hexdigest()}, 偽の中身),
            "空": b"",
            "見出しが読めない": b"not json\n" + base64.encodebytes(中身),
        }
        for 訳, 悪い in 悪い出力たち.items():
            self.assertEqual(self.取ってくる(self.偽のssh(悪い)), 1, 訳)
        self.assertEqual(self.取ってくる(self.偽のssh(出たもの, 255)), 1)  # つながらない（ssh が失敗で終わる）
        self.assertEqual(self.写したち(), ["2026-10-25.鍵付き"])
        self.assertFalse([名前 for 名前 in os.listdir(self.写しの場所) if 名前.endswith(".書きかけ")])
        self.assertEqual(self.取ってきた記録().count("うまくいかなかった："), 7)

    def Windowsのpython(self):
        """本物の鍵（Windows の仕組み）を試せる Python と、そこから見た場所の書き方。無ければ (None, None)。"""
        if sys.platform == "win32":
            return sys.executable, (lambda 場所: 場所)
        python = shutil.which("python.exe")
        if not python or not shutil.which("wslpath"):
            return None, None
        try:
            if subprocess.run([python, "-c", "import sys; print(sys.platform)"], capture_output=True, text=True, timeout=60).stdout.strip() != "win32":
                return None, None
        except (OSError, subprocess.SubprocessError):
            return None, None
        return python, (lambda 場所: subprocess.run(["wslpath", "-w", 場所], capture_output=True, text=True).stdout.strip())

    def test_107_本物の鍵は_このWindowsの利用者で外せて元の控えに戻り_中の字は見えない(self):
        python, 窓から = self.Windowsのpython()
        if not python:
            self.skipTest("Windows の Python が無い（サーバーの上など）。作業用PC・自宅PCで確かめる")
        with open(self.控えを作る("2026-10-26", "本物の鍵で守る話"), "rb") as f:
            元 = f.read()
        _, 偽, 出力, _ = self.偽のssh(self.控えを出す()[1])
        # 自宅PCと同じ Windows の Python で、取ってきて本物の鍵をかける
        書き = ("import sys; sys.path.insert(0, sys.argv[1]); import 控えを取ってくる as k; "
                "sys.exit(k.取ってくる([sys.executable, sys.argv[2], sys.argv[3], '0'], sys.argv[4], k.鍵をかける, 4))")
        返り = subprocess.run([python, "-B", "-c", 書き, 窓から(self.道具), 窓から(偽), 窓から(出力), 窓から(self.写しの場所)],
                             capture_output=True, encoding="utf-8", errors="replace", timeout=120)
        self.assertEqual(返り.returncode, 0, 返り.stderr)
        [名前] = self.写したち()
        with open(os.path.join(self.写しの場所, 名前), "rb") as f:
            写し = f.read()
        self.assertNotIn("本物の鍵で守る話".encode(), 写し)
        self.assertNotIn(b"SQLite format 3", 写し)
        # 戻す時は「開く」で、鍵を外した控えを書き出す
        戻した = os.path.join(self.置き場, "戻した.db")
        返り = subprocess.run([python, "-B", 窓から(os.path.join(self.道具, "控えを取ってくる.py")), "開く",
                              窓から(os.path.join(self.写しの場所, 名前)), 窓から(戻した)], capture_output=True, encoding="utf-8", errors="replace", timeout=120)
        self.assertEqual(返り.returncode, 0, 返り.stderr)
        with open(戻した, "rb") as f:
            self.assertEqual(f.read(), 元)
        # 書き出す先が既にあれば、上書きしない
        返り = subprocess.run([python, "-B", 窓から(os.path.join(self.道具, "控えを取ってくる.py")), "開く",
                              窓から(os.path.join(self.写しの場所, 名前)), 窓から(戻した)], capture_output=True, encoding="utf-8", errors="replace", timeout=120)
        self.assertNotEqual(返り.returncode, 0)
        with open(戻した, "rb") as f:
            self.assertEqual(f.read(), 元)

if __name__ == "__main__":
    unittest.main(verbosity=2)
