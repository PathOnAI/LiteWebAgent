import json
import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import VectorStoreIndex
from llama_index.core.vector_stores import (
    MetadataFilter,
    MetadataFilters,
    FilterOperator,
)

class WorkflowMemory:
    def setup(self, top_k: int = 6, website: str = None):
        self.top_k = top_k
        self.website = website

        chromadb_path = "memory/db/chroma_db"
        chromadb_collection_name = "workflow"
        workflow_mapping_path = "memory/db/workflow_mapping.json"
        vector_store_config_path = "memory/db/vector_store_config.json"

        with open(workflow_mapping_path, 'r', encoding='utf8') as f:
            self.all_cleaned_workflow = json.load(f)

        with open(vector_store_config_path, 'r', encoding='utf8') as f:
                vector_store_config = json.load(f)

        use_openai_embedding = vector_store_config['use_openai_embedding']
        embedding_model_name = vector_store_config['embedding_model_name']
        if use_openai_embedding:
            from llama_index.embeddings.openai import OpenAIEmbedding
            embed_model = OpenAIEmbedding(model=embedding_model_name)
        else:
            from llama_index.embeddings.huggingface import HuggingFaceEmbedding
            embed_model = HuggingFaceEmbedding(model_name=embedding_model_name)

        db = chromadb.PersistentClient(path=chromadb_path)
        chroma_collection = db.get_or_create_collection(chromadb_collection_name)
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        self.index = VectorStoreIndex.from_vector_store(
            vector_store,
            embed_model=embed_model,
        )

    def retrieve(self, task: str):
        filters = MetadataFilters(
            filters=[
                MetadataFilter(
                    key="website", operator=FilterOperator.EQ, value=self.website
                ),
            ]
        )
        retriever = self.index.as_retriever(
            similarity_top_k = self.top_k,
            filters=filters,
        )

        retrieved_nodes = retriever.retrieve(task)
        if len(retrieved_nodes) > 0:
            workflow_txts = [self.all_cleaned_workflow[node.metadata['website']][node.metadata['index']] for node in retrieved_nodes]
            memory_txt = '## Summary Workflows:\n'
            memory_txt = '\n\n'.join(workflow_txts)
        else:
            memory_txt = ""
        return memory_txt