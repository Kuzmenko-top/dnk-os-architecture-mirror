# --- DNK-MRH-HEADER ---
# mrh_id: "tests_shopify_test_checkout_extension"
# purpose: "Comprehensive Unit and Integration Tests for Shopify Checkout UI Extensions (DNK-ECOM-004)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import uuid
import pytest
from apps.api.services.shopify_checkout_extension import (
    ShopifyCheckoutExtensionService,
    CheckoutExtensionType,
    TargetPlacement,
    FieldType,
    CustomFieldDefinition,
)
from apps.api.db.models.shopify_checkout_extension_config import ShopifyCheckoutExtensionConfigModel


@pytest.fixture
def checkout_service():
    return ShopifyCheckoutExtensionService()


def test_create_and_get_checkout_extension_config(checkout_service):
    workspace_id = str(uuid.uuid4())
    custom_fields = [
        {
            "key": "shipping_instructions",
            "label": "Delivery Instructions",
            "field_type": "textarea",
            "required": False,
            "max_length": 300,
        },
        {
            "key": "is_gift",
            "label": "This is a gift order",
            "field_type": "checkbox",
            "required": False,
            "default_value": False,
        },
        {
            "key": "gift_message",
            "label": "Gift Message Card",
            "field_type": "text",
            "required": False,
            "max_length": 150,
        },
        {
            "key": "delivery_time_slot",
            "label": "Preferred Time Slot",
            "field_type": "select",
            "options": ["Morning (09:00 - 13:00)", "Evening (14:00 - 18:00)"],
            "required": True,
        },
    ]

    config = checkout_service.create_extension_config(
        workspace_id=workspace_id,
        extension_name="Custom Delivery & Gift Options",
        shopify_app_id="app_dnk_checkout_01",
        extension_type=CheckoutExtensionType.CHECKOUT_UI,
        target_placement=TargetPlacement.SHIPPING_OPTION_LIST_RENDER_AFTER.value,
        custom_fields=custom_fields,
    )

    assert config.id is not None
    assert config.workspace_id == workspace_id
    assert config.extension_name == "Custom Delivery & Gift Options"
    assert len(config.custom_fields) == 4
    assert config.custom_fields[0].key == "shipping_instructions"
    assert config.custom_fields[3].field_type == FieldType.SELECT

    fetched = checkout_service.get_extension_config(config.id)
    assert fetched is not None
    assert fetched.id == config.id


def test_update_and_delete_extension_config(checkout_service):
    workspace_id = str(uuid.uuid4())
    config = checkout_service.create_extension_config(
        workspace_id=workspace_id,
        extension_name="Initial Name",
        shopify_app_id="app_test",
    )

    updated = checkout_service.update_extension_config(
        config.id,
        extension_name="Updated Extension Name",
        enabled=False,
    )
    assert updated.extension_name == "Updated Extension Name"
    assert updated.enabled is False

    deleted = checkout_service.delete_extension_config(config.id)
    assert deleted is True
    assert checkout_service.get_extension_config(config.id) is None


def test_validate_checkout_payload_valid(checkout_service):
    workspace_id = str(uuid.uuid4())
    config = checkout_service.create_extension_config(
        workspace_id=workspace_id,
        extension_name="B2B Order Fields",
        shopify_app_id="app_b2b",
        custom_fields=[
            {"key": "po_number", "label": "Purchase Order Number", "field_type": "text", "required": True, "max_length": 20},
            {"key": "tax_exempt", "label": "Tax Exempt Organization", "field_type": "checkbox", "required": False},
            {"key": "headcount", "label": "Department Headcount", "field_type": "number", "required": False},
        ],
    )

    submitted = {
        "po_number": "PO-2026-9988",
        "tax_exempt": True,
        "headcount": 42,
    }

    is_valid, errors, sanitized = checkout_service.validate_checkout_payload(config, submitted)
    assert is_valid is True
    assert len(errors) == 0
    assert sanitized["po_number"] == "PO-2026-9988"
    assert sanitized["tax_exempt"] is True
    assert sanitized["headcount"] == 42


def test_validate_checkout_payload_errors(checkout_service):
    workspace_id = str(uuid.uuid4())
    config = checkout_service.create_extension_config(
        workspace_id=workspace_id,
        extension_name="Strict Checkout Fields",
        shopify_app_id="app_strict",
        custom_fields=[
            {"key": "po_number", "label": "Purchase Order Number", "field_type": "text", "required": True, "max_length": 5},
            {
                "key": "delivery_slot",
                "label": "Delivery Slot",
                "field_type": "select",
                "options": ["slot_a", "slot_b"],
                "required": True,
            },
            {
                "key": "pin_code",
                "label": "4-Digit PIN",
                "field_type": "text",
                "validation_regex": r"^\d{4}$",
                "required": False,
            },
        ],
    )

    # Test missing required field, length violation, invalid select option, regex violation
    submitted = {
        "po_number": "PO-WAY-TOO-LONG",
        "delivery_slot": "invalid_slot",
        "pin_code": "ABC",
    }

    is_valid, errors, sanitized = checkout_service.validate_checkout_payload(config, submitted)
    assert is_valid is False
    assert len(errors) == 3
    assert any("exceeds max length" in e for e in errors)
    assert any("Invalid option" in e for e in errors)
    assert any("pattern" in e for e in errors)


def test_generate_shopify_extension_manifest(checkout_service):
    workspace_id = str(uuid.uuid4())
    config = checkout_service.create_extension_config(
        workspace_id=workspace_id,
        extension_name="Gift Option Extension",
        shopify_app_id="app_gift_01",
        target_placement=TargetPlacement.ORDER_SUMMARY_RENDER_AFTER.value,
        custom_fields=[
            {"key": "gift_wrap", "label": "Add Gift Wrap ($5)", "field_type": "checkbox", "required": False},
        ],
    )

    manifest = checkout_service.generate_shopify_extension_manifest(config)
    assert manifest["name"] == "Gift Option Extension"
    assert manifest["type"] == "checkout_ui"
    assert manifest["app_id"] == "app_gift_01"
    assert manifest["extension_points"][0]["target"] == TargetPlacement.ORDER_SUMMARY_RENDER_AFTER.value
    assert len(manifest["settings"]["fields"]) == 1
    assert manifest["settings"]["fields"][0]["key"] == "gift_wrap"


def test_generate_react_extension_snippet(checkout_service):
    workspace_id = str(uuid.uuid4())
    config = checkout_service.create_extension_config(
        workspace_id=workspace_id,
        extension_name="Delivery Slot Selector",
        shopify_app_id="app_delivery_slot",
        target_placement=TargetPlacement.SHIPPING_OPTION_LIST_RENDER_AFTER.value,
        custom_fields=[
            {"key": "notes", "label": "Gate Access Code", "field_type": "text"},
            {"key": "contactless", "label": "Contactless Drop-off", "field_type": "checkbox"},
        ],
    )

    jsx = checkout_service.generate_react_extension_snippet(config)
    assert "reactExtension" in jsx
    assert "purchase.checkout.shipping-option-list.render-after" in jsx
    assert "Gate Access Code" in jsx
    assert "Contactless Drop-off" in jsx
    assert "useApplyAttributeChange" in jsx


def test_orm_model_instantiation():
    model = ShopifyCheckoutExtensionConfigModel(
        workspace_id=str(uuid.uuid4()),
        extension_name="Test Checkout UI Extension",
        extension_type="checkout_ui",
        shopify_app_id="app_12345",
        target_placement="purchase.checkout.payment-method.render-before",
        custom_fields_schema=[{"key": "vip_code", "label": "VIP Access Code", "field_type": "text"}],
        enabled=True,
    )
    assert model.extension_name == "Test Checkout UI Extension"
    assert model.extension_type == "checkout_ui"
    assert model.custom_fields_schema[0]["key"] == "vip_code"
    assert model.enabled is True
