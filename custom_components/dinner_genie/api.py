from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

import aiohttp
import async_timeout


class DinnerGenieApiError(Exception):
    """Raised when the Savelio API returns an error."""


class DinnerGenieClient:
    def __init__(self, session: aiohttp.ClientSession, base_url: str, group_id: str, api_key: str) -> None:
        self.session = session
        self.base_url = base_url.rstrip("/")
        self.group_id = group_id.strip()
        self.api_key = api_key.strip()

    def _url(self, endpoint: str, params: dict[str, Any] | None = None) -> str:
        endpoint = endpoint.lstrip("/")
        url = f"{self.base_url}/groups/{self.group_id}/{endpoint}"
        if params:
            cleaned = {key: value for key, value in params.items() if value not in (None, "", "all")}
            if cleaned:
                url = f"{url}?{urlencode(cleaned)}"
        return url

    async def _get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        headers = {"X-API-Key": self.api_key}
        url = self._url(endpoint, params)

        try:
            async with async_timeout.timeout(20):
                async with self.session.get(url, headers=headers) as response:
                    try:
                        data = await response.json(content_type=None)
                    except Exception as err:
                        text = await response.text()
                        raise DinnerGenieApiError(f"Ongeldige API response: {text[:200]}") from err

                    if response.status >= 400:
                        message = data.get("error") if isinstance(data, dict) else None
                        raise DinnerGenieApiError(message or f"API fout {response.status}")

                    if not isinstance(data, dict):
                        raise DinnerGenieApiError("API response is geen JSON object")
                    return data
        except aiohttp.ClientError as err:
            raise DinnerGenieApiError(f"Kan Savelio niet bereiken: {err}") from err

    async def recipes(self, **filters: Any) -> dict[str, Any]:
        return await self._get("recipes", filters)

    async def random(self, **filters: Any) -> dict[str, Any]:
        return await self._get("random", filters)

    async def week_menus(self, limit: int = 1) -> dict[str, Any]:
        return await self._get("week-menus", {"limit": limit})

    async def validate(self) -> None:
        await self.recipes(limit=1)
