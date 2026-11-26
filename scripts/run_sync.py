import logging

from rag.container import build_container
from rag.logging_setup import setup_logging

logger = logging.getLogger(__name__)


def main() -> None:
    setup_logging()
    logger.info("Starting Drive metadata sync")

    container = build_container()
    container.data_source.connect()

    files = container.data_source.list_source_files()
    container.file_repo.upsert_files(files)
    logger.info("Listed %d files from Drive", len(files))
    print(f"listed {len(files)} files from Drive")

    total = container.file_repo.count_files()
    logger.info("Total files in repository: %d", total)
    print(f"files in repository: {total}")


if __name__ == "__main__":
    main()
