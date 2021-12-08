import curses
from curses import wrapper, window
from constant import *
from bs4 import BeautifulSoup
from bs4.element import Tag
import httpx
import asyncio


async def xkom_search(search: str) -> dict[str: list[float | str | bool]]:
    """This function takes what it will search for in x-kom store and it will return a dictionary of items sorted by
    the best price. Product name is the key and list containing price, link, category and info about availability."""
    url = f"https://www.x-kom.pl/szukaj?q={search}".replace(" ", "%20")
    html: httpx.Response = httpx.get(url, headers={'user-agent': 'product-web-scraper'})

    soup = BeautifulSoup(html, "lxml")
    list_of_pages_buttons: list[Tag] = soup.find_all(class_="sc-1h16fat-0 sc-1xy3kzh-0 eqFjDt")
    num_of_pages = int(list_of_pages_buttons[-1].text) if len(list_of_pages_buttons) > 0 else 1
    num_of_pages_to_search = num_of_pages // 10 + 4 if num_of_pages > 9 else num_of_pages

    async with httpx.AsyncClient() as client:
        pages_html = (client.get(f"{url}&page={page}&sort_by=accuracy_desc") for page in
                      range(1, num_of_pages_to_search + 1))

        reqs = await asyncio.gather(*pages_html)

    htmls: list[str] = [req.text for req in reqs]
    dictionary_of_items: dict = get_product_dict_sorted_by_price(search, htmls)
    return dictionary_of_items


def get_product_dict_sorted_by_price(search: str, html_list: list[str]) -> dict[str: list[float | str | bool]]:
    """This function gets list of html from a website and the item searched. It returns dictionary of product name as
    a key and list of price and link to the product as a value, sorted by price. Moreover, returned dictionary is also
    filtered by a category of the first product that appears."""

    dictionary_of_items: dict[str: list[float | str | bool]] = {}
    list_of_category_acc_order: list[str] = []

    for html in html_list:
        soup = BeautifulSoup(html, "lxml")
        for product in soup.find_all(class_="sc-1yu46qn-9 klYVjF sc-16zrtke-0 cDhuES"):
            product: Tag

            title: str = product["title"]
            product_name: str = next(product.children).text.strip()
            category: str = title[0: len(title) - len(product_name)].strip()
            link = f"https://www.x-kom.pl{product.parent['href']}"

            specs_div: Tag = product.find_parent(class_="sc-1yu46qn-10 iQhjQS")
            price_div: Tag = specs_div.next_sibling.find_next(class_="sc-6n68ef-0 sc-6n68ef-3 hIoPZN")
            cart_button_div: Tag = specs_div.parent.next_sibling
            button: Tag = cart_button_div.find(class_="sc-15ih3hi-0 sc-1yu46qn-1 hzpsVQ sc-1j3ie3s-1 jBRfGl")
            chip: str = specs_div.find(class_="vb9gxz-2 fNMXGL").text

            price: str = price_div.text
            price_float: float = float(price[0: -2].replace(",", ".").replace(" ", ""))

            if category not in list_of_category_acc_order:
                list_of_category_acc_order.append(category)

            if ((product_name not in dictionary_of_items) or (price_float < dictionary_of_items[product_name][0])) and (
                chip[-len(search):].lower() == search.lower()
            ):
                dictionary_of_items[product_name] = [price_float, link, category, not button.has_attr("disabled")]

    dictionary_of_items = {k: v for k, v in
                           filter(lambda item: item[1][2] == list_of_category_acc_order[0], dictionary_of_items.items())
                           }

    return {k: v for k, v in sorted(dictionary_of_items.items(), key=lambda item: item[1][0])}


def print_result(dict_of_items: dict[str: list[float | str | bool]], stdscr: window, company: str) -> None:
    """This function prints product in an aesthetic way."""

    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    gpu_text_color = curses.color_pair(1 if company == "n" else 2)

    for i, gpu_info in enumerate(dict_of_items.items()):
        # print(gpu_info)
        stdscr.addstr(f"{gpu_info[0]} ", gpu_text_color)
        stdscr.addstr(f"Price: {gpu_info[1][0]} Available: {'yes' if gpu_info[1][3] else 'no'} | ")
        stdscr.addstr("\n") if i % 3 == 2 else None
        stdscr.refresh()

    stdscr.addstr("\n")
    stdscr.refresh()


async def main(stdscr: window) -> None:
    """Main function responsible for getting GPUs info and displaying it."""
    stdscr.clear()
    list_of_nvidia_gpus_dict = []
    list_of_amd_gpus_dict = []

    stdscr.addstr("Waiting for Nvidia GPUS...\n")
    stdscr.refresh()

    try:
        list_of_nvidia_gpus_dict = await asyncio.gather(*(xkom_search(gpu) for gpu in LIST_OF_NVIDIA_GPUS))
    except OSError:
        stdscr.addstr("Something went wrong!")

    for gpu in list_of_nvidia_gpus_dict:
        print_result(gpu, stdscr, "n")

    stdscr.addstr("Waiting for AMD GPUS...\n")
    stdscr.refresh()

    try:
        list_of_amd_gpus_dict = await asyncio.gather(*(xkom_search(gpu) for gpu in LIST_OF_AMD_GPUS))
    except OSError:
        stdscr.addstr("Something went wrong!")

    for gpu in list_of_amd_gpus_dict:
        print_result(gpu, stdscr, "a")

    stdscr.getch()

if __name__ == "__main__":
    asyncio.run(wrapper(main))
