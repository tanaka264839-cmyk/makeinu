"""負け犬の癒し：見た目（色・並び）と、どの画面でも同じ小さな部品。"""
import html
import re
from datetime import datetime
from urllib.parse import quote

import 決まり
import 時計


def 時刻を見せる(iso):
    return datetime.fromisoformat(iso).astimezone(時計.日本時間).strftime("%m/%d %H:%M")


def 本文を見せる(本文):
    return html.escape(本文).replace("\n", "<br>")


def 断りを見せる(断る訳):
    return f'<div class="断り">{html.escape(断る訳)}</div>' if 断る訳 else ""


def 話を見せる(行):
    """その後の話の棚の1話は「あの時」と「その後」。ほかの書き込みは本文だけ。"""
    if not 行["あの時"]:
        return f'<p>{本文を見せる(行["本文"])}</p>'
    return f"""<p class="あの時"><span>あの時</span>{本文を見せる(行["あの時"])}</p>
<p class="その後"><span>その後</span>{本文を見せる(行["本文"])}</p>"""


def _道にする(行):
    """[文字](/道) を、この場の中への道にする。外への道（http や // で始まるもの）は文字のまま。来た人を外へ連れ出さない。"""
    return re.sub(r"\[([^\]]+)\]\((/(?!/)[^)\s]*)\)", r'<a href="\2">\1</a>', html.escape(行))


def 中身を見せる(文, 置き換え=None):
    """中身/ の文（利用の決まり・個人情報の扱い）を画面の形にする。■＝見出し、▼＝小見出し、・＝箇条、
    置き換えの印だけの行（{相談先} など）＝渡された部品。# で始まる行はメモとして出さない。"""
    置き換え = 置き換え or {}
    出す, 箇条 = [], False
    for 行 in 文.splitlines():
        行 = 行.strip()
        if 行.startswith("#"):
            continue
        if 箇条 and not 行.startswith("・"):
            出す.append("</ul>")
            箇条 = False
        if not 行:
            continue
        if 行 in 置き換え:
            出す.append(置き換え[行])
        elif 行.startswith("■"):
            出す.append(f"<h2>{_道にする(行[1:].strip())}</h2>")
        elif 行.startswith("▼"):
            出す.append(f"<h3>{_道にする(行[1:].strip())}</h3>")
        elif 行.startswith("・"):
            if not 箇条:
                出す.append("<ul>")
                箇条 = True
            出す.append(f"<li>{_道にする(行[1:].strip())}</li>")
        else:
            出す.append(f"<p>{_道にする(行)}</p>")
    if 箇条:
        出す.append("</ul>")
    return "".join(出す)


def 知らせる道(番号):
    """持ち主へ知らせる入口。どの書き込みにも、行の右の端に小さく置く。"""
    return f'<a class="知らせる" href="/shiraseru?bangou={番号}">知らせる</a>'


def 見出しを見せる(行):
    """名乗りと時刻。名乗りを押すと、同じ名乗りの人の書き込みが見られる。
    聞き役（AI）の名乗りには道を付けない（人は使えない名乗りで、聞き役の返事を1か所に集めて見せないため）。"""
    名乗り = 行["名乗り"]
    if 名乗り == 決まり.聞き役の名乗り:
        誰 = f'<span class="名乗り 聞き役">{html.escape(名乗り)}</span>'
    elif 名乗り:
        誰 = f'<a class="名乗り" href="/nanori?n={quote(名乗り)}">{html.escape(名乗り)}</a>'
    else:
        誰 = '<span class="名乗り">名無し</span>'
    return f'<span class="時刻">{誰}　{時刻を見せる(行["書いた時刻"])}</span>'


# 夜の屋台。角丸のカード・丸い押しボタン・線の印を並べた画面は、作り物に見える。
# 板は掛けた木札、ほかの場所は品書き、書き込みは掲示板の行で見せる
見た目 = """
:root{--地:#1c2242;--紙:#232a4e;--深:#151a33;--字:#ece3cf;--薄字:#aaa6bf;--線:#3a4370;--灯:#f2b45e;--赤:#b93d29;--木:#e6cf9f;--木の線:#a67c45;--墨:#33231a;--そっと:#22332f;
--明朝:"Yu Mincho","YuMincho","Hiragino Mincho ProN","Noto Serif JP","BIZ UDMincho",serif;
--ざらつき:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0 0 0 .05 0'/%3E%3C/filter%3E%3Crect width='160' height='160' filter='url(%23n)'/%3E%3C/svg%3E")}
*{box-sizing:border-box}
html{background:#12152d;overflow-x:clip}
body{margin:0;min-height:100vh;background:var(--ざらつき),linear-gradient(#1f2546,#12152d 100vh) no-repeat #12152d;color:var(--字);font-family:"BIZ UDPGothic","Hiragino Sans","Yu Gothic",sans-serif;line-height:1.85;counter-reset:行}
main{max-width:640px;margin:0 auto;padding:0 16px 64px}
a{color:var(--灯);text-underline-offset:3px;text-decoration-thickness:1px}
h1{font-family:var(--明朝);font-weight:700;font-size:1.45rem;letter-spacing:.08em;margin:6px 0 0}
h2{font-size:1.05rem;margin:0}
.読み上げ{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.屋台の帯{width:100vw;margin-left:calc(50% - 50vw);background:linear-gradient(#1c2242 0,#1c2242 3.6%,#6e4a2e 3.6%,#6e4a2e 6.4%,#1c2242 6.4%,#1c2242 85%,#c09062 85%,#c09062 87%,#9a6e45 87%)}
.屋台{display:block;width:100%;max-width:640px;margin:0 auto;height:auto}
.小のれん{display:block;width:100vw;margin-left:calc(50% - 50vw);background:linear-gradient(#6e4a2e,#6e4a2e) 0 2px/100% 6px no-repeat}
.小のれん svg{display:block;width:100%;max-width:390px;height:auto;margin:0 auto}
.掛け軸{display:flex;flex-direction:row-reverse;justify-content:flex-end;gap:18px;align-items:flex-start;margin:22px 0 2px}
.禅語{writing-mode:vertical-rl;font-family:var(--明朝);font-size:1.32rem;font-weight:700;letter-spacing:.2em;line-height:1.7;margin:0;padding:0 0 0 14px;border-left:1px solid var(--線)}
.問い{color:var(--薄字);margin:4px 0 20px;font-size:.95rem}
.掛け軸 .問い{margin:2px 0 0;line-height:1.95}
.板たち{display:grid;grid-template-columns:repeat(6,1fr);gap:7px;align-items:start;padding:20px 2px 6px;position:relative;margin:4px 0 40px}
.板たち::before{content:"";position:absolute;left:-6px;right:-6px;top:7px;height:4px;border-radius:2px;background:#6e4a2e;transform:rotate(-.4deg)}
.板{position:relative;display:flex;flex-direction:column;align-items:center;padding:16px 0 10px;min-height:138px;border-radius:2px 2px 3px 3px;text-decoration:none;
background:linear-gradient(90deg,rgba(0,0,0,.06),transparent 30%,rgba(255,255,255,.08) 55%,rgba(0,0,0,.05)),var(--木);border:1px solid var(--木の線);color:var(--墨);box-shadow:2px 4px 6px rgba(0,0,0,.35);transform-origin:50% 0}
.板::before{content:"";position:absolute;top:-13px;left:50%;width:1px;height:13px;background:#8a6a48}
.板:nth-child(1){transform:rotate(-1.8deg);min-height:118px;margin-top:2px}.板:nth-child(2){transform:rotate(1.1deg);min-height:128px}
.板:nth-child(3){transform:rotate(-.4deg);min-height:110px;margin-top:5px}.板:nth-child(4){transform:rotate(2deg);min-height:122px}
.板:nth-child(5){transform:rotate(-1.2deg);min-height:136px;margin-top:1px}.板:nth-child(6){transform:rotate(.6deg);min-height:114px;margin-top:4px}
.板 h2{writing-mode:vertical-rl;font-family:var(--明朝);font-weight:700;font-size:1.16rem;letter-spacing:.14em}
.板 small{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.品書き{font-family:var(--明朝);font-weight:700;letter-spacing:.3em;color:var(--薄字);font-size:.9rem;margin:0 0 2px}
.場所へ{display:block;padding:9px 2px;text-decoration:none;color:var(--字)}
.場所へ b{font-family:var(--明朝);font-size:1.06rem;letter-spacing:.04em;margin-right:.7em}
.場所へ small{color:var(--薄字);font-size:.82rem;line-height:1.7}
.場所へ:nth-of-type(2n){padding-left:1.2em}.場所へ:nth-of-type(3n){padding-top:14px}
.夜へ b{color:#d9d3f5}
.独り言へ b{font-weight:normal;color:var(--薄字)}
.いまの話{display:block;padding:7px 2px;color:var(--字);text-decoration:none;font-size:.92rem;line-height:1.7;overflow-wrap:anywhere}
.いまの話 span{display:block;color:var(--薄字);font-size:.78rem}
.いまの話たち{margin:-10px 0 30px}
.戻る{display:inline-block;margin:4px 0 2px;font-size:.88rem;font-family:var(--明朝);text-decoration:none;color:var(--薄字);letter-spacing:.06em}
.書き込み{padding:12px 2px 10px;border-bottom:1px dotted var(--線);margin:0}
.書き込み::before{counter-increment:行;content:counter(行);font-family:var(--明朝);color:var(--灯);font-weight:700;margin-right:8px}
.書き込み .時刻{color:var(--薄字);font-size:.82rem}
.書き込み p{margin:4px 0 8px;overflow-wrap:anywhere}
.わかる{display:flex;align-items:center;gap:10px;flex-wrap:wrap;font-size:.84rem;color:var(--薄字)}
button{font:inherit;font-size:.86rem;border:none;background:transparent;color:var(--灯);padding:2px 0;cursor:pointer}
.わかる button::before{content:"○";margin-right:3px;font-size:.8em}.わかる button[disabled]::before{content:"●"}
button[disabled]{opacity:.55;cursor:default}
textarea,input[type=text],input[type=password]{width:100%;font:inherit;line-height:1.9;padding:0 12px;border:none;border-radius:1px;color:#2b1e15;box-shadow:1px 2px 4px rgba(0,0,0,.4);
background:repeating-linear-gradient(transparent 0,transparent calc(1.9em - 1px),#b5a588 calc(1.9em - 1px),#b5a588 1.9em) 0 .5em/100% 1.9em local,#d3c7ab}
textarea{min-height:120px}
::placeholder{color:#7a6a55}
input[type=text],input[type=password]{background:#d3c7ab;padding:.25em 12px}
textarea{padding-top:.5em;padding-bottom:.5em}
.わかる .送る::before{content:none}
.送る{margin-top:10px;background:#e6d9bc;color:#2b1e15;padding:6px 20px;font-size:.95rem;letter-spacing:.12em;border-radius:2px;text-decoration:none;transform:rotate(-.6deg);box-shadow:1px 2px 3px rgba(0,0,0,.35)}
.断り{border-left:2px solid var(--灯);padding:6px 12px;margin:12px 0;color:#f3dcb4}
.そっと{border-top:1px dotted #7d8aa8;border-bottom:1px dotted #7d8aa8;padding:12px 2px;margin:16px 0}
.そっと ul{margin:6px 0;padding-left:1.2em}
.番号{white-space:nowrap;font-weight:bold}
.独り言 p{margin:4px 0 0}
.残り{color:var(--薄字);font-size:.82rem}
.あの時{color:var(--薄字)}
.結び{display:inline-block;margin:0 0 8px;padding:0 10px;border:1px solid var(--線);font-size:.85rem}
.結ぶ{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px;font-size:.85rem;color:var(--薄字)}
.その後{font-weight:bold}
.あの時 span,.その後 span{display:block;font-size:.78rem;font-weight:normal;color:var(--灯)}
label{display:block;font-size:.9rem;color:var(--薄字);margin-top:8px}
.名乗り{font-weight:bold;margin-right:2px}
a.名乗り{text-decoration:none}
.聞き役{font-weight:normal;color:var(--薄字)}
.名乗りの欄{border-top:1px solid var(--線);padding:16px 2px 0;margin:44px 0 20px}
.名乗りの欄 b{font-family:var(--明朝)}
.名乗りの欄 small{color:var(--薄字)}
.名乗りの欄 input{margin-top:8px}
.いまの名乗り{color:var(--薄字);font-size:.88rem;margin:0 0 6px}
.消した{opacity:.5}
.返事たち{margin:6px 0 0 4px;padding-left:12px;border-left:1px solid #5a4636}
.返事{margin:0 0 8px}
.返事 p{margin:2px 0}
details summary{cursor:pointer;color:var(--薄字);font-size:.84rem;margin-top:6px}
details textarea{min-height:72px;margin-top:6px}
.知らせる{margin-left:auto;font-size:.76rem;color:var(--薄字);text-decoration:none;letter-spacing:.04em}
.知らせる段{display:flex;margin-top:2px}
.下の道{margin:30px 0 0;font-size:.84rem;line-height:2.2}
.下の道 a{color:var(--薄字);margin-right:1.2em;white-space:nowrap}
.文 h2{font-family:var(--明朝);font-size:1.08rem;margin:26px 0 6px}
.文 h3{font-size:.96rem;margin:16px 0 2px}
.文 p{margin:6px 0;overflow-wrap:anywhere}
.文 ul{margin:4px 0;padding-left:1.2em}
.文 li{margin:3px 0;overflow-wrap:anywhere}
.届いた{color:var(--灯);margin:12px 0}
.知らせ{padding:10px 2px;border-bottom:1px dotted var(--線)}
.知らせ .時刻{color:var(--薄字);font-size:.82rem}
.知らせ p{margin:4px 0;overflow-wrap:anywhere}
.知らせ small{color:var(--薄字)}
"""


def 頁(題, 中身, 説明=None):
    """説明は検索結果に出る文。検索に出す画面（はじめの画面）だけが渡す。"""
    説明の行 = f'\n<meta name="description" content="{html.escape(説明)}">' if 説明 else ""
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">{説明の行}
<title>{html.escape(題)}</title><style>{見た目}</style></head>
<body><main>{中身}</main></body></html>"""
