import argparse
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent


def _run_command(command, description):
    print(f"\n[{description}]")
    print(" ".join(str(part) for part in command))
    subprocess.run(command, cwd=ROOT_DIR.parent, check=True)


def _install_requirements(python_executable):
    _run_command(
        [python_executable, "-m", "pip", "install", "-r", str(ROOT_DIR / "requirements.txt")],
        "Installing backend dependencies",
    )


def _warm_up_embedding_model():
    print("\n[Downloading / validating embedding model]")
    from utils.embedding import generate_embedding

    embedding = generate_embedding("semantic product recommendation setup")
    print(f"Embedding model ready with {len(embedding)} dimensions.")


def _create_vector_index(index_name=None):
    print("\n[Creating MongoDB Atlas vector index]")
    from agents.recommendation_agent import RecommendationAgent

    try:
        result = RecommendationAgent.create_vector_index(index_name=index_name)
        print(f"Vector index ready: {result['indexName']}")
    except Exception as exc:
        message = str(exc).lower()
        if "already exists" in message or "index already exists" in message:
            print("Vector index already exists. Skipping creation.")
            return
        raise


def _backfill_embeddings(batch_size=50, limit=None, force=False):
    print("\n[Backfilling product embeddings]")
    from agents.recommendation_agent import RecommendationAgent

    result = RecommendationAgent.backfill_product_embeddings(
        batch_size=batch_size,
        limit=limit,
        force=force,
    )
    print(
        "Processed={processed}, Updated={updated}, Skipped={skipped}".format(
            processed=result.get("processed", 0),
            updated=result.get("updated", 0),
            skipped=result.get("skipped", 0),
        )
    )


def main():
    parser = argparse.ArgumentParser(
        description="One-command setup for MongoDB Atlas vector recommendations."
    )
    parser.add_argument("--skip-install", action="store_true", help="Skip pip install -r backend/requirements.txt")
    parser.add_argument("--skip-index", action="store_true", help="Skip vector index creation")
    parser.add_argument("--skip-backfill", action="store_true", help="Skip embedding backfill")
    parser.add_argument("--force", action="store_true", help="Recompute embeddings even if they already exist")
    parser.add_argument("--batch-size", type=int, default=50, help="Batch size for embedding backfill")
    parser.add_argument("--limit", type=int, default=None, help="Optional limit for products to process")
    parser.add_argument("--index-name", default=None, help="Override Atlas vector index name")
    args = parser.parse_args()

    python_executable = sys.executable

    if not args.skip_install:
        _install_requirements(python_executable)

    _warm_up_embedding_model()

    if not args.skip_index:
        _create_vector_index(index_name=args.index_name)

    if not args.skip_backfill:
        _backfill_embeddings(
            batch_size=args.batch_size,
            limit=args.limit,
            force=args.force,
        )

    print("\nVector recommendation setup completed successfully.")


if __name__ == "__main__":
    main()
