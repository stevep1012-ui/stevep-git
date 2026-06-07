"""Tests for subscription tiers and quotas."""

import pytest
from tools.youtube_healing.subscription import (
    SubscriptionTier,
    get_quota,
    can_upload,
    can_export_format,
    get_max_resolution,
    get_price,
)


def test_free_tier_quota():
    """Test Free tier quotas."""
    quota = get_quota(SubscriptionTier.FREE)
    assert quota.monthly_videos == 3
    assert quota.max_resolution == "720p"
    assert quota.concurrent_uploads == 1


def test_pro_tier_quota():
    """Test Pro tier quotas."""
    quota = get_quota(SubscriptionTier.PRO)
    assert quota.monthly_videos == 50
    assert quota.max_resolution == "4k"
    assert quota.concurrent_uploads == 3


def test_enterprise_tier_quota():
    """Test Enterprise tier quotas."""
    quota = get_quota(SubscriptionTier.ENTERPRISE)
    assert quota.monthly_videos == 1000
    assert quota.max_resolution == "8k"
    assert quota.concurrent_uploads == 10


def test_can_upload():
    """Test upload capability check."""
    assert can_upload(SubscriptionTier.FREE, 0) is True
    assert can_upload(SubscriptionTier.FREE, 1) is False
    assert can_upload(SubscriptionTier.PRO, 2) is True


def test_can_export_format():
    """Test export format availability."""
    assert can_export_format(SubscriptionTier.FREE, "mp4") is True
    assert can_export_format(SubscriptionTier.FREE, "webm") is False
    assert can_export_format(SubscriptionTier.PRO, "webm") is True


def test_get_max_resolution():
    """Test max resolution for tiers."""
    assert get_max_resolution(SubscriptionTier.FREE) == "720p"
    assert get_max_resolution(SubscriptionTier.PRO) == "4k"


def test_pricing():
    """Test tier pricing."""
    assert get_price(SubscriptionTier.FREE) == 0
    assert get_price(SubscriptionTier.PRO) == 9.99
