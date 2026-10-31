"""Multi-provider public web search with standard-library fallbacks.

No search key or cookies are required. Queries are sent to public search providers
only when a user explicitly selects web search / deep research.
"""
from __future__ import annotations

import concurrent.futures
import json
import re
import time
import ipaddress
from html import unescape
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote_plus, quote, urlparse, unquote, urljoin
from urllib.request import Request, urlopen, build_opener, HTTPRedirectHandler

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36 Avora/1.4.0"
HTTP_TIMEOUT = 5
MAX_HTML_BYTES = 2_000_000
MAX_PAGE_BYTES = 1_200_000
PAGE_TIMEOUT = 3.5


def _clean(value: str, max_len: int = 1200) -> str:
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", str(value or ""))).split())[:max_len]


def _absolute_url(value: str) -> str:
    """Normalize a public HTTP(S) URL and reject local/private literal targets."""
    url = unescape(str(value or "").strip())
    if url.startswith("//"):
        url = "https:" + url
    parsed = urlparse(url)
    if parsed.path == "/url" and (url.startswith("/url?") or (parsed.hostname or "").lower() in {"google.com", "www.google.com"}):
        wrapper = parse_qs(parsed.query)
        target = (wrapper.get("q") or wrapper.get("url") or [""])[0]
        if target:
            url = target
            parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or not parsed.hostname:
        return ""
    host = (parsed.hostname or "").rstrip(".").lower()
    if host in {"localhost", "localhost.localdomain"} or host.endswith((".local", ".localhost", ".internal")):
        return ""
    if parsed.username or parsed.password:
        return ""
    # Search results should not be able to expose arbitrary local service ports.
    try:
        if parsed.port is not None and parsed.port not in {80, 443}:
            return ""
    except ValueError:
        return ""
    try:
        address = ipaddress.ip_address(host.strip("[]"))
        if not address.is_global:
            return ""
    except ValueError:
        pass
    if host.endswith("duckduckgo.com") and parsed.path.startswith("/l/"):
        target = parse_qs(parsed.query).get("uddg", [""])[0]
        if target:
            url = unquote(target)
            parsed = urlparse(url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                return ""
    return url


def _get_text(url: str, timeout: int = HTTP_TIMEOUT) -> str:
    request = Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
        "Accept-Language": "it-IT,it;q=0.9,en;q=0.7",
    })
    with urlopen(request, timeout=timeout) as response:
        status = getattr(response, "status", 200)
        if status != 200:
            raise URLError(f"HTTP {status}")
        return response.read(MAX_HTML_BYTES).decode("utf-8", errors="replace")


class _DuckParser(HTMLParser):
    """Parser for DuckDuckGo HTML/lite result layouts."""
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.results: list[dict[str, str]] = []
        self._title_parts: list[str] = []
        self._snippet_parts: list[str] = []
        self._title_href = ""
        self._in_title = False
        self._in_snippet = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = set((attrs.get("class") or "").split())
        testid = attrs.get("data-testid", "")
        if tag == "a" and (classes.intersection({"result__a", "result-link", "result-title-link"}) or testid == "result-title-a"):
            self._in_title = True
            self._title_parts = []
            self._title_href = attrs.get("href", "")
        if classes.intersection({"result__snippet", "result-snippet", "result-snippet-text"}) or testid == "result-snippet":
            self._in_snippet = True
            self._snippet_parts = []

    def handle_data(self, data):
        if self._in_title:
            self._title_parts.append(data)
        if self._in_snippet:
            self._snippet_parts.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self._in_title:
            title = _clean("".join(self._title_parts), 300)
            url = _absolute_url(self._title_href)
            self._in_title = False
            if url and title:
                self.results.append({"title": title, "url": url, "snippet": ""})
        if tag in {"div", "a", "td", "span"} and self._in_snippet:
            snippet = _clean("".join(self._snippet_parts), 900)
            self._in_snippet = False
            if snippet:
                for item in reversed(self.results):
                    if not item["snippet"]:
                        item["snippet"] = snippet
                        break


class _BingParser(HTMLParser):
    """Small parser for Bing's b_algo list entries."""
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.results: list[dict[str, str]] = []
        self._in_result = False
        self._in_h2 = False
        self._in_anchor = False
        self._in_caption = False
        self._href = ""
        self._title: list[str] = []
        self._snippet: list[str] = []
        self._current: dict[str, str] | None = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = set((attrs.get("class") or "").split())
        if tag == "li" and "b_algo" in classes:
            self._in_result = True
            self._current = {"title": "", "url": "", "snippet": ""}
        elif self._in_result and tag == "h2":
            self._in_h2 = True
        elif self._in_result and tag == "a" and self._in_h2:
            self._in_anchor = True
            self._href = attrs.get("href", "")
            self._title = []
        elif self._in_result and classes.intersection({"b_caption", "b_snippet", "b_algoSlug"}):
            self._in_caption = True
            self._snippet = []

    def handle_data(self, data):
        if self._in_anchor:
            self._title.append(data)
        if self._in_caption:
            self._snippet.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self._in_anchor:
            self._in_anchor = False
            url = _absolute_url(self._href)
            title = _clean("".join(self._title), 300)
            if self._current is not None:
                self._current["url"] = url
                self._current["title"] = title
        elif tag == "h2" and self._in_h2:
            self._in_h2 = False
        elif tag in {"div", "p"} and self._in_caption:
            self._in_caption = False
            if self._current is not None:
                self._current["snippet"] = _clean("".join(self._snippet), 900)
        elif tag == "li" and self._in_result:
            self._in_result = False
            if self._current and self._current.get("url") and self._current.get("title"):
                self.results.append(self._current)
            self._current = None



class _ReadablePageParser(HTMLParser):
    """Extract readable text from ordinary pages while discarding navigation/code."""
    _SKIP_TAGS = {"script", "style", "noscript", "svg", "canvas", "nav", "footer", "header", "aside", "form", "button", "iframe", "template"}
    _BLOCK_TAGS = {"p", "h1", "h2", "h3", "h4", "li", "blockquote", "article", "section", "br", "tr"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._in_title = False
        self._title: list[str] = []
        self._description = ""
        self._parts: list[str] = []
        self._text_chars = 0
        self._body_seen = False

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag in self._SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag == "body":
            self._body_seen = True
        if tag == "title":
            self._in_title = True
        if tag == "meta" and (attributes.get("name") or "").lower() in {"description", "og:description"}:
            value = _clean(attributes.get("content", ""), 500)
            if value and len(value) > len(self._description):
                self._description = value
        if tag in self._BLOCK_TAGS:
            self._parts.append("\n")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_data(self, data):
        text = " ".join(str(data or "").split())
        if not text:
            return
        if self._in_title:
            self._title.append(text)
        elif self._skip_depth == 0:
            self._parts.append(text)
            self._text_chars += len(text)

    def handle_endtag(self, tag):
        if tag in self._SKIP_TAGS:
            if self._skip_depth:
                self._skip_depth -= 1
            return
        if tag == "title":
            self._in_title = False
        if self._skip_depth == 0 and tag in self._BLOCK_TAGS:
            self._parts.append("\n")

    def output(self) -> dict[str, str]:
        text = _clean(" ".join(self._parts), 6000)
        # Keep the first few content-rich fragments; do not pass boilerplate endlessly.
        title = _clean(" ".join(self._title), 300)
        if self._description and self._description not in text:
            text = (self._description + " " + text).strip()
        return {"page_title": title, "content": text[:2600], "description": self._description[:500]}


class _PublicRedirectHandler(HTTPRedirectHandler):
    """Prevent a search result from redirecting a page fetch to a local URL."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        absolute_target = urljoin(req.full_url, newurl)
        if not _absolute_url(absolute_target):
            return None
        return super().redirect_request(req, fp, code, msg, headers, absolute_target)


def _fetch_page_content(url: str, timeout: float = PAGE_TIMEOUT) -> dict[str, str]:
    """Fetch a public result page and extract a bounded text excerpt for grounded answers.

    Pages are treated as untrusted evidence: only text is returned, never executed.
    We skip binary files and validate the URL before following it.
    """
    safe_url = _absolute_url(url)
    if not safe_url:
        return {"page_title": "", "content": "", "description": ""}
    request = Request(safe_url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,text/plain,application/json;q=0.9,*/*;q=0.5",
        "Accept-Language": "it-IT,it;q=0.9,en;q=0.7",
    })
    try:
        opener = build_opener(_PublicRedirectHandler())
        with opener.open(request, timeout=timeout) as response:
            final_url = _absolute_url(response.geturl())
            if not final_url:
                return {"page_title": "", "content": "", "description": ""}
            content_type = str(response.headers.get("Content-Type", "")).lower()
            if content_type and not any(kind in content_type for kind in ("text/html", "application/xhtml+xml", "text/plain", "application/json", "application/xml", "text/xml")):
                return {"page_title": "", "content": "", "description": ""}
            raw = response.read(MAX_PAGE_BYTES)
    except Exception:
        return {"page_title": "", "content": "", "description": ""}
    text = raw.decode("utf-8", errors="replace")
    if "json" in content_type or "text/plain" in content_type or "xml" in content_type:
        clean = _clean(text, 2600)
        return {"page_title": "", "content": clean, "description": ""}
    parser = _ReadablePageParser()
    try:
        parser.feed(text)
        parser.close()
        return parser.output()
    except Exception:
        return {"page_title": "", "content": "", "description": ""}


def _enrich_results(results: list[dict[str, str]], max_pages: int = 3) -> list[dict[str, str]]:
    """Add actual page excerpts to a small number of search results in parallel."""
    if not results:
        return results
    selected = results[:max(0, min(int(max_pages), 4))]
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=len(selected) or 1, thread_name_prefix="avora-fetch")
    future_map = {executor.submit(_fetch_page_content, item["url"]): item for item in selected}
    try:
        for future in concurrent.futures.as_completed(future_map, timeout=PAGE_TIMEOUT + 0.75):
            item = future_map[future]
            try:
                page = future.result()
            except Exception:
                continue
            if page.get("content"):
                item["content"] = page["content"][:2600]
                if page.get("page_title") and len(page["page_title"]) > len(item.get("title", "")):
                    item["page_title"] = page["page_title"][:300]
                if not item.get("snippet") and page.get("description"):
                    item["snippet"] = page["description"][:900]
    except concurrent.futures.TimeoutError:
        pass
    finally:
        executor.shutdown(wait=False, cancel_futures=True)
    return results

def _search_duckduckgo(terms: str) -> list[dict[str, str]]:
    for base in ("https://html.duckduckgo.com/html/?q=", "https://lite.duckduckgo.com/lite/?q="):
        try:
            html = _get_text(base + quote_plus(terms))
            parser = _DuckParser()
            parser.feed(html)
            if parser.results:
                return parser.results
        except Exception:
            continue
    return []


class _GoogleParser(HTMLParser):
    """Parser for standard Google result anchors containing an h3 title."""
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.results: list[dict[str, str]] = []
        self._anchor_href = ""
        self._h3_depth = 0
        self._title_parts: list[str] = []
        self._title_href = ""

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a":
            self._anchor_href = attrs.get("href", "")
        elif tag == "h3":
            self._h3_depth += 1
            self._title_parts = []
            self._title_href = self._anchor_href

    def handle_data(self, data):
        if self._h3_depth:
            self._title_parts.append(data)

    def handle_endtag(self, tag):
        if tag == "h3" and self._h3_depth:
            self._h3_depth -= 1
            title = _clean("".join(self._title_parts), 300)
            url = _absolute_url(self._title_href)
            host = (urlparse(url).hostname or "").lower()
            if title and url and host not in {"google.com", "www.google.com", "accounts.google.com"} and not host.endswith(".google.com"):
                self.results.append({"title": title, "url": url, "snippet": ""})
            self._title_parts = []
        elif tag == "a":
            self._anchor_href = ""


def _search_google(terms: str) -> list[dict[str, str]]:
    url = "https://www.google.com/search?udm=14&num=10&q=" + quote_plus(terms)
    html = _get_text(url, timeout=5)
    parser = _GoogleParser()
    parser.feed(html)
    return parser.results


def _search_bing(terms: str) -> list[dict[str, str]]:
    html = _get_text("https://www.bing.com/search?q=" + quote_plus(terms) + "&count=10")
    parser = _BingParser()
    parser.feed(html)
    return parser.results


def _search_wikipedia(terms: str, language: str = "it") -> list[dict[str, str]]:
    """Encyclopedic fallback using MediaWiki's documented Action API."""
    api = f"https://{language}.wikipedia.org/w/api.php?action=query&list=search&format=json&utf8=1&srlimit=6&srsearch={quote_plus(terms)}"
    payload = json.loads(_get_text(api, timeout=6))
    results = []
    pages = payload.get("query", {}).get("search", [])
    for page in pages:
        title = _clean(page.get("title", ""), 300)
        if not title:
            continue
        url = f"https://{language}.wikipedia.org/wiki/{quote(title.replace(' ', '_'), safe='()_,-')}"
        results.append({"title": title, "url": url, "snippet": _clean(page.get("snippet", ""), 900)})
    return results


def _search_wikipedia_opensearch(terms: str, language: str = "it") -> list[dict[str, str]]:
    """A second, simpler MediaWiki endpoint if full-text search is restricted."""
    api = (f"https://{language}.wikipedia.org/w/api.php?action=opensearch&search={quote_plus(terms)}"
           "&limit=5&namespace=0&format=json")
    payload = json.loads(_get_text(api, timeout=5))
    if not isinstance(payload, list) or len(payload) < 4:
        return []
    output = []
    for title, snippet, url in zip(payload[1] or [], payload[2] or [], payload[3] or []):
        clean_url = _absolute_url(url)
        clean_title = _clean(title, 300)
        if clean_url and clean_title:
            output.append({"title": clean_title, "url": clean_url, "snippet": _clean(snippet, 900)})
    return output


def _search_ddg_instant(terms: str) -> list[dict[str, str]]:
    url = "https://api.duckduckgo.com/?" + "q=" + quote_plus(terms) + "&format=json&no_html=1&skip_disambig=1"
    payload = json.loads(_get_text(url, timeout=5))
    results: list[dict[str, str]] = []
    abstract_url = _absolute_url(payload.get("AbstractURL", ""))
    if abstract_url and payload.get("AbstractText"):
        results.append({"title": _clean(payload.get("Heading") or terms, 300), "url": abstract_url, "snippet": _clean(payload["AbstractText"], 900)})
    def walk(items):
        for item in items or []:
            if isinstance(item, dict):
                if item.get("FirstURL") and item.get("Text"):
                    candidate = _absolute_url(item["FirstURL"])
                    if candidate:
                        results.append({"title": _clean(item["Text"].split(" - ")[0], 300), "url": candidate, "snippet": _clean(item["Text"], 900)})
                walk(item.get("Topics"))
    walk(payload.get("RelatedTopics"))
    return results


class WebSearchUnavailable(RuntimeError):
    """No public search provider returned any usable results."""


def search_web(query: str, limit: int = 5) -> list[dict[str, str]]:
    """Search several no-key public sources; merge distinct result sets by URL.

    Every provider is capped to keep one broad encyclopedia response from hiding
    results from general web search. The search phase waits at most nine seconds.
    """
    terms = " ".join(str(query or "").split())[:400]
    if not terms:
        return []
    max_results = max(1, min(int(limit), 8))
    providers = (
        ("DuckDuckGo", _search_duckduckgo),
        ("Google", _search_google),
        ("Bing", _search_bing),
        ("DuckDuckGo Instant", _search_ddg_instant),
        ("Wikipedia IT", lambda q: _search_wikipedia(q, "it")),
        ("Wikipedia EN", lambda q: _search_wikipedia(q, "en")),
        ("Wikipedia OpenSearch", lambda q: _search_wikipedia_opensearch(q, "it")),
    )
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=len(providers), thread_name_prefix="avora-search")
    futures = {executor.submit(provider, terms): label for label, provider in providers}
    all_results: list[dict[str, str]] = []
    seen: set[str] = set()
    provider_count = 0
    deadline = time.monotonic() + 9.0
    try:
        pending = set(futures)
        while pending and time.monotonic() < deadline:
            done, pending = concurrent.futures.wait(
                pending, timeout=max(0.0, deadline - time.monotonic()),
                return_when=concurrent.futures.FIRST_COMPLETED,
            )
            if not done:
                break
            for future in done:
                source = futures[future]
                try:
                    results = future.result() or []
                except Exception:
                    continue
                accepted_from_provider = 0
                for item in results:
                    if accepted_from_provider >= 4 or len(all_results) >= max_results:
                        break
                    url = _absolute_url(item.get("url", ""))
                    if not url or url in seen:
                        continue
                    title = _clean(item.get("title", ""), 300) or urlparse(url).netloc
                    snippet = _clean(item.get("snippet", ""), 900)
                    seen.add(url)
                    all_results.append({"title": title, "url": url, "snippet": snippet, "source": source})
                    accepted_from_provider += 1
                if accepted_from_provider:
                    provider_count += 1
            # Once we have enough real links from at least two providers, don't make
            # the user wait for a slow provider that's already likely to time out.
            if len(all_results) >= max_results and provider_count >= 2:
                break
    finally:
        for future in futures:
            future.cancel()
        executor.shutdown(wait=False, cancel_futures=True)
    if not all_results:
        raise WebSearchUnavailable("Nessun motore di ricerca ha restituito risultati utilizzabili. Verifica la connessione Internet e riprova.")
    # Titles/snippets alone are too thin for a small local model. Read a few of the
    # actual public pages, with strict time and size limits, to ground the answer.
    selected = all_results[:max_results]
    return _enrich_results(selected, max_pages=min(3, len(selected)))
