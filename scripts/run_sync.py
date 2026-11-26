from rag.container import build_container


def main() -> None:
    container = build_container()
    container.data_source.connect()

    files = container.data_source.list_source_files()
    container.file_repo.upsert_files(files)
    print(f"listed {len(files)} files from Drive")

    with container.database.get_conn() as conn:
        total = conn.execute("SELECT count(*) FROM files").fetchone()[0]
    print(f"files in db: {total}")


if __name__ == "__main__":
    main()