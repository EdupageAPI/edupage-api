from httpx import Response
from edupage_api.module import Module


class CustomRequest(Module):
    async def custom_request(self, url: str, method: str, data: str = "", headers: dict = {}) -> Response:
        if method == "GET":
            response = await self.edupage.session.get(url, headers=headers)
        elif method == "POST":
            response = await self.edupage.session.post(url, data=data, headers=headers)

        return response
