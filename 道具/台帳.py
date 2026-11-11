"""負け犬の癒し：書き込みと「わかる」の台帳（SQLite）。

消すときは行を消さず「消した印」を付ける。戻せるようにし、何を消したかも残す。
返事も書き込みの1行として持つ（親番号つき）。守り・連投・消すを書き込みと同じ決まりで扱うため。
名乗りは書いた時のものを書き込みに写して残す。後で名乗りを変えても、前の書き込みは書いた時のまま。
同時に来た人ごとに、別のつなぎで読み書きする。1つのつなぎを分け合うと、ある人の「確かめてから書く」の途中に
ほかの人の書き込みが混ざるため。待たされた書き込みは、捨てずに少し待ってから書く。
書いた人の記録（接続元の番地と港と時刻）は、書き込みと同じ動きの中で別の台に残す（書き込みだけ置かれて記録が欠けないように）。
どの画面も読まない。控えには入れず、半年を過ぎたら消す。取り出すのは、法律にもとづいて正式に求められた時と、
命の危険が差し迫っていると持ち主が見て警察に相談する時だけ。
聞き役（AI）の返事も書き込みの1行（聞き役の鍵・聞き役の名乗り）。どの書き込みに尋ねて、どうなったかは聞き役の記録に残す（本文は持たない）。
"""
import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import 決まり
import 時計

# わかるは数を返さず「誰かが押したか」「自分が押したか」だけ（数で比べない場）。? は見る人の鍵
_わかるの印 = """EXISTS (SELECT 1 FROM わかる WHERE 書き込み番号 = 書き込み.番号) AS 誰かがわかる,
       EXISTS (SELECT 1 FROM わかる WHERE 書き込み番号 = 書き込み.番号 AND 押した人の鍵 = ?) AS 自分がわかる"""

# 人の返事がまだ無い（書いた本人の書き足しと、消された返事は数えない）。書き込みを「元」と呼んで使う
_人の返事が無い = """NOT EXISTS (SELECT 1 FROM 書き込み AS 返 WHERE 返.親番号 = 元.番号 AND 返.消した時刻 IS NULL
       AND 返.書いた人の鍵 != 元.書いた人の鍵)"""


class 台帳:
    待つ秒 = 10

    def __init__(self, 場所):
        self.場所 = 場所
        self._人ごと = threading.local()
        # 書きながら読めるようにする（記録の中に残る設定なので、最初の1回でよい）
        self.つなぎ.execute("PRAGMA journal_mode=WAL")
        self.つなぎ.executescript(
            """
            CREATE TABLE IF NOT EXISTS 書き込み (
                番号 INTEGER PRIMARY KEY AUTOINCREMENT,
                板 TEXT NOT NULL,
                本文 TEXT NOT NULL,
                書いた人の鍵 TEXT NOT NULL,
                書いた時刻 TEXT NOT NULL,
                消した時刻 TEXT
            );
            CREATE INDEX IF NOT EXISTS 板ごと ON 書き込み (板, 番号);
            CREATE TABLE IF NOT EXISTS 名乗り (
                鍵 TEXT PRIMARY KEY,
                名乗り TEXT NOT NULL,
                変えた時刻 TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS 小部屋 (
                番号 INTEGER PRIMARY KEY AUTOINCREMENT,
                名乗りの形 TEXT NOT NULL,
                鍵1 TEXT NOT NULL,
                鍵2 TEXT NOT NULL,
                作った時刻 TEXT NOT NULL,
                閉じた時刻 TEXT,
                閉じた人の鍵 TEXT,
                UNIQUE (名乗りの形, 鍵1, 鍵2)
            );
            CREATE TABLE IF NOT EXISTS わかる (
                書き込み番号 INTEGER NOT NULL,
                押した人の鍵 TEXT NOT NULL,
                押した時刻 TEXT NOT NULL,
                PRIMARY KEY (書き込み番号, 押した人の鍵)
            );
            CREATE TABLE IF NOT EXISTS 書いた人の記録 (
                書き込み番号 INTEGER PRIMARY KEY,
                番地 TEXT NOT NULL,
                港 INTEGER,
                書いた時刻 TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS 書いた人の記録の時刻 ON 書いた人の記録 (書いた時刻);
            CREATE TABLE IF NOT EXISTS 小部屋を受けない (
                鍵 TEXT PRIMARY KEY,
                決めた時刻 TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS 知らせ (
                番号 INTEGER PRIMARY KEY AUTOINCREMENT,
                送った人の鍵 TEXT NOT NULL,
                書き込み番号 INTEGER,
                本文 TEXT NOT NULL,
                送った時刻 TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS 聞き役の記録 (
                書き込み番号 INTEGER PRIMARY KEY,
                結果 TEXT NOT NULL,
                試した回数 INTEGER NOT NULL,
                最初に試した時刻 TEXT NOT NULL,
                最後に試した時刻 TEXT NOT NULL,
                返事の番号 INTEGER
            );
            """
        )
        列 = [行[1] for 行 in self.つなぎ.execute("PRAGMA table_info(書き込み)")]
        # 前の版の記録に無い列を足す（名乗りの形＝同じ名乗りを探すための、そろえた形）
        for 名前, 型 in (("親番号", "INTEGER"), ("名乗り", "TEXT"), ("名乗りの形", "TEXT"), ("あの時", "TEXT"), ("結び", "TEXT")):
            if 名前 not in 列:
                self.つなぎ.execute(f"ALTER TABLE 書き込み ADD COLUMN {名前} {型}")
        self.つなぎ.execute("CREATE INDEX IF NOT EXISTS 返事ごと ON 書き込み (親番号, 番号)")
        self.つなぎ.execute("CREATE INDEX IF NOT EXISTS 名乗りごと ON 書き込み (名乗りの形, 番号)")
        self.つなぎ.execute("CREATE INDEX IF NOT EXISTS 書いた人ごと ON 書き込み (書いた人の鍵, 番号)")

    @property
    def つなぎ(self):
        """いま受けている人の分のつなぎ。無ければ開く。"""
        つなぎ = getattr(self._人ごと, "つなぎ", None)
        if つなぎ is None:
            つなぎ = sqlite3.connect(self.場所, timeout=self.待つ秒, isolation_level=None)
            つなぎ.row_factory = sqlite3.Row
            self._人ごと.つなぎ = つなぎ
        return つなぎ

    def 閉じる(self):
        つなぎ = getattr(self._人ごと, "つなぎ", None)
        if つなぎ is not None:
            つなぎ.close()
            self._人ごと.つなぎ = None

    @contextmanager
    def ひとりずつ(self):
        """この中の読み書きは、ほかの人の書き込みと混ざらない（確かめてから書く、を1つの動きにする）。"""
        self.つなぎ.execute("BEGIN IMMEDIATE")
        try:
            yield
        except BaseException:
            self.つなぎ.execute("ROLLBACK")
            raise
        self.つなぎ.execute("COMMIT")

    def 毎日の手入れ(self, 控えの場所):
        """半年を過ぎた書いた人の記録を消してから、その日の控えを作る（起動した時と、毎日0:05）。"""
        self.古い書いた人の記録を消す(決まり.書いた人の記録を残す日数)
        return self.控えを取る(控えの場所)

    def 控えを取る(self, 控えの場所):
        """その日の控えが無ければ1つ作る（毎日の控え）。書いている最中でも欠けない写し方で取る。
        控えには書いた人の記録を入れない。控えは消さずに溜まり、外へ持ち出すこともあるので、半年で消す決まりが守れなくなるため。
        作り終えてから控えの名前を付ける。作っている最中の写し（まだ書いた人の記録が残っている）を、控えとして外へ出さないため。"""
        os.makedirs(控えの場所, exist_ok=True)
        控え = os.path.join(控えの場所, 時計.いま().astimezone(時計.日本時間).strftime("%Y-%m-%d") + ".db")
        if not os.path.exists(控え) and os.path.exists(self.場所):
            書きかけ = 控え + ".書きかけ"
            self._書きかけを消す(書きかけ)  # 前に途中で止まった時の残り
            写し = sqlite3.connect(書きかけ)
            try:
                self.つなぎ.backup(写し)
                # 写した記録を消し、空いた所も詰め直して、ファイルの中に番地を残さない
                写し.execute("PRAGMA journal_mode=DELETE")
                写し.execute("DELETE FROM 書いた人の記録")
                写し.commit()
                写し.execute("VACUUM")
            except BaseException:
                写し.close()
                self._書きかけを消す(書きかけ)  # 書いた人の記録が残ったかもしれない写しは置かない
                raise
            写し.close()
            os.replace(書きかけ, 控え)
        return 控え

    @staticmethod
    def _書きかけを消す(書きかけ):
        for 場所 in (書きかけ, 書きかけ + "-journal", 書きかけ + "-wal", 書きかけ + "-shm"):
            if os.path.exists(場所):
                os.remove(場所)

    def 書く(self, 板, 本文, 書いた人の鍵, 親番号=None, 名乗り=None, 名乗りの形=None, あの時=None, 番地=None, 港=None):
        """あの時＝その後の話の棚だけで使う、「負け」とされた時のこと。接続元の番地があれば、書いた人の記録も同じ時刻で残す。"""
        書いた時刻 = 時計.いま().isoformat()
        印 = self.つなぎ.execute(
            "INSERT INTO 書き込み (板, 本文, 書いた人の鍵, 書いた時刻, 親番号, 名乗り, 名乗りの形, あの時) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (板, 本文, 書いた人の鍵, 書いた時刻, 親番号, 名乗り or None, 名乗りの形 or None, あの時 or None),
        )
        if 番地:
            self.つなぎ.execute(
                "INSERT INTO 書いた人の記録 (書き込み番号, 番地, 港, 書いた時刻) VALUES (?, ?, ?, ?)",
                (印.lastrowid, 番地, 港, 書いた時刻),
            )
        return 印.lastrowid

    def 古い書いた人の記録を消す(self, 日数):
        """日数を過ぎた書いた人の記録を消す。消した中身は0で上書きし、書き足しの帳面（WAL）も空にして、ファイルに残さない。"""
        いつまで = (時計.いま() - timedelta(days=日数)).isoformat()
        self.つなぎ.execute("PRAGMA secure_delete = ON")
        印 = self.つなぎ.execute("DELETE FROM 書いた人の記録 WHERE 書いた時刻 < ?", (いつまで,))
        self.つなぎ.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        return 印.rowcount

    def 書いた人の記録を取り出す(self, 書き込み番号):
        """正式に求められた時と、命の危険が差し迫っている時だけ使う。消した書き込みでも取り出せる。記録が無ければ None。"""
        return self.つなぎ.execute(
            """SELECT 記録.書き込み番号, 記録.番地, 記録.港, 記録.書いた時刻, 書き込み.板, 書き込み.本文, 書き込み.あの時, 書き込み.消した時刻
            FROM 書いた人の記録 AS 記録 JOIN 書き込み ON 書き込み.番号 = 記録.書き込み番号
            WHERE 記録.書き込み番号 = ?""",
            (書き込み番号,),
        ).fetchone()

    def 名乗りを読む(self, 鍵):
        行 = self.つなぎ.execute("SELECT 名乗り FROM 名乗り WHERE 鍵 = ?", (鍵,)).fetchone()
        return 行[0] if 行 else ""

    def 名乗りを決める(self, 鍵, 名乗り):
        """空なら名乗りを外す（名無しに戻る）。"""
        if not 名乗り:
            self.つなぎ.execute("DELETE FROM 名乗り WHERE 鍵 = ?", (鍵,))
            return
        self.つなぎ.execute(
            "INSERT INTO 名乗り VALUES (?, ?, ?) ON CONFLICT (鍵) DO UPDATE SET 名乗り = excluded.名乗り, 変えた時刻 = excluded.変えた時刻",
            (鍵, 名乗り, 時計.いま().isoformat()),
        )

    def 名乗りの書き込み(self, 名乗りの形, 見る人の鍵, 件数=100):
        """同じ名乗り（そろえた形で比べる）の書き込み・返事・勝ち。新しい順。親を消した返事は出さない（親を引用した返事が残らないように）。"""
        return self.つなぎ.execute(
            f"""SELECT 番号, 板, 親番号, 本文, あの時, 書いた時刻, 名乗り, 書いた人の鍵, {_わかるの印}
            FROM 書き込み WHERE 名乗りの形 = ? AND 消した時刻 IS NULL
              AND (親番号 IS NULL OR 親番号 IN (SELECT 番号 FROM 書き込み WHERE 消した時刻 IS NULL))
            ORDER BY 番号 DESC LIMIT ?""",
            (見る人の鍵, 名乗りの形, 件数),
        ).fetchall()

    def 最後に書いた時刻(self, 書いた人の鍵):
        行 = self.つなぎ.execute(
            "SELECT MAX(書いた時刻) FROM 書き込み WHERE 書いた人の鍵 = ?", (書いた人の鍵,)
        ).fetchone()
        return datetime.fromisoformat(行[0]) if 行[0] else None

    def 同じ書き込みがあるか(self, 板, 本文, 書いた人の鍵, 秒, 親番号=None):
        いつから = (時計.いま() - timedelta(seconds=秒)).isoformat()
        return self.つなぎ.execute(
            "SELECT 1 FROM 書き込み WHERE 板 = ? AND 本文 = ? AND 書いた人の鍵 = ? AND 書いた時刻 >= ? AND 消した時刻 IS NULL AND 親番号 IS ?",
            (板, 本文, 書いた人の鍵, いつから, 親番号),
        ).fetchone() is not None

    def 板の書き込み(self, 板, 見る人の鍵, 件数=100, いつから=None):
        """新しい順。返事は含めない。いつからがあれば、それより前のものは出さない（独り言・夜の部屋）。"""
        いつから = いつから.astimezone(timezone.utc).isoformat() if いつから else ""
        return self.つなぎ.execute(
            f"""
            SELECT 番号, 本文, あの時, 結び, 書いた人の鍵, 書いた時刻, 名乗り, {_わかるの印}
            FROM 書き込み
            WHERE 板 = ? AND 消した時刻 IS NULL AND 親番号 IS NULL AND 書いた時刻 >= ?
            ORDER BY 番号 DESC LIMIT ?
            """,
            (見る人の鍵, 板, いつから, 件数),
        ).fetchall()

    def 板たちの新しい書き込み(self, 板たち, 件数=3):
        """はじめの画面に出す、板の新しい書き込みと返事。板の外（独り言・夜・小部屋など）は渡された板たちに入れない。
        聞き役（AI）の返事は出さない（人がいる気配を見せる段なので）。"""
        if not 板たち:
            return []
        印 = ",".join("?" * len(板たち))
        return self.つなぎ.execute(
            f"""SELECT 番号, 板, 親番号, 本文, 書いた時刻 FROM 書き込み
            WHERE 板 IN ({印}) AND 消した時刻 IS NULL AND 書いた人の鍵 != ?
              AND (親番号 IS NULL OR 親番号 IN (SELECT 番号 FROM 書き込み WHERE 消した時刻 IS NULL))
            ORDER BY 番号 DESC LIMIT ?""",
            [*板たち, 決まり.聞き役の鍵, 件数],
        ).fetchall()

    def 返事たち(self, 親番号たち, 見る人の鍵):
        """親番号ごとの返事。古い順（話の流れどおり）。わかるの印は 板の書き込み と同じ。"""
        if not 親番号たち:
            return {}
        印 = ",".join("?" * len(親番号たち))
        まとめ = {番号: [] for 番号 in 親番号たち}
        for 行 in self.つなぎ.execute(
            f"""SELECT 番号, 親番号, 本文, 書いた時刻, 名乗り, {_わかるの印}
            FROM 書き込み WHERE 親番号 IN ({印}) AND 消した時刻 IS NULL ORDER BY 番号""",
            [見る人の鍵, *親番号たち],
        ):
            まとめ[行["親番号"]].append(行)
        return まとめ

    def 返事できる親(self, 番号):
        """返事をつけられる書き込み（消されていない・返事ではない）の板。無ければ None。"""
        行 = self.つなぎ.execute(
            "SELECT 板 FROM 書き込み WHERE 番号 = ? AND 消した時刻 IS NULL AND 親番号 IS NULL", (番号,)
        ).fetchone()
        return 行[0] if 行 else None

    def わかると押す(self, 書き込み番号, 押した人の鍵):
        """押せたら True。消された書き込み・無い書き込み・押し済みは False。"""
        if not self.つなぎ.execute(
            "SELECT 1 FROM 書き込み WHERE 番号 = ? AND 消した時刻 IS NULL", (書き込み番号,)
        ).fetchone():
            return False
        印 = self.つなぎ.execute(
            "INSERT OR IGNORE INTO わかる VALUES (?, ?, ?)", (書き込み番号, 押した人の鍵, 時計.いま().isoformat())
        )
        return 印.rowcount == 1

    def 結ぶ(self, 番号, 書いた人の鍵, 板, 結び):
        """宣言した本人だけ、1回だけ結びを付けられる。付けられたら True。"""
        印 = self.つなぎ.execute(
            "UPDATE 書き込み SET 結び = ? WHERE 番号 = ? AND 書いた人の鍵 = ? AND 板 = ? AND 結び IS NULL AND 消した時刻 IS NULL",
            (結び, 番号, 書いた人の鍵, 板),
        )
        return 印.rowcount == 1

    def 書いた人(self, 書き込み番号):
        """(書いた人の鍵, 名乗りの形)。消されていれば None。"""
        行 = self.つなぎ.execute(
            "SELECT 書いた人の鍵, 名乗りの形 FROM 書き込み WHERE 番号 = ? AND 消した時刻 IS NULL", (書き込み番号,)
        ).fetchone()
        return (行[0], 行[1]) if 行 else None

    def 小部屋を開く(self, 名乗りの形, 自分の鍵, 相手の鍵):
        """同じ名乗りの2人の部屋。もうあればそれを返す（同じ2人に部屋を増やさない）。"""
        鍵1, 鍵2 = sorted((自分の鍵, 相手の鍵))
        self.つなぎ.execute(
            "INSERT OR IGNORE INTO 小部屋 (名乗りの形, 鍵1, 鍵2, 作った時刻) VALUES (?, ?, ?, ?)",
            (名乗りの形, 鍵1, 鍵2, 時計.いま().isoformat()),
        )
        return self.つなぎ.execute(
            "SELECT 番号 FROM 小部屋 WHERE 名乗りの形 = ? AND 鍵1 = ? AND 鍵2 = ?", (名乗りの形, 鍵1, 鍵2)
        ).fetchone()[0]

    def 小部屋(self, 部屋番号, 鍵):
        """その人が入れる部屋なら1行、入れなければ None。"""
        return self.つなぎ.execute(
            "SELECT * FROM 小部屋 WHERE 番号 = ? AND ? IN (鍵1, 鍵2)", (部屋番号, 鍵)
        ).fetchone()

    def 自分の小部屋(self, 鍵, 置き場の頭):
        """最後に話した順。最後に書いたのが自分かどうかも返す（相手からの話が待っているか）。"""
        return self.つなぎ.execute(
            """SELECT 小部屋.*, 最後.書いた時刻 AS 最後の時刻, 最後.書いた人の鍵 = ? AS 最後は自分
            FROM 小部屋 LEFT JOIN 書き込み AS 最後 ON 最後.番号 = (
                SELECT MAX(番号) FROM 書き込み WHERE 板 = ? || 小部屋.番号 AND 消した時刻 IS NULL)
            WHERE ? IN (鍵1, 鍵2)
            ORDER BY COALESCE(最後.書いた時刻, 小部屋.作った時刻) DESC""",
            (鍵, 置き場の頭, 鍵),
        ).fetchall()

    def 最初に書いた時刻(self, 書いた人の鍵):
        """そのブラウザ（匿名の鍵）で初めて書いた時刻。まだ何も書いていなければ None。消した書き込みも数える。"""
        行 = self.つなぎ.execute("SELECT MIN(書いた時刻) FROM 書き込み WHERE 書いた人の鍵 = ?", (書いた人の鍵,)).fetchone()
        return datetime.fromisoformat(行[0]) if 行[0] else None

    def 閉じた部屋の相手たち(self, 鍵):
        """この鍵と一度でも部屋を閉じた相手の鍵。どちらが閉じたかも名乗りも問わない（名乗りを変えて開き直すのを止める）。"""
        return {
            行[0] for 行 in self.つなぎ.execute(
                "SELECT CASE WHEN 鍵1 = ? THEN 鍵2 ELSE 鍵1 END FROM 小部屋 WHERE ? IN (鍵1, 鍵2) AND 閉じた時刻 IS NOT NULL", (鍵, 鍵))
        }

    def 小部屋を受けないか(self, 鍵):
        return self.つなぎ.execute("SELECT 1 FROM 小部屋を受けない WHERE 鍵 = ?", (鍵,)).fetchone() is not None

    def 小部屋の受け方を決める(self, 鍵, 受ける):
        """受けない人とは、ほかの人が新しく部屋を開けない。いまある部屋はそのまま（閉じるのはそれぞれの部屋で）。"""
        if 受ける:
            self.つなぎ.execute("DELETE FROM 小部屋を受けない WHERE 鍵 = ?", (鍵,))
        else:
            self.つなぎ.execute("INSERT OR IGNORE INTO 小部屋を受けない VALUES (?, ?)", (鍵, 時計.いま().isoformat()))

    def 小部屋を閉じる(self, 部屋番号, 鍵):
        印 = self.つなぎ.execute(
            "UPDATE 小部屋 SET 閉じた時刻 = ?, 閉じた人の鍵 = ? WHERE 番号 = ? AND ? IN (鍵1, 鍵2) AND 閉じた時刻 IS NULL",
            (時計.いま().isoformat(), 鍵, 部屋番号, 鍵),
        )
        return 印.rowcount == 1

    def 書き込みの板(self, 書き込み番号):
        行 = self.つなぎ.execute("SELECT 板 FROM 書き込み WHERE 番号 = ?", (書き込み番号,)).fetchone()
        return 行[0] if 行 else None

    def 新しい書き込み(self, 件数=200):
        """持ち主の見回り用。消したものも含めて新しい順。同じブラウザ（匿名の鍵）で書いた数も付ける（鍵そのものは渡さない）。"""
        return self.つなぎ.execute(
            """SELECT 番号, 板, 本文, あの時, 書いた時刻, 消した時刻, 親番号, 名乗り,
            (SELECT COUNT(*) FROM 書き込み AS 同じ WHERE 同じ.書いた人の鍵 = 書き込み.書いた人の鍵) AS 同じブラウザの数
            FROM 書き込み ORDER BY 番号 DESC LIMIT ?""", (件数,)
        ).fetchall()

    def 同じブラウザの書き込み(self, 書き込み番号):
        """その書き込みを書いたブラウザ（匿名の鍵）の書き込み。消したものも含めて新しい順。番号が無ければ空。"""
        return self.つなぎ.execute(
            """SELECT 番号, 板, 本文, 書いた時刻, 消した時刻, 名乗り FROM 書き込み
            WHERE 書いた人の鍵 = (SELECT 書いた人の鍵 FROM 書き込み WHERE 番号 = ?) ORDER BY 番号 DESC""", (書き込み番号,)
        ).fetchall()

    def まとめて消す(self, 書き込み番号, ここまで):
        """その書き込みを書いたブラウザの、出ている書き込みを消す。ここまで（番号）より後に書かれた物は、一覧で見ていないので消さない。"""
        return self.つなぎ.execute(
            """UPDATE 書き込み SET 消した時刻 = ? WHERE 書いた人の鍵 = (SELECT 書いた人の鍵 FROM 書き込み WHERE 番号 = ?)
            AND 番号 <= ? AND 消した時刻 IS NULL""", (時計.いま().isoformat(), 書き込み番号, ここまで)
        ).rowcount

    def まとめて戻す(self, 書き込み番号, ここまで):
        return self.つなぎ.execute(
            """UPDATE 書き込み SET 消した時刻 = NULL WHERE 書いた人の鍵 = (SELECT 書いた人の鍵 FROM 書き込み WHERE 番号 = ?)
            AND 番号 <= ? AND 消した時刻 IS NOT NULL""", (書き込み番号, ここまで)
        ).rowcount

    def 知らせる(self, 送った人の鍵, 書き込み番号, 本文):
        """持ち主への知らせ。書き込みとは別の台に置き、どの画面も読まない（見回りだけが読む）。"""
        return self.つなぎ.execute(
            "INSERT INTO 知らせ (送った人の鍵, 書き込み番号, 本文, 送った時刻) VALUES (?, ?, ?, ?)",
            (送った人の鍵, 書き込み番号, 本文, 時計.いま().isoformat()),
        ).lastrowid

    def 同じ知らせがあるか(self, 送った人の鍵, 書き込み番号, 本文, 秒):
        いつから = (時計.いま() - timedelta(seconds=秒)).isoformat()
        return self.つなぎ.execute(
            "SELECT 1 FROM 知らせ WHERE 送った人の鍵 = ? AND 書き込み番号 IS ? AND 本文 = ? AND 送った時刻 >= ?",
            (送った人の鍵, 書き込み番号, 本文, いつから),
        ).fetchone() is not None

    def 最後に知らせた時刻(self, 送った人の鍵):
        行 = self.つなぎ.execute("SELECT MAX(送った時刻) FROM 知らせ WHERE 送った人の鍵 = ?", (送った人の鍵,)).fetchone()
        return datetime.fromisoformat(行[0]) if 行[0] else None

    def 知らせたち(self, 件数=100):
        """持ち主の見回り用。新しい順。知らせた書き込みの置き場と、書いた人と同じブラウザからの知らせかも返す。"""
        return self.つなぎ.execute(
            """SELECT 知らせ.番号, 知らせ.書き込み番号, 知らせ.本文, 知らせ.送った時刻, 知らせ.送った人の鍵,
                      書き込み.板, 書き込み.消した時刻, 書き込み.書いた人の鍵 = 知らせ.送った人の鍵 AS 本人から
            FROM 知らせ LEFT JOIN 書き込み ON 書き込み.番号 = 知らせ.書き込み番号
            ORDER BY 知らせ.番号 DESC LIMIT ?""",
            (件数,),
        ).fetchall()

    def 書いた書き込みの番号(self, 書いた人の鍵, 件数=10):
        """そのブラウザ（匿名の鍵）で書いた書き込みの番号。新しい順。知らせが書いた本人からかを、持ち主が確かめるため。"""
        return [行[0] for 行 in self.つなぎ.execute(
            "SELECT 番号 FROM 書き込み WHERE 書いた人の鍵 = ? ORDER BY 番号 DESC LIMIT ?", (書いた人の鍵, 件数))]

    def 聞き役を待つ書き込み(self, 板たち, いつまで, いつから, 試す回数, 件数):
        """聞き役が返す時が来た板の書き込み（返事ではない・消されていない・人の返事が無い）。古い順。
        いつまでより前、いつからより後に書かれた物だけ。見送った・止めた・返した物と、試す回数うまくいかなかった物は入れない。"""
        if not 板たち:
            return []
        印 = ",".join("?" * len(板たち))
        return self.つなぎ.execute(
            f"""SELECT 元.番号, 元.板, 元.本文, COALESCE(記.試した回数, 0) AS 試した回数
            FROM 書き込み AS 元 LEFT JOIN 聞き役の記録 AS 記 ON 記.書き込み番号 = 元.番号
            WHERE 元.板 IN ({印}) AND 元.親番号 IS NULL AND 元.消した時刻 IS NULL
              AND 元.書いた時刻 <= ? AND 元.書いた時刻 >= ? AND {_人の返事が無い}
              AND (記.書き込み番号 IS NULL OR (記.結果 = '失敗' AND 記.試した回数 < ?))
            ORDER BY 元.番号 LIMIT ?""",
            [*板たち, いつまで.isoformat(), いつから.isoformat(), 試す回数, 件数],
        ).fetchall()

    def 聞き役が尋ねた数(self, いつから):
        """いつから後に、聞き役が初めてAIへ尋ねた書き込みの数（見送った物はAIに送っていないので数えない）。"""
        return self.つなぎ.execute(
            "SELECT COUNT(*) FROM 聞き役の記録 WHERE 最初に試した時刻 >= ? AND 結果 != '見送った'", (いつから.isoformat(),)
        ).fetchone()[0]

    def 聞き役の記録をつける(self, 書き込み番号, 結果, 返事の番号=None):
        """結果は、返した・止めた（AIの文が守りにかかった）・失敗（尋ねるのがうまくいかなかった）・見送った（つらすぎる言葉）・
        置かなかった（尋ねている間に人が返した、または消された）のどれか。"""
        いま = 時計.いま().isoformat()
        self.つなぎ.execute(
            """INSERT INTO 聞き役の記録 VALUES (?, ?, 1, ?, ?, ?) ON CONFLICT (書き込み番号) DO UPDATE SET
            結果 = excluded.結果, 試した回数 = 試した回数 + 1, 最後に試した時刻 = excluded.最後に試した時刻, 返事の番号 = excluded.返事の番号""",
            (書き込み番号, 結果, いま, いま, 返事の番号),
        )

    def 聞き役が返す(self, 書き込み番号, 板, 返事):
        """まだ人の返事が無く消されてもいなければ、聞き役の返事を置いて番号を返す。置かなければ None。
        AIに尋ねている間に人が返したり持ち主が消したりした時に、あとから重ねて置かないよう、確かめてから書くを1つの動きにする。"""
        with self.ひとりずつ():
            if not self.つなぎ.execute(
                f"SELECT 1 FROM 書き込み AS 元 WHERE 番号 = ? AND 親番号 IS NULL AND 消した時刻 IS NULL AND {_人の返事が無い}",
                (書き込み番号,),
            ).fetchone():
                return None
            return self.書く(板, 返事, 決まり.聞き役の鍵, 書き込み番号, 決まり.聞き役の名乗り)

    def 消す(self, 書き込み番号):
        印 = self.つなぎ.execute(
            "UPDATE 書き込み SET 消した時刻 = ? WHERE 番号 = ? AND 消した時刻 IS NULL",
            (時計.いま().isoformat(), 書き込み番号),
        )
        return 印.rowcount == 1

    def 戻す(self, 書き込み番号):
        印 = self.つなぎ.execute(
            "UPDATE 書き込み SET 消した時刻 = NULL WHERE 番号 = ? AND 消した時刻 IS NOT NULL", (書き込み番号,)
        )
        return 印.rowcount == 1
