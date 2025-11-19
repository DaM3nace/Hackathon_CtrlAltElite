# Knowledge Base Chatbot with RAG

A powerful chatbot that uses Retrieval-Augmented Generation (RAG) to answer questions based on your document collection. This version uses local storage with semantic search to provide intelligent responses. Supports multiple document formats including PDF, Word, Excel, text, and markdown files.

**Status:** ✅ Working with local vector storage (PyPDF2, sentence-transformers)

## Features

- **Multi-format document processing**: PDF, DOCX, DOC, TXT, MD, XLSX, XLS
- **Vector similarity search**: Using sentence transformers for semantic search
- **Conversation logging**: All interactions logged with metadata
- **Databricks export**: Export conversation data to DG-prefixed tables for reporting
- **Multiple interfaces**: Web UI, REST API, CLI with session management
- **Intelligent chunking**: Optimized text splitting with overlap
- **Source attribution**: Track which documents provided each answer
- **Performance metrics**: Response times and usage analytics

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install sentence-transformers fastapi uvicorn python-docx openpyxl pandas python-multipart python-dotenv tiktoken PyPDF2
   ```

2. **Add documents to knowledge base**:
   - Place your documents in the `SOP/` directory  
   - Run: ```bash
   python main.py update
   ```

3. **Run the chatbot**:
   ```bash
   # Web interface (recommended) 🌐
   python main.py web
   # Then open: http://127.0.0.1:8000
   
   # Command line chat
   python main.py chat
   
   # Quick demo
   python demo.py
   
   # Alternative web starter
   python start_web_chat.py
   ```

## Working Commands

- `python main.py update` - Process documents from SOP directory
- `python main.py web` - Start web chat interface at http://127.0.0.1:8000
- `python main.py chat` - Interactive Q&A session  
- `python main.py export-databricks` - Export conversation data for Databricks
- `python demo.py` - See example questions and answers
- `python start_web_chat.py` - Start web chat with auto-open browser
- `python test_conversation_logging.py` - Test conversation logging & export

## Usage Examples

### Web Interface
The Streamlit web app provides an intuitive chat interface with:
- Real-time document processing
- Knowledge base statistics
- Source document display
- Chat history

### Command Line Chat
```bash
python main.py chat
> What is the main topic of the research papers?
🤖 Answer: Based on the uploaded documents, the main research focus appears to be...
📄 Sources: paper1.pdf, research_notes.docx
```

### REST API
```bash
# Start the API server
python main.py api

# Query via curl
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{"query": "What are the key findings?", "top_k": 5}'
```

## Architecture

```
Documents → Document Processor → Text Chunking → Embeddings → Databricks
     ↓                                                            ↓
User Query → Embedding → Vector Search → Context → LLM → Response
```

### Components

- **DocumentProcessor**: Extracts text from various file formats
- **TextProcessor**: Chunks text and generates embeddings
- **DatabricksConnector**: Manages vector storage and retrieval
- **RAGSystem**: Orchestrates the retrieval-augmented generation
- **Interfaces**: Web app, API, and CLI for user interaction

## Configuration

### Environment Variables
- `DATABRICKS_SERVER_HOSTNAME`: Your Databricks workspace URL
- `DATABRICKS_HTTP_PATH`: SQL warehouse HTTP path
- `DATABRICKS_TOKEN`: Personal access token
- `DATABRICKS_CATALOG`: Catalog name (default: main)
- `DATABRICKS_SCHEMA`: Schema name (default: default)
- `OPENAI_API_KEY`: OpenAI API key for response generation
- `CHUNK_SIZE`: Text chunk size in tokens (default: 512)
- `CHUNK_OVERLAP`: Overlap between chunks (default: 50)

### Supported File Formats
- **PDF**: `.pdf` - Extracted using PyMuPDF
- **Word**: `.docx`, `.doc` - Processed with python-docx
- **Excel**: `.xlsx`, `.xls` - Converted to text with pandas
- **Text**: `.txt`, `.md` - Direct text processing

## Databricks Integration

### Conversation Storage & Reporting

The system automatically logs all conversations with:
- **Session tracking**: Unique session IDs for user journey analysis
- **Performance metrics**: Response times and query complexity
- **Source attribution**: Which documents contributed to each response
- **User analytics**: Usage patterns and engagement metrics

### DG-Prefixed Tables

All Databricks tables use the **DG** prefix for easy identification:

- **`DG_CONVERSATIONS`**: Main conversation records with queries, responses, and metadata
- **`DG_CONVERSATION_SOURCES`**: Source documents and similarity scores per response  
- **`DG_CONVERSATION_METRICS`**: Aggregated metrics for reporting and analytics

### Export & Import Process

1. **Export conversations**: `python main.py export-databricks`
2. **Upload to Databricks**: Copy the generated package to your Databricks workspace
3. **Create tables**: Run `01_create_tables.sql` 
4. **Import data**: Use CSV files or run `02_insert_data.sql`
5. **Analytics**: Execute pre-built queries from `03_reporting_queries.sql`

### Built-in Reports

- Daily conversation volume and trends
- Most frequently asked questions
- Document usage and relevance analysis  
- User engagement patterns
- Performance metrics and response times
- Session analysis and user journeys

## API Endpoints

- `GET /`: Service status
- `GET /health`: Health check
- `POST /query`: Ask a question
- `GET /stats`: Knowledge base statistics
- `POST /export-databricks`: Export conversation data
- `POST /update-knowledge-base`: Process new documents
- `POST /upload-documents`: Upload files directly

## Databricks Setup

1. Create a SQL warehouse in your Databricks workspace
2. Generate a personal access token
3. The system will automatically create the vector table:
   ```sql
   CREATE TABLE knowledge_base_vectors (
       chunk_id STRING,
       content STRING,
       embedding ARRAY<DOUBLE>,
       file_name STRING,
       file_path STRING,
       file_extension STRING,
       token_count INT,
       created_at TIMESTAMP
   )
   ```

## Security Considerations

- Store credentials securely in `.env` file (never commit to version control)
- Use Databricks personal access tokens with minimal required permissions
- Consider network security for production deployments
- Validate and sanitize file uploads

## Troubleshooting

### Common Issues

1. **Connection errors**: Check Databricks credentials and network connectivity
2. **Empty responses**: Verify documents were processed and embeddings generated
3. **Memory issues**: Reduce chunk size or process documents in batches
4. **File format errors**: Ensure documents are not corrupted

### Debugging
Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details