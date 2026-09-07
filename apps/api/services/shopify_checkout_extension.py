# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_shopify_checkout_extension"
# purpose: "Shopify Checkout UI Extension Management & Field Validation Engine (DNK-ECOM-004)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import re
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, Field


class CheckoutExtensionType(str, Enum):
    CHECKOUT_UI = "checkout_ui"
    POST_PURCHASE = "post_purchase"
    PAYMENT_GATEWAY = "payment_gateway"


class TargetPlacement(str, Enum):
    SHIPPING_OPTION_LIST_RENDER_AFTER = "purchase.checkout.shipping-option-list.render-after"
    PAYMENT_METHOD_RENDER_BEFORE = "purchase.checkout.payment-method.render-before"
    ORDER_SUMMARY_RENDER_AFTER = "purchase.checkout.order-summary.render-after"
    CART_LINE_ITEM_RENDER_AFTER = "purchase.checkout.cart-line-item.render-after"
    INFORMATION_FORM_RENDER_BEFORE = "purchase.checkout.information.render-before"
    POST_PURCHASE_RENDER_PRIMARY = "purchase.post-purchase.render"


class FieldType(str, Enum):
    TEXT = "text"
    TEXTAREA = "textarea"
    CHECKBOX = "checkbox"
    SELECT = "select"
    NUMBER = "number"
    DATE = "date"


class CustomFieldDefinition(BaseModel):
    key: str = Field(..., description="Unique field identifier (e.g. shipping_instructions, gift_message, b2b_po_number)")
    label: str = Field(..., description="User-facing input label")
    field_type: FieldType = Field(default=FieldType.TEXT)
    required: bool = Field(default=False)
    default_value: Optional[Any] = None
    options: Optional[List[str]] = Field(default_factory=list, description="Allowed choices for select fields")
    validation_regex: Optional[str] = None
    max_length: Optional[int] = 500
    help_text: Optional[str] = None


class CheckoutExtensionConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    extension_name: str
    extension_type: CheckoutExtensionType = CheckoutExtensionType.CHECKOUT_UI
    shopify_app_id: str
    api_version: str = "2024-07"
    target_placement: str = TargetPlacement.SHIPPING_OPTION_LIST_RENDER_AFTER.value
    custom_fields: List[CustomFieldDefinition] = Field(default_factory=list)
    enabled: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ShopifyCheckoutExtensionService:
    """Service managing Checkout UI Extensions, manifest generation, and custom field validation."""

    def __init__(self, db_session=None):
        self.db_session = db_session
        self._in_memory_configs: Dict[str, CheckoutExtensionConfig] = {}

    def create_extension_config(
        self,
        workspace_id: str,
        extension_name: str,
        shopify_app_id: str,
        extension_type: CheckoutExtensionType = CheckoutExtensionType.CHECKOUT_UI,
        target_placement: str = TargetPlacement.SHIPPING_OPTION_LIST_RENDER_AFTER.value,
        custom_fields: Optional[List[Union[Dict[str, Any], CustomFieldDefinition]]] = None,
        api_version: str = "2024-07",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CheckoutExtensionConfig:
        fields = []
        if custom_fields:
            for f in custom_fields:
                if isinstance(f, CustomFieldDefinition):
                    fields.append(f)
                else:
                    fields.append(CustomFieldDefinition(**f))

        config = CheckoutExtensionConfig(
            workspace_id=workspace_id,
            extension_name=extension_name,
            extension_type=extension_type,
            shopify_app_id=shopify_app_id,
            api_version=api_version,
            target_placement=target_placement,
            custom_fields=fields,
            metadata=metadata or {},
        )
        self._in_memory_configs[config.id] = config
        return config

    def get_extension_config(self, config_id: str) -> Optional[CheckoutExtensionConfig]:
        return self._in_memory_configs.get(config_id)

    def list_extension_configs(
        self, workspace_id: Optional[str] = None, extension_type: Optional[CheckoutExtensionType] = None
    ) -> List[CheckoutExtensionConfig]:
        results = list(self._in_memory_configs.values())
        if workspace_id:
            results = [c for c in results if c.workspace_id == workspace_id]
        if extension_type:
            results = [c for c in results if c.extension_type == extension_type]
        return results

    def update_extension_config(
        self,
        config_id: str,
        **updates: Any,
    ) -> Optional[CheckoutExtensionConfig]:
        config = self.get_extension_config(config_id)
        if not config:
            return None

        for k, v in updates.items():
            if k == "custom_fields" and v is not None:
                parsed_fields = []
                for f in v:
                    parsed_fields.append(f if isinstance(f, CustomFieldDefinition) else CustomFieldDefinition(**f))
                setattr(config, k, parsed_fields)
            elif hasattr(config, k) and v is not None:
                setattr(config, k, v)

        config.updated_at = datetime.now(timezone.utc)
        return config

    def delete_extension_config(self, config_id: str) -> bool:
        if config_id in self._in_memory_configs:
            del self._in_memory_configs[config_id]
            return True
        return False

    def validate_checkout_payload(
        self,
        config_id_or_config: Any,
        submitted_fields: Dict[str, Any],
    ) -> Tuple[bool, List[str], Dict[str, Any]]:
        """Validate customer input against the defined custom fields schema.

        Returns: (is_valid, error_list, sanitized_values)
        """
        if isinstance(config_id_or_config, str):
            config = self.get_extension_config(config_id_or_config)
            if not config:
                return False, [f"Config '{config_id_or_config}' not found"], {}
        else:
            config = config_id_or_config

        errors: List[str] = []
        sanitized: Dict[str, Any] = {}

        field_map = {f.key: f for f in config.custom_fields}

        for key, field_def in field_map.items():
            val = submitted_fields.get(key)

            # Required check
            if field_def.required and (val is None or val == ""):
                errors.append(f"Field '{field_def.label}' ({key}) is required.")
                continue

            if val is None:
                sanitized[key] = field_def.default_value
                continue

            # Type validations
            if field_def.field_type == FieldType.CHECKBOX:
                sanitized[key] = bool(val)
            elif field_def.field_type == FieldType.NUMBER:
                try:
                    sanitized[key] = float(val) if "." in str(val) else int(val)
                except (ValueError, TypeError):
                    errors.append(f"Field '{key}' must be a valid number.")
            elif field_def.field_type == FieldType.SELECT:
                val_str = str(val)
                if field_def.options and val_str not in field_def.options:
                    errors.append(f"Invalid option '{val_str}' for field '{key}'. Allowed: {field_def.options}")
                else:
                    sanitized[key] = val_str
            else:
                val_str = str(val).strip()
                if field_def.max_length and len(val_str) > field_def.max_length:
                    errors.append(f"Field '{key}' exceeds max length of {field_def.max_length} characters.")
                elif field_def.validation_regex:
                    if not re.match(field_def.validation_regex, val_str):
                        errors.append(f"Field '{key}' does not match required format pattern.")
                    else:
                        sanitized[key] = val_str
                else:
                    sanitized[key] = val_str

        return len(errors) == 0, errors, sanitized

    def generate_shopify_extension_manifest(self, config_id_or_config: Any) -> Dict[str, Any]:
        """Generates Shopify Checkout Extension TOML-compatible manifest dictionary."""
        if isinstance(config_id_or_config, str):
            config = self.get_extension_config(config_id_or_config)
            if not config:
                raise ValueError(f"Config '{config_id_or_config}' not found")
        else:
            config = config_id_or_config

        return {
            "name": config.extension_name,
            "type": config.extension_type.value,
            "api_version": config.api_version,
            "app_id": config.shopify_app_id,
            "extension_points": [
                {
                    "target": config.target_placement,
                    "module": "./src/CheckoutExtension.tsx",
                }
            ],
            "settings": {
                "fields": [
                    {
                        "key": f.key,
                        "type": f.field_type.value,
                        "name": f.label,
                        "required": f.required,
                        "options": f.options,
                        "help_text": f.help_text,
                    }
                    for f in config.custom_fields
                ]
            },
        }

    def generate_react_extension_snippet(self, config_id_or_config: Any) -> str:
        """Generates React + TypeScript JSX code for Shopify Checkout UI Extensions."""
        if isinstance(config_id_or_config, str):
            config = self.get_extension_config(config_id_or_config)
            if not config:
                raise ValueError(f"Config '{config_id_or_config}' not found")
        else:
            config = config_id_or_config

        field_renderers = []
        for f in config.custom_fields:
            if f.field_type == FieldType.CHECKBOX:
                field_renderers.append(
                    f'      <Checkbox id="{f.key}" name="{f.key}" checked={{Boolean(attributes["{f.key}"])}} '
                    f'onChange={{(value) => updateAttribute("{f.key}", value)}}>{f.label}</Checkbox>'
                )
            elif f.field_type == FieldType.SELECT:
                options_str = ", ".join([f'{{ value: "{opt}", label: "{opt}" }}' for opt in (f.options or [])])
                field_renderers.append(
                    f'      <Select id="{f.key}" label="{f.label}" options={{[{options_str}]}} '
                    f'value={{attributes["{f.key}"] || ""}} onChange={{(value) => updateAttribute("{f.key}", value)}} />'
                )
            elif f.field_type == FieldType.TEXTAREA:
                field_renderers.append(
                    f'      <TextField id="{f.key}" label="{f.label}" multiline={{3}} '
                    f'value={{attributes["{f.key}"] || ""}} onChange={{(value) => updateAttribute("{f.key}", value)}} />'
                )
            else:
                field_renderers.append(
                    f'      <TextField id="{f.key}" label="{f.label}" '
                    f'value={{attributes["{f.key}"] || ""}} onChange={{(value) => updateAttribute("{f.key}", value)}} />'
                )

        rendered_body = "\n".join(field_renderers)

        snippet = f"""import React, {{ useState }} from 'react';
import {{
  reactExtension,
  useApplyAttributeChange,
  BlockStack,
  TextField,
  Checkbox,
  Select,
  Text,
}} from '@shopify/ui-extensions-react/checkout';

export default reactExtension(
  '{config.target_placement}',
  () => <Extension />
);

function Extension() {{
  const applyAttributeChange = useApplyAttributeChange();
  const [attributes, setAttributes] = useState<Record<string, any>>({{}});

  const updateAttribute = async (key: string, value: any) => {{
    setAttributes((prev) => ({{ ...prev, [key]: value }}));
    await applyAttributeChange({{
      type: 'updateAttribute',
      key: `custom_${{key}}`,
      value: String(value),
    }});
  }};

  return (
    <BlockStack spacing="loose">
      <Text size="medium" emphasis="bold">{config.extension_name}</Text>
{rendered_body}
    </BlockStack>
  );
}}
"""
        return snippet
