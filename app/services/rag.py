"""RAG (Retrieval-Augmented Generation) service."""
import logging
import os
from typing import List, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document
from app.config import settings

logger = logging.getLogger(__name__)


class RAGService:
    """Service for RAG functionality - document indexing and retrieval."""
    
    def __init__(self):
        """Initialize RAG service."""
        self.vector_store_path = settings.vector_store_path
        self.embeddings = None
        self.vector_store = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
    
    async def initialize(self):
        """Initialize embeddings and vector store."""
        try:
            # Initialize embeddings model
            logger.info("Loading embeddings model...")
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                model_kwargs={'device': 'cpu'}
            )
            
            # Load or create vector store
            os.makedirs(self.vector_store_path, exist_ok=True)
            index_path = os.path.join(self.vector_store_path, "index")
            
            if os.path.exists(os.path.join(index_path, "index.faiss")):
                logger.info("Loading existing vector store...")
                self.vector_store = FAISS.load_local(
                    index_path,
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
            else:
                logger.info("Creating new vector store...")
                # Create with a dummy document
                dummy_doc = Document(
                    page_content="Initialization document",
                    metadata={"source": "init"}
                )
                self.vector_store = FAISS.from_documents(
                    [dummy_doc],
                    self.embeddings
                )
                self.vector_store.save_local(index_path)
            
            logger.info("RAG service initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing RAG service: {e}", exc_info=True)
            raise
    
    async def add_document(
        self,
        content: str,
        filename: str,
        metadata: Optional[dict] = None
    ) -> int:
        """
        Add a document to the vector store.
        
        Args:
            content: Document text content
            filename: Name of the file
            metadata: Additional metadata
            
        Returns:
            Number of chunks created
        """
        try:
            # Split document into chunks
            chunks = self.text_splitter.split_text(content)
            
            # Create documents with metadata
            documents = []
            for i, chunk in enumerate(chunks):
                doc_metadata = {
                    "source": filename,
                    "chunk_id": i,
                    **(metadata or {})
                }
                documents.append(Document(
                    page_content=chunk,
                    metadata=doc_metadata
                ))
            
            # Add to vector store
            self.vector_store.add_documents(documents)
            
            # Save vector store
            index_path = os.path.join(self.vector_store_path, "index")
            self.vector_store.save_local(index_path)
            
            logger.info(f"Added document '{filename}' with {len(chunks)} chunks")
            return len(chunks)
            
        except Exception as e:
            logger.error(f"Error adding document: {e}", exc_info=True)
            raise
    
    async def search(
        self,
        query: str,
        k: int = 4,
        score_threshold: float = 0.5
    ) -> List[dict]:
        """
        Search for relevant documents.
        
        Args:
            query: Search query
            k: Number of results to return
            score_threshold: Minimum relevance score
            
        Returns:
            List of relevant documents with metadata and scores
        """
        try:
            # Perform similarity search with scores
            results = self.vector_store.similarity_search_with_score(
                query,
                k=k
            )
            
            # Filter by score threshold and format results
            filtered_results = []
            for doc, score in results:
                # Note: FAISS returns distance, lower is better
                # Convert to similarity score (inverse)
                similarity = 1 / (1 + score)
                
                if similarity >= score_threshold:
                    filtered_results.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "score": similarity
                    })
            
            logger.info(f"Found {len(filtered_results)} relevant documents for query")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}", exc_info=True)
            return []
    
    async def clear_documents(self):
        """Clear all documents from the vector store."""
        try:
            # Create new empty vector store
            dummy_doc = Document(
                page_content="Initialization document",
                metadata={"source": "init"}
            )
            self.vector_store = FAISS.from_documents(
                [dummy_doc],
                self.embeddings
            )
            
            # Save empty vector store
            index_path = os.path.join(self.vector_store_path, "index")
            self.vector_store.save_local(index_path)
            
            logger.info("All documents cleared from vector store")
            
        except Exception as e:
            logger.error(f"Error clearing documents: {e}", exc_info=True)
            raise

