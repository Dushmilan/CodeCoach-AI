import httpx
import asyncio

async def test_api():
    async with httpx.AsyncClient() as client:
        # Simulate a request to /api/run/
        response = await client.post("http://localhost:8000/api/run/", json={
            "language": "python",
            "code": "print('hello')",
            "version": "3.10"
        }, headers={"Authorization": "Bearer invalid-token"})
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")

asyncio.run(test_api())
