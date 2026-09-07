# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_node_tasks/conversational_intake.py"
# purpose: "Gerych Conversational Task & Ideas Intake Engine: extracts structured DAG nodes and edges from user chat messages"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger("dnk_node_tasks.conversational_intake")

from services.dnk_node_tasks.models import (
    NodeType,
    ExecutionStage,
    NodeStatus,
    EdgeRelation,
    NodePosition,
    NodeItem,
    DependencyEdge,
    NodeTaskGraph,
)
from services.dnk_node_tasks.graph_engine import NodeTaskGraphEngine


AGENT_ROUTING_MAP = [
    # Shopify / Ecom
    (re.compile(r"(shopify|liquid|checkout|cart|каталог|кошик|чекаут|магазин|товари)", re.I), "dnk_shopify"),
    # Video / Media / Remotion
    (re.compile(r"(video|відео|анімаці|remotion|capcut|reels|tiktok|сторіз|монтаж)", re.I), "dnk_video_ai_creator"),
    # Frontend / UI / Stitch / Canvas
    (re.compile(r"(фронтенд|інтерфейс|ui|ux|stitch|canvas|компонент|кнопк|панел|стил|дизайн|кабінет)", re.I), "gerych_builder"),
    # Quality / Audit / Tests
    (re.compile(r"(тест|pytest|аудит|перевір|security|безпек|gate|якост|валідац)", re.I), "gerych_auditor"),
    # Backend / API / Database
    (re.compile(r"(бек|backend|api|fastapi|роутер|баз|database|модел|sql|ендпоінт|server)", re.I), "dnk_dev_fullstack"),
    # Default: Gerych Prime
    (re.compile(r".*", re.I), "gerych_prime"),
]


def resolve_assigned_agent(text: str) -> str:
    """Detects the best matching swarm agent from the user message."""
    for pattern, agent in AGENT_ROUTING_MAP:
        if pattern.search(text):
            return agent
    return "gerych_prime"


def extract_priority(text: str) -> str:
    """Extracts priority from urgency keywords."""
    if re.search(r"(терміново|критично|asap|блокер|p0|негайно|важливо!)", text, re.I):
        return "critical"
    if re.search(r"(важливо|пріоритет|high|p1)", text, re.I):
        return "high"
    if re.search(r"(низький|потім|low|p3|колись)", text, re.I):
        return "low"
    return "medium"


def classify_node_type_and_stage(text: str) -> Tuple[NodeType, ExecutionStage]:
    """Determines whether the item is an Idea, Task, Epic, or Gate."""
    if re.search(r"^(ідея|idea|а що якщо|можна було б|як щодо|подумай над|концепт)", text, re.I):
        return NodeType.IDEA, ExecutionStage.IDEATION
    if re.search(r"^(епік|epic|система|великий блок|архітектура)", text, re.I):
        return NodeType.EPIC, ExecutionStage.READY
    if re.search(r"^(перевірка|тестування|аудит|гейт|gate|тест)", text, re.I):
        return NodeType.GATE, ExecutionStage.READY
    return NodeType.TASK, ExecutionStage.READY


def is_conversational_inquiry(text: str) -> bool:
    """
    Detects if a user message is an informational question, greeting, or conversational chitchat
    rather than an actionable instruction to create tasks/ideas/gates in the DAG.
    """
    raw = text.strip()
    normalized = re.sub(r"^(?:герич|herych)[\s,:—–.!?*-]+", "", raw, flags=re.I).strip()

    # Greetings
    if re.match(r"^(?:привіт|добрий день|вітаю|доброго дня|hello|hi|hey|добрий вечір|доброго ранку)[\s!.,?]*$", normalized, re.I):
        return True

    # Check for date / time queries first
    if re.search(r"\b(?:який час|котра година|напиши дату|яка дата|сьогоднішній день|яке сьогодні число)\b", normalized, re.I):
        return True

    # Explicit task creation keywords are NEVER treated as passive inquiries
    if re.match(r"^(?:ідея:|idea:|задача:|task:|епік:|epic:|гейт:|gate:|створи\b|додай\b|зроби\b|реалізуй\b|розроби\b|побудуй\b|запусти\b|перевір\b|протестуй\b|декомпозуй\b|видали\b|create\b|add\b|build\b|implement\b|test\b|make\b)", normalized, re.I):
        return False
    if re.match(r"^напиши\b", normalized, re.I) and not re.search(r"\b(?:код|тест|скрипт|документацію|модуль|компонент|функцію|воркер|ендпоінт|роут)\b", normalized, re.I):
        return True

    # Phrases asking to show, list, explain, or query nodes / status
    if re.search(r"\b(?:що за|які у нас|які є|покажи|список|перелік|розкажи|поясни|чи є|що є|який статус|стан|інфо)\b", normalized, re.I):
        return True

    # Question words at start
    if re.match(r"^(?:чому|як|що|де|хто|коли|скільки|навіщо|чи|який|яка|яке|які|підкажи|why|how|what|where|when|who)\b", normalized, re.I):
        return True

    # Question mark at the end without imperative action verbs
    if normalized.endswith("?"):
        return True

    return False


def format_conversational_reply(prompt: str, graph: NodeTaskGraph) -> str:
    """Generates an intelligent context-aware reply for informational chat messages without creating DAG nodes."""
    raw = prompt.strip()
    normalized = re.sub(r"^(?:герич|herych)[\s,:—–.!?*-]+", "", raw, flags=re.I).strip()

    if re.search(r"\b(?:який час|котра година|час|напиши дату|яка дата|число|сьогоднішній день)\b", normalized, re.I):
        try:
            from .gerych_agent_bridge import get_kyiv_time_str
            time_str = get_kyiv_time_str()
        except Exception:
            time_str = "зараз у Києві робочий час"
        return f"👋 **Герич:** Зараз {time_str}. Готовий до роботи над задачами рою!"

    if re.match(r"^(?:привіт|добрий день|вітаю|доброго дня|hello|hi|hey|добрий вечір|доброго ранку)", normalized, re.I):
        return (
            "👋 **Привіт, Максиме! Я Герич — твій AI Swarm Manager.**\n\n"
            "Я допомагаю керувати архітектурою, декомпонувати задачі та синхронізувати DAG-граф із воркерами. "
            "Опиши нову ідею чи фічу, або скористайся швидкими кнопками під полем вводу."
        )

    # Detailed listing of nodes
    if re.search(r"(що за ноди|які.*нод|покажи.*нод|список|перелік|що у нас є|які є ноди)", normalized, re.I):
        lines = [f"📋 **Поточні вузли в DAG-графі ({len(graph.nodes)} шт.):**\n"]
        for idx, node in enumerate(graph.nodes.values(), 1):
            type_icon = "💡" if node.node_type == NodeType.IDEA else "🎯" if node.node_type == NodeType.TASK else "🏛️" if node.node_type == NodeType.EPIC else "🛡️"
            agent_tag = f"`{node.assigned_agent}`" if node.assigned_agent else "—"
            lines.append(f"{idx}. {type_icon} **{node.title}**\n   Тип: `{node.node_type.value}`, Статус: `{node.status.value}`, Агент: {agent_tag}")
        lines.append("\nЩоб створити нову задачу або ідею, напиши наприклад: *«Створи задачу: назва»* або скористайся кнопками швидких дій.")
        return "\n".join(lines)

    if re.search(r"(кількість|нод|вузл|багато|чому|скільки|статус|стан)", normalized, re.I):
        total = len(graph.nodes)
        ideas = sum(1 for n in graph.nodes.values() if n.node_type == NodeType.IDEA)
        tasks = sum(1 for n in graph.nodes.values() if n.node_type == NodeType.TASK)
        epics = sum(1 for n in graph.nodes.values() if n.node_type == NodeType.EPIC)
        blocked = sum(1 for n in graph.nodes.values() if n.is_blocked)
        return (
            f"📊 **Герич: Аналітика DAG-графа**\n\n"
            f"Зараз у графі **{total} вузлів**:\n"
            f"• 💡 Ідеї: {ideas}\n"
            f"• 🎯 Задачі: {tasks}\n"
            f"• 🏛️ Епіки: {epics}\n"
            f"• ⚠️ Заблоковані: {blocked}\n\n"
            f"Велика кількість нод виникає після декомпозицій або попередніх інтеграційних тестів. "
            f"Ти завжди можеш повернути граф до канонічного стану кнопкою **Reset** або скористатися кнопками дій під чатом."
        )

    return (
        "💬 **Герич:** Я зрозумів твоє запитання. Якщо ти хочеш створити відповідну задачу або дослідження у DAG-графі, "
        "сформулюй команду (наприклад, *«Створи задачу: ...»* або *«Ідея: ...»*) або скористайся швидкими кнопками під полем чату."
    )



class ConversationalTaskExtractor:
    """
    Parses conversational user messages into structured DAG nodes & edges,
    adding them to the live NodeTaskGraph.
    """

    @classmethod
    def _build_nodes_from_specs(
        cls,
        nodes_data: List[Dict[str, Any]],
        graph: NodeTaskGraph,
        workspace_id: str = "ws-alpha-001",
        default_agent: Optional[str] = None
    ) -> Tuple[List[NodeItem], List[DependencyEdge]]:
        created_nodes: List[NodeItem] = []
        created_edges: List[DependencyEdge] = []

        existing_count = len(graph.nodes)
        col_index = existing_count % 4
        row_index = existing_count // 4
        base_x = 250 + (col_index * 320)
        base_y = 150 + (row_index * 220)

        prev_node: Optional[NodeItem] = None

        for idx, item in enumerate(nodes_data):
            title = str(item.get("title", f"Task {idx+1}")).strip()
            desc = str(item.get("description", title)).strip()

            raw_type = str(item.get("node_type", "task")).lower()
            if "idea" in raw_type:
                node_type = NodeType.IDEA
            elif "gate" in raw_type or "audit" in raw_type:
                node_type = NodeType.GATE
            elif "epic" in raw_type:
                node_type = NodeType.EPIC
            else:
                node_type = NodeType.TASK

            raw_stage = str(item.get("stage", "ready")).lower()
            stage_map = {
                "ideation": ExecutionStage.IDEATION,
                "architecture": ExecutionStage.ARCHITECTURE,
                "ready": ExecutionStage.READY,
                "in_progress": ExecutionStage.IN_PROGRESS,
                "verification": ExecutionStage.VERIFICATION,
                "completed": ExecutionStage.COMPLETED,
            }
            stage = stage_map.get(raw_stage, ExecutionStage.READY)

            assigned = item.get("assigned_agent") or default_agent or resolve_assigned_agent(title)
            priority = str(item.get("priority", "medium")).lower()
            if priority not in ["low", "medium", "high", "critical"]:
                priority = "medium"

            prefix = "idea" if node_type == NodeType.IDEA else ("gate" if node_type == NodeType.GATE else "task")
            suffix = str(uuid.uuid4())[:5]
            node_id = f"{prefix}-chat-{suffix}"
            while node_id in graph.nodes:
                suffix = str(uuid.uuid4())[:5]
                node_id = f"{prefix}-chat-{suffix}"

            pos_x = base_x + (idx * 260)
            pos_y = base_y + (idx * 40)

            tags = ["conversational", node_type.value]
            if assigned:
                tags.append(assigned)

            node = NodeItem(
                id=node_id,
                title=title,
                description=desc,
                node_type=node_type,
                stage=stage,
                status=NodeStatus.DRAFT,
                progress=0.0,
                assigned_agent=assigned,
                target_module="core",
                target_files=[],
                acceptance_criteria=[],
                tags=tags,
                priority=priority,
                position=NodePosition(x=pos_x, y=pos_y),
                is_blocked=False,
                blocked_by=[],
                created_at=datetime.now(timezone.utc).isoformat(),
                updated_at=datetime.now(timezone.utc).isoformat(),
            )
            graph.nodes[node.id] = node
            created_nodes.append(node)

            if prev_node:
                edge_id = f"edge-{prev_node.id}-to-{node.id}"
                edge = DependencyEdge(
                    id=edge_id,
                    source=prev_node.id,
                    target=node.id,
                    relation=EdgeRelation.DEPENDS_ON,
                    description="Auto-generated sequence by Gerych LLM"
                )
                graph.edges.append(edge)
                created_edges.append(edge)

            prev_node = node

        NodeTaskGraphEngine.recalculate_graph_dependencies(graph)
        return created_nodes, created_edges

    @classmethod
    def process_chat_message(
        cls,
        prompt: str,
        graph: NodeTaskGraph,
        workspace_id: str = "ws-alpha-001",
        default_agent: Optional[str] = None,
        history: Optional[List[Dict[str, Any]]] = None,
        selected_node_id: Optional[str] = None,
    ) -> Tuple[List[NodeItem], List[DependencyEdge], str, Optional[str], Optional[str]]:
        clean_text = prompt.strip()
        if not clean_text:
            return [], [], "Повідомлення порожнє. Напишіть задачу чи ідею для створення.", None, None

        # 1. Living Gerych Prime LLM Bridge
        try:
            from services.dnk_node_tasks.gerych_agent_bridge import GerychAgentBridge
            if GerychAgentBridge.is_available():
                summary_nodes = [
                    f"• {n.title} (ID: {n.id}, тип: {n.node_type.value}, статус: {n.status.value}, виконавець: {n.assigned_agent})"
                    for n in list(graph.nodes.values())[:20]
                ]
                graph_summary = f"Всього нод у графі: {len(graph.nodes)}.\n" + "\n".join(summary_nodes)

                selected_node_info = ""
                if selected_node_id and selected_node_id in graph.nodes:
                    sn = graph.nodes[selected_node_id]
                    selected_node_info = f"Виділена нода на полотні: '{sn.title}' (ID: {sn.id}, тип: {sn.node_type.value}, статус: {sn.status.value}, виконавець: {sn.assigned_agent})"

                llm_res = GerychAgentBridge.call_living_gerych(
                    clean_text,
                    graph_summary=graph_summary,
                    history=history,
                    selected_node_info=selected_node_info,
                )
                if llm_res and isinstance(llm_res, dict):
                    intent = llm_res.get("intent", "inquiry")
                    gerych_reply = llm_res.get("reply", "")
                    nodes_data = llm_res.get("nodes", [])
                    target_node_id = llm_res.get("target_node_id") or selected_node_id

                    if gerych_reply and "Герич" not in gerych_reply:
                        gerych_reply = f"🤖 Герич: {gerych_reply}"

                    # Intent: auto_layout
                    if intent == "auto_layout":
                        NodeTaskGraphEngine.compute_auto_layout(graph)
                        return [], [], gerych_reply or "🤖 Герич: Топологію графа автоматично вирівняно. Ноди розподілені за рівнями без перекриттів.", "auto_layout", None

                    # Intent: execute_task
                    if intent == "execute_task":
                        if not target_node_id and selected_node_id in graph.nodes:
                            target_node_id = selected_node_id
                        if not target_node_id:
                            for nid in reversed(list(graph.nodes.keys())):
                                n = graph.nodes[nid]
                                if n.node_type == NodeType.TASK and n.status != NodeStatus.COMPLETED:
                                    target_node_id = nid
                                    break

                        node_title = graph.nodes[target_node_id].title if target_node_id and target_node_id in graph.nodes else "задачі"
                        return [], [], gerych_reply or f"🤖 Герич: Запускаю виконання задачі '{node_title}'. Хід транслюється в термінал.", "execute", target_node_id

                    # Intent: inquiry
                    if intent == "inquiry" or not nodes_data:
                        return [], [], gerych_reply or "Привіт! Герич на зв'язку і готовий допомогти.", None, None

                    # Intent: task_creation - Deduplicate against existing node titles
                    existing_titles = {n.title.strip().lower() for n in graph.nodes.values()}
                    filtered_nodes = [
                        item for item in nodes_data
                        if str(item.get("title", "")).strip().lower() not in existing_titles
                    ]

                    if not filtered_nodes and nodes_data:
                        return [], [], "🤖 Герич: Зазначені задачі вже існують у графі. Ви можете запустити їх виконання або виконати автовирівнювання полотна.", None, None

                    created_nodes, created_edges = cls._build_nodes_from_specs(
                        filtered_nodes, graph, workspace_id, default_agent
                    )
                    # Automatically compute layout so new nodes never overlap
                    NodeTaskGraphEngine.compute_auto_layout(graph)

                    return created_nodes, created_edges, gerych_reply, "auto_layout", None
        except Exception as exc:
            logger.warning(f"Living Gerych LLM bridge encountered error, falling back to heuristics: {exc}")

        # 2. Heuristic fallback: Detect layout/ordering requests
        if re.search(r"\b(?:вирівня|автолейаут|auto-layout|впорядку|розподіли|налазять|перекрива|хаос)\b", clean_text, re.I):
            NodeTaskGraphEngine.compute_auto_layout(graph)
            return [], [], "🤖 Герич: Виконано автоматичне вирівнювання графа для усунення перекриття нод.", "auto_layout", None

        # 3. Heuristic fallback: Detect execution commands
        if re.search(r"\b(?:запускай|запусти|виконуй|стартуй|починай|роби|run)\b", clean_text, re.I):
            target_id = selected_node_id
            if not target_id or target_id not in graph.nodes:
                for nid in reversed(list(graph.nodes.keys())):
                    n = graph.nodes[nid]
                    if n.node_type == NodeType.TASK and n.status != NodeStatus.COMPLETED:
                        target_id = nid
                        break
            if target_id and target_id in graph.nodes:
                return [], [], f"🤖 Герич: Запускаю виконання задачі '{graph.nodes[target_id].title}'. Хід транслюється в термінал.", "execute", target_id

        # 4. Heuristic fallback: Detect conversational inquiries, greetings, or questions without creating tasks
        if is_conversational_inquiry(clean_text):
            reply = format_conversational_reply(clean_text, graph)
            return [], [], reply, None, None


        # Check for multi-step prompts (split by "і потім", "а після цього", ";", "\n", "->", "і протестуй")
        sub_prompts = []
        if "\n" in clean_text:
            lines = [l.strip("-* 0123456789.") for l in clean_text.splitlines() if l.strip()]
            if len(lines) > 1:
                sub_prompts = lines

        if not sub_prompts:
            split_patterns = re.split(r"(?:\s+та\s+потім\s+|\s+і\s+потім\s+|\s+після\s+цього\s+|;\s*|\s*->\s*)", clean_text, flags=re.I)
            if len(split_patterns) > 1 and all(len(s.strip()) > 5 for s in split_patterns):
                sub_prompts = [s.strip() for s in split_patterns]

        # If not multi-part, check if it's "Зроби X і протестуй/перевір Y"
        if not sub_prompts:
            compound_match = re.search(r"^(.*?)\s+(?:і|та)\s+(перевір(?:ити)?|протестуй(?:ти)?|проведи аудит)\s*(.*)$", clean_text, re.I)
            if compound_match:
                main_part = compound_match.group(1).strip()
                test_action = compound_match.group(2).strip()
                test_target = compound_match.group(3).strip() or "реалізацію"
                sub_prompts = [main_part, f"{test_action} {test_target}"]

        if not sub_prompts:
            sub_prompts = [clean_text]

        created_nodes: List[NodeItem] = []
        created_edges: List[DependencyEdge] = []

        # Calculate a pleasant position in canvas space
        existing_count = len(graph.nodes)
        col_index = existing_count % 4
        row_index = existing_count // 4
        base_x = 250 + (col_index * 320)
        base_y = 150 + (row_index * 220)

        prev_node: Optional[NodeItem] = None

        for idx, sub_text in enumerate(sub_prompts):
            node_type, stage = classify_node_type_and_stage(sub_text)
            assigned_agent = default_agent if (default_agent and default_agent != "gerych_prime") else resolve_assigned_agent(sub_text)
            priority = extract_priority(sub_text)

            # Generate concise title (first 50 chars up to punctuation)
            title = sub_text
            if len(title) > 60:
                first_sentence = re.split(r"[.!?\n]", title)[0]
                if len(first_sentence) > 15:
                    title = first_sentence[:60]
                else:
                    title = title[:57] + "..."

            # Generate unique ID
            prefix = "idea" if node_type == NodeType.IDEA else ("gate" if node_type == NodeType.GATE else "task")
            suffix = str(uuid.uuid4())[:5]
            node_id = f"{prefix}-chat-{suffix}"

            # Ensure ID is unique
            while node_id in graph.nodes:
                suffix = str(uuid.uuid4())[:5]
                node_id = f"{prefix}-chat-{suffix}"

            pos_x = base_x + (idx * 260)
            pos_y = base_y + (idx * 40)

            # Tags extraction
            tags = ["conversational", node_type.value]
            if assigned_agent:
                tags.append(assigned_agent)
            if "stitch" in sub_text.lower() or "кабінет" in sub_text.lower():
                tags.append("stitch")

            node = NodeItem(
                id=node_id,
                title=title,
                description=sub_text,
                node_type=node_type,
                stage=stage,
                status=NodeStatus.DRAFT,
                progress=0.0,
                assigned_agent=assigned_agent,
                target_module="core",
                target_files=[],
                acceptance_criteria=[],
                tags=tags,
                priority=priority,
                position=NodePosition(x=pos_x, y=pos_y),
                is_blocked=False,
                blocked_by=[],
                created_at=datetime.now(timezone.utc).isoformat(),
                updated_at=datetime.now(timezone.utc).isoformat(),
            )

            graph.nodes[node.id] = node
            created_nodes.append(node)

            # Link sequential tasks with depends_on edge
            if prev_node:
                edge_id = f"edge-{prev_node.id}-to-{node.id}"
                edge = DependencyEdge(
                    id=edge_id,
                    source=prev_node.id,
                    target=node.id,
                    relation=EdgeRelation.DEPENDS_ON,
                    description=f"Auto-generated sequence from chat intake"
                )
                graph.edges.append(edge)
                created_edges.append(edge)

            prev_node = node

        # Recalculate dependencies, stages, blockers in the graph
        NodeTaskGraphEngine.recalculate_graph_dependencies(graph)

        # Generate Gerych's Ukrainian response
        if len(created_nodes) == 1:
            n = created_nodes[0]
            type_label = "Ідею" if n.node_type == NodeType.IDEA else ("Гейт якості" if n.node_type == NodeType.GATE else "Задачу")
            reply = (
                f"🎯 **Герич: {type_label} успішно створено та додано до DAG-графа!**\n\n"
                f"• **Назва:** {n.title}\n"
                f"• **ID:** `{n.id}`\n"
                f"• **Тип:** {n.node_type.value.upper()} | **Пріоритет:** {n.priority.upper()}\n"
                f"• **Призначений агент:** `{n.assigned_agent}`\n"
                f"• **Стадія:** `{n.stage.value}`\n\n"
                f"Вузол миттєво відображено на інтерактивному полотні. Готовий розпочати виконання або додати залежності."
            )
        else:
            nodes_summary = "\n".join([
                f"  {idx+1}. [{n.node_type.value.upper()}] **{n.title}** (`{n.id}`) ➔ Агент: `{n.assigned_agent}`"
                for idx, n in enumerate(created_nodes)
            ])
            edges_summary = f"Створено {len(created_edges)} зв'язок залежностей між етапами." if created_edges else ""
            reply = (
                f"⚡ **Герич: Комплексний запит декомпозовано на {len(created_nodes)} елементів DAG-графа!**\n\n"
                f"{nodes_summary}\n\n"
                f"{edges_summary}\n\n"
                f"Всі елементи нанесено на просторове полотно та збережено в Obsidian."
            )

        NodeTaskGraphEngine.compute_auto_layout(graph)
        return created_nodes, created_edges, reply, "auto_layout", None

    @classmethod
    def decompose_node(
        cls,
        node: NodeItem,
        graph: NodeTaskGraph,
        instructions: Optional[str] = None,
        workspace_id: str = "ws-alpha-001",
    ) -> Tuple[List[NodeItem], List[DependencyEdge], str]:
        """
        Decomposes a complex Epic or Task into 3 specialized atomic child subtasks
        (Architecture/Spec -> Implementation/Build -> Quality Gate), assigning specialized
        swarm agents, positioning them downstream, and creating dependency edges.
        """
        created_nodes: List[NodeItem] = []
        created_edges: List[DependencyEdge] = []

        base_x = node.position.x + 360
        base_y = node.position.y - 120

        # Determine domain specialization based on parent tags and title
        context_text = f"{node.title} {node.description} {' '.join(node.tags)} {instructions or ''}".lower()
        if "shopify" in context_text or "liquid" in context_text or "store" in context_text:
            builder_agent = "dnk_shopify"
            builder_title = f"Shopify Liquid & Store: {node.title[:40]}"
        elif "video" in context_text or "remotion" in context_text or "media" in context_text:
            builder_agent = "dnk_video_ai_creator"
            builder_title = f"Video AI Composition: {node.title[:40]}"
        elif "api" in context_text or "backend" in context_text or "database" in context_text:
            builder_agent = "dnk_dev_fullstack"
            builder_title = f"API & Backend Integration: {node.title[:40]}"
        else:
            builder_agent = "gerych_builder"
            builder_title = f"Component Construction: {node.title[:40]}"

        subtask_specs = [
            {
                "suffix": "spec",
                "title": f"Arch & Spec: {node.title[:45]}",
                "desc": f"Архітектурна специфікація, моделі даних та дизайн контрактів для [{node.title}]. " + (instructions or ""),
                "type": NodeType.TASK,
                "agent": "antigravity_mentor",
                "priority": node.priority,
                "stage": ExecutionStage.READY,
                "offset_y": 0,
            },
            {
                "suffix": "build",
                "title": builder_title,
                "desc": f"Фізична імплементація та підключення компонентів для [{node.title}] роєм воркерів.",
                "type": NodeType.TASK,
                "agent": builder_agent,
                "priority": node.priority,
                "stage": ExecutionStage.READY,
                "offset_y": 140,
            },
            {
                "suffix": "audit",
                "title": f"Gate & Audit: {node.title[:45]}",
                "desc": f"Автоматизована перевірка тестів, перевірка регресій та Adversarial Audit для [{node.title}].",
                "type": NodeType.GATE,
                "agent": "gerych_auditor",
                "priority": "high",
                "stage": ExecutionStage.READY,
                "offset_y": 280,
            },
        ]

        prev_sub: Optional[NodeItem] = None
        for idx, spec in enumerate(subtask_specs):
            sub_id = f"task-{node.id}-{spec['suffix']}-{str(uuid.uuid4())[:4]}"
            while sub_id in graph.nodes:
                sub_id = f"task-{node.id}-{spec['suffix']}-{str(uuid.uuid4())[:4]}"

            pos = NodePosition(x=base_x, y=base_y + spec["offset_y"])
            sub_node = NodeItem(
                id=sub_id,
                title=spec["title"],
                description=spec["desc"],
                node_type=spec["type"],
                stage=spec["stage"],
                status=NodeStatus.DRAFT,
                progress=0.0,
                assigned_agent=spec["agent"],
                target_module=node.target_module or "core",
                target_files=[],
                acceptance_criteria=[f"Complete {spec['title']}"],
                tags=list(set(node.tags + ["decomposed", spec["agent"]])),
                priority=spec["priority"],
                position=pos,
                is_blocked=(idx > 0),
                blocked_by=[prev_sub.id] if prev_sub else [],
                created_at=datetime.now(timezone.utc).isoformat(),
                updated_at=datetime.now(timezone.utc).isoformat(),
            )
            graph.nodes[sub_node.id] = sub_node
            created_nodes.append(sub_node)

            if idx == 0:
                edge_id = f"edge-{node.id}-to-{sub_node.id}"
                e = DependencyEdge(
                    id=edge_id,
                    source=node.id,
                    target=sub_node.id,
                    relation=EdgeRelation.DEPENDS_ON,
                    description=f"Decomposed from parent {node.id}"
                )
                graph.edges.append(e)
                created_edges.append(e)

            if prev_sub:
                edge_id = f"edge-{prev_sub.id}-to-{sub_node.id}"
                e = DependencyEdge(
                    id=edge_id,
                    source=prev_sub.id,
                    target=sub_node.id,
                    relation=EdgeRelation.DEPENDS_ON,
                    description=f"Sequential pipeline dependency"
                )
                graph.edges.append(e)
                created_edges.append(e)

            prev_sub = sub_node

        NodeTaskGraphEngine.recalculate_graph_dependencies(graph)

        reply = (
            f"⚡ **Герич: Вузол [{node.title}] успішно декомпозовано на 3 атомні задачі!**\n\n"
            f"1. 📐 **{created_nodes[0].title}** ➔ `{created_nodes[0].assigned_agent}`\n"
            f"2. 🛠️ **{created_nodes[1].title}** ➔ `{created_nodes[1].assigned_agent}`\n"
            f"3. 🛡️ **{created_nodes[2].title}** ➔ `{created_nodes[2].assigned_agent}`\n\n"
            f"Створено {len(created_edges)} спрямованих зв'язків DAG. Всі підзадачі нанесені на полотно."
        )

        return created_nodes, created_edges, reply
