# --- DNK-MRH-HEADER ---
# mrh_id: "services_dnk_git_research_cli"
# purpose: "CLI Interface for GitHub Research, Audit & SOTA Assimilation in DNK OS"
# author: "DNK-e.com Maksym"
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-09-02"
# --- END DNK-MRH-HEADER ---

import sys
import argparse
from pathlib import Path

HUB_ROOT = Path(__file__).resolve().parents[2]
if str(HUB_ROOT) not in sys.path:
    sys.path.insert(0, str(HUB_ROOT))

from services.dnk_git_research.src.git_researcher import GitResearchEngine


def main():
    parser = argparse.ArgumentParser(description="DNK OS GitHub Researcher & Assimilator CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Search Command
    search_parser = subparsers.add_parser("search", help="Search GitHub for agentic / open-source repositories")
    search_parser.add_argument("query", type=str, help="Search query (e.g. 'agentic workflow', 'spatial canvas')")
    search_parser.add_argument("--limit", type=int, default=5, help="Number of results (default: 5)")
    search_parser.add_argument("--sort", type=str, default="stars", help="Sort order (stars, updated)")

    # Assimilate Command
    assimilate_parser = subparsers.add_parser("assimilate", help="Audit and assimilate a repository into DNK OS")
    assimilate_parser.add_argument("repo", type=str, help="Repository owner/name (e.g. 'langchain-ai/langgraph')")
    assimilate_parser.add_argument("--context", type=str, default="core/orchestrator", help="Target DNK bounded context")

    args = parser.parse_args()

    engine = GitResearchEngine()

    if args.command == "search":
        print(f"\n🔍 Searching GitHub for: '{args.query}' (Limit: {args.limit})...\n")
        results = engine.search_repositories(args.query, sort=args.sort, limit=args.limit)
        
        if not results:
            print("No matching repositories found.")
            return

        for idx, r in enumerate(results, 1):
            audit = engine.audit_and_classify(r)
            print(f"[{idx}] 📦 {r['full_name']} ({r['stars']:,} ⭐)")
            print(f"    📝 Description: {r['description'][:100]}...")
            print(f"    ⚖️  License: {r['license']} | 🏷️  Mode: {audit['assimilation_level']}")
            print(f"    💡 Reason: {audit['classification_reason']}")
            print(f"    🔗 URL: {r['url']}\n")

    elif args.command == "assimilate":
        print(f"\n🧬 Auditing & Assimilating: {args.repo} into '{args.context}'...")
        results = engine.search_repositories(args.repo, limit=1)
        if not results:
            repo_meta = {
                "full_name": args.repo,
                "name": args.repo.split("/")[-1],
                "stars": 0,
                "license": "MIT",
                "description": f"Manually assimilated repository {args.repo}",
                "url": f"https://github.com/{args.repo}"
            }
        else:
            repo_meta = results[0]

        spec_path = engine.assimilate_into_dnk(repo_meta, target_context=args.context)
        print(f"✅ Assimilation Spec created at: {spec_path}")
        print(f"✨ Registered into DNK OS SOTA Knowledge Base.\n")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
