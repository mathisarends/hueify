from __future__ import annotations

from typing import TYPE_CHECKING

from hueify.shared.cache.lookup.base import EntityLookupCache

if TYPE_CHECKING:
    pass


class GroupedLightsLookupCache(EntityLookupCache["GroupedLightInfo"]):
    pass
