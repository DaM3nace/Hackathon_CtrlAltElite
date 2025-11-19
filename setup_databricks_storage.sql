-- ============================================================================
-- DATABRICKS STORAGE SETUP FOR DOCUMENTS AND CHUNKS
-- ============================================================================
-- Purpose: Create tables to store documents, chunks, and vectors in Databricks
-- Database: hackathon.hackathon_ctrl_alt_elite
-- ============================================================================

USE CATALOG hackathon;
USE SCHEMA hackathon_ctrl_alt_elite;

-- ============================================================================
-- TABLE 1: DG_DOCUMENTS
-- Stores original documents and metadata
-- ============================================================================

DROP TABLE IF EXISTS hackathon.hackathon_ctrl_alt_elite.DG_DOCUMENTS;

CREATE TABLE hackathon.hackathon_ctrl_alt_elite.DG_DOCUMENTS (
    document_id STRING NOT NULL COMMENT 'Unique identifier for document',
    file_name STRING NOT NULL COMMENT 'Original file name',
    file_path STRING COMMENT 'Original file path',
    file_extension STRING COMMENT 'File extension (.pdf, .docx, etc)',
    file_size BIGINT COMMENT 'File size in bytes',
    content STRING COMMENT 'Full document content',
    content_hash STRING COMMENT 'SHA-256 hash of content for deduplication',
    upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP() COMMENT 'When document was uploaded',
    last_processed TIMESTAMP COMMENT 'When document was last processed into chunks',
    status STRING DEFAULT 'active' COMMENT 'active, archived, deleted',
    metadata STRING COMMENT 'JSON metadata (author, tags, etc)',

    CONSTRAINT pk_documents PRIMARY KEY (document_id)
)
COMMENT 'Stores original documents and their metadata'
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
);

-- ============================================================================
-- TABLE 2: DG_CHUNKS
-- Stores document chunks with embeddings
-- ============================================================================

DROP TABLE IF EXISTS hackathon.hackathon_ctrl_alt_elite.DG_CHUNKS;

CREATE TABLE hackathon.hackathon_ctrl_alt_elite.DG_CHUNKS (
    chunk_id STRING NOT NULL COMMENT 'Unique identifier for chunk',
    document_id STRING NOT NULL COMMENT 'Reference to parent document',
    chunk_index INT NOT NULL COMMENT 'Order of chunk within document (0-based)',
    content STRING NOT NULL COMMENT 'Chunk text content',
    content_length INT COMMENT 'Length in characters',
    token_count INT COMMENT 'Number of tokens',

    -- Embedding vector (stored as string, converted to/from array)
    embedding STRING COMMENT 'Embedding vector as JSON array',
    embedding_model STRING COMMENT 'Model used for embedding (e.g., all-MiniLM-L6-v2)',
    embedding_dimension INT COMMENT 'Dimension of embedding vector',

    -- Chunk settings
    chunk_size INT COMMENT 'Target chunk size in tokens',
    chunk_overlap INT COMMENT 'Overlap with adjacent chunks in tokens',

    -- Timestamps
    created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP() COMMENT 'When chunk was created',
    updated_timestamp TIMESTAMP COMMENT 'When chunk was last updated',

    -- Metadata from parent document
    file_name STRING COMMENT 'Parent document file name',
    file_extension STRING COMMENT 'Parent document file extension',

    -- Additional metadata
    metadata STRING COMMENT 'JSON metadata',

    CONSTRAINT pk_chunks PRIMARY KEY (chunk_id)
)
COMMENT 'Stores document chunks with embeddings for vector search'
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
);

-- ============================================================================
-- TABLE 3: DG_VECTORS (Optimized for Vector Search)
-- Denormalized table for fast vector similarity search
-- ============================================================================

DROP TABLE IF EXISTS hackathon.hackathon_ctrl_alt_elite.DG_VECTORS;

CREATE TABLE hackathon.hackathon_ctrl_alt_elite.DG_VECTORS (
    vector_id STRING NOT NULL COMMENT 'Unique identifier (same as chunk_id)',
    chunk_id STRING NOT NULL COMMENT 'Reference to chunk',
    document_id STRING NOT NULL COMMENT 'Reference to document',

    -- Content for retrieval
    content STRING NOT NULL COMMENT 'Chunk content',

    -- Vector for similarity search
    embedding STRING NOT NULL COMMENT 'Embedding vector as JSON array',
    embedding_dimension INT COMMENT 'Vector dimension',

    -- Metadata for filtering
    file_name STRING COMMENT 'Document file name',
    file_extension STRING COMMENT 'File extension',
    token_count INT COMMENT 'Token count',

    -- Timestamps
    created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP() COMMENT 'Creation timestamp',

    CONSTRAINT pk_vectors PRIMARY KEY (vector_id)
)
COMMENT 'Optimized table for vector similarity search'
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Index on DG_DOCUMENTS
CREATE INDEX idx_documents_filename
ON hackathon.hackathon_ctrl_alt_elite.DG_DOCUMENTS (file_name);

CREATE INDEX idx_documents_status
ON hackathon.hackathon_ctrl_alt_elite.DG_DOCUMENTS (status);

CREATE INDEX idx_documents_hash
ON hackathon.hackathon_ctrl_alt_elite.DG_DOCUMENTS (content_hash);

-- Index on DG_CHUNKS
CREATE INDEX idx_chunks_document
ON hackathon.hackathon_ctrl_alt_elite.DG_CHUNKS (document_id);

CREATE INDEX idx_chunks_filename
ON hackathon.hackathon_ctrl_alt_elite.DG_CHUNKS (file_name);

CREATE INDEX idx_chunks_index
ON hackathon.hackathon_ctrl_alt_elite.DG_CHUNKS (document_id, chunk_index);

-- Index on DG_VECTORS
CREATE INDEX idx_vectors_document
ON hackathon.hackathon_ctrl_alt_elite.DG_VECTORS (document_id);

CREATE INDEX idx_vectors_filename
ON hackathon.hackathon_ctrl_alt_elite.DG_VECTORS (file_name);

-- ============================================================================
-- VIEWS
-- ============================================================================

-- View: Document Summary
CREATE OR REPLACE VIEW hackathon.hackathon_ctrl_alt_elite.VW_DOCUMENT_SUMMARY AS
SELECT
    d.document_id,
    d.file_name,
    d.file_extension,
    d.file_size,
    LENGTH(d.content) as content_length,
    d.upload_timestamp,
    d.last_processed,
    d.status,
    COUNT(c.chunk_id) as chunk_count,
    AVG(c.token_count) as avg_chunk_tokens,
    MIN(c.created_timestamp) as first_chunk_created,
    MAX(c.updated_timestamp) as last_chunk_updated
FROM hackathon.hackathon_ctrl_alt_elite.DG_DOCUMENTS d
LEFT JOIN hackathon.hackathon_ctrl_alt_elite.DG_CHUNKS c
    ON d.document_id = c.document_id
WHERE d.status = 'active'
GROUP BY
    d.document_id,
    d.file_name,
    d.file_extension,
    d.file_size,
    d.content,
    d.upload_timestamp,
    d.last_processed,
    d.status;

-- View: Chunk Details with Document Info
CREATE OR REPLACE VIEW hackathon.hackathon_ctrl_alt_elite.VW_CHUNK_DETAILS AS
SELECT
    c.chunk_id,
    c.document_id,
    c.chunk_index,
    c.content,
    c.content_length,
    c.token_count,
    c.embedding_model,
    c.embedding_dimension,
    c.chunk_size,
    c.chunk_overlap,
    c.created_timestamp,
    d.file_name,
    d.file_extension,
    d.file_path,
    d.upload_timestamp as document_uploaded
FROM hackathon.hackathon_ctrl_alt_elite.DG_CHUNKS c
JOIN hackathon.hackathon_ctrl_alt_elite.DG_DOCUMENTS d
    ON c.document_id = d.document_id
WHERE d.status = 'active';

-- View: Storage Statistics
CREATE OR REPLACE VIEW hackathon.hackathon_ctrl_alt_elite.VW_STORAGE_STATS AS
SELECT
    'documents' as table_name,
    COUNT(*) as record_count,
    SUM(file_size) as total_size_bytes,
    SUM(LENGTH(content)) as total_content_length,
    COUNT(DISTINCT file_extension) as unique_extensions
FROM hackathon.hackathon_ctrl_alt_elite.DG_DOCUMENTS
WHERE status = 'active'

UNION ALL

SELECT
    'chunks' as table_name,
    COUNT(*) as record_count,
    SUM(content_length) as total_size_bytes,
    SUM(token_count) as total_content_length,
    COUNT(DISTINCT embedding_model) as unique_extensions
FROM hackathon.hackathon_ctrl_alt_elite.DG_CHUNKS

UNION ALL

SELECT
    'vectors' as table_name,
    COUNT(*) as record_count,
    SUM(LENGTH(content)) as total_size_bytes,
    SUM(token_count) as total_content_length,
    COUNT(DISTINCT embedding_dimension) as unique_extensions
FROM hackathon.hackathon_ctrl_alt_elite.DG_VECTORS;

-- ============================================================================
-- INITIAL DATA VALIDATION
-- ============================================================================

-- Check table creation
SELECT
    'Table creation complete' as status,
    (SELECT COUNT(*) FROM hackathon.hackathon_ctrl_alt_elite.DG_DOCUMENTS) as documents_count,
    (SELECT COUNT(*) FROM hackathon.hackathon_ctrl_alt_elite.DG_CHUNKS) as chunks_count,
    (SELECT COUNT(*) FROM hackathon.hackathon_ctrl_alt_elite.DG_VECTORS) as vectors_count;

-- ============================================================================
-- USAGE EXAMPLES
-- ============================================================================

-- Example 1: Insert a document
/*
INSERT INTO hackathon.hackathon_ctrl_alt_elite.DG_DOCUMENTS
(document_id, file_name, file_extension, content, content_hash, status)
VALUES
('doc_001', 'sample_policy.md', '.md', 'Document content here...',
 'abc123hash', 'active');
*/

-- Example 2: Insert chunks for a document
/*
INSERT INTO hackathon.hackathon_ctrl_alt_elite.DG_CHUNKS
(chunk_id, document_id, chunk_index, content, token_count, embedding, embedding_model)
VALUES
('chunk_001', 'doc_001', 0, 'First chunk content...', 250,
 '[0.1, 0.2, 0.3, ...]', 'all-MiniLM-L6-v2');
*/

-- Example 3: Query similar vectors (manual similarity calculation)
/*
-- Note: In production, you would use a vector database or
-- Databricks Vector Search for efficient similarity search
SELECT
    v.vector_id,
    v.file_name,
    v.content,
    v.token_count
FROM hackathon.hackathon_ctrl_alt_elite.DG_VECTORS v
WHERE v.file_name LIKE '%policy%'
ORDER BY v.created_timestamp DESC
LIMIT 5;
*/

-- Example 4: Get document summary
/*
SELECT * FROM hackathon.hackathon_ctrl_alt_elite.VW_DOCUMENT_SUMMARY
ORDER BY upload_timestamp DESC;
*/

-- ============================================================================
-- MAINTENANCE QUERIES
-- ============================================================================

-- Clean up old documents
/*
UPDATE hackathon.hackathon_ctrl_alt_elite.DG_DOCUMENTS
SET status = 'archived'
WHERE upload_timestamp < CURRENT_TIMESTAMP() - INTERVAL 90 DAYS
AND status = 'active';
*/

-- Rebuild vectors table from chunks
/*
INSERT OVERWRITE hackathon.hackathon_ctrl_alt_elite.DG_VECTORS
SELECT
    c.chunk_id as vector_id,
    c.chunk_id,
    c.document_id,
    c.content,
    c.embedding,
    c.embedding_dimension,
    c.file_name,
    c.file_extension,
    c.token_count,
    c.created_timestamp
FROM hackathon.hackathon_ctrl_alt_elite.DG_CHUNKS c
JOIN hackathon.hackathon_ctrl_alt_elite.DG_DOCUMENTS d
    ON c.document_id = d.document_id
WHERE d.status = 'active';
*/

-- ============================================================================
-- END OF SETUP
-- ============================================================================

SELECT 'Databricks storage tables created successfully!' as message;
