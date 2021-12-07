from bs4 import BeautifulSoup
from bs4.element import Tag
import httpx
import asyncio


async def main():
    search = input("What do you want to search for?\n")
    url = f"https://www.x-kom.pl/szukaj?q={search}".replace(" ", "%20")
    html: httpx.Response = httpx.get(url, headers={'user-agent': 'product-web-scraper'})

    soup = BeautifulSoup(html, "lxml")
    num_of_pages = int(soup.find_all(class_="sc-1h16fat-0 sc-1xy3kzh-0 eqFjDt")[-1].text)
    num_of_pages_to_search = num_of_pages // 10 + 4 if num_of_pages > 9 else num_of_pages

    async with httpx.AsyncClient() as client:
        pages_html = (client.get(f"{url}&page={page}&sort_by=accuracy_desc") for page in
                      range(1, num_of_pages_to_search + 1))

        reqs = await asyncio.gather(*pages_html)

    htmls: list[str] = [req.text for req in reqs]
    dictionary_of_items: dict = get_product_dict_sorted_by_price(htmls)
    print(dictionary_of_items)


def get_product_dict_sorted_by_price(html_list: list[str]) -> dict[str: list[float | str]]:
    """This function gets list of html from a website and returns dictionary of product name as a key and list of price
    and link to the product as a value, sorted by price. Moreover, returned dictionary is also filtered by a category
    of the first product that appears."""

    dictionary_of_items: dict[str: list[float | str]] = {}
    list_of_category_acc_order: list[str] = []

    for html in html_list:
        soup = BeautifulSoup(html, "lxml")
        for product in soup.find_all(class_="sc-1yu46qn-9 klYVjF sc-16zrtke-0 cDhuES"):
            product: Tag

            title: str = product["title"]
            product_name: str = next(product.children).text
            category: str = title[0: len(title) - len(product_name)]
            link = f"https://www.x-kom.pl{product.parent['href']}"

            specs_div: Tag = product.find_parent(class_="sc-1yu46qn-10 iQhjQS")
            price_div: Tag = specs_div.next_sibling.find_next(class_="sc-6n68ef-0 sc-6n68ef-3 hIoPZN")

            price: str = price_div.text
            price_float: float = float(price[0: -2].replace(",", ".").replace(" ", ""))

            if category not in list_of_category_acc_order:
                list_of_category_acc_order.append(category)

            if (product_name not in dictionary_of_items) or (price_float < dictionary_of_items[product_name][0]):
                dictionary_of_items[product_name] = [price_float, link, category]

    dictionary_of_items = {k: v for k, v in
                           filter(lambda item: item[1][2] == list_of_category_acc_order[0], dictionary_of_items.items())
                           }

    return {k: v for k, v in sorted(dictionary_of_items.items(), key=lambda item: item[1][0])}


if __name__ == "__main__":
    asyncio.run(main())
