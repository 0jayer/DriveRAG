# DriveRAG

**DriveRAG is a local RAG system that lets you chat with documents from multiple Google Drives.** Connect the Drive accounts you want to search, let DriveRAG build and maintain a searchable corpus from their documents, then ask questions in a chat powered by models running on your own PC.

The intended model stack is [EmbeddingGemma 2](https://ai.google.dev/gemma/docs/embeddinggemma/model_card_2) for embeddings and [Qwen3.5 9B](https://ollama.com/library/qwen3.5) for answer generation, both run locally through Ollama. Google Drive is the remote source of documents; parsing, indexing, retrieval, and answer generation are designed to run locally. Model choices may change as development progresses.

> **Status: work in progress.** The multi-Drive chat product is the goal, not the current feature set. The repository currently has an early local-Markdown RAG prototype and a separate Google Drive metadata-ingestion prototype. It does not yet connect Drive document contents to the chat flow.

## Intended data pipeline

The architecture below is the planned ingestion flow. PostgreSQL tracks files and processing state, while Qdrant stores searchable vectors. The parser, cache, chunker, embedder, incremental updates, and deletion handling are planned parts of the pipeline.

![DriveRAG planned data pipeline](<Data Pipeline Architecture (1).jpg>)

The intended user flow is:

1. Connect one or more Google Drive accounts using read-only access.
2. Discover files and track each file's metadata and processing state in PostgreSQL.
3. Parse supported file contents into a consistent intermediate representation and cache parsed results.
4. Split the content into chunks, embed those chunks locally with EmbeddingGemma 2, and store vectors and chunk information in Qdrant. Keep processing state in PostgreSQL so changed or removed files can be reprocessed or deleted from the index.
5. Ask questions in a local chat. Retrieve relevant chunks from the connected Drive corpus and use the local Qwen3.5 9B model to compose answers grounded in those documents.

## Project layout

```text
data/       Google Drive metadata and database code
docs/       Markdown files used by the current RAG prototype (create this directory)
sql/        PostgreSQL schema
test/       Database inspection and metadata-ingestion scripts
rag.py      Local Markdown retrieval and question-answering prototype
compose.yaml PostgreSQL and Qdrant services
```

## Privacy and scope

The intended design runs embedding and answer-generation models locally. Google OAuth and Drive API access are still required to read metadata and, in the planned ingestion pipeline, retrieve Drive content. The current prototype only handles local Markdown for question answering; supported Drive file types, multi-account management, and end-to-end indexing are still to be implemented.
