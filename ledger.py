"""The khata: SQLite. kind: credit = we gave udhaar, payment = they paid.
void: 0 = active, 1 = undone one by one, 2 = cleared together. Nothing is ever really deleted."""
import sqlite3

DB = "khata.db"
BAL = "SUM(CASE kind WHEN 'credit' THEN amount ELSE -amount END)"

def _c():
    return sqlite3.connect(DB)

def init():
    with _c() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS txns(
            id INTEGER PRIMARY KEY, name TEXT, kind TEXT, amount REAL,
            ts TEXT DEFAULT (datetime('now','localtime')), void INTEGER DEFAULT 0)""")
        c.execute("CREATE TABLE IF NOT EXISTS contacts(name TEXT PRIMARY KEY COLLATE NOCASE, phone TEXT)")
        try:  # old databases from before this feature
            c.execute("ALTER TABLE txns ADD COLUMN void INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        try:
            c.execute("ALTER TABLE txns ADD COLUMN note TEXT")
        except sqlite3.OperationalError:
            pass

def add(name, kind, amount, note=None):
    with _c() as c:
        c.execute("INSERT INTO txns(name, kind, amount, note) VALUES (?,?,?,?)", (name, kind, amount, note))

def names():
    with _c() as c:
        return [r[0] for r in c.execute("SELECT DISTINCT name FROM txns WHERE void=0")]

def balance(name):
    with _c() as c:
        return c.execute(f"SELECT {BAL} FROM txns WHERE void=0 AND name=? COLLATE NOCASE", (name,)).fetchone()[0]

def people():
    with _c() as c:
        rows = c.execute(f"""SELECT name, {BAL} b, (SELECT phone FROM contacts WHERE contacts.name=txns.name)
                             FROM txns WHERE void=0 GROUP BY name COLLATE NOCASE ORDER BY b DESC""").fetchall()
    return [{"name": n, "balance": b, "phone": ph} for n, b, ph in rows]

def today():
    with _c() as c:
        rows = c.execute("""SELECT kind, SUM(amount) FROM txns WHERE void=0
                            AND date(ts)=date('now','localtime') GROUP BY kind""").fetchall()
    d = dict(rows)
    return {"given": d.get("credit", 0) or 0, "received": d.get("payment", 0) or 0}

def undo():
    """Hide the newest entry. Returns (name, kind, amount) or None."""
    with _c() as c:
        r = c.execute("SELECT id, name, kind, amount FROM txns WHERE void=0 ORDER BY id DESC LIMIT 1").fetchone()
        if r:
            c.execute("UPDATE txns SET void=1 WHERE id=?", (r[0],))
    return r[1:] if r else None

def clear():
    with _c() as c:
        c.execute("UPDATE txns SET void=2 WHERE void=0")

def restore():
    with _c() as c:
        c.execute("UPDATE txns SET void=0 WHERE void=2")

def archived():
    with _c() as c:
        return c.execute("SELECT COUNT(*) FROM txns WHERE void=2").fetchone()[0]

def redo():
    """Bring back the entry that was undone last."""
    with _c() as c:
        r = c.execute("SELECT id FROM txns WHERE void=1 ORDER BY id ASC LIMIT 1").fetchone()
        if r:
            c.execute("UPDATE txns SET void=0 WHERE id=?", (r[0],))

def undone():
    with _c() as c:
        return c.execute("SELECT COUNT(*) FROM txns WHERE void=1").fetchone()[0]

def set_phone(name, phone):
    with _c() as c:
        if phone:
            c.execute("INSERT OR REPLACE INTO contacts(name, phone) VALUES (?,?)", (name, phone))
        else:
            c.execute("DELETE FROM contacts WHERE name=?", (name,))

def get_phone(name):
    with _c() as c:
        r = c.execute("SELECT phone FROM contacts WHERE name=?", (name,)).fetchone()
    return r[0] if r else None

def history(name):
    """A customer's statement, newest first."""
    with _c() as c:
        rows = c.execute("SELECT ts, kind, amount, note FROM txns WHERE void=0 AND name=? COLLATE NOCASE ORDER BY id DESC LIMIT 40", (name,)).fetchall()
    return [{"ts": r[0], "kind": r[1], "amount": r[2], "note": r[3]} for r in rows]
