from bs4 import BeautifulSoup
import httpx
import asyncio


async def main():
    search = input("What do you want to search for?\n")
    url = f"https://www.x-kom.pl/szukaj?q={search}".replace(" ", "%20")
    html = httpx.get(url, headers={'user-agent': 'product-web-scraper'})

    soup = BeautifulSoup(html, "lxml")
    num_of_pages = int(soup.find_all(class_="sc-1h16fat-0 sc-1xy3kzh-0 eqFjDt")[-1].text)

    async with httpx.AsyncClient() as client:
        pages_html = (client.get(f"{url}&page={page}&sort_by=accuracy_desc") for page in range(1, num_of_pages + 1))

        reqs = await asyncio.gather(*pages_html)

    htmls = [req.text for req in reqs]

    for html in htmls:
        soup = BeautifulSoup(html, "lxml")
        for product in soup.find_all(class_="sc-1yu46qn-9 klYVjF sc-16zrtke-0 cDhuES"):
            title = product["title"]
            product_name = next(product.children).text
            category = title[0: len(title) - len(product_name)]
            link = f"https://www.x-kom.pl{product.parent['href']}"
            specs_div = product.parent.parent.parent.next_sibling
            print(product)
            print(link)
            #print(category)
            #print(product_name)
            #print(title)

if __name__ == "__main__":
    asyncio.run(main())
