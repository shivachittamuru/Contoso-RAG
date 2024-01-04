from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from starlette import status
import httpx

router = APIRouter(prefix="/proxy",tags=["proxy"])

@router.get('/', status_code=status.HTTP_200_OK)
async def proxy(request: Request, query: str):
    token = request.cookies.get("auth_token")
    print(f'token {token}')
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Assemble the URL for the destination API
    url = f"http://localhost:8000/agent/chat/stream?query={query}"

    # Set up the client with headers
    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Send the request and stream the response
    async with httpx.AsyncClient() as client:
        async with client.stream("GET", url, headers=headers) as response:

            # Check if the request was successful
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Upstream API error")
            
            # Stream the response back to the client
            async def response_generator():
                async for chunk in response.aiter_bytes():
                    yield chunk

            return StreamingResponse(response_generator(), media_type=response.headers["Content-Type"])
