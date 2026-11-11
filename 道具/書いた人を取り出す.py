"""負け犬の癒し：書いた人の記録を、書き込み番号から取り出す。使うのは、法律にもとづいて正式に求められた時
（裁判所の命令・警察などからの照会）と、命の危険が差し迫っていると持ち主が見て警察に相談する時だけ。

動かし方（サーバーで）：sudo -u makeinu python3 /srv/makeinu/道具/書いた人を取り出す.py /srv/makeinu/記録/場.db 書き込み番号
開示の求めに出す項目（IPアドレス・タイムスタンプ・発信元ポート番号・投稿時接続先IPアドレス）の順に出す。
投稿時接続先IPアドレスは、このサーバーの番地（決定メモ「書いた人の記録」）。
"""
import os
import sys
from datetime import datetime, timezone

import 時計
from 台帳 import 台帳


def 書き出す(台帳の場所, 書き込み番号):
    """見つかれば 0、記録が無ければ 1 を返す。"""
    帳 = 台帳(台帳の場所)
    try:
        行 = 帳.書いた人の記録を取り出す(書き込み番号)
    finally:
        帳.閉じる()
    if not 行:
        print(f"書き込み番号 {書き込み番号} の書いた人の記録はありません（半年を過ぎて消えたか、記録を始める前の書き込みです）。")
        return 1
    時刻 = datetime.fromisoformat(行["書いた時刻"])
    print(f"書き込み番号：{行['書き込み番号']}（置き場 {行['板']}）" + ("・消した書き込み" if 行["消した時刻"] else ""))
    print(f"タイムスタンプ：{時刻.astimezone(時計.日本時間):%Y-%m-%d %H:%M:%S}（日本時間）／{時刻.astimezone(timezone.utc):%Y-%m-%d %H:%M:%S}（協定世界時）")
    print(f"IPアドレス：{行['番地']}")
    print(f"発信元ポート番号：{行['港'] if 行['港'] else '記録なし'}")
    print("投稿時接続先IPアドレス：このサーバーの番地（決定メモ「書いた人の記録」）")
    if 行["あの時"]:
        print(f"あの時：{行['あの時']}")
    print(f"本文：{行['本文']}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3 or not sys.argv[2].isdigit():
        print("使い方：python3 書いた人を取り出す.py 台帳の場所 書き込み番号")
        sys.exit(2)
    if not os.path.exists(sys.argv[1]):
        print(f"台帳が見つかりません：{sys.argv[1]}")  # 打ち違えた場所に、空の台帳を作らないため
        sys.exit(2)
    sys.exit(書き出す(sys.argv[1], int(sys.argv[2])))
