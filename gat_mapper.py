import urllib
from collections import deque
from typing import Tuple, Set
from urllib.parse import urlsplit

import networkx as nx
import requests
import requests.exceptions
from bs4 import BeautifulSoup
from pyvis.network import Network


class GATMapper:
    def __init__(self):
        self.URL = "https://www.globalapptesting.com/"
        self.urls_to_visit = deque()
        self.found_url = set()
        self.edges = set()
        self.external = set()
        self.broken = set()

    def create_map(self):
        self.urls_to_visit.append((self.URL, None))
        while self.urls_to_visit:
            url, from_url = self.urls_to_visit.pop()
            print("Visiting", url, "from", from_url)
            try:
                response = self._make_request(url)
            except requests.exceptions.RequestException as e:
                print(e)
                self.broken.add(url)
                continue
            soup = BeautifulSoup(response.text, "html.parser")
            self._find_links(soup, url)
        return self.edges

    def _make_request(self, url: str) -> requests.Response:
        response = requests.get(url)
        return response

    def _find_base_url(self, soup: BeautifulSoup) -> str:
        base_url = soup.find("base")
        if base_url is None:
            return ""
        return base_url.get("href", "")

    def _find_links(self, soup: BeautifulSoup, url: str) -> None:
        base_url = self._find_base_url(soup)

        for link in soup.find_all("a", href=True):
            link_url = link["href"]

            if link_url.startswith("mailto:"):
                continue

            if not link_url.startswith("http"):
                link_url = urllib.parse.urljoin(
                    url, urllib.parse.urljoin(base_url, link_url)
                )

            if link_url.startswith(self.URL):
                link_url = urllib.parse.urljoin(
                    link_url, urllib.parse.urlparse(link_url).path
                )
            else:
                self.external.add(link_url)

            if link_url not in self.found_url and link_url.startswith(self.URL):
                self.found_url.add(link_url)
                self.urls_to_visit.append((link_url, url))
                self.edges.add((url, link_url))


class GATMapVisualizer:
    def __init__(self, edges: Set[Tuple]):
        self.edges = edges

    def save_map(self):
        graph = self._create_graph()
        net = Network(width=1200, height=1200, directed=True)
        net.from_nx(graph)
        net.save_graph("gat_map.html")

    def _create_graph(self):
        graph = nx.DiGraph()
        graph.add_edges_from(self.edges)
        return graph


if __name__ == "__main__":
    edges = GATMapper().create_map()
    GATMapVisualizer(edges).save_map()
