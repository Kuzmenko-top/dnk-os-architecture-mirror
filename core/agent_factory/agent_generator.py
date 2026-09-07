# --- DNK-MRH-HEADER ---
# mrh_id: "core/agent_factory/agent_generator.py"
# purpose: "Automated Agent Generator instantiating new Swarm Agents from canonical agent_template."
# canonical_source: true
# alters_files: ["core/agent_factory/agents/*"]
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-07"
# --- END DNK-MRH-HEADER ---

import os
import argparse
from typing import Optional


def create_agent(agent_id: str, name: str, role: str, specialty: str) -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(base_dir, "templates", "agent_template")
    agents_dir = os.path.join(base_dir, "agents")
    target_agent_dir = os.path.join(agents_dir, agent_id)

    os.makedirs(os.path.join(target_agent_dir, "skills"), exist_ok=True)
    os.makedirs(os.path.join(target_agent_dir, "memory"), exist_ok=True)

    # Read templates
    with open(os.path.join(templates_dir, "SOUL.md"), "r", encoding="utf-8") as f:
        soul_template = f.read()

    with open(os.path.join(templates_dir, "MANIFEST.yaml"), "r", encoding="utf-8") as f:
        manifest_template = f.read()

    # Replace placeholders
    soul_content = (
        soul_template.replace("{{AGENT_NAME}}", name)
        .replace("{{AGENT_ROLE}}", role)
        .replace("{{AGENT_SPECIALTY}}", specialty)
    )

    manifest_content = (
        manifest_template.replace("{{agent_id}}", agent_id)
        .replace("{{agent_name}}", name)
        .replace("{{agent_role}}", role)
    )

    # Write target files
    soul_path = os.path.join(target_agent_dir, "SOUL.md")
    manifest_path = os.path.join(target_agent_dir, "MANIFEST.yaml")

    with open(soul_path, "w", encoding="utf-8") as f:
        f.write(soul_content)

    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write(manifest_content)

    print(f"✅ [Agent Factory] Створено нового агента `{name}` ({agent_id}) у `{target_agent_dir}`!")
    return target_agent_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="DNK OS Agent Factory Generator")
    parser.add_argument("--id", type=str, required=True, help="Agent unique ID (e.g. agent_rick)")
    parser.add_argument("--name", type=str, required=True, help="Agent display name (e.g. Rick)")
    parser.add_argument("--role", type=str, required=True, help="Agent role description")
    parser.add_argument("--specialty", type=str, default="General Development", help="Agent specialty")

    args = parser.parse_args()
    create_agent(agent_id=args.id, name=args.name, role=args.role, specialty=args.specialty)


if __name__ == "__main__":
    main()
