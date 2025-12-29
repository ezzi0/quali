"""Platform adapters for advertising APIs"""

from .meta_marketing import MetaMarketingAdapter
from .google_ads import GoogleAdsAdapter
from .tiktok_ads import TikTokAdsAdapter

__all__ = [
    "MetaMarketingAdapter",
    "GoogleAdsAdapter",
    "TikTokAdsAdapter",
]
