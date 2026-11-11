import argparse
from pathlib import Path
import sys

from psycopg import sql
from psycopg.rows import dict_row

# test_db.py lives in the test subdirectory, while metadata.py is at the
# project root. Ensure the root is importable both from the editor and when
# this file is run directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data.metadata import get_conn


# uv run test_db.py                                   # summary
# uv run test_db.py --dump --limit 0 --full           # everything
# uv run test_db.py --table files --where "status <> 'ok'" --limit 0 --full

def human_size(n):
    if n is None:
        return "-"
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024


def clip(value, max_len):
    text = str(value)
    if max_len and len(text) > max_len:
        return text[:max_len] + f"... [{len(text)} chars]"
    return text


def print_table(headers, rows, out, right=()):
    rows = [[str(c) for c in row] for row in rows]
    widths = [
        max([len(h)] + [len(row[i]) for row in rows])
        for i, h in enumerate(headers)
    ]

    def fmt(cells):
        return "  ".join(
            c.rjust(w) if i in right else c.ljust(w)
            for i, (c, w) in enumerate(zip(cells, widths))
        ).rstrip()

    print(fmt(headers), file=out)
    print("  ".join("-" * w for w in widths), file=out)
    for row in rows:
        print(fmt(row), file=out)


def summary(conn, out):
    print("== files by status ==", file=out)
    rows = conn.execute(
        "SELECT status, count(*) FROM files GROUP BY status ORDER BY status"
    ).fetchall()
    print_table(["status", "count"], rows, out, right={1})
    print(f"total: {sum(n for _, n in rows)}", file=out)

    print("\n== files ==", file=out)
    rows = [
        (status, human_size(size), f"{mod:%Y-%m-%d}", path)
        for status, size, mod, path in conn.execute(
            "SELECT status, size_bytes, modified_time, path FROM files ORDER BY path"
        )
    ]
    print_table(["status", "size", "modified", "path"], rows, out, right={1})


def dump(conn, out, tables, limit, max_len, where):
    existing = [
        r[0]
        for r in conn.execute(
            """SELECT table_name FROM information_schema.tables
               WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
               ORDER BY table_name"""
        )
    ]
    for t in tables or []:
        if t not in existing:
            sys.exit(f"no such table: {t} (have: {', '.join(existing)})")

    for table in tables or existing:
        ident = sql.Identifier(table)

        query = sql.SQL("SELECT * FROM {}").format(ident)
        count_q = sql.SQL("SELECT count(*) FROM {}").format(ident)
        if where:
            query += sql.SQL(" WHERE ") + sql.SQL(where)
            count_q += sql.SQL(" WHERE ") + sql.SQL(where)
        total = conn.execute(count_q).fetchone()[0]
        if limit:
            query += sql.SQL(" LIMIT {}").format(sql.Literal(limit))

        print("=" * 60, file=out)
        print(f"{table}  ({total} matching rows)", file=out)
        print("=" * 60, file=out)

        shown = 0
        with conn.cursor(name="dump_cur", row_factory=dict_row) as cur:
            cur.itersize = 1000
            cur.execute(query)
            for row in cur:
                shown += 1
                width = max(len(k) for k in row)
                print("-" * 40, file=out)
                for key, value in row.items():
                    print(f"{key.ljust(width)} : {clip(value, max_len)}", file=out)

        print(f"\n{shown} of {total} row(s) shown\n", file=out)


def main():
    parser = argparse.ArgumentParser(description="Read-only view of the rag database")
    parser.add_argument("--dump", action="store_true", help="print full rows instead of the summary")
    parser.add_argument("--table", action="append", help="table to dump (repeatable; implies --dump)")
    parser.add_argument("--where", help="SQL condition for --dump, e.g. \"status = 'failed'\"")
    parser.add_argument("--limit", type=int, default=50, help="max rows per table, 0 = all")
    parser.add_argument("--full", action="store_true", help="never truncate long values")
    parser.add_argument("--out", help="write to this file instead of the screen")
    args = parser.parse_args()

    if args.out:
        out = open(args.out, "w", encoding="utf-8")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        out = sys.stdout

    try:
        with get_conn() as conn:
            conn.read_only = True
            if args.dump or args.table or args.where:
                dump(conn, out, args.table, args.limit, None if args.full else 80, args.where)
            else:
                summary(conn, out)
    finally:
        if args.out:
            out.close()


if __name__ == "__main__":
    main()