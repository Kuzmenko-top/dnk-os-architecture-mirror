# --- DNK-MRH-HEADER ---
# mrh_id: "core/lakehouse/__init__.py"
# purpose: "Package entrypoint for DNK OS DuckDB Lakehouse Engine & Parquet Caching."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

from .duckdb_engine import (
    DuckDBLakehouseEngine,
    LakehouseQueryResult,
    get_lakehouse_engine,
)

__all__ = [
    "DuckDBLakehouseEngine",
    "LakehouseQueryResult",
    "get_lakehouse_engine",
]
