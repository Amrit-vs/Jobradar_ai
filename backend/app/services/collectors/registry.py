from app.services.collectors.adobe import AdobeAdapter
from app.services.collectors.amazon import AmazonAdapter
from app.services.collectors.base import JobSourceAdapter
from app.services.collectors.google import GoogleAdapter
from app.services.collectors.microsoft import MicrosoftAdapter
from app.services.collectors.nvidia import NvidiaAdapter


class CompanyAdapterRegistry:
    def __init__(self, adapters: list[JobSourceAdapter] | None = None):
        self._adapters = adapters or [GoogleAdapter(), MicrosoftAdapter(), AmazonAdapter(), NvidiaAdapter(), AdobeAdapter()]

    def enabled_adapters(self) -> list[JobSourceAdapter]:
        return list(self._adapters)

