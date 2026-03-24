"""
CLI tool to index knowledge base documents into Pinecone.

Usage:
    python -m tools.legal_receptionist.ingest
    python -m tools.legal_receptionist.ingest --dir path/to/docs
    python -m tools.legal_receptionist.ingest --reset  (delete + re-index)
"""

import argparse
import os
import sys

# Ensure project root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from dotenv import load_dotenv
load_dotenv()

from tools.legal_receptionist.rag import ingest_directory, delete_namespace, ensure_index
from tools.legal_receptionist.config import PINECONE_NAMESPACE

DEFAULT_KNOWLEDGE_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "knowledge")
)


def main():
    parser = argparse.ArgumentParser(description="Index legal knowledge base into Pinecone")
    parser.add_argument("--dir", default=DEFAULT_KNOWLEDGE_DIR, help="Directory of markdown docs to index")
    parser.add_argument("--reset", action="store_true", help="Delete existing vectors before indexing")
    parser.add_argument("--namespace", default=PINECONE_NAMESPACE, help="Pinecone namespace")
    args = parser.parse_args()

    if not os.path.isdir(args.dir):
        print(f"Error: Directory not found: {args.dir}")
        sys.exit(1)

    print(f"Legal Receptionist — Knowledge Base Ingestion")
    print(f"  Directory: {args.dir}")
    print(f"  Namespace: {args.namespace}")
    print()

    # Ensure index exists
    print("Ensuring Pinecone index exists...")
    ensure_index()

    if args.reset:
        print("Resetting namespace...")
        delete_namespace(args.namespace)

    print("Indexing documents...")
    total = ingest_directory(args.dir, namespace=args.namespace)
    print(f"\nDone. {total} chunks indexed.")


if __name__ == "__main__":
    main()
