from bs4 import BeautifulSoup
import httpx
import asyncio


async def main():
    product = input("What do you want to search for?\n")
    url = f"https://www.x-kom.pl/szukaj?q={product}".replace(" ", "%20")
    html = httpx.get(url, headers={'user-agent': 'product-web-scraper'})

    soup = BeautifulSoup(html, "lxml")
    num_of_pages = int(soup.find_all(class_="sc-1h16fat-0 sc-1xy3kzh-0 eqFjDt")[-1].text)

    async with httpx.AsyncClient() as client:
        pages_html = (client.get(f"{url}&{page}&sort_by=accuracy_desc") for page in range(1, num_of_pages + 1))
        reqs = await asyncio.gather(*pages_html)

if __name__ == "__main__":
    asyncio.run(main())
