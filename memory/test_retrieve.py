import argparse
import json
import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import VectorStoreIndex
from llama_index.core.vector_stores import (
    MetadataFilter,
    MetadataFilters,
    FilterOperator,
)

from memory.workflow_memory import WorkflowMemory

def main(website: str, task: str):
    memory = WorkflowMemory()
    memory.setup(website=website)
    memory_txt = memory.retrieve(task)
    print(memory_txt)
    
if __name__ == '__main__':
    main('aa', 'find a flight for two')
 