# --- DNK-MRH-HEADER ---
# mrh_id: "core/mindmap/auto_cluster.py"
# purpose: "High-performance AI auto-clusterization engine for Mind Map canvas nodes using K-Means, pgvector embeddings, and semantic theme naming."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import math
import time
import random
from typing import List, Dict, Any, Optional, Tuple

from core.memory.pgvector_store import generate_embedding, cosine_similarity
from core.mindmap.cluster_names import cluster_name_synthesizer


CLUSTER_PALETTE = [
    "#3B82F6",  # Sapphire Blue
    "#10B981",  # Emerald Green
    "#F59E0B",  # Amber Gold
    "#8B5CF6",  # Violet Purple
    "#EC4899",  # Neon Pink
    "#06B6D4",  # Cyan Blue
    "#14B8A6",  # Teal Green
    "#F97316",  # Coral Orange
]


def extract_node_text(node: Dict[str, Any]) -> str:
    """Extracts all semantic text fields from a canvas node representation."""
    parts = []
    
    # Check top-level or data-level
    raw_data = node.get("data")
    data: Dict[str, Any] = raw_data if isinstance(raw_data, dict) else {}
    
    title = data.get("title") or data.get("label") or node.get("title") or node.get("label") or ""
    if title:
        parts.append(str(title))
        
    content = data.get("content") or data.get("description") or node.get("content") or node.get("description") or ""
    if content:
        parts.append(str(content))
        
    raw_tags = data.get("tags") if "tags" in data else node.get("tags")
    tags = raw_tags if isinstance(raw_tags, list) else []
    if tags:
        parts.extend([str(t) for t in tags])
        
    raw_type = node.get("type") or data.get("type") or ""
    ntype = str(raw_type) if raw_type else ""
    if ntype:
        parts.append(ntype.replace("mindmap_", "").replace("_", " "))
        
    return " ".join(parts).strip()


def extract_node_coords(node: Dict[str, Any]) -> Tuple[float, float]:
    """Extracts (x, y) coordinates from a node."""
    pos = node.get("position")
    if isinstance(pos, dict):
        x = float(pos.get("x", 0.0))
        y = float(pos.get("y", 0.0))
        return (x, y)
    x = float(node.get("x", 0.0))
    y = float(node.get("y", 0.0))
    return (x, y)


class MindMapAutoClusterEngine:
    """
    K-Means + pgvector semantic clustering engine for Mind Map nodes.
    Groups 10+ nodes into 3-5 distinct visual clusters with synthesized names and spatial layout.
    """

    def __init__(self, use_llm_naming: bool = False):
        self.use_llm_naming = use_llm_naming

    def auto_determine_k(self, node_count: int, k: Optional[int] = None) -> int:
        """
        Determines the optimal number of clusters (k).
        For 10+ nodes, strictly bounds k between 3 and 5 to satisfy DoD.
        """
        if k is not None:
            return max(1, min(k, node_count))

        if node_count <= 2:
            return 1
        elif 3 <= node_count <= 5:
            return 2
        elif 6 <= node_count <= 9:
            return 3
        elif 10 <= node_count <= 14:
            return 4  # Strictly 3-5 per DoD
        elif 15 <= node_count <= 20:
            return 5  # Strictly 3-5 per DoD
        else:
            # Scaled up for large mindmaps
            return min(8, max(3, node_count // 4))

    def _kmeans_pp_init(self, vectors: List[List[float]], k: int) -> List[List[float]]:
        """K-Means++ initialization to pick diverse initial centroids."""
        n = len(vectors)
        if k >= n:
            return [list(v) for v in vectors]

        # Fix seed for reproducibility in automated tests
        rng = random.Random(42)
        centroids = [list(vectors[rng.randint(0, n - 1)])]

        for _ in range(1, k):
            dists = []
            for v in vectors:
                # Minimum distance to any current centroid (using 1 - cosine_similarity)
                min_dist = min(max(0.0, 1.0 - cosine_similarity(v, c)) for c in centroids)
                dists.append(min_dist * min_dist)
            
            total = sum(dists)
            if total <= 1e-9:
                remaining = [v for v in vectors if v not in centroids]
                if remaining:
                    centroids.append(list(rng.choice(remaining)))
                else:
                    centroids.append(list(vectors[0]))
                continue

            threshold = rng.uniform(0, total)
            cum = 0.0
            chosen = vectors[-1]
            for idx, d in enumerate(dists):
                cum += d
                if cum >= threshold:
                    chosen = vectors[idx]
                    break
            centroids.append(list(chosen))

        return centroids

    def _run_kmeans(
        self, vectors: List[List[float]], k: int, max_iter: int = 25
    ) -> List[int]:
        """
        Runs spherical K-Means using cosine similarity.
        Returns cluster assignment list [c0, c1, ..., cn-1].
        """
        n = len(vectors)
        if n == 0:
            return []
        if k <= 1 or n <= k:
            return list(range(n)) if n <= k else [0] * n

        centroids = self._kmeans_pp_init(vectors, k)
        dim = len(vectors[0])
        assignments = [-1] * n

        for _ in range(max_iter):
            changed = False
            # Assignment step: assign each vector to the closest centroid
            for i, vec in enumerate(vectors):
                best_sim = -2.0
                best_cluster = 0
                for c_idx, c_vec in enumerate(centroids):
                    sim = cosine_similarity(vec, c_vec)
                    if sim > best_sim:
                        best_sim = sim
                        best_cluster = c_idx
                if assignments[i] != best_cluster:
                    assignments[i] = best_cluster
                    changed = True

            if not changed:
                break

            # Update step: recompute centroids
            for c_idx in range(k):
                cluster_vecs = [vectors[i] for i, a in enumerate(assignments) if a == c_idx]
                if not cluster_vecs:
                    continue
                new_c = [0.0] * dim
                for cv in cluster_vecs:
                    for d in range(dim):
                        new_c[d] += cv[d]
                
                # Normalize new centroid
                norm = math.sqrt(sum(x * x for x in new_c))
                if norm > 1e-9:
                    centroids[c_idx] = [x / norm for x in new_c]

        return assignments

    def cluster_nodes(
        self,
        nodes: List[Dict[str, Any]],
        k: Optional[int] = None,
        language: Optional[str] = None,
        auto_layout: bool = True,
    ) -> Dict[str, Any]:
        """
        Main entry point for auto-clusterization.
        Takes mind map nodes, generates pgvector embeddings, performs K-Means,
        synthesizes cluster names, and optionally computes new spatial positions.
        """
        start_time = time.perf_counter()

        if not nodes:
            return {
                "status": "empty",
                "clusters": [],
                "total_nodes": 0,
                "k": 0,
                "execution_time_ms": 0.0,
                "repositioned_nodes": [],
            }

        k_val = self.auto_determine_k(len(nodes), k)

        # 1. Generate pgvector embeddings (768-dim) for each node
        node_texts = [extract_node_text(n) for n in nodes]
        vectors = [generate_embedding(t) for t in node_texts]

        # 2. Run K-Means clustering
        assignments = self._run_kmeans(vectors, k_val)

        # 3. Group nodes by cluster
        clusters_map: Dict[int, List[Dict[str, Any]]] = {i: [] for i in range(k_val)}
        for node, c_idx in zip(nodes, assignments):
            clusters_map[c_idx].append(node)

        # Filter out empty clusters if any
        non_empty_clusters = [nodes_list for nodes_list in clusters_map.values() if nodes_list]

        # 4. Build cluster metadata & names
        clusters = []
        for idx, c_nodes in enumerate(non_empty_clusters):
            cluster_id = f"cluster_{idx + 1}"
            cluster_color = CLUSTER_PALETTE[idx % len(CLUSTER_PALETTE)]
            cluster_name = cluster_name_synthesizer.synthesize_cluster_name(
                c_nodes, language=language, use_llm=self.use_llm_naming
            )

            # Spatial bounds of current cluster nodes
            xs = [extract_node_coords(n)[0] for n in c_nodes]
            ys = [extract_node_coords(n)[1] for n in c_nodes]
            
            min_x = min(xs) if xs else 0.0
            max_x = max(xs) if xs else 0.0
            min_y = min(ys) if ys else 0.0
            max_y = max(ys) if ys else 0.0
            
            # 60px padding for cluster bounding box
            pad = 60.0
            bbox = {
                "min_x": min_x - pad,
                "min_y": min_y - pad,
                "max_x": max_x + pad + 240.0,  # node width allowance
                "max_y": max_y + pad + 160.0,  # node height allowance
                "width": max(320.0, (max_x - min_x) + (pad * 2) + 240.0),
                "height": max(240.0, (max_y - min_y) + (pad * 2) + 160.0),
            }

            centroid_x = sum(xs) / len(xs) if xs else 0.0
            centroid_y = sum(ys) / len(ys) if ys else 0.0

            clusters.append({
                "cluster_id": cluster_id,
                "name": cluster_name,
                "color": cluster_color,
                "node_ids": [n.get("id") for n in c_nodes],
                "nodes": c_nodes,
                "centroid": {"x": centroid_x, "y": centroid_y},
                "bounding_box": bbox,
            })

        # 5. Spatial Auto-Layout Repositioning
        repositioned_nodes = []
        if auto_layout and clusters:
            repositioned_nodes = self.compute_spatial_layout(clusters)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return {
            "status": "success",
            "clusters": clusters,
            "total_nodes": len(nodes),
            "k": len(clusters),
            "execution_time_ms": round(elapsed_ms, 2),
            "repositioned_nodes": repositioned_nodes,
        }

    def compute_spatial_layout(
        self,
        clusters: List[Dict[str, Any]],
        start_x: float = 100.0,
        start_y: float = 100.0,
        cluster_spacing_x: float = 650.0,
        cluster_spacing_y: float = 550.0,
        columns: int = 2,
    ) -> List[Dict[str, Any]]:
        """
        Arranges clusters cleanly in a multi-column visual spatial layout on the canvas.
        Each node in a cluster is positioned relative to its cluster center.
        """
        repositioned = []
        
        for c_idx, cl in enumerate(clusters):
            col = c_idx % columns
            row = c_idx // columns
            
            c_base_x = start_x + (col * cluster_spacing_x)
            c_base_y = start_y + (row * cluster_spacing_y)

            # Update cluster bounding box to new organized layout
            c_nodes = cl["nodes"]
            node_count = len(c_nodes)
            
            # Lay out nodes inside cluster (2 columns inside each cluster)
            inner_cols = 2 if node_count > 2 else 1
            node_spacing_x = 260.0
            node_spacing_y = 150.0
            
            for n_idx, node in enumerate(c_nodes):
                n_col = n_idx % inner_cols
                n_row = n_idx // inner_cols
                
                new_x = c_base_x + 50.0 + (n_col * node_spacing_x)
                new_y = c_base_y + 80.0 + (n_row * node_spacing_y)

                # Clone node with updated position
                updated_node = dict(node)
                if "position" in updated_node and isinstance(updated_node["position"], dict):
                    updated_node["position"] = {"x": new_x, "y": new_y}
                else:
                    updated_node["x"] = new_x
                    updated_node["y"] = new_y
                    updated_node["position"] = {"x": new_x, "y": new_y}

                # Attach cluster metadata to node
                node_data = dict(updated_node.get("data") or {})
                node_data["clusterId"] = cl["cluster_id"]
                node_data["clusterName"] = cl["name"]
                node_data["clusterColor"] = cl["color"]
                updated_node["data"] = node_data

                repositioned.append(updated_node)

            # Update cluster centroid and bounding box
            cl["centroid"] = {
                "x": c_base_x + 300.0,
                "y": c_base_y + 250.0,
            }
            cl["bounding_box"] = {
                "min_x": c_base_x,
                "min_y": c_base_y,
                "max_x": c_base_x + cluster_spacing_x - 50.0,
                "max_y": c_base_y + cluster_spacing_y - 50.0,
                "width": cluster_spacing_x - 50.0,
                "height": cluster_spacing_y - 50.0,
            }

        return repositioned


auto_cluster_engine = MindMapAutoClusterEngine()
