from __future__ import annotations

from src.parsers.gymshark_parser import parse_hit, normalize_listing_record


def test_parse_hit_extracts_expected_fields():
    payload = {
        'objectID': 'prod-100',
        'sku': 'sku-100',
        'title': 'Gymshark Training Tee',
        'brand': 'Gymshark',
        'category': 'Menswear',
        'handle': 'training-tee',
        'productUrl': 'https://www.gymshark.com/products/training-tee',
        'currency': 'GBP',
        'price': 39.95,
        'compareAtPrice': 49.95,
        'availableColours': [{'code': 'black'}],
        'featuredImage': {'src': 'https://img.example.com/x.jpg'},
        'inStock': True,
    }
    record = parse_hit(payload, extraction_time='2025-01-01T00:00:00Z')
    assert record['listing_id'] == 'prod-100'
    assert record['title'] == 'Gymshark Training Tee'
    assert record['current_price'] == 39.95
    assert record['image_url'] == 'https://img.example.com/x.jpg'
    assert record['is_available'] is True


def test_parse_hit_handles_missing_and_malformed_values():
    payload = {
        'objectID': None,
        'title': 'Broken',
        'price': 'free',
        'featuredImage': {},
    }
    record = parse_hit(payload, extraction_time='2025-01-01T00:00:00Z')
    assert record['listing_id'] is None
    assert record['current_price'] is None
    assert record['image_url'] is None


def test_normalize_listing_record_is_idempotent_for_valid_input():
    payload = {
        'listing_id': 'abc',
        'title': '   Training Tee   ',
        'category': ' Menswear ',
        'brand': ' Gymshark ',
        'product_url': 'https://www.gymshark.com/products/training-tee',
        'sku': ' sku-1 ',
        'currency': 'gbp',
        'current_price': '39.99',
        'old_price': '49.99',
        'colour_name': 'Black',
        'available_colours': ['Black', 'White'],
    }
    normalized = normalize_listing_record(payload)
    assert normalized['title'] == 'Training Tee'
    assert normalized['category'] == 'Menswear'
    assert normalized['brand'] == 'Gymshark'
    assert normalized['currency'] == 'GBP'
    assert normalized['current_price'] == 39.99
    assert normalized['old_price'] == 49.99
