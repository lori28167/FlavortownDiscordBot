import aiohttp
import asyncio
from typing import Optional, Dict, Any, List

BASE_URL = "https://flavortown.hackclub.com/api/v1"


class FlavorTownAPI:
    # Client for interacting with the Flavortown API

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = BASE_URL
        self.headers = {"Authorization": f"Bearer {api_key}"}

    async def _request(
        self, method: str, endpoint: str, params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        # Make an HTTP request to the API
        url = f"{self.base_url}{endpoint}"
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method, url, headers=self.headers, params=params
            ) as response:
                if response.status == 401:
                    raise ValueError("Invalid API key")
                if response.status == 404:
                    raise ValueError("Resource not found")
                if response.status >= 400:
                    error_data = await response.json()
                    raise ValueError(f"API Error: {error_data.get('error', 'Unknown error')}")
                return await response.json()

    async def get_projects(self, page: int = 1, query: Optional[str] = None) -> Dict:
        # Fetch a list of projects
        params = {"page": page}
        if query:
            params["query"] = query
        return await self._request("GET", "/projects", params)

    async def get_project(self, project_id: int) -> Dict:
        # Fetch a specific project by ID
        return await self._request("GET", f"/projects/{project_id}")

    async def create_project(
        self,
        title: str,
        description: str,
        repo_url: Optional[str] = None,
        demo_url: Optional[str] = None,
        readme_url: Optional[str] = None,
        ai_declaration: Optional[str] = None,
    ) -> Dict:
        # Create a new project
        data = {
            "title": title,
            "description": description,
        }
        if repo_url:
            data["repo_url"] = repo_url
        if demo_url:
            data["demo_url"] = demo_url
        if readme_url:
            data["readme_url"] = readme_url
        if ai_declaration:
            data["ai_declaration"] = ai_declaration

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/projects",
                headers=self.headers,
                data=data,
            ) as response:
                if response.status >= 400:
                    error_data = await response.json()
                    raise ValueError(f"API Error: {error_data.get('error', 'Unknown error')}")
                return await response.json()

    async def update_project(self, project_id: int, **kwargs) -> Dict:
        # Update an existing project
        async with aiohttp.ClientSession() as session:
            async with session.patch(
                f"{self.base_url}/projects/{project_id}",
                headers=self.headers,
                data=kwargs,
            ) as response:
                if response.status >= 400:
                    error_data = await response.json()
                    raise ValueError(f"API Error: {error_data.get('error', 'Unknown error')}")
                return await response.json()

    async def get_devlogs(self, page: int = 1) -> Dict:
        # Fetch all devlogs
        return await self._request("GET", "/devlogs", {"page": page})

    async def get_devlog(self, devlog_id: int) -> Dict:
        # Fetch a specific devlog by ID
        return await self._request("GET", f"/devlogs/{devlog_id}")

    async def get_store_items(self) -> List[Dict]:
        # Fetch all store items
        return await self._request("GET", "/store")

    async def get_store_item(self, item_id: int) -> Dict:
        # Fetch a specific store item by ID
        return await self._request("GET", f"/store/{item_id}")

    async def get_users(self, page: int = 1, query: Optional[str] = None) -> Dict:
        # Fetch a list of users
        params = {"page": page}
        if query:
            params["query"] = query
        return await self._request("GET", "/users", params)

    async def get_user(self, user_id: int) -> Dict:
        # Fetch a specific user by ID
        return await self._request("GET", f"/users/{user_id}")
