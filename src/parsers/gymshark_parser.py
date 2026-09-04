from __future__ import annotations

from typing import Any


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace(',', '').replace('£', '').replace('€', '').replace('$', '')
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    return str(value)


def _normalize_url(value: Any) -> str | None:
    cleaned = _clean_text(value)
    if not cleaned:
        return None
    if cleaned.startswith('http://') or cleaned.startswith('https://'):
        return cleaned
    if cleaned.startswith('//'):
        return 'https:' + cleaned
    return cleaned


def _extract_nested_image_url(hit: dict[str, Any]) -> str | None:
    featured = hit.get('featuredImage')
    if isinstance(featured, dict):
        for key in ('src', 'url', 'imageUrl'):
            if key in featured:
                return _normalize_url(featured.get(key))
    return _normalize_url(hit.get('imageUrl'))


def parse_hit(hit: dict[str, Any], extraction_time: str | None = None) -> dict[str, Any]:
    if not isinstance(hit, dict):
        return {
            'listing_id': None,
            'title': None,
            'sku': None,
            'category': None,
            'brand': None,
            'product_url': None,
            'currency': None,
            'current_price': None,
            'old_price': None,
            'availability': None,
            'image_url': None,
            'colour_name': None,
            'colour_code': None,
            'available_colours': None,
            'is_available': None,
            'extracted_at': extraction_time,
        }

    listing_id = hit.get('objectID') or hit.get('id') or hit.get('listingId') or hit.get('productId')
    title = _clean_text(hit.get('title')) or _clean_text(hit.get('name'))
    sku = _clean_text(hit.get('sku'))
    category = _clean_text(hit.get('category')) or _clean_text(hit.get('categories'))
    brand = _clean_text(hit.get('brand')) or _clean_text(hit.get('brandName'))
    handle = _clean_text(hit.get('handle'))
    product_url = _normalize_url(hit.get('productUrl')) or _normalize_url(hit.get('url'))
    if handle and not product_url:
        product_url = f'https://www.gymshark.com/products/{handle}'
    currency = _clean_text(hit.get('currency')) or 'GBP'
    if isinstance(currency, str):
        currency = currency.upper()

    current_price = _coerce_float(hit.get('price')) or _coerce_float(hit.get('salePrice'))
    old_price = _coerce_float(hit.get('compareAtPrice')) or _coerce_float(hit.get('oldPrice'))
    availability = hit.get('inStock') if isinstance(hit.get('inStock'), bool) else None
    if availability is None and isinstance(hit.get('availability'), str):
        availability = hit.get('availability').strip().lower() in {'true', 'available', 'in_stock'}

    image_url = _extract_nested_image_url(hit)
    colour_name = _clean_text(hit.get('colourName')) or _clean_text(hit.get('canonicalColour'))
    colour_code = _clean_text(hit.get('colour')) or _clean_text(hit.get('canonicalColour'))
    available_colours = hit.get('availableColours')
    if available_colours is not None and not isinstance(available_colours, list):
        available_colours = [available_colours]

    return {
        'listing_id': listing_id,
        'title': title,
        'sku': sku,
        'category': category,
        'brand': brand,
        'handle': handle,
        'product_url': product_url,
        'currency': currency,
        'current_price': current_price,
        'old_price': old_price,
        'availability': availability,
        'image_url': image_url,
        'colour_name': colour_name,
        'colour_code': colour_code,
        'available_colours': available_colours,
        'is_available': availability,
        'extracted_at': extraction_time,
    }


def normalize_listing_record(record: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(record)
    if 'title' in normalized:
        normalized['title'] = _clean_text(normalized['title'])
    if 'category' in normalized:
        normalized['category'] = _clean_text(normalized['category'])
    if 'brand' in normalized:
        normalized['brand'] = _clean_text(normalized['brand'])
    if 'sku' in normalized:
        normalized['sku'] = _clean_text(normalized['sku'])
    if 'currency' in normalized:
        normalized['currency'] = _clean_text(normalized['currency'])
        if normalized['currency']:
            normalized['currency'] = normalized['currency'].upper()
    if 'current_price' in normalized:
        normalized['current_price'] = _coerce_float(normalized['current_price'])
    if 'old_price' in normalized:
        normalized['old_price'] = _coerce_float(normalized['old_price'])
    if 'product_url' in normalized:
        normalized['product_url'] = _normalize_url(normalized['product_url'])
    if 'image_url' in normalized:
        normalized['image_url'] = _normalize_url(normalized['image_url'])
    if 'is_available' in normalized and normalized['is_available'] is not None:
        normalized['is_available'] = bool(normalized['is_available'])
    return normalized
