# --- DNK-MRH-HEADER ---
# mrh_id: "skills/openwiki_assimilated/scripts/wiki_sync.py"
# purpose: "Python port of OpenWiki markdown index-sync and frontmatter parser"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# --- END DNK-MRH-HEADER ---

import os
import re
import yaml

class OpenWikiSync:
    """
    Python-based port of OpenWiki indexing and sync logic.
    Provides wiki-graph memory indexing and markdown frontmatter synchronization.
    """
    @staticmethod
    def parse_frontmatter(content: str):
        match = re.match(r'^---\\s*\\n(.*?)\\n---\\s*\\n(.*)', content, re.DOTALL)
        if not match:
            return {}, content
        try:
            fields = yaml.safe_load(match.group(1))
            return fields or {}, match.group(2)
        except Exception:
            return {}, content

    @staticmethod
    def render_frontmatter(fields: dict) -> str:
        yaml_content = yaml.safe_dump(fields, default_flow_style=False)
        return f"---\\n{yaml_content}---\\n\\n"

    @classmethod
    def sync_directory(cls, dir_path: str):
        if not os.path.exists(dir_path):
            return
        files = []
        for item in sorted(os.listdir(dir_path)):
            if item.endswith('.md') and item != 'index.md':
                full_path = os.path.join(dir_path, item)
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                fields, _ = cls.parse_frontmatter(content)
                title = fields.get('title', item[:-3].replace('-', ' ').title())
                description = fields.get('description', 'No description.')
                files.append({"filename": item, "title": title, "description": description})
        
        index_content = f"# 📂 Wiki Index\\n\\n"
        for f_info in files:
            index_content += f"- [{f_info['title']}]({f_info['filename']}) - {f_info['description']}\\n"
            
        index_path = os.path.join(dir_path, 'index.md')
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_content)
        print(f"Synchronized index at {index_path}")
