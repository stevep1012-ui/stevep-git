#!/usr/bin/env python3
"""
Scrapling 으로 'Hybrid Human-AI Cooperation' 관련 논문 메타데이터를 수집한다.

설치:
    pip install "scrapling[fetchers]"

실행:
    python find_paper.py

주의: 인터넷에 직접 나갈 수 있는 환경에서 실행해야 한다.
(Claude Code 웹 샌드박스는 아웃바운드가 차단되어 동작하지 않음)

검증 환경: scrapling 0.4.8 (Response API: .css / .xpath / .find, node.text / node.attrib)
"""
from scrapling.fetchers import Fetcher


def first_text(page, selector):
    nodes = page.css(selector)
    return nodes[0].text.strip() if nodes and nodes[0].text else None


def all_text(page, selector):
    return [n.text.strip() for n in page.css(selector) if n.text and n.text.strip()]


def fetch_arxiv(arxiv_id: str) -> dict | None:
    """arXiv 공식 Atom API 로 메타데이터를 가져온다 (JS 불필요, 안정적)."""
    url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
    page = Fetcher.get(url, stealthy_headers=True, timeout=30)
    if page.status != 200:
        print(f"  [arXiv {arxiv_id}] HTTP {page.status}")
        return None

    pdf = None
    for link in page.css("entry link"):
        if link.attrib.get("title") == "pdf":
            pdf = link.attrib.get("href")

    return {
        "id": arxiv_id,
        "title": first_text(page, "entry > title"),
        "authors": all_text(page, "entry author > name"),
        "published": first_text(page, "entry > published"),
        "doi": first_text(page, "entry arxiv\\:doi") or first_text(page, "entry doi"),
        "pdf": pdf,
        "abstract": first_text(page, "entry > summary"),
    }


def search_arxiv(query: str, max_results: int = 5) -> list[dict]:
    """제목/초록 키워드로 arXiv 를 검색한다."""
    from urllib.parse import quote_plus
    url = (
        "http://export.arxiv.org/api/query?"
        f"search_query=all:{quote_plus(query)}"
        f"&start=0&max_results={max_results}&sortBy=relevance"
    )
    page = Fetcher.get(url, stealthy_headers=True, timeout=30)
    if page.status != 200:
        print(f"  [search] HTTP {page.status}")
        return []
    results = []
    for entry in page.css("entry"):
        title = entry.css("title")
        results.append({
            "title": title[0].text.strip() if title else None,
            "authors": [n.text.strip() for n in entry.css("author > name")],
            "id": (entry.css("id")[0].text if entry.css("id") else "").rsplit("/", 1)[-1],
        })
    return results


if __name__ == "__main__":
    print("=== 키워드 검색: 'Modelling Hybrid Human-AI Cooperation' ===")
    for r in search_arxiv("Modelling Hybrid Human AI Cooperation", max_results=5):
        print(f"  - [{r['id']}] {r['title']}  ({', '.join(r['authors'][:3])} …)")

    print("\n=== 주요 후보 상세 ===")
    for aid in ["2306.17747", "2402.05605"]:
        info = fetch_arxiv(aid)
        if not info:
            continue
        print(f"\n[{info['id']}] {info['title']}")
        print(f"  Authors  : {', '.join(info['authors'])}")
        print(f"  Published: {info['published']}   DOI: {info['doi']}")
        print(f"  PDF      : {info['pdf']}")
        print(f"  Abstract : {(info['abstract'] or '')[:400]}…")
