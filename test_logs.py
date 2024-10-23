import time
import requests
import asyncio
import aiohttp

REPO = "telegram-clone"
OWNER = "abdulazizkomilov"
JOB_ID = "11472282466"
GITHUB_TOKEN = "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"


async def stream_logs():
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/actions/jobs/{JOB_ID}/logs"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                async for line in response.content:
                    print(line.decode().strip())
            else:
                print(f"Failed to fetch logs: {response.status}")


if __name__ == "__main__":
    asyncio.run(stream_logs())
