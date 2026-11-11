"""負け犬の癒し：見る画面（はじめ・板・各置き場・小部屋・見回り）。

場.py の受け口が、この画面たちを受け継いで使う。ここは見せるだけで、書き込みはしない。
"""
import html
from datetime import datetime, timedelta
from urllib.parse import urlparse

import 決まり
import 時計
from 置き場 import 置き場の名前, 置き場の場所, 置き場を言う
from 絵 import 屋台の絵, 小さいのれん
from 見た目 import 頁, 時刻を見せる, 本文を見せる, 断りを見せる, 話を見せる, 見出しを見せる, 知らせる道, 中身を見せる


# 検索に出すのは、はじめの画面だけ（ほかの画面には受け口が noindex を付ける）。
# 題には探す人が打つ言葉を入れ、説明は持ち主が書いた文をそのまま使う（決定メモ「検索に出す字」）
はじめの題 = "負け犬の癒し｜匿名で愚痴を吐き出せる掲示板"
検索の説明 = ("ポジティブでいろ。前向きな言葉を使おう。元気出していこう。・・・うるせーな。わかってんだよ。"
          "いいじゃねえかよネガティブにいたってよ。無理に前を向かなくていいんだよ。")


def 残りを見せる(iso):
    残り秒 = 決まり.独り言が見える秒 - (時計.いま() - datetime.fromisoformat(iso)).total_seconds()
    return f"あと{int(残り秒 // 3600)}時間で消えます" if 残り秒 >= 3600 else "もうすぐ消えます"


def 抜き出す(本文, 字数=40):
    """1行にまとめ、長ければ途中で切る。"""
    一行 = " ".join(本文.split())
    return 一行 if len(一行) <= 字数 else 一行[:字数] + "…"


def 今夜の始まり():
    return 決まり.今夜の始まり(時計.いま().astimezone(時計.日本時間))


class 画面たち:
    def _はじめ(self, 鍵, 新しい鍵, 問い, 断る訳="", 書きかけ=None):
        板の一覧 = 決まり.板の一覧を読む()
        板たち = "".join(
            f'<a class="板" href="/ita/{板.鍵}"><h2>{html.escape(板.名前)}</h2><small>{html.escape(板.ひとこと)}</small></a>'
            for 板 in 板の一覧
        )
        # 来た人がまず吐き出せるよう、板を一番上に。名乗りは無くても書けるので一番下に置く
        # 「その負け、本当に負けか」は作り手の芯で、表には出さない。前に出すのは、無理に前を向かず自然体でいる禅の言葉
        # 題はのれんの絵に書いてあるので、見出しは読み上げ用にだけ置く
        中身 = f"""{屋台の絵()}<h1 class="読み上げ">負け犬の癒し</h1>
<div class="掛け軸"><p class="禅語">柳は緑、<br>花は紅。</p>
<p class="問い">無理に前を向かなくていい。<br>そのままで、いていい。<br>名前も肩書きもいりません。<br>吐き出して、同じ境遇の人と<br>話していってください。</p></div>
<div class="板たち">{板たち}</div>
{self._いまの話(板の一覧)}
<p class="品書き">ほかの席</p>
<a class="場所へ" href="/kachi"><b>今日の小さな勝ち</b><small>世間では数えられない勝ちを、1行だけ置いていく</small></a>
<a class="場所へ" href="/sonogo"><b>その後の話の棚</b><small>つらかったあの時と、そのあとどうなったか</small></a>
<a class="場所へ" href="/mouikkai"><b>もう一回の宣言</b><small>「もう一回やってみる」を置いていく。みんなは静かに見守るだけ</small></a>
<a class="場所へ 夜へ" href="/yoru"><b>夜の部屋</b><small>{"いま開いています。" if 今夜の始まり() else ""}23時から朝5時まで。眠れない夜、同じ時間に起きている人とだけ</small></a>
<a class="場所へ" href="/heya"><b>1対1の小部屋</b><small>同じ名乗りの人と、匿名のまま2人で話す</small></a>
<a class="場所へ 独り言へ" href="/hitori"><b>独り言</b><small>誰にも返されない。24時間で消える</small></a>
<div id="nanori">{self._そっと(問い)}{self._名乗りの欄(鍵, 断る訳, 書きかけ)}</div>
<p class="下の道"><a href="/kimari">利用の決まり</a><a href="/kojin">個人情報の扱い</a><a href="/shiraseru">持ち主へ知らせる</a></p>"""
        self._返す(400 if 断る訳 else 200, 頁(はじめの題, 中身, 検索の説明), 新しい鍵)

    def _いまの話(self, 板の一覧):
        """人がいる気配として、板の新しい書き込みを3つだけ。名乗りは出さない。まだ何も無ければ、この段ごと出さない。"""
        名前 = {板.鍵: 板.名前 for 板 in 板の一覧}
        行たち = self.台帳.板たちの新しい書き込み(list(名前), 件数=3)
        if not 行たち:
            return ""
        話たち = "".join(
            f'''<a class="いまの話" href="/ita/{行["板"]}#k{行["親番号"] or 行["番号"]}"><span>{html.escape(名前[行["板"]])}{"への返事" if 行["親番号"] else ""}　{時刻を見せる(行["書いた時刻"])}</span>{html.escape(抜き出す(行["本文"]))}</a>'''
            for 行 in 行たち
        )
        # data-nosnippet：はじめの画面は検索に出すが、人の書いた字は検索結果の文に出さない
        return f'<div class="いまの話たち" data-nosnippet><p class="品書き">さっきの話</p>{話たち}</div>'

    def _名乗りの欄(self, 鍵, 断る訳="", 書きかけ=None):
        """はじめの画面の一番下。名乗った後も止めた時もここ（#nanori）へ飛ぶので、断りと相談先はこのそばに出す。"""
        名乗り = self.台帳.名乗りを読む(鍵) if 書きかけ is None else 書きかけ
        断り = 断りを見せる(断る訳)
        return f"""<form class="名乗りの欄" method="post" action="/nanori#nanori">{断り}
<b>ゆるい名乗り</b> <small>匿名のまま、肩書きだけ。空にすると名無しに戻ります。</small>
<input type="text" name="nanori" maxlength="{決まり.名乗りの上限}" placeholder="例：元・就活全落ち" value="{html.escape(名乗り)}">
<button class="送る" type="submit">名乗る</button></form>"""

    def _いまの名乗り(self, 鍵):
        名乗り = self.台帳.名乗りを読む(鍵)
        return f'<p class="いまの名乗り">{html.escape(名乗り) if 名乗り else "名無し"} として書きます（<a href="/#nanori">変える</a>）</p>'

    def _名乗りを見せる(self, 名乗り, 見る人の鍵, 新しい鍵):
        名乗り = 決まり.名乗りを整える(名乗り)
        if not 名乗り:
            return self._移る("/", 新しい鍵)
        名前 = 置き場の名前()
        同じ名乗り = 決まり.そろえる(self.台帳.名乗りを読む(見る人の鍵)) == 決まり.そろえる(名乗り)
        開ける = 同じ名乗り and self._書き始めて1日たったか(見る人の鍵)
        閉じた相手たち = self.台帳.閉じた部屋の相手たち(見る人の鍵) if 開ける else set()
        行たち = "".join(
            f"""<div class="書き込み" id="k{行["番号"]}">{見出しを見せる(行)}
{話を見せる(行)}<div class="知らせる段"><small><a href="{置き場の場所(行["板"])}#k{行["親番号"] or 行["番号"]}">{html.escape(置き場を言う(行["板"], 名前))}{"への返事" if 行["親番号"] else ""}で見る</a></small>{知らせる道(行["番号"])}</div>
{f'<form method="post" action="/heya/hiraku"><input type="hidden" name="bangou" value="{行["番号"]}"><button type="submit">この人と2人で話す</button></form>' if 開ける and 行["書いた人の鍵"] != 見る人の鍵 and self._相手と開けるか(行["書いた人の鍵"], 閉じた相手たち) else ""}</div>"""
            for 行 in self.台帳.名乗りの書き込み(決まり.そろえる(名乗り), 見る人の鍵)
        ) or '<p class="問い">この名乗りの書き込みは、まだありません。</p>'
        案内 = ""
        if not 同じ名乗り:
            案内 = '<p class="いまの名乗り">同じ名乗りにすると、この人たちと2人で話せます。</p>'
        elif not 開ける:
            案内 = '<p class="いまの名乗り">2人で話せるのは、書き始めて1日たってからです。</p>'
        中身 = f"""{小さいのれん()}<a class="戻る" href="/">← はじめへ</a>
<h1>「{html.escape(名乗り)}」の人たち</h1><p class="問い">同じ名乗りで書かれたものを、新しい順に。</p>
{案内}{行たち}"""
        self._返す(200, 頁(f"{名乗り}｜負け犬の癒し", 中身), 新しい鍵)

    def _板を見せる(self, 板の鍵, 見る人の鍵, 新しい鍵, 問い, 断る訳="", 書きかけ="", 返事の断り=None):
        """返事の断り＝(返事先の番号, 断る訳, 書きかけ)。止めた返事は、その書き込みの下に書きかけごと戻す。"""
        板 = self._板(板の鍵)
        if not 板:
            return self._見つからない(新しい鍵)
        行たち = self.台帳.板の書き込み(板.鍵, 見る人の鍵)
        返事 = self.台帳.返事たち([行["番号"] for 行 in 行たち], 見る人の鍵)
        書き込みたち = "".join(self._書き込みを見せる(行, 返事[行["番号"]], 返事の断り) for 行 in 行たち)
        if not 書き込みたち:
            書き込みたち = '<p class="問い">まだ誰も書いていません。最初のひとことをどうぞ。</p>'
        断り = 断りを見せる(断る訳)
        中身 = f"""{小さいのれん()}<a class="戻る" href="/">← はじめへ</a>
<h1>{html.escape(板.名前)}の板</h1><p class="問い">{html.escape(板.ひとこと)}</p>
{self._そっと(問い)}
{self._いまの名乗り(見る人の鍵)}<form method="post" action="/ita/{板.鍵}/kaku">{断り}
<textarea name="honbun" maxlength="{決まり.本文の上限}" placeholder="ここに吐き出してください。名前はいりません。">{html.escape(書きかけ)}</textarea>
<button class="送る" type="submit">置いていく</button></form>
{書き込みたち}"""
        self._返す(400 if 断る訳 or 返事の断り else 200, 頁(f"{板.名前}の板｜負け犬の癒し", 中身), 新しい鍵)

    def _そっと(self, 問い):
        """つらすぎる言葉を書いた本人にだけ出す相談先の箱。"""
        if 問い.get("sotto") != "1":
            return ""
        return f"""<div class="そっと">書いてくれてありがとう。ここに置いていって大丈夫です。
<br>もし今とてもつらいなら、話を聞いてくれる所もあります。{self._相談先の一覧()}</div>"""

    def _相談先の一覧(self):
        """相談先は 中身/相談先.txt の1か所から出す（そっと出す箱と、利用の決まりのページ）。"""
        相談先たち = "".join(
            f'<li>{html.escape(先.名前)}　<span class="番号">{html.escape(先.番号)}</span>（{html.escape(先.ひとこと)}）</li>' for 先 in 決まり.相談先を読む()
        )
        return f"<ul>{相談先たち}</ul>"

    def _文を見せる(self, ファイル名, 題, 新しい鍵):
        """利用の決まり・個人情報の扱い。文は 中身/ に置き、相談先は相談先の一覧から出す（番号を2か所に書くと直し漏れる）。"""
        中身 = f"""{小さいのれん()}<a class="戻る" href="/">← はじめへ</a>
<h1>{html.escape(題)}</h1><div class="文">{中身を見せる(決まり.文を読む(ファイル名), {"{相談先}": self._相談先の一覧()})}</div>"""
        self._返す(200, 頁(f"{題}｜負け犬の癒し", 中身), 新しい鍵)

    def _わかるを見せる(self, 行, 押す字="わかる", 押した字="わかった", 言った字="わかる、と言った人がいます"):
        """わかるの段。右の端に、持ち主へ知らせる入口も置く。"""
        if 行["自分がわかる"]:
            return f'<div class="わかる"><button disabled>{押した字}</button><span>{言った字}</span>{知らせる道(行["番号"])}</div>'
        誰か = f"<span>{言った字}</span>" if 行["誰かがわかる"] else ""
        return f'<div class="わかる"><form method="post" action="/wakaru/{行["番号"]}"><button type="submit">{押す字}</button></form>{誰か}{知らせる道(行["番号"])}</div>'

    def _書き込みを見せる(self, 行, 返事, 返事の断り):
        返事たち = "".join(
            f'<div class="返事" id="k{返["番号"]}">{見出しを見せる(返)}<p>{本文を見せる(返["本文"])}</p>{self._わかるを見せる(返)}</div>'
            for 返 in 返事
        )
        断り, 書きかけ, 開く = "", "", ""
        if 返事の断り and 返事の断り[0] == 行["番号"]:
            断り = 断りを見せる(返事の断り[1])
            書きかけ, 開く = 返事の断り[2], " open"
        return f"""<div class="書き込み" id="k{行["番号"]}">{見出しを見せる(行)}
<p>{本文を見せる(行["本文"])}</p>{self._わかるを見せる(行)}
{f'<div class="返事たち">{返事たち}</div>' if 返事たち else ""}
<details{開く}><summary>返事をする</summary><form method="post" action="/henji/{行["番号"]}">{断り}
<textarea name="honbun" maxlength="{決まり.本文の上限}" placeholder="わかるの一言や、自分ならこう見る、を。">{html.escape(書きかけ)}</textarea>
<button class="送る" type="submit">返す</button></form></details></div>"""

    def _勝ちを見せる(self, 見る人の鍵, 新しい鍵, 問い, 断る訳="", 書きかけ=""):
        勝ちたち = "".join(
            f"""<div class="書き込み" id="k{行["番号"]}">{見出しを見せる(行)}
<p>{本文を見せる(行["本文"])}</p>{self._わかるを見せる(行, "それ、勝ち", "勝ちと言った", "勝ち、と言った人がいます")}</div>"""
            for 行 in self.台帳.板の書き込み(決まり.勝ちの置き場, 見る人の鍵)
        ) or '<p class="問い">まだ誰も置いていません。最初の勝ちをどうぞ。</p>'
        断り = 断りを見せる(断る訳)
        中身 = f"""{小さいのれん()}<a class="戻る" href="/">← はじめへ</a>
<h1>今日の小さな勝ち</h1><p class="問い">世間では数えられない勝ちを、1行だけ。</p>
{self._そっと(問い)}
{self._いまの名乗り(見る人の鍵)}<form method="post" action="/kachi/kaku">{断り}
<input type="text" name="honbun" maxlength="{決まり.勝ちの上限}" placeholder="例：今日は布団から出た" value="{html.escape(書きかけ)}">
<button class="送る" type="submit">置く</button></form>
{勝ちたち}"""
        self._返す(400 if 断る訳 else 200, 頁("今日の小さな勝ち｜負け犬の癒し", 中身), 新しい鍵)

    def _独り言を見せる(self, 新しい鍵, 問い, 断る訳="", 書きかけ=""):
        """名乗りも、わかるも、返事も出さない。24時間たつと画面から消える（記録は見回り用に残る）。"""
        独り言たち = "".join(
            f"""<div class="書き込み 独り言"><span class="残り">{残りを見せる(行["書いた時刻"])}</span><p>{本文を見せる(行["本文"])}</p><div class="知らせる段">{知らせる道(行["番号"])}</div></div>"""
            for 行 in self.台帳.板の書き込み(
                決まり.独り言の置き場, "", いつから=時計.いま() - timedelta(seconds=決まり.独り言が見える秒)
            )
        ) or '<p class="問い">いまは静かです。</p>'
        断り = 断りを見せる(断る訳)
        中身 = f"""{小さいのれん()}<a class="戻る" href="/">← はじめへ</a>
<h1>独り言</h1><p class="問い">誰にも返されません。名乗りも出ません。24時間で消えます。</p>
{self._そっと(問い)}
<form method="post" action="/hitori/kaku">{断り}
<textarea name="honbun" maxlength="{決まり.本文の上限}" placeholder="ただ、吐き出す。">{html.escape(書きかけ)}</textarea>
<button class="送る" type="submit">つぶやく</button></form>
{独り言たち}"""
        self._返す(400 if 断る訳 else 200, 頁("独り言｜負け犬の癒し", 中身), 新しい鍵)

    def _その後を見せる(self, 見る人の鍵, 新しい鍵, 問い, 断る訳="", 書きかけ="", あの時の書きかけ=""):
        話たち = "".join(
            f"""<div class="書き込み" id="k{行["番号"]}">{見出しを見せる(行)}
{話を見せる(行)}{self._わかるを見せる(行, "沁みた", "沁みた", "沁みた、と言った人がいます")}</div>"""
            for 行 in self.台帳.板の書き込み(決まり.その後の置き場, 見る人の鍵)
        ) or '<p class="問い">まだ棚は空です。最初の1話をどうぞ。</p>'
        断り = 断りを見せる(断る訳)
        中身 = f"""{小さいのれん()}<a class="戻る" href="/">← はじめへ</a>
<h1>その後の話の棚</h1><p class="問い">つらかったあの時と、そのあとどうなったか。</p>
{self._そっと(問い)}
{self._いまの名乗り(見る人の鍵)}<form method="post" action="/sonogo/kaku">{断り}
<label for="ano">あの時（{決まり.あの時の上限}字まで）</label>
<input type="text" id="ano" name="ano" maxlength="{決まり.あの時の上限}" placeholder="例：受験に全部落ちた" value="{html.escape(あの時の書きかけ)}">
<label for="sonogo">その後</label>
<textarea id="sonogo" name="honbun" maxlength="{決まり.本文の上限}" placeholder="例：浪人はせず働いた。10年たって、今は…">{html.escape(書きかけ)}</textarea>
<button class="送る" type="submit">棚に置く</button></form>
{話たち}"""
        self._返す(400 if 断る訳 else 200, 頁("その後の話の棚｜負け犬の癒し", 中身), 新しい鍵)

    def _宣言を見せる(self, 見る人の鍵, 新しい鍵, 問い, 断る訳="", 書きかけ=""):
        """応援の言葉は求めない。押せるのは「見守る」だけ。宣言した本人だけが、あとで結びを付けられる。"""
        宣言たち = []
        for 行 in self.台帳.板の書き込み(決まり.宣言の置き場, 見る人の鍵):
            結び = ""
            if 行["結び"]:
                結び = f'<span class="結び">{html.escape(決まり.結びの言葉.get(行["結び"], ""))}</span>'
            elif 見る人の鍵 and 行["書いた人の鍵"] == 見る人の鍵:
                ボタン = "".join(
                    f'<button type="submit" name="musubi" value="{値}">{html.escape(言葉)}</button>' for 値, 言葉 in 決まり.結びの言葉.items()
                )
                結び = f'<form class="結ぶ" method="post" action="/musubu/{行["番号"]}"><span>あなたの宣言です。</span>{ボタン}</form>'
            宣言たち.append(
                f"""<div class="書き込み" id="k{行["番号"]}">{見出しを見せる(行)}
<p>もう一回、{本文を見せる(行["本文"])}</p>{結び}{self._わかるを見せる(行, "見守る", "見守ってる", "見守っている人がいます")}</div>"""
            )
        断り = 断りを見せる(断る訳)
        中身 = f"""{小さいのれん()}<a class="戻る" href="/">← はじめへ</a>
<h1>もう一回の宣言</h1><p class="問い">「もう一回やってみる」を1行で。<br>みんなは静かに見守るだけ。やめても、それでいい。</p>
{self._そっと(問い)}
{self._いまの名乗り(見る人の鍵)}<form method="post" action="/mouikkai/kaku">{断り}
<label for="sengen">もう一回、</label>
<input type="text" id="sengen" name="honbun" maxlength="{決まり.宣言の上限}" placeholder="例：来月、面接を受けてみる" value="{html.escape(書きかけ)}">
<button class="送る" type="submit">宣言する</button></form>
{"".join(宣言たち) or '<p class="問い">まだ宣言はありません。</p>'}"""
        self._返す(400 if 断る訳 else 200, 頁("もう一回の宣言｜負け犬の癒し", 中身), 新しい鍵)

    def _夜を見せる(self, 見る人の鍵, 新しい鍵, 問い, 断る訳="", 書きかけ=""):
        """開いている間は、今夜の書き込みだけを古い順に（話の流れどおり）。閉まっている間は何も見せない。"""
        始まり = 今夜の始まり()
        if not 始まり:
            中身 = f"""{小さいのれん()}<a class="戻る" href="/">← はじめへ</a>
<h1>夜の部屋</h1><p class="問い">いまは閉まっています。{決まり.夜の始まり時}時から朝{決まり.夜の終わり時}時まで開きます。<br>夜の話は、その夜だけのものです。</p>"""
            return self._返す(400 if 断る訳 else 200, 頁("夜の部屋｜負け犬の癒し", 中身 + 断りを見せる(断る訳)), 新しい鍵)
        話たち = "".join(
            f"""<div class="書き込み" id="k{行["番号"]}">{見出しを見せる(行)}
<p>{本文を見せる(行["本文"])}</p>{self._わかるを見せる(行)}</div>"""
            for 行 in reversed(self.台帳.板の書き込み(決まり.夜の置き場, 見る人の鍵, いつから=始まり))
        ) or '<p class="問い">まだ誰もいません。起きているのは、あなただけかも。</p>'
        中身 = f"""{小さいのれん()}<a class="戻る" href="/">← はじめへ</a>
<h1>夜の部屋</h1><p class="問い">朝{決まり.夜の終わり時}時に閉まり、今夜の話は見えなくなります。<a href="/yoru#yoru-kaku">新しい書き込みを見る</a></p>
{self._そっと(問い)}
{話たち}
{self._いまの名乗り(見る人の鍵)}<form id="yoru-kaku" method="post" action="/yoru/kaku">{断りを見せる(断る訳)}
<textarea name="honbun" maxlength="{決まり.本文の上限}" placeholder="眠れないね。">{html.escape(書きかけ)}</textarea>
<button class="送る" type="submit">話す</button></form>"""
        self._返す(400 if 断る訳 else 200, 頁("夜の部屋｜負け犬の癒し", 中身), 新しい鍵)

    def _書き始めて1日たったか(self, 鍵):
        最初 = self.台帳.最初に書いた時刻(鍵)
        return 最初 is not None and 時計.いま() - 最初 >= timedelta(seconds=決まり.小部屋を開けるまでの秒)

    def _相手と開けるか(self, 相手の鍵, 閉じた相手たち):
        return 相手の鍵 not in 閉じた相手たち and not self.台帳.小部屋を受けないか(相手の鍵)

    def _部屋を開けるか(self, 自分の鍵, 相手の鍵):
        """つきまといを防ぐ決まり：書き始めて1日たったブラウザからだけ。小部屋を受けない人とは開けない。
        一度部屋を閉じた2人は、名乗りを変えても開けない。名乗りの頁の「2人で話す」も同じ決まりで出す。"""
        return self._書き始めて1日たったか(自分の鍵) and self._相手と開けるか(相手の鍵, self.台帳.閉じた部屋の相手たち(自分の鍵))

    def _小部屋の一覧(self, 鍵, 新しい鍵):
        部屋たち = "".join(
            f"""<a class="場所へ" href="/heya/{部屋["番号"]}"><h2>小部屋#{部屋["番号"]}</h2><small>{
                "閉じられました" if 部屋["閉じた時刻"] else ("相手から話が来ています" if 部屋["最後の時刻"] and not 部屋["最後は自分"] else "")
            }</small></a>"""
            for 部屋 in self.台帳.自分の小部屋(鍵, 決まり.小部屋の頭)
        ) or '<p class="問い">まだ小部屋はありません。</p>'
        if self.台帳.小部屋を受けないか(鍵):
            受け方 = """<form method="post" action="/heya/ukeru"><p class="いまの名乗り">いまは小部屋を受けていません。ほかの人は、あなたと新しく部屋を開けません。
いまある部屋は、それぞれの部屋で閉じられます。 <button type="submit">小部屋を受ける</button></p></form>"""
        else:
            受け方 = """<form method="post" action="/heya/ukenai"><p class="いまの名乗り">知らない人から部屋を開かれたくない時は <button type="submit">小部屋を受けない</button></p></form>"""
        中身 = f"""{小さいのれん()}<a class="戻る" href="/">← はじめへ</a>
<h1>1対1の小部屋</h1><p class="問い">同じ名乗りの人と、匿名のまま2人で話す部屋。<br>
名乗りを押すと同じ名乗りの人たちが並び、「この人と2人で話す」から始められます（自分も同じ名乗りの時だけ）。<br>
書き始めて1日たってから開けます。一度閉じた相手とは、名乗りを変えても、もう開けません。</p>
{受け方}
{部屋たち}"""
        self._返す(200, 頁("1対1の小部屋｜負け犬の癒し", 中身), 新しい鍵)

    def _小部屋を見せる(self, 部屋番号, 鍵, 新しい鍵, 問い, 断る訳="", 書きかけ=""):
        """2人だけが入れる。ほかの人には部屋があることも見せない。"""
        部屋 = self.台帳.小部屋(部屋番号, 鍵)
        if not 部屋:
            return self._見つからない(新しい鍵)
        話たち = "".join(
            f"""<div class="書き込み" id="k{行["番号"]}"><span class="時刻"><span class="名乗り">{"あなた" if 行["書いた人の鍵"] == 鍵 else "相手"}</span>　{時刻を見せる(行["書いた時刻"])}</span>
<p>{本文を見せる(行["本文"])}</p><div class="知らせる段">{知らせる道(行["番号"])}</div></div>"""
            for 行 in reversed(self.台帳.板の書き込み(決まり.小部屋の置き場(部屋番号), 鍵))
        ) or '<p class="問い">まだ話はありません。最初のひとことをどうぞ。</p>'
        if 部屋["閉じた時刻"]:
            書く欄 = f'<p class="断り">この部屋は{"あなたが" if 部屋["閉じた人の鍵"] == 鍵 else "相手が"}閉じました。もう書けません。</p>'
        else:
            書く欄 = f"""<form id="heya-kaku" method="post" action="/heya/{部屋番号}/kaku">{断りを見せる(断る訳)}
<textarea name="honbun" maxlength="{決まり.本文の上限}" placeholder="ここは2人だけの部屋です。">{html.escape(書きかけ)}</textarea>
<button class="送る" type="submit">話す</button></form>
<form method="post" action="/heya/{部屋番号}/tojiru"><p class="いまの名乗り">嫌なことがあったら、いつでも閉じてください。 <button type="submit">この部屋を閉じる</button></p></form>"""
        中身 = f"""{小さいのれん()}<a class="戻る" href="/heya">← 小部屋の一覧</a>
<h1>小部屋#{部屋番号}</h1><p class="問い">2人だけの部屋です。ただし守りのため、持ち主が中を見ることがあります。<a href="/heya/{部屋番号}#heya-kaku">新しい話を見る</a></p>
{self._そっと(問い)}
{話たち}
{書く欄}"""
        self._返す(400 if 断る訳 else 200, 頁(f"小部屋#{部屋番号}｜負け犬の癒し", 中身), 新しい鍵)

    def _知らせる欄(self, 鍵, 新しい鍵, 問い, 断る訳="", 書きかけ=""):
        """持ち主へ知らせる。選んだ書き込みの中身はここに出さない（小部屋や消した書き込みの番号を当てても、中身が漏れないように）。"""
        読んだ番号 = 決まり.番号を読む(問い.get("bangou", ""))
        番号 = 読んだ番号 if 読んだ番号 is not None and self.台帳.書き込みの板(読んだ番号) else ""
        届いた = '<p class="届いた">持ち主に届きました。ありがとう。</p>' if 問い.get("okutta") == "1" else ""
        選んだ = (
            f'<p class="いまの名乗り">選んだ書き込み（#{番号}）について知らせます。理由は書かなくてもかまいません。</p>'
            f'<input type="hidden" name="bangou" value="{番号}">'
        ) if 番号 else ""
        中身 = f"""{小さいのれん()}<a class="戻る" href="/">← はじめへ</a>
<h1>持ち主へ知らせる</h1><p class="問い">読むのは持ち主だけです。名前も連絡先も聞きません。返事が要る時だけ、届け先（メールアドレスなど）を書き添えてください。<br>
まずい書き込みや、消してほしい書き込みがあれば、その書き込みの「知らせる」から送ってください。<br>
自分が書いたものなら、書いた時と同じブラウザから送ると、書いた本人からだと確かめられます。</p>
{届いた}{self._そっと(問い)}
<form method="post" action="/shiraseru">{断りを見せる(断る訳)}{選んだ}
<textarea name="honbun" maxlength="{決まり.本文の上限}" placeholder="例：この書き込みに、知っている人の名前が出ています">{html.escape(書きかけ)}</textarea>
<button class="送る" type="submit">知らせる</button></form>"""
        self._返す(400 if 断る訳 else 200, 頁("持ち主へ知らせる｜負け犬の癒し", 中身), 新しい鍵)

    def _見回りの知らせ(self, 名前):
        """知らせを新しい順に。書いた人と同じブラウザからの知らせか、そのブラウザで書いた書き込みの番号も出す（本人からの依頼かを確かめるため）。"""
        知らせたち = []
        for 行 in self.台帳.知らせたち():
            対象 = "持ち主への知らせ"
            if 行["書き込み番号"]:
                対象 = (f'<a href="#m{行["書き込み番号"]}">#{行["書き込み番号"]}（{html.escape(置き場を言う(行["板"], 名前))}）への知らせ</a>'
                        + ("　書いた人と同じブラウザから" if 行["本人から"] else "") + ("　消した書き込み" if 行["消した時刻"] else ""))
            書いたもの = self.台帳.書いた書き込みの番号(行["送った人の鍵"])
            知らせたち.append(
                f"""<div class="知らせ"><span class="時刻">知らせ#{行["番号"]}　{時刻を見せる(行["送った時刻"])}　{対象}</span>
<p>{本文を見せる(行["本文"]) if 行["本文"] else "（理由なし）"}</p>{f'<small>このブラウザで書いたもの：{"　".join(f"#{番号}" for 番号 in 書いたもの)}</small>' if 書いたもの else ""}</div>"""
            )
        return "".join(知らせたち) or '<p class="問い">知らせはまだありません。</p>'

    def _うまくいかなかった(self):
        """場の中で思わぬ誤りが起きた時の画面。記録には触らない。書いた字は捨てず、同じ場所へもう一度送れる形で見せる。
        見回りの動きは欄を戻さない（合言葉と合い札を画面に戻さないため）。"""
        道 = urlparse(self.path).path
        if self.command != "POST":
            文 = '<p>うまくいきませんでした。少し待ってから、開き直してください。</p><a href="/">はじめへ</a>'
        elif 道.startswith("/kanri"):
            文 = '<p>うまくいきませんでした。少し待ってから、見回りを開き直してください。</p><a href="/kanri">見回りへ</a>'
        else:
            隠す欄 = "".join(
                f'<input type="hidden" name="{html.escape(名)}" value="{html.escape(値)}">' for 名, 値 in self._送った中身.items() if 名 != "honbun")
            本文の欄 = f'<textarea name="honbun">{html.escape(self._送った中身["honbun"])}</textarea>' if "honbun" in self._送った中身 else ""
            文 = (f'<p>いま混み合っていて、置けませんでした。書いた字は下に残してあります。少し待ってから、もう一度送ってください。</p>'
                 f'<form method="post" action="{html.escape(道)}">{隠す欄}{本文の欄}<button class="送る" type="submit">もう一度送る</button></form><a href="/">はじめへ</a>')
        self._返す(503, 頁("うまくいきませんでした｜負け犬の癒し", 文), None, [("Cache-Control", "no-store")])

    def _見回りの入口(self, 新しい鍵, 断る訳="", 状態=200):
        """合言葉はこの欄から送る（ページの場所に載せない）。"""
        中身 = f"""<h1>見回り</h1>
<form method="post" action="/kanri/hairu">{断りを見せる(断る訳)}
<input type="password" name="aikotoba" autocomplete="current-password" aria-label="合言葉" placeholder="合言葉">
<button class="送る" type="submit">入る</button></form>"""
        self._返す(状態, 頁("見回り｜負け犬の癒し", 中身), 新しい鍵)

    def _見回り(self, 合い札, 新しい鍵):
        """持ち主だけが見る画面。消す・戻す・出るの欄には、札の合い札を入れる。"""
        名前 = 置き場の名前()
        合い札の欄 = f'<input type="hidden" name="aifuda" value="{合い札}">'
        行たち = []
        for 行 in self.台帳.新しい書き込み():
            消した = 行["消した時刻"] is not None
            動き = "modosu" if 消した else "kesu"
            行たち.append(
                f"""<div class="書き込み{' 消した' if 消した else ''}" id="m{行["番号"]}"><span class="時刻">#{行["番号"]}　{html.escape(置き場を言う(行["板"], 名前))}{f'　#{行["親番号"]}への返事' if 行["親番号"] else ''}　{html.escape(行["名乗り"] or "名無し")}　{時刻を見せる(行["書いた時刻"])}{'　消した' if 消した else ''}</span>
{話を見せる(行)}
<form method="post" action="/kanri/{動き}">{合い札の欄}<input type="hidden" name="bangou" value="{行["番号"]}">
<button type="submit">{'戻す' if 消した else '消す'}</button></form>{self._このブラウザへの道(行)}</div>"""
            )
        中身 = (
            f'<h1>見回り</h1><form method="post" action="/kanri/deru">{合い札の欄}<button type="submit">見回りを出る</button></form>'
            + '<p class="品書き">知らせ</p>' + self._見回りの知らせ(名前)
            + '<p class="品書き">書き込み</p><p class="問い">新しい順。消しても記録は残り、戻せます。</p>'
            + ("".join(行たち) or "<p>まだ書き込みはありません。</p>")
        )
        # 出た後に「戻る」で見回りの画面が出ないよう、ブラウザに残させない
        self._返す(200, 頁("見回り｜負け犬の癒し", 中身), 新しい鍵, [("Cache-Control", "no-store")])

    def _このブラウザへの道(self, 行):
        """同じブラウザで2件以上書いていれば、その一覧（まとめて消す・戻す）への道。ブラウザの乱数は画面に出さず、書き込みの番号で辿る。
        聞き役の返事はみな同じ鍵で置くので、聞き役の返事の一覧になる。"""
        if 行["同じブラウザの数"] < 2:
            return ""
        名前 = "聞き役の返事" if 行["名乗り"] == 決まり.聞き役の名乗り else "このブラウザの書き込み"
        return f'<small><a href="/kanri/matome?bangou={行["番号"]}">{名前}（{行["同じブラウザの数"]}件）</a></small>'

    def _このブラウザの書き込み(self, 番号, 書き込みたち, 合い札, 新しい鍵):
        """まとめて消す・戻す前に、何が消える（戻る）かを見せる。欄の「ここまで」は、いま見せている一番新しい番号。"""
        名前 = 置き場の名前()
        出ている = [行 for 行 in 書き込みたち if 行["消した時刻"] is None]
        消した = [行 for 行 in 書き込みたち if 行["消した時刻"] is not None]
        欄 = (f'<input type="hidden" name="aifuda" value="{合い札}"><input type="hidden" name="bangou" value="{番号}">'
             f'<input type="hidden" name="made" value="{max(行["番号"] for 行 in 書き込みたち)}">')

        def 並べる(行たち):
            return "".join(
                f'<div class="書き込み{" 消した" if 行["消した時刻"] else ""}"><span class="時刻">#{行["番号"]}　'
                f'{html.escape(置き場を言う(行["板"], 名前))}　{時刻を見せる(行["書いた時刻"])}</span><p>{html.escape(抜き出す(行["本文"]))}</p></div>'
                for 行 in 行たち) or '<p class="問い">ありません。</p>'
        if 書き込みたち[0]["名乗り"] == 決まり.聞き役の名乗り:
            題, 説明 = "聞き役の返事", f"「{決まり.聞き役の名乗り}」が置いた返事です。まとめて消すと、聞き役の返事がみな見えなくなります。"
        else:
            題, 説明 = "このブラウザの書き込み", f"#{番号} を書いたブラウザ（同じクッキー）の書き込みです。接続元（IPアドレス）では見分けていません。クッキーを消して書かれた物は入りません。"
        中身 = (
            f'<a class="戻る" href="/kanri#m{番号}">← 見回りへ</a><h1>{題}</h1>'
            f'<p class="問い">{説明}</p>'
            f'<p class="品書き">出ている（{len(出ている)}件）</p>' + 並べる(出ている)
            + (f'<form method="post" action="/kanri/matomete-kesu">{欄}<button class="送る" type="submit">出ている{len(出ている)}件をまとめて消す</button></form>' if 出ている else "")
            + f'<p class="品書き">消した（{len(消した)}件）</p>' + 並べる(消した)
            + (f'<form method="post" action="/kanri/matomete-modosu">{欄}<button type="submit">消した{len(消した)}件をまとめて戻す</button></form>' if 消した else "")
        )
        self._返す(200, 頁("見回り｜負け犬の癒し", 中身), 新しい鍵, [("Cache-Control", "no-store")])
