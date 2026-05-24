import asyncio
import httpx

BASE_URL = "http://127.0.0.1:8000"

async def main():
    async with httpx.AsyncClient(timeout=120) as client:
        # 登入
        res = await client.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "1234"})
        token = res.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"登入成功")

        """
        # 觸發爬蟲
        res = await client.post(f"{BASE_URL}/crawl/1", headers=headers)
        print(f"爬蟲: {res.json()}")

        # 看圖片
        res = await client.get(f"{BASE_URL}/images/", headers=headers)
        images = res.json()
        print(f"圖片數量: {len(images)}")
        for img in images[:3]:
            print(f"  - {img['original_url']}")
        """
        """
        res = await client.get(f"{BASE_URL}/images/search?tag=Character Design", headers=headers)
        print(f"搜尋結果: {len(res.json())} 張")
        """
        """
        res = await client.get(f"{BASE_URL}/images/?page=1&size=5", headers=headers)
        print(f"第一頁: {len(res.json())} 張")

        res = await client.get(f"{BASE_URL}/images/?page=2&size=5", headers=headers)
        print(f"第二頁: {len(res.json())} 張")
        """
        res = await client.get(f"{BASE_URL}/images/1", headers=headers)
        print(f"圖片細節: {res.json()}")
        res = await client.get(f"{BASE_URL}/images/1", headers=headers)
        print(f"圖片細節: {res.json()}")


asyncio.run(main())