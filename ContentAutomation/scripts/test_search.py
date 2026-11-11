"""
Test DuckDuckGo and Wikipedia web search capability.
"""
import urllib.request
import urllib.parse
import json
import re

def search_ddg(query: str, max_results: int = 5) -> list[dict]:
    encoded = urllib.parse.quote(query)
    url = f"https://html.duckduckgo.com/html/?q={encoded}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    results = []
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            # Parse results
            # Result links
            links = re.findall(r'<a class="result__snippet[^"]*"[^>]*>(.*?)</a>', html, re.DOTALL)
            titles = re.findall(r'<a class="result__url[^"]*"[^>]*>(.*?)</a>', html, re.DOTALL)
            for i in range(min(len(links), max_results)):
                clean_snippet = re.sub(r"<[^>]+>", "", links[i]).strip()
                clean_url = re.sub(r"<[^>]+>", "", titles[i]).strip() if i < len(titles) else ""
                results.append({
                    "title": query,
                    "snippet": clean_snippet,
                    "url": f"https://{clean_url}" if clean_url and not clean_url.startswith("http") else clean_url,
                })
    except Exception as exc:
        print(f"DDG search error: {exc}")
    return results

def search_wikipedia(query: str) -> list[dict]:
    """Search Wikipedia API for encyclopedic topic grounding."""
    encoded = urllib.parse.quote(query)
    url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={encoded}&limit=3&namespace=0&format=json"
    results = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ContentAutomationBot/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if len(data) >= 4:
                titles = data[1]
                snippets = data[2]
                urls = data[3]
                for t, s, u in zip(titles, snippets, urls):
                    if s:
                        results.append({"title": t, "snippet": s, "url": u})
    except Exception as exc:
        print(f"Wikipedia search error: {exc}")
    return results

if __name__ == "__main__":
    test_q = "Llama 3 70B parameter model compute"
    print(f"Testing DDG search for '{test_q}':")
    ddg_res = search_ddg(test_q, max_results=3)
    print(f"  Got {len(ddg_res)} results:")
    for r in ddg_res:
        print(f"   • {r['snippet'][:120]}... ({r['url']})")

    print(f"\nTesting Wikipedia search for 'Large language model':")
    wiki_res = search_wikipedia("Large language model")
    for r in wiki_res:
        print(f"   • [{r['title']}] {r['snippet'][:120]}...")
