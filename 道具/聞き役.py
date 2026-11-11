"""負け犬の癒し：AIの聞き役（案9）。人の返事が無いまま10分たった板の書き込みに、AIが一度だけ短く返す。

場（場.py）とは別に、決まった時刻に動かす（サーバーでは makeinu-kikiyaku.timer で2分ごと）。AIが止まっても場は止めない。
いつ・どこに・何回返すかは普通のプログラムで決め、AIは返す文を書くだけ（設計の型6）。
AIを呼ぶのは さくらに尋ねる の1か所だけ（設計の型5。入れ替わりの速い部品は取り替えられる形でつなぐ）。
AIに送るのは頼みの文と書き込みの本文だけ。名乗り・接続元の番号・ブラウザの乱数は送らない。
返ってきた文も人の書き込みと同じ守りを通し、かかれば出さない（設計の型7。AIは失敗する前提で組む）。

動かし方：環境変数 MAKEINU_SAKURA_AI_TOKEN にさくらのAI Engine の負け犬だけの鍵（名前 makeinu）を入れて python3 聞き役.py <台帳の場所>
"""
import json
import os
import sys
import urllib.error
import urllib.request
from collections import Counter
from datetime import timedelta

import 決まり
import 時計
from 台帳 import 台帳

窓口 = "https://api.ai.sakura.ad.jp/v1/chat/completions"
モデル = "gpt-oss-120b"
鍵の名前 = "MAKEINU_SAKURA_AI_TOKEN"  # 鍵は件ごとに分ける。家計簿の件の鍵（SAKURA_AI_TOKEN）があっても読まない
返事を待つ秒 = 60  # AIの返事が来なければ、その書き込みは次の回にやり直す


def さくらに尋ねる(本文, 鍵, 頼み):
    """書き込みの本文に返す文を、さくらのAI Engine に1つ書いてもらう。うまくいかなければ例外を投げる。
    返す文は決まった形（{"henji": 文}）で受け取る（前置きや説明を付けさせないため）。"""
    中身 = {
        "model": モデル,
        "messages": [{"role": "system", "content": 頼み}, {"role": "user", "content": 本文}],
        "response_format": {"type": "json_schema", "json_schema": {"name": "henji", "strict": True, "schema": {
            "type": "object", "properties": {"henji": {"type": "string"}}, "required": ["henji"], "additionalProperties": False}}},
        "max_tokens": 1500,  # 考える分も含む。返す文は120字くらい
    }
    頼み先 = urllib.request.Request(
        窓口, json.dumps(中身).encode("utf-8"), {"Authorization": f"Bearer {鍵}", "Content-Type": "application/json"})
    with urllib.request.urlopen(頼み先, timeout=返事を待つ秒) as 返り:
        答え = json.load(返り)
    return json.loads(答え["choices"][0]["message"]["content"])["henji"]


def _返事を整える(返事):
    """AIは改行を「\\n」の字のまま返すことがあるので、改行に直してから、書き込みと同じ形に整える。"""
    return 決まり.本文を整える(str(返事).replace("\\n", "\n"))


def _失敗の名前(誤り):
    """記録に残す失敗の種類（中身は残さない）。"""
    return type(誤り).__name__ + (f" {誤り.code}" if isinstance(誤り, urllib.error.HTTPError) else "")


def ひと回り(帳, 尋ねる):
    """返す時が来た書き込みに、1回分だけ返す。尋ねる(本文) は返す文を返す（うまくいかなければ例外を投げる）。
    結果ごとの数を返す（本文は返さない）。"""
    いま = 時計.いま()
    数 = Counter()
    待つ = 帳.聞き役を待つ書き込み(
        [板.鍵 for 板 in 決まり.板の一覧を読む()], いま - timedelta(seconds=決まり.聞き役が待つ秒),
        いま - timedelta(seconds=決まり.聞き役が返す期限の秒), 決まり.聞き役が試す回数, 決まり.聞き役の1回の数)
    for 行 in 待つ:
        if 決まり.見立てる(行["本文"]).相談先を出す:
            # つらすぎる言葉には返さず、AIにも送らない（書いた本人には相談先が出ている）
            帳.聞き役の記録をつける(行["番号"], "見送った")
            数["見送った"] += 1
            continue
        if 行["試した回数"] == 0 and 帳.聞き役が尋ねた数(いま - timedelta(days=1)) >= 決まり.聞き役の1日の上限:
            数["上限"] += 1  # 新しい書き込みは尋ねない。やり直しの書き込みは数に入っているので続ける
            continue
        try:
            返事 = _返事を整える(尋ねる(行["本文"]))
        except Exception as 誤り:
            帳.聞き役の記録をつける(行["番号"], "失敗")
            数[f"失敗（{_失敗の名前(誤り)}）"] += 1
            continue
        if not 決まり.聞き役の返事を出せるか(返事):
            帳.聞き役の記録をつける(行["番号"], "止めた")
            数["止めた"] += 1
            continue
        返事の番号 = 帳.聞き役が返す(行["番号"], 行["板"], 返事)
        結果 = "返した" if 返事の番号 else "置かなかった"
        帳.聞き役の記録をつける(行["番号"], 結果, 返事の番号)
        数[結果] += 1
    return 数


def 動かす(台帳の場所):
    鍵 = os.environ.get(鍵の名前, "").strip()
    if not 鍵:
        print(f"聞き役：{鍵の名前} にさくらのAI Engine の鍵が無いので、尋ねずに止めます。", file=sys.stderr)
        return 1
    頼み = 決まり.聞き役への頼みを読む()
    数 = ひと回り(台帳(台帳の場所), lambda 本文: さくらに尋ねる(本文, 鍵, 頼み))
    if 数:  # 何もしなかった回は何も残さない（2分ごとに動くため）
        print("聞き役：" + "・".join(f"{名前}{件数}" for 名前, 件数 in 数.items()))
    return 0


if __name__ == "__main__":
    sys.exit(動かす(sys.argv[1]))
