
import argparse
import json
import os
import re
from typing import Any, Callable, Dict, List, Sequence, Optional
import chromadb
from llama_index.core.schema import TextNode
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import (
    StorageContext, 
    VectorStoreIndex,
)

def splite_workflows(text: str) -> List[str]:
    pattern = r'(\d+\..+?)(?=\n\d+\.|$)'
    workflows = re.findall(pattern, text, re.DOTALL)
    clear_pattern = r'^\d+\.\s*'
    cleaned_workflows = [re.sub(clear_pattern, '', workflow).strip() for workflow in workflows]
    tasks = [re.match(r'^(.*)', item).group(1) for item in cleaned_workflows]
    return tasks, cleaned_workflows

def create_nodes(website, tasks):
    return [
        TextNode(
            text=task,
            metadata={
                "website": website,
                "index": idx,
            },
        )
        for idx, task in enumerate(tasks)
    ]

def extract_single(workflow_path):
    with open(workflow_path, 'r', encoding='utf-8') as f:
        workflow_text = f.read()

    website = os.path.splitext(os.path.basename(workflow_path))[0]
    tasks, cleaned_workflows = splite_workflows(workflow_text)
    nodes = create_nodes(website, tasks)
    return website, cleaned_workflows, nodes

def main(use_openai_embedding: bool, embedding_model_name: str):
    os.makedirs("memory/db/", exist_ok=True)
    chromadb_path = "memory/db/chroma_db"
    chromadb_collection_name = "workflow"
    workflow_path = "memory/workflow"
    workflow_mapping_path = "memory/db/workflow_mapping.json"
    vector_store_config_path = "memory/db/vector_store_config.json"

    workflow_paths = []
    for root, dirs, files in os.walk(workflow_path):
        for file in files:
            workflow_paths.append(os.path.join(root, file))

    workflow_mapping = {}
    all_nodes = []
    for workflow_path in workflow_paths:
        website, cleaned_workflows, nodes = extract_single(workflow_path)
        workflow_mapping[website] = cleaned_workflows
        all_nodes.extend(nodes)

    with open(workflow_mapping_path, 'w', encoding='utf-8') as f:
        json.dump(workflow_mapping, f)

    if use_openai_embedding:
        from llama_index.embeddings.openai import OpenAIEmbedding
        embed_model = OpenAIEmbedding(model=embedding_model_name)
    else:
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
        embed_model = HuggingFaceEmbedding(model_name=embedding_model_name)

    vector_store_config = {
        'use_openai_embedding': use_openai_embedding,
        'embedding_model_name': embedding_model_name,
    }
    with open(vector_store_config_path, 'w', encoding='utf-8') as f:
        json.dump(vector_store_config, f)

    db = chromadb.PersistentClient(path=chromadb_path)
    chroma_collection = db.get_or_create_collection(chromadb_collection_name)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    VectorStoreIndex(all_nodes, embed_model=embed_model, storage_context=storage_context)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--use_openai_embedding", type=bool, default=False,
                        help="Use openai embedding model")
    parser.add_argument("--embedding_model_name", type=str, default="BAAI/bge-large-en-v1.5",
                        help="Eembedding model name")
    args = parser.parse_args()
    main(args.use_openai_embedding, args.embedding_model_name)