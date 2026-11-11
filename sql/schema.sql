-- files: one row per file per account (folders are not stored)
-- (no CREATE EXTENSION vector: vectors live in Qdrant now)

CREATE TABLE IF NOT EXISTS files (
  account_id      text        NOT NULL,
  external_id     text        NOT NULL,
  source          text        NOT NULL,
  name            text        NOT NULL,
  path            text        NOT NULL,
  mime_type       text        NOT NULL,
  size_bytes      bigint,
  source_hash     text,
  modified_time   timestamptz NOT NULL,
  content_hash    text,
  status          text        NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('pending','ok','failed','skipped','deleted')),
  error           text,
  enabled         boolean     NOT NULL DEFAULT true,
  parser_version  text,
  chunk_config    jsonb,
  downloaded_at   timestamptz,
  parsed_at       timestamptz,
  embedded_at     timestamptz,
  ingested_at     timestamptz,
  first_seen_at   timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (account_id, external_id)
);

CREATE INDEX IF NOT EXISTS files_status_idx ON files (status);
CREATE INDEX IF NOT EXISTS files_account_status_idx ON files (account_id, status);
CREATE INDEX IF NOT EXISTS files_source_idx ON files (source);

-- chunks: text + metadata only. The vector lives in Qdrant under the same id.
CREATE TABLE IF NOT EXISTS chunks (
  chunk_id         uuid        PRIMARY KEY,   -- also the Qdrant point id
  account_id       text        NOT NULL,
  external_id      text        NOT NULL,
  file_hash        text        NOT NULL,
  chunk_index      int         NOT NULL,
  content          text COMPRESSION lz4 NOT NULL,
  text_hash        text        NOT NULL,
  token_count      int,
  page             int,
  heading_path     text,
  start_time       real,
  end_time         real,
  embedding_model  text        NOT NULL,
  embedding_collection text    NOT NULL DEFAULT 'default',
  embedding_dimension smallint NOT NULL DEFAULT 768
                   CHECK (embedding_dimension > 0),
  embedding_status text        NOT NULL DEFAULT 'pending'
                   CHECK (embedding_status IN ('pending', 'ok', 'failed')),
  embedding_error  text,
  chunker_version  text,
  embedded_at      timestamptz,
  created_at       timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (account_id, external_id)
    REFERENCES files (account_id, external_id) ON DELETE CASCADE
) WITH (toast_tuple_target = 128);

CREATE INDEX IF NOT EXISTS chunks_file_idx ON chunks (account_id, external_id);
CREATE INDEX IF NOT EXISTS chunks_account_idx ON chunks (account_id);
CREATE UNIQUE INDEX IF NOT EXISTS chunks_file_hash_index_uidx
  ON chunks (account_id, external_id, file_hash, chunk_index);

ALTER TABLE files
  ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();

ALTER TABLE chunks
  ADD COLUMN IF NOT EXISTS embedding_collection text NOT NULL DEFAULT 'default',
  ADD COLUMN IF NOT EXISTS embedding_dimension smallint NOT NULL DEFAULT 768,
  ADD COLUMN IF NOT EXISTS embedding_status text NOT NULL DEFAULT 'pending',
  ADD COLUMN IF NOT EXISTS embedding_error text,
  ADD COLUMN IF NOT EXISTS embedded_at timestamptz;