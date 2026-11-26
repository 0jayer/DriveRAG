<!-- Summary: Configure trusted adapter class paths once, validate them through one loader, keep parsing focused, and test shared contracts. -->

rag/
├── pyproject.toml
├── README.md
├── .gitignore                       # secrets/, .env, __pycache__/
├── .env.example
├── config.yaml                      # class paths/options for adapters and their dependencies
├── compose.yaml                     # PostgreSQL and Qdrant services
├── .python-version
├── Data Pipeline Architecture (1).jpg
├── secrets/                         # credentials.json, token.json (never committed)
├── scripts/
│   ├── check_drive_auth.py          # checks Google Drive OAuth credentials
│   ├── inspect_db.py                # read-only PostgreSQL inspection
│   ├── run_sync.py                  # syncs Drive to the index (currently metadata only)
│   ├── run_chat.py                  # builds objects via container, starts chatbot
│   └── run_eval.py                  # runs evaluation questions
├── src/
│   └── rag/
│       ├── __init__.py
│       ├── config.py                # typed Settings: loads and validates config.yaml and .env
│       ├── logging_setup.py
│       ├── container.py             # composition root: wires configured adapters and nested dependencies
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   └── loader.py            # allowlists class paths, validates contracts, constructs with options
│       │
│       ├── domain/                  # plain data classes
│       │   ├── __init__.py
│       │   ├── document.py          # Document, Block, Table, Cell, image/media refs, locations
│       │   ├── chunk.py             # Chunk (text or media reference, position, parent file)
│       │   ├── query.py             # Query, RetrievedChunk
│       │   └── answer.py            # Answer (text + citations)
│       │
│       ├── sources/                 # where files come from
│       │   ├── __init__.py
│       │   ├── data_source.py       # DataSource (abstract)
│       │   ├── source_file.py       # SourceFile
│       │   └── gdrive/
│       │       ├── __init__.py
│       │       ├── drive.py         # Drive(DataSource)
│       │       ├── cred_provider.py # CredentialProvider (abstract)
│       │       ├── token_store.py   # TokenStore (abstract) + JsonTokenStore
│       │       ├── drive_auth_cred_provider.py # OAuth flow + refresh (uses TokenStore)
│       │       ├── file_mapper.py   # FileMapper (abstract) + GDriveFileMapper
│       │       ├── path_resolver.py # PathResolver (abstract)
│       │       ├── gdrive_path_resolver.py # GDrivePathResolver(PathResolver)
│       │       └── exporter.py      # downloads / exports file bytes
│       │
│       ├── parsing/                 # file -> Document
│       │   ├── __init__.py
│       │   ├── parser.py            # Parser (abstract)
│       │   ├── processor.py         # Processor (abstract)
│       │   ├── router.py            # picks configured parser by mime type
│       │   ├── pipeline.py          # parse -> process -> Document; no cache or persistence
│       │   ├── errors.py            # UnsupportedFormatError, ParseError
│       │   ├── parsers/
│       │   │   ├── __init__.py
│       │   │   ├── _docling_common.py   # shared Docling conversion
│       │   │   ├── pdf_docling.py
│       │   │   ├── docx_docling.py
│       │   │   ├── html_docling.py
│       │   │   ├── markdown_docling.py
│       │   │   ├── xml_lxml.py
│       │   │   ├── text_plain.py
│       │   │   ├── python_ast.py
│       │   │   └── image_passthrough.py # represents images in Documents; no OCR
│       │   └── processors/
│       │       ├── __init__.py
│       │       ├── headers_footers.py
│       │       ├── dehyphenate.py
│       │       └── whitespace.py
│       │
│       ├── chunking/                # Document -> Chunks
│       │   ├── __init__.py
│       │   ├── chunker.py           # Chunker (abstract)
│       │   └── chunkers/
│       │       ├── __init__.py
│       │       └── recursive.py
│       │
│       ├── embedding/               # shared by sync and retrieval
│       │   ├── __init__.py
│       │   ├── embedder.py          # Embedder contract for supported text/media inputs
│       │   └── embedders/
│       │       ├── __init__.py
│       │       └── embeddinggemma.py
│       │
│       ├── storage/                 # persistence
│       │   ├── __init__.py
│       │   ├── database.py          # connection context manager
│       │   ├── file_repo.py         # FileRepo (abstract)
│       │   ├── postgres_file_repo.py
│       │   ├── schema_initializer.py # applies schema.sql
│       │   ├── schema.sql
│       │   ├── vector_store.py      # VectorStore (abstract)
│       │   ├── vector_stores/
│       │   │   ├── __init__.py
│       │   │   └── qdrant.py
│       │   ├── cache.py             # Cache (abstract)
│       │   └── disk_cache.py        # DiskCache(Cache)
│       │
│       ├── retrieval/               # query -> relevant chunks
│       │   ├── __init__.py
│       │   ├── retriever.py         # uses Embedder + VectorStore
│       │   ├── query_rewriter.py
│       │   ├── reranker.py          # Reranker (abstract)
│       │   └── rerankers/
│       │       ├── __init__.py
│       │       └── cross_encoder.py # add only if needed
│       │
│       ├── generation/              # chunks -> answer
│       │   ├── __init__.py
│       │   ├── llm.py               # LLM (abstract)
│       │   ├── llms/
│       │   │   ├── __init__.py
│       │   │   └── qwen_ollama.py
│       │   ├── prompt_builder.py    # context assembly + citations
│       │   └── conversation.py      # chat history
│       │
│       ├── services/                # orchestration, depends on abstractions
│       │   ├── __init__.py
│       │   ├── change_detector.py   # new / changed / deleted files
│       │   ├── sync_service.py      # source -> cache/read -> parse -> chunk -> embed -> persist
│       │   └── chatbot.py           # rewrite -> retrieve -> rerank -> generate
│       │
│       └── evaluation/
│           ├── __init__.py
│           └── evaluator.py
│
└── test/
    ├── conftest.py
    ├── test_gdrive_components.py    # current
    ├── test_path_resolver.py        # current
    ├── test_postgres_file_repo.py   # current
    ├── fakes/                       # fake source, vector store, embedder, LLM
    ├── core/
    │   └── test_loader.py           # allowlist, contract, and options validation
    ├── sources/                     # DataSource contract and adapter tests
    ├── parsing/                     # Parser/Processor contract and adapter tests
    ├── chunking/                    # Chunker contract and adapter tests
    ├── embedding/                   # Embedder contract and adapter tests
    ├── storage/                     # FileRepo/VectorStore/Cache contract and adapter tests
    ├── retrieval/                   # Retriever/Reranker contract and adapter tests
    ├── generation/                  # LLM contract and adapter tests
    └── services/