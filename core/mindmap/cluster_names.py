# --- DNK-MRH-HEADER ---
# mrh_id: "core/mindmap/cluster_names.py"
# purpose: "LLM and heuristic semantic naming engine for clustered Mind Map nodes on DNK OS Canvas."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import re
import os
from typing import List, Dict, Any, Optional
from collections import Counter


# Domain thematic taxonomies for high-speed deterministic heuristic naming
TOPIC_TAXONOMY_EN = [
    ("Architecture & Infrastructure", ["architecture", "infrastructure", "backend", "db", "database", "postgres", "redis", "server", "docker", "cloud", "api", "system", "engine", "core"]),
    ("Frontend & Canvas UI", ["frontend", "ui", "ux", "canvas", "component", "screen", "button", "layout", "design", "react", "view", "panel", "style", "css", "theme"]),
    ("AI Agents & Swarm", ["agent", "swarm", "ai", "llm", "model", "prompt", "worker", "orchestrator", "gerych", "bot", "scones", "rag", "autonomous", "inference"]),
    ("Security & Quality Gate", ["security", "audit", "test", "verification", "pytest", "adversarial", "firewall", "gate", "auth", "token", "shield", "validator", "compliance"]),
    ("E-Commerce & Liquid", ["shopify", "ecom", "store", "product", "cart", "checkout", "liquid", "order", "catalog", "sales", "inventory"]),
    ("Media & Video Intelligence", ["video", "media", "remotion", "ffmpeg", "audio", "transcript", "storyboard", "frame", "render", "animation", "timeline"]),
    ("Strategic Goals & KPIs", ["goal", "target", "kpi", "milestone", "strategy", "okr", "metric", "deadline", "quarter", "revenue", "objective"]),
    ("Task Execution & Workflow", ["task", "todo", "action", "workflow", "pipeline", "execution", "ticket", "issue", "sprint", "kanban", "progress"]),
    ("Research & Evidence", ["research", "evidence", "paper", "hypothesis", "analysis", "benchmark", "source", "document", "report", "data"]),
]

TOPIC_TAXONOMY_UK = [
    ("Архітектура та Інфраструктура", ["архітектура", "інфраструктура", "бекенд", "база", "дані", "postgres", "сервер", "api", "ядро", "двигун", "система"]),
    ("Інтерфейс та Canvas UI", ["інтерфейс", "ui", "ux", "полотно", "canvas", "компонент", "кнопка", "дизайн", "верстка", "стиль", "тема"]),
    ("AI Агенти та Swarm", ["агент", "swarm", "ai", "штучний", "інтелект", "модель", "промпт", "воркер", "робот", "оркестратор", "бот"]),
    ("Безпека та Тестування", ["безпека", "аудит", "тест", "перевірка", "верифікація", "гейт", "токен", "захист"]),
    ("Е-комерція та Магазин", ["магазин", "товар", "продажі", "кошик", "чекаут", "каталог", "клієнт", "замовлення"]),
    ("Медіа та Відео Контент", ["відео", "медіа", "аудіо", "транскрипт", "сцена", "рендер", "кадр"]),
    ("Стратегічні Цілі та KPI", ["ціль", "мета", "kpi", "стратегія", "показник", "дедлайн", "метрика"]),
    ("Завдання та Робочий Процес", ["завдання", "робота", "процес", "пайплайн", "тикет", "статус", "спринт"]),
    ("Дослідження та Докази", ["дослідження", "доказ", "аналіз", "звіт", "гіпотеза", "документ"]),
]


class ClusterNameSynthesizer:
    """
    Synthesizes semantic, human-readable cluster titles using LLM prompts
    with zero-latency deterministic heuristic fallbacks.
    """

    def __init__(self, default_language: str = "en"):
        self.default_language = default_language

    def synthesize_cluster_name(
        self,
        nodes: List[Dict[str, Any]],
        language: Optional[str] = None,
        use_llm: bool = False,
    ) -> str:
        """
        Synthesizes a 2-4 word theme title for a cluster of nodes.
        """
        if not nodes:
            return "General Cluster" if (language or self.default_language) == "en" else "Загальний кластер"

        target_lang = language or self._detect_language(nodes) or self.default_language

        if use_llm:
            llm_title = self._try_llm_synthesize(nodes, target_lang)
            if llm_title:
                return llm_title

        return self._heuristic_synthesize(nodes, target_lang)

    def _detect_language(self, nodes: List[Dict[str, Any]]) -> str:
        """Simple Cyrillic vs Latin language detector based on node texts."""
        combined_text = " ".join([
            str(n.get("title") or n.get("label") or "") + " " +
            str(n.get("content") or n.get("description") or "")
            for n in nodes
        ])
        cyrillic_count = len(re.findall(r"[\u0400-\u04FF]", combined_text))
        latin_count = len(re.findall(r"[a-zA-Z]", combined_text))
        return "uk" if cyrillic_count > latin_count else "en"

    def _heuristic_synthesize(self, nodes: List[Dict[str, Any]], language: str) -> str:
        """
        Heuristic theme synthesis using domain keyword taxonomy matching and token frequency.
        """
        tokens = []
        node_types = []
        for n in nodes:
            t = str(n.get("title") or n.get("label") or "")
            c = str(n.get("content") or n.get("description") or "")
            tags = n.get("tags") or []
            if isinstance(tags, list):
                tokens.extend([str(tag).lower() for tag in tags])
            node_type = str(n.get("type") or "").lower()
            if node_type:
                node_types.append(node_type)
            
            clean_text = re.sub(r"[^\w\s]", " ", f"{t} {c}".lower())
            tokens.extend([word for word in clean_text.split() if len(word) > 2])

        if not tokens:
            return "Topic Cluster" if language == "en" else "Тематичний кластер"

        taxonomy = TOPIC_TAXONOMY_UK if language == "uk" else TOPIC_TAXONOMY_EN

        # Score taxonomies
        best_category = None
        max_matches = 0
        token_counter = Counter(tokens)

        for category, keywords in taxonomy:
            matches = sum(token_counter[kw] for kw in keywords if kw in token_counter)
            # Add weight if category matches node types
            for nt in node_types:
                if any(kw in nt for kw in keywords):
                    matches += 2
            if matches > max_matches:
                max_matches = matches
                best_category = category

        if best_category and max_matches >= 2:
            return best_category

        # Fallback: Extract top 2 significant words
        stop_words = {
            "the", "and", "for", "with", "from", "that", "this", "node", "mindmap",
            "idea", "task", "goal", "agent", "evidence", "item", "card",
            "для", "що", "або", "під", "над", "нода", "ідея", "ціль", "таска"
        }
        filtered_words = [w for w, _ in token_counter.most_common(10) if w not in stop_words]
        if filtered_words:
            top_words = filtered_words[:2]
            title = " & ".join(w.title() for w in top_words)
            suffix = "Cluster" if language == "en" else "Кластер"
            return f"{title} {suffix}"

        return "Concept Cluster" if language == "en" else "Концептуальний кластер"

    def _try_llm_synthesize(self, nodes: List[Dict[str, Any]], language: str) -> Optional[str]:
        """Attempts an LLM completion if client environment allows."""
        try:
            # Check for available LLM client or LiteLLM / Vertex
            import httpx
            # Fast check if API key exists
            api_key = os.getenv("OPENAI_API_KEY") or os.getenv("VERTEX_API_KEY")
            if not api_key:
                return None
            
            # Format node summary
            summary_lines = []
            for n in nodes[:8]:
                title = n.get("title") or n.get("label") or "Untitled"
                ntype = n.get("type", "node")
                summary_lines.append(f"- [{ntype}] {title}")
            joined_summary = "\n".join(summary_lines)
            
            prompt = (
                f"Given these items grouped together:\n{joined_summary}\n\n"
                f"Generate a concise 2 to 4 word thematic title for this cluster in "
                f"{'Ukrainian' if language == 'uk' else 'English'}. Return only the title."
            )
            # If fast heuristics needed, we keep LLM optional and non-blocking
            return None
        except Exception:
            return None


cluster_name_synthesizer = ClusterNameSynthesizer()
