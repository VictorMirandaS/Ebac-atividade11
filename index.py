import requests
import time
import csv
import random
import concurrent.futures
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

MAX_THREADS = 10
BASE_URL = "https://havokkmorands.github.io"


def extract_movie_details(movie_link):
    time.sleep(random.uniform(0, 0.2))
    try:
        response = requests.get(movie_link, headers=headers, timeout=20)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Erro ao acessar {movie_link}: {e}")
        return None

    movie_soup = BeautifulSoup(response.content, "html.parser")
    detail_container = movie_soup.find("section", attrs={"data-testid": "movie-detail"})

    if detail_container is None:
        print(f"Detalhe do filme não encontrado: {movie_link}")
        return None

    title_tag     = detail_container.find(attrs={"data-testid": "movie-title"})
    release_tag   = detail_container.find(attrs={"data-testid": "movie-release"})
    rating_tag    = detail_container.find(attrs={"data-testid": "movie-rating"})
    synopsis_tag  = detail_container.find(attrs={"data-testid": "movie-synopsis"})

    title     = title_tag.get_text(strip=True) if title_tag else None
    date      = release_tag.get_text(strip=True).replace("Lançamento:", "").strip() if release_tag else None
    rating    = rating_tag.get_text(strip=True).replace("Nota:", "").strip() if rating_tag else None
    plot_text = synopsis_tag.get_text(strip=True).replace("Sinopse:", "").strip() if synopsis_tag else None

    if all([title, date, rating, plot_text]):
        return [title, date, rating, plot_text]

    return None


def extract_movies(soup):
    container = soup.find("section", attrs={"data-testid": "movies-list"})
    if container is None:
        print("Container principal não encontrado.")
        with open("debug.html", "w", encoding="utf-8") as f:
            f.write(soup.prettify())
        return

    movies_table = container.find_all("article", attrs={"data-testid": "movie-item"})
    if not movies_table:
        print("Lista de filmes não encontrada.")
        return

    movie_links = []
    for movie in movies_table:
        a_tag = movie.find("a", attrs={"data-testid": "movie-link"}, href=True)
        if a_tag:
            movie_links.append(BASE_URL + "/" + a_tag["href"])

    if not movie_links:
        print("Nenhum link de filme foi encontrado.")
        with open("debug_links.html", "w", encoding="utf-8") as f:
            f.write(container.prettify())
        return

    threads = min(MAX_THREADS, len(movie_links))
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        results = list(executor.map(extract_movie_details, movie_links))

    # Escreve o CSV uma única vez, com cabeçalho
    movies = [r for r in results if r is not None]
    with open("movies.csv", mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["title", "release_date", "rating", "synopsis"])
        writer.writerows(movies)

    print(f"{len(movies)} filmes salvos em movies.csv")


def main():
    start_time = time.time()
    popular_movies_url = f"{BASE_URL}/movie-catalog/"
    
    try:
        response = requests.get(popular_movies_url, headers=headers, timeout=20)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Erro ao acessar a página principal: {e}")
        return

    print("Status:", response.status_code)
    print("URL final:", response.url)

    soup = BeautifulSoup(response.content, "html.parser")
    extract_movies(soup)

    print(f"Tempo total: {time.time() - start_time:.2f}s")


if __name__ == "__main__":
    main()