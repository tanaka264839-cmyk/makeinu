"""負け犬の癒し：絵（夜の屋台ののれん・赤ちょうちん・眠る犬）。手書きのSVGで、外から何も読み込まない。

見た目の案B「夜の屋台」（本人 2026-10-24 選択）。元の下書きは 見た目の案/作る.py。
線と形は「手」のゆらぎを通して描く。定規で引いたような真っすぐさと、揃いすぎた並びは作り物に見えるため。
"""

線の色 = "#e6d6b8"

題 = "負け犬の癒し"
明朝 = "'Yu Mincho','YuMincho','Hiragino Mincho ProN','Noto Serif JP','BIZ UDMincho',serif"

# のれん1枚ごとの丈。字はまっすぐ真ん中に置き、揺れは布の裾だけで出す（字まで揺らすと、わざとらしい）
のれんの丈 = [2, -3, 4, -1, 3, 0]
のれんの幅 = [57, 54, 58, 55, 56, 53]


def ゆらぎ(名前, 強さ):
    """線を手で引いたように少し揺らす。feTurbulence の種は固定なので、毎回同じ揺れになる。"""
    return (f'<filter id="{名前}" x="-5%" y="-5%" width="110%" height="110%">'
            f'<feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="2" seed="7"/>'
            f'<feDisplacementMap in="SourceGraphic" scale="{強さ}"/></filter>')


def 犬(x, y, 大きさ=1.0):
    """前足にあごをのせて眠る犬を、塗りでなく線で描く。左が鼻先。左下が (x, y)、幅およそ 120×大きさ。"""
    return f"""<g transform="translate({x} {y}) scale({大きさ})" fill="#283057" stroke="{線の色}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
<path d="M104 46C116 44 120 32 112 26" fill="none" stroke-width="2.3"/>
<path d="M38 62C30 42 50 26 76 28C100 30 114 44 110 62Z" stroke-dasharray="120 3 60 2 400"/>
<path d="M8 62C8 57 20 55 34 57C38 59 38 62 34 63H10Z"/>
<path d="M9 50C6 40 16 30 30 31C42 32 48 42 45 52C43 58 34 60 24 59C17 59 11 56 9 50Z"/>
<path d="M10 49C3 49 0 53 3 56C6 59 14 58 18 56" />
<ellipse cx="2.6" cy="52.5" rx="2.4" ry="2" fill="{線の色}" stroke="none"/>
<path d="M26 32C36 29 42 38 39 50C34 47 29 41 26 32Z" stroke-width="1.2"/>
<path d="M16 44q3 2.2 6 0" fill="none" stroke-width="2.2"/>
</g>"""


def _のれん(上, 高さ, 字の大きさ):
    布 = []
    for i, (丈, 幅) in enumerate(zip(のれんの丈, のれんの幅)):
        x, h, 半 = 16 + i * 60, 高さ + 丈, 幅 / 2
        布.append(f"""<g><path d="M{x} {上}h{幅}v{h}q-{半 + 1} 5-{半} 1q-{半 - 1}-5-{半} 0z" fill="#25366a"/>
<path d="M{x + 3} {上 + h - 3}q12-3 25 0" stroke="#1b2850" stroke-width="1.5" fill="none" opacity=".7"/>
<text x="{x + 半:.0f}" y="{上 + 高さ * 0.62:.0f}" text-anchor="middle" font-size="{字の大きさ}" font-family="{明朝}" font-weight="700" fill="#efe4cc">{題[i]}</text></g>""")
    return "".join(布)


def 屋台の絵():
    """はじめの画面の一番上。のれんに題、赤ちょうちんに「おつかれ」、カウンターで犬が眠っている。"""
    # 広い画面では、竿とカウンターの色を左右の端まで延ばす（絵だけが真ん中の箱に見えないように）
    return f"""<div class="屋台の帯"><svg class="屋台" viewBox="0 0 390 230" role="img" aria-label="夜の屋台。のれんに{題}、赤ちょうちんの下で犬が眠っている">
<defs>{ゆらぎ("手", 3)}{ゆらぎ("手弱", 1.6)}
<radialGradient id="灯" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#ffb85c" stop-opacity=".42"/><stop offset=".6" stop-color="#ffb85c" stop-opacity=".1"/><stop offset="1" stop-color="#ffb85c" stop-opacity="0"/></radialGradient></defs>
<rect width="390" height="230" fill="#1c2242"/>
<g fill="#efe6d0"><circle cx="150" cy="104" r="1.1" opacity=".7"/><circle cx="262" cy="98" r=".9" opacity=".5"/><circle cx="352" cy="112" r="1.2" opacity=".6"/></g>
<circle cx="70" cy="150" r="84" fill="url(#灯)"/>
<g filter="url(#手弱)"><path d="M-4 11.5C120 9 270 13 394 10.5" stroke="#6e4a2e" stroke-width="7" stroke-linecap="round"/>{_のれん(13, 72, 30)}</g>
<g filter="url(#手)">
<path d="M68 88v18" stroke="#2a1d14" stroke-width="2"/><path d="M56 104h24v7H56z" fill="#2a1d14"/>
<path d="M68 111C40 112 38 150 44 166C50 184 86 184 92 166C98 150 96 112 68 111Z" fill="#c4452f"/>
<g fill="none" stroke="#8f2f22" stroke-width="1.4" opacity=".7"><path d="M43 126q25 6 50 0"/><path d="M41 140q27 6 54 0"/><path d="M41 154q27 6 54 0"/><path d="M44 168q24 6 47 0"/></g>
<path d="M57 179h24v7H57z" fill="#2a1d14"/>
<path d="M-4 199C100 196 280 201 394 197V230H-4z" fill="#9a6e45"/><path d="M-4 197C120 194 260 199 394 195" stroke="#c09062" stroke-width="5"/>
{犬(198, 134, 1.0)}
<path d="M330 174h23l-2.6 20c-.3 1.8-1.4 2.6-3 2.6h-11.6c-1.6 0-2.7-.8-3-2.6z" fill="#283057" stroke="{線の色}" stroke-width="1.3" stroke-linejoin="round" stroke-dasharray="40 2 200"/>
</g>
<text x="68" y="144" font-size="12" text-anchor="middle" writing-mode="vertical-rl" font-family="{明朝}" font-weight="700" fill="#fbefdc" letter-spacing="1" transform="rotate(-2 68 151)">おつかれ</text>
<path d="M336 166c-3-4 3-6 0-11M346 166c-3-4 3-6 0-11" fill="none" stroke="#dcd8ea" stroke-width="1.8" stroke-linecap="round" opacity=".55"/>
</svg></div>"""


def 小さいのれん():
    """はじめ以外の画面の一番上。押すと、はじめの画面へ戻る。"""
    return f"""<a class="小のれん" href="/" aria-label="{題}（はじめの画面へ）"><svg viewBox="0 0 390 58" aria-hidden="true">
<defs>{ゆらぎ("手弱", 1.6)}</defs><g filter="url(#手弱)"><path d="M-4 5C120 3 270 6 394 4" stroke="#6e4a2e" stroke-width="6" stroke-linecap="round"/>{_のれん(6, 44, 21)}</g></svg></a>"""
