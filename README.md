# DriveRAG

DriveRAG is being built as a local RAG system for documents from Google Drive. The long-term goal is to index Drive files and answer questions using locally run models.

> **Status: work in progress.** The current application syncs Google Drive file metadata to PostgreSQL. It does not yet download Drive content or run parsing, chunking, embedding, retrieval, or chat. Qdrant is available in Docker Compose but is not yet used by the application.

## How the current application is wired

The current sync path is:

1. `scripts/run_sync.py` calls `build_container()`.
2. `rag.config` loads `config.yaml`, loads a neighboring `.env` file if present, and expands `${ENV_VAR}` references. Missing variables and invalid configuration are reported as errors.
3. `rag.core.loader` imports the configured `module:ClassName`, restricts imports to the trusted `rag` package, checks the class against the expected component type, and resolves named dependencies such as `{ref: database}`.
4. `rag.container` builds the configured Google Drive source and file repository. The repository owns the database interaction; the container exposes the source and repository to the sync script.
5. The script connects to Drive, lists file metadata, upserts it through `FileRepo`, and asks the repository for the stored file count.

Run the current sync with `uv run python scripts/run_sync.py` after configuring the environment and initializing the PostgreSQL schema.

`Drive.fetch_content()` is not implemented yet, so the current sync does not ingest document contents. `SchemaInitializer` exists, but `run_sync.py` does not initialize the database schema; initialize it before running the sync. The PostgreSQL integration tests initialize the schema themselves.

The loader currently supports the component roles wired by the container: database, credential provider, path resolver, data source, and file repository. The abstract extension contracts include `Database`, `CredentialProvider`, `PathResolver`, `DataSource`, and `FileRepo`.

## Adding or switching an adapter

For an existing component role with an abstract contract, implement an adapter under `src/rag/`, add tests for it, and select it in `config.yaml`. For example, a compatible file repository can be selected by changing the class path:

```yaml
components:
  file_repo:
    class: rag.storage.my_file_repo:MyFileRepo
    dependencies:
      database:
        ref: database
```

The class path uses `module:ClassName`; constructor values go under `options`, and shared components are injected through `dependencies` references. The example assumes `MyFileRepo` accepts the current `Database` dependency. If the adapter needs an additional Python package, add it to `pyproject.toml`. The loader only trusts classes from the `rag` package.

Switching an implementation of an already wired role should not require changes to the sync script or container, provided it satisfies the same contract and dependency shape. Adding a **new role** (for example, the first parser or vector-store component) requires adding its contract and wiring that role into the loader/container once. After that, implementations of that role can be selected through configuration.

## Current repository structure

```text
rag/
├── .env                         # local configuration; do not commit
├── .gitignore
├── .python-version
├── Data Pipeline Architecture (1).jpg
├── README.md
├── compose.yaml                 # PostgreSQL/pgvector and Qdrant
├── config.yaml                  # configured component classes and dependencies
├── planned_structure.md         # evolving target structure
├── pyproject.toml
├── secrets/                     # local Google OAuth files; do not commit
├── uv.lock
├── scripts/
│   ├── check_drive_auth.py
│   ├── inspect_db.py
│   └── run_sync.py
├── src/
│   └── rag/
│       ├── __init__.py
│       ├── config.py             # YAML and environment settings
│       ├── container.py          # component composition
│       ├── core/
│       │   ├── init.py
│       │   └── loader.py         # trusted class-path loading and dependency resolution
│       ├── parser/
│       │   └── init.py           # placeholder; parser implementations are not present yet
│       ├── sources/
│       │   ├── __init__.py
│       │   ├── data_source.py    # DataSource contract
│       │   ├── source_file.py    # SourceFile metadata
│       │   └── gdrive/
│       │       ├── __init__.py
│       │       ├── cred_provider.py
│       │       ├── drive.py
│       │       ├── drive_auth_cred_provider.py
│       │       ├── file_mapper.py
│       │       ├── gdrive_path_resolver.py
│       │       ├── path_resolver.py
│       │       └── token_store.py
│       └── storage/
│           ├── __init__.py
│           ├── database.py
│           ├── file_repo.py      # FileRepo contract: upsert and count
│           ├── postgres_database.py
│           ├── postgres_file_repo.py
│           ├── schema.sql
│           └── schema_initializer.py
└── test/
    ├── core/
    │   ├── test_config.py
    │   ├── test_container.py
    │   └── test_loader.py
    ├── test_gdrive_components.py
    ├── test_path_resolver.py
    ├── test_postgres_file_repo.py
    └── test_run_sync.py
```

The PostgreSQL integration tests need PostgreSQL to run (for example, with `docker compose up -d postgres`); they skip when `DATABASE_URL` is unset or PostgreSQL is unavailable. The current tests do not require Qdrant.

## Planned RAG pipeline

The diagram and flow below describe the target architecture, not current functionality. PostgreSQL is intended to track file state and chunk metadata, while Qdrant stores vectors.

![DriveRAG planned data pipeline](<Data Pipeline Architecture (1).jpg>)

The intended pipeline is:

1. Connect one or more Google Drive accounts using read-only access.
2. Discover files and track metadata and processing state in PostgreSQL.
3. Download and parse supported content into a consistent document representation; cache parsed results.
4. Chunk the content, embed text or media locally, and store vectors and chunk metadata. Reprocess changed files and remove deleted files from the index.
5. Retrieve relevant chunks for a question and use a local language model to generate a cited answer.

EmbeddingGemma 2 and Qwen3.5 9B through Ollama are current model candidates; model choices may change as development progresses.

## Privacy

Google OAuth and Drive API access are required for Drive metadata and, once implemented, content retrieval. Keep `.env` and OAuth files in `secrets/` local and never commit their contents. The intended embedding and answer-generation models run locally.
