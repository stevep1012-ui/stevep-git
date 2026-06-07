"""Subscription tiers and quota management."""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
from typing import Dict


class SubscriptionTier(str, Enum):
    """Available subscription tiers."""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


@dataclass
class SubscriptionQuota:
    """Quota limits for each tier."""
    monthly_videos: int
    max_resolution: str
    max_file_size_gb: int
    export_formats: list[str]
    api_calls_per_month: int
    concurrent_uploads: int
    has_priority_support: bool
    has_custom_branding: bool


SUBSCRIPTION_QUOTAS: Dict[SubscriptionTier, SubscriptionQuota] = {
    SubscriptionTier.FREE: SubscriptionQuota(
        monthly_videos=3,
        max_resolution="720p",
        max_file_size_gb=1,
        export_formats=["mp4"],
        api_calls_per_month=100,
        concurrent_uploads=1,
        has_priority_support=False,
        has_custom_branding=False,
    ),
    SubscriptionTier.PRO: SubscriptionQuota(
        monthly_videos=50,
        max_resolution="4k",
        max_file_size_gb=5,
        export_formats=["mp4", "webm", "mov"],
        api_calls_per_month=5000,
        concurrent_uploads=3,
        has_priority_support=True,
        has_custom_branding=False,
    ),
    SubscriptionTier.ENTERPRISE: SubscriptionQuota(
        monthly_videos=1000,
        max_resolution="8k",
        max_file_size_gb=50,
        export_formats=["mp4", "webm", "mov", "mkv"],
        api_calls_per_month=100000,
        concurrent_uploads=10,
        has_priority_support=True,
        has_custom_branding=True,
    ),
}


def get_quota(tier: str | SubscriptionTier) -> SubscriptionQuota:
    """Get quota for a subscription tier."""
    if isinstance(tier, str):
        tier = SubscriptionTier(tier)
    return SUBSCRIPTION_QUOTAS.get(tier, SUBSCRIPTION_QUOTAS[SubscriptionTier.FREE])


def can_upload(tier: str, current_uploads: int) -> bool:
    """Check if user can start a new upload."""
    quota = get_quota(tier)
    return current_uploads < quota.concurrent_uploads


def can_export_format(tier: str, format: str) -> bool:
    """Check if format is available for tier."""
    quota = get_quota(tier)
    return format in quota.export_formats


def get_max_resolution(tier: str) -> str:
    """Get maximum resolution for tier."""
    quota = get_quota(tier)
    return quota.max_resolution


TIER_PRICING = {
    SubscriptionTier.FREE: 0,
    SubscriptionTier.PRO: 9.99,
    SubscriptionTier.ENTERPRISE: 99.99,
}


def get_price(tier: str | SubscriptionTier) -> float:
    """Get monthly price for tier."""
    if isinstance(tier, str):
        tier = SubscriptionTier(tier)
    return TIER_PRICING.get(tier, 0)
