"""Catalog area. Files matching app/catalog* map to area `catalog`."""

from fastapi import APIRouter

from app import flags

router = APIRouter(prefix="/catalog")

_ITEMS = [
    {"sku": "MUG-001", "name": "Stone mug", "price": 12.00},
    {"sku": "TEA-002", "name": "Earl grey", "price": 5.00},
    {"sku": "TEA-001", "name": "Green tea", "price": 4.50},
]


@router.get("/items")
def catalog_items() -> dict:
    sorted_items = sorted(_ITEMS, key=lambda item: item["price"])
    body = {"items": sorted_items}
    if flags.enabled("catalog_item_count"):
        body["count"] = len(sorted_items)
    return body
