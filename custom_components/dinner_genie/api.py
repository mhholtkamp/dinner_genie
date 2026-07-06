from __future__ import annotations

import async_timeout
from typing import Any

import aiohttp


class DinnerGenieApiError(Exception):
    """Raised when the Dinner Genie API returns an error."""


class DinnerGenieClient:
    def __init__(self, session: aiohttp.ClientSession, base_url: str, group_id: str, api_key: str) -> None:
        self.session = session
        self.base_url = base_url.rstrip("/")
        self.group_id = group_id.strip().strip("/")
        self.api_key = api_key.strip()

    def _url(self, endpoint: str) -> str:
        endpoint = endpoint.strip("/")
        return f"{self.base_url}/groups/{self.group_id}/{endpoint}"

    async def _get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        headers = {
            "X-API-Key": self.api_key,
            "Accept": "application/json",
        }
        url = self._url(endpoint)

        try:
            async with async_timeout.timeout(20):
                async with self.session.get(url, headers=headers, params=params) as response:
                    text = await response.text()
                    if response.status >= 400:
                        raise DinnerGenieApiError(
                            f"Dinner Genie API fout {response.status}: {text[:300]}"
                        )
                    try:
                        data = await response.json()
                    except Exception as err:
                        raise DinnerGenieApiError("Dinner Genie gaf geen geldige JSON terug") from err
        except aiohttp.ClientError as err:
            raise DinnerGenieApiError(f"Kan Dinner Genie niet bereiken: {err}") from err

        if not isinstance(data, dict):
            raise DinnerGenieApiError("Dinner Genie response heeft een onverwacht formaat")

        return data

    async def async_test_connection(self) -> None:
        await self.recipes(limit=1)

    async def recipes(self, limit: int | None = None) -> dict[str, Any]:
        params = {"limit": limit} if limit else None
        return await self._get("recipes", params=params)

    async def random(self) -> dict[str, Any]:
        return await self._get("random", params={"recipeType": "dinner"})

    async def week_plan(self, days: int, servings: int) -> dict[str, Any]:
        return await self._get(
            "week-plan",
            params={
                "days": days,
                "servings": servings,
                "recipeType": "dinner",
            },
        )
