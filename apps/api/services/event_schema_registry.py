# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/services/event_schema_registry.py"
# purpose: "Event Schema Registry Service with versioning and validation (DNK-STREAM-001)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import hashlib
import json
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from apps.api.db.models.stream_event_schema import StreamEventSchema


class SchemaValidationError(Exception):
    pass


class SchemaCompatibilityError(Exception):
    pass


class EventSchemaRegistryService:
    """Manages event schemas, semantic versioning, and payload validation."""

    def __init__(self):
        self._schemas: Dict[str, List[StreamEventSchema]] = {}  # subject -> list of versioned schemas
        self._schema_by_id: Dict[str, StreamEventSchema] = {}
        self._lock = threading.RLock()

    def register_schema(
        self,
        subject: str,
        schema_definition: Dict[str, Any],
        schema_format: str = "JSON_SCHEMA",
        compatibility_mode: str = "BACKWARD",
        workspace_id: str = "ws-default",
    ) -> StreamEventSchema:
        """Registers a new schema version under a subject with compatibility checks."""
        subject_versions = self._schemas.get(subject, [])
        next_version = len(subject_versions) + 1

        if subject_versions and compatibility_mode != "NONE":
            latest = subject_versions[-1]
            self._check_compatibility(latest.schema_definition, schema_definition, compatibility_mode)

        schema = StreamEventSchema(
            subject=subject,
            version=next_version,
            schema_format=schema_format,
            schema_definition=schema_definition,
            compatibility_mode=compatibility_mode,
            workspace_id=workspace_id,
        )

        if subject not in self._schemas:
            self._schemas[subject] = []
        self._schemas[subject].append(schema)
        self._schema_by_id[schema.id] = schema
        return schema

    def get_latest_schema(self, subject: str) -> Optional[StreamEventSchema]:
        """Retrieves the latest registered schema for a subject."""
        versions = self._schemas.get(subject, [])
        if not versions:
            return None
        return versions[-1]

    def get_schema_by_version(self, subject: str, version: int) -> Optional[StreamEventSchema]:
        """Retrieves a specific version of a schema."""
        versions = self._schemas.get(subject, [])
        for sch in versions:
            if sch.version == version:
                return sch
        return None

    def get_schema_by_id(self, schema_id: str) -> Optional[StreamEventSchema]:
        """Retrieves a schema by unique id."""
        return self._schema_by_id.get(schema_id)

    def validate_payload(self, schema: StreamEventSchema, payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validates payload against the schema definition."""
        definition = schema.schema_definition
        if not isinstance(definition, dict):
            return True, None

        req_fields = definition.get("required", [])
        for f in req_fields:
            if f not in payload or payload[f] is None:
                return False, f"Missing required field: '{f}'"

        properties = definition.get("properties", {})
        for field, spec in properties.items():
            if field in payload and payload[field] is not None:
                val = payload[field]
                expected_type = spec.get("type")
                if expected_type == "string" and not isinstance(val, str):
                    return False, f"Field '{field}' expected string, got {type(val).__name__}"
                elif expected_type == "number" and not isinstance(val, (int, float)):
                    return False, f"Field '{field}' expected number, got {type(val).__name__}"
                elif expected_type == "integer" and not isinstance(val, int):
                    return False, f"Field '{field}' expected integer, got {type(val).__name__}"
                elif expected_type == "boolean" and not isinstance(val, bool):
                    return False, f"Field '{field}' expected boolean, got {type(val).__name__}"
                elif expected_type == "object" and not isinstance(val, dict):
                    return False, f"Field '{field}' expected object, got {type(val).__name__}"
                elif expected_type == "array" and not isinstance(val, list):
                    return False, f"Field '{field}' expected array, got {type(val).__name__}"

        return True, None

    def _check_compatibility(
        self,
        prev_def: Dict[str, Any],
        new_def: Dict[str, Any],
        mode: str,
    ) -> None:
        """Validates evolution compatibility between schema definitions."""
        prev_req = set(prev_def.get("required", []))
        new_req = set(new_def.get("required", []))

        if mode in ("BACKWARD", "FULL"):
            # New schema cannot add new required fields without defaults
            added_required = new_req - prev_req
            if added_required:
                raise SchemaCompatibilityError(
                    f"Backward compatibility violation: cannot add new required fields {list(added_required)}"
                )

        if mode in ("FORWARD", "FULL"):
            # New schema cannot delete previously required fields
            removed_required = prev_req - new_req
            if removed_required:
                raise SchemaCompatibilityError(
                    f"Forward compatibility violation: cannot remove required fields {list(removed_required)}"
                )
