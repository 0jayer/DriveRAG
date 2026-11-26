from rag.container import build_container


def main() -> None:
    container = build_container()
    container.data_source.connect()

    files = container.data_source.list_source_files()
    container.file_repo.upsert_files(files)
    print(f"listed {len(files)} files from Drive")

    total = container.file_repo.count_files()
    print(f"files in repository: {total}")


if __name__ == "__main__":
    main()