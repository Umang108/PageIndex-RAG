# PageIndex RAG: Hierarchical Document Understanding with LLMs

A **Retrieval-Augmented Generation (RAG)** system powered by **PageIndex** for intelligent document querying using hierarchical tree-based document understanding and Azure OpenAI.

## 📋 Table of Contents

- [Overview](#overview)
- [Key Concepts](#key-concepts)
- [Architecture](#architecture)
- [vs. Traditional RAG](#comparison-with-traditional-rag)
- [Setup](#setup)
- [Usage](#usage)
- [Project Structure](#project-structure)

---

## Overview

This project implements a **semantic RAG pipeline** that leverages PageIndex's hierarchical document processing to:

1. **Parse PDFs intelligently** - Convert documents into structured hierarchical trees with parent-child relationships
2. **Reason over structure** - Use LLMs to intelligently select relevant document sections based on semantic understanding
3. **Retrieve with context** - Pull text from optimal document nodes while maintaining parent-child relationships
4. **Generate accurate answers** - Combine selected context with LLM reasoning for grounded, accurate responses

**Key Innovation**: Instead of simple text chunking + vector similarity, this system uses **intelligent hierarchical reasoning** to understand document structure and select relevant information at the right abstraction level.

---

## Key Concepts

### 1. **PageIndex Client**

A service that processes PDF documents and creates a hierarchical tree representation:

- Automatically structures documents into logical sections
- Creates parent-child relationships between sections
- Provides node IDs and titles for each section
- Returns text content for each node

### 2. **Document Tree Structure**

Instead of flat chunks, documents are represented as trees:

```
Document
├── Chapter 1
│   ├── Section 1.1
│   │   ├── Subsection 1.1.1
│   │   └── Subsection 1.1.2
│   └── Section 1.2
├── Chapter 2
│   └── Section 2.1
└── Conclusions
```

Each node contains:

- `node_id` - Unique identifier
- `title` - Node title/heading
- `text` - Content (can be single string or list of paragraphs)
- `children` - Child nodes

### 3. **Two-Stage LLM Reasoning**

#### Stage 1: Tree Search (Semantic Reasoning)

- LLM analyzes the **tree structure** without full text
- Reasons about which nodes are likely relevant to the query
- Returns a list of node IDs to retrieve
- This is **fast** because it only processes the tree structure summary

**Prompt includes**: Query + Document tree structure

**Output**: `{"thinking": "...", "node_list": ["node_1", "node_3", ...]}`

#### Stage 2: Answer Generation

- Retrieves full text from selected nodes
- LLM generates final answer using the combined context
- Maintains node ID references for transparency

**Prompt includes**: Query + Full context from selected nodes

**Output**: Grounded answer with node citations

### 4. **Node Mapping**

A utility that creates a dictionary mapping node IDs to full node objects for quick lookup.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                          USER QUERY                         │
│                    "What are conclusions?"                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │  1. PDF Submission (PageIndex)     │
        │  - Upload & Process Document      │
        │  - Generate Hierarchical Tree     │
        └────────────────┬───────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │  2. Tree Search (LLM Reasoning)    │
        │  - Analyze tree structure         │
        │  - Select relevant nodes          │
        │  - Output: node_list              │
        └────────────────┬───────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │  3. Node Retrieval                 │
        │  - Fetch text from selected nodes │
        │  - Build context from node_list   │
        └────────────────┬───────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │  4. Answer Generation (LLM)        │
        │  - Generate grounded answer       │
        │  - Cite node IDs used             │
        └────────────────┬───────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │      Final Grounded Answer         │
        └────────────────────────────────────┘
```

---

## Comparison with Traditional RAG

### Traditional RAG Pipeline

```
PDF → Text Chunking → Embedding → Vector DB → Vector Similarity Search → LLM
```

**Characteristics:**

- Uses **fixed-size chunking** (e.g., 512 tokens) or sliding windows
- Converts chunks to **embeddings** to measure semantic similarity
- Retrieves top-k most similar chunks regardless of document structure
- Often loses context about what chunks belong to which sections
- May retrieve redundant or incomplete information

**Limitations:**

- ❌ No awareness of document hierarchy
- ❌ Chunks can be split across logical boundaries
- ❌ Expensive embedding computation for all chunks
- ❌ Can retrieve content from multiple unrelated sections
- ❌ Difficulty handling multi-scale queries (high-level vs. detailed)

---

### PageIndex RAG Pipeline

```
PDF → Intelligent Parsing (PageIndex) → Hierarchical Tree → LLM Tree Reasoning → Targeted Retrieval → LLM Answer
```

**Characteristics:**

- Uses **intelligent document parsing** to understand structure
- Creates **hierarchical representation** with parent-child relationships
- LLM reasons over **tree structure** (no embedding needed)
- Retrieves **complete sections** with full context
- Respects document boundaries and logical grouping

**Advantages:**

- ✅ Leverages document structure/hierarchy
- ✅ Full context for selected sections
- ✅ No embedding model required (cost savings)
- ✅ Intelligent section selection at right abstraction level
- ✅ Faster reasoning over tree vs. all chunks
- ✅ Transparent node-based citation
- ✅ Handles multi-scale information (from summary to details)

---

### Comparison Table

| Aspect                   | Traditional RAG                    | PageIndex RAG                            |
| ------------------------ | ---------------------------------- | ---------------------------------------- |
| **Document Parsing**     | Simple text extraction             | Intelligent hierarchical parsing         |
| **Structure Awareness**  | None                               | Full hierarchical understanding          |
| **Retrieval Method**     | Vector similarity (embeddings)     | LLM reasoning over tree structure        |
| **Chunk References**     | Unnamed chunks                     | Named nodes with IDs and titles          |
| **Context Preservation** | Often lost at chunk boundaries     | Maintained via parent-child links        |
| **Scalability**          | O(n) embeddings for n chunks       | O(tree size) for reasoning               |
| **Citation Quality**     | Chunk references                   | Semantic node references                 |
| **Multi-level Queries**  | Difficult                          | Natural (tree structure provides levels) |
| **Embedding Vector DB**  | ✅ Required                        | ❌ Not required                          |
| **Cost**                 | Higher (embedding model + storage) | Lower (LLM only)                         |

---

## Setup

### Prerequisites

- Python 3.12+
- Azure OpenAI API access
- PageIndex API key and account
- A PDF file to process

### Installation

1. **Clone or navigate to the project**

   ```bash
   cd d:\TCS_Work\pageindex_rag
   ```

2. **Install UV (Python package manager)**

   ```bash
   pip install uv
   ```

3. **Install dependencies**
   ```bash
   uv sync
   ```
   This installs:
   - `langchain` - LLM framework
   - `langchain-openai` - Azure OpenAI integration
   - `pageindex` - Document parsing and tree generation
   - `python-dotenv` - Environment variable management
   - `requests` - HTTP client

### Environment Configuration

Create a `.env` file in the project root:

```env
# PageIndex API Configuration
PAGEINDEX_API_KEY=your_pageindex_api_key_here

# Azure OpenAI Configuration
AZURE_OPENAI_DEPLOYMENT=
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_API_KEY=your_azure_openai_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
```

**Getting API Keys:**

- **PageIndex API Key**: Sign up at [PageIndex](https://www.pageindex.ai/) and get your API key
- **Azure OpenAI**: Create an Azure OpenAI resource and deploy a `gpt-4` or similar model

---

## Usage

### Basic Query Flow

```python
python main.py
```

The script will:

1. **Submit PDF to PageIndex**
   - Uploads your PDF document
   - Receives `doc_id` for the processing job
2. **Wait for Tree Generation**
   - Polls PageIndex until the hierarchical tree is ready
   - Times out after 5 minutes (60 × 5-second intervals)

3. **Create Node Mapping**
   - Converts tree into a dictionary for O(1) node lookup

4. **Remove Full Text from Tree**
   - Strips text content for tree reasoning
   - LLM analyzes structure only (faster, cheaper)

5. **LLM Tree Search**
   - Sends query + tree structure to Azure OpenAI
   - LLM returns list of relevant node IDs
6. **Retrieve Node Content**
   - Fetches full text from selected nodes
   - Combines into single context string

7. **Generate Answer**
   - Sends query + context to LLM
   - Receives grounded answer with node citations

### Customization

**Change the query:**

```python
query = "What are the key findings?"  # Modify this line
```

**Add error handling:**

```python
try:
    submit_resp = pi_client.submit_document(pdf_path)
except pageindex.client.PageIndexAPIError as e:
    print(f"API Error: {e}")
    # Handle rate limit, quota, etc.
```

**Adjust LLM parameters:**

```python
llm = AzureChatOpenAI(
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    temperature=0.3,  # Adjust creativity (0 = deterministic)
    max_tokens=2000,  # Limit response length
)
```

---

## Project Structure

```
pageindex_rag/
├── main.py                 # Main RAG pipeline script
├── pyproject.toml         # Project configuration & dependencies
├── README.md              # This file
├── .env                   # Environment variables (create this)
│
└── data/                  # Output directory
    └── [downloaded files]
```

**Last Updated**: February 28, 2026
