from bs4 import BeautifulSoup
import grequests

html = grequests.get("https://www.amazon.pl/s?k=rtx+3080&rh=n%3A20788256031%2Cn%3A20788599031&dc&__mk_pl_PL=%C3%85M%C3%85%C5%BD%C3%95%C3%91&qid=1638022020&rnid=20876086031&ref=sr_nr_n_2")
text = grequests.map([html])[0].text

soup = BeautifulSoup(text, "lxml")

list_of_prices = soup.find_all("span", class_="a-offscreen")

for price in list_of_prices:
    print(price.text)

