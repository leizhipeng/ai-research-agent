"""Bounded scholarly discovery, retained text, and conservative deduplication.

Only the two fixed scholarly API hosts and arXiv HTML are fetched. Retrieved
material is data, never an instruction to the application or its model.
"""

from __future__ import annotations

import hashlib
import json
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Callable
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from typing import Any

from research_agent.models.workflow import Retrieval, Source

CacheGet = Callable[[str], dict[str, Any] | None]
CacheSet = Callable[[str, dict[str, Any]], None]
_ARXIV_LOCK = threading.Lock()
_LAST_ARXIV_REQUEST = 0.0
_RETRY_STATUSES = {429, 500, 502, 503, 504}
_ARXIV_ID = re.compile(r"(?:\d{4}\.\d{4,5}|[a-z][a-z.\-]+/\d{7})(?:v\d+)?", re.I)


class DiscoveryError(RuntimeError):
    """A provider or retrieval failure safe to persist without credentials."""


class _AllowedRedirects(urllib.request.HTTPRedirectHandler):
    def __init__(self, before_request, remaining_seconds):
        self.before_request = before_request
        self.remaining_seconds = remaining_seconds

    def redirect_request(self, request, response, code, message, headers, new_url):
        origin = urllib.parse.urlsplit(request.full_url)
        target = urllib.parse.urlsplit(new_url)
        if target.scheme != "https" or target.hostname != origin.hostname:
            raise DiscoveryError("provider redirected outside its original HTTPS host")
        if target.hostname in {"export.arxiv.org", "arxiv.org"}:
            # The enclosing retrieval already holds the arXiv lock.
            global _LAST_ARXIV_REQUEST
            _wait(max(0, 3 - (time.monotonic() - _LAST_ARXIV_REQUEST)), self.remaining_seconds)
        if self.before_request:
            self.before_request()
        request.timeout = min(request.timeout, self.remaining_seconds())
        if request.timeout <= 0:
            raise DiscoveryError("remaining redirect time is exhausted")
        if target.hostname in {"export.arxiv.org", "arxiv.org"}:
            _LAST_ARXIV_REQUEST = time.monotonic()
        return super().redirect_request(request, response, code, message, headers, new_url)


def _wait(delay: float, remaining_seconds: Callable[[], float] | None) -> None:
    """Preserve provider delays, or stop when there is no time to honor them."""
    delay = max(0, delay)
    if remaining_seconds and delay >= remaining_seconds():
        raise DiscoveryError("provider delay exceeds remaining retrieval time")
    if delay:
        time.sleep(delay)


def _get(
    url: str,
    *,
    timeout: float = 20,
    max_bytes: int = 2_000_000,
    openalex_api_key: str | None = None,
    cache_get: CacheGet | None = None,
    cache_set: CacheSet | None = None,
    before_request: Callable[[], None] | None = None,
    on_bytes: Callable[[int], None] | None = None,
    on_retry: Callable[[str], None] | None = None,
    remaining_seconds: Callable[[], float] | None = None,
) -> dict[str, Any]:
    """Cache successful bounded reads; retry transient failures at most twice."""
    if not 0 < timeout <= 300 or not 1 <= max_bytes <= 20_000_000:
        raise ValueError("timeout must be 0..300 seconds; max_bytes must be 1..20,000,000")
    host = urllib.parse.urlsplit(url).hostname
    if host not in {"export.arxiv.org", "api.openalex.org", "arxiv.org"}:
        raise ValueError("retrieval host is outside the scholarly-provider allowlist")
    cache_key = "http:" + hashlib.sha256(url.encode()).hexdigest()
    cached = cache_get(cache_key) if cache_get else None
    if cached and len(cached["body"].encode()) <= max_bytes:
        return {**cached, "cache_hit": True}
    headers = {"User-Agent": "ai-research-agent/0.2 (personal scholarly research demo)"}
    if host == "api.openalex.org" and openalex_api_key:
        headers["Authorization"] = "Bearer " + openalex_api_key
    for attempt in range(3):
        try:
            # Serialize arXiv network calls, including retries and HTML reads.
            # This process-wide limit cannot coordinate independent CLI processes.
            if host in {"export.arxiv.org", "arxiv.org"}:
                with _ARXIV_LOCK:
                    global _LAST_ARXIV_REQUEST
                    _wait(max(0, 3 - (time.monotonic() - _LAST_ARXIV_REQUEST)), remaining_seconds)
                    if before_request:
                        before_request()
                    _LAST_ARXIV_REQUEST = time.monotonic()
                    effective_timeout = (
                        min(timeout, remaining_seconds()) if remaining_seconds else timeout
                    )
                    result = _read_response(
                        url,
                        headers,
                        effective_timeout,
                        max_bytes,
                        on_bytes,
                        remaining_seconds,
                        before_request,
                    )
            else:
                if before_request:
                    before_request()
                effective_timeout = (
                    min(timeout, remaining_seconds()) if remaining_seconds else timeout
                )
                result = _read_response(
                    url,
                    headers,
                    effective_timeout,
                    max_bytes,
                    on_bytes,
                    remaining_seconds,
                    before_request,
                )
            if cache_set:
                cache_set(cache_key, result)
            return {**result, "cache_hit": False}
        except urllib.error.HTTPError as exc:
            status = exc.code
            retry_after = exc.headers.get("Retry-After", "")
            exc.close()
            if status not in _RETRY_STATUSES or attempt == 2:
                suffix = (
                    " (configure OPENALEX_API_KEY or wait for the provider budget reset)"
                    if host == "api.openalex.org" and status in {401, 403, 409, 429}
                    else ""
                )
                raise DiscoveryError(f"{host}: HTTP {status}{suffix}") from None
            # Do not violate a long provider Retry-After just to continue quickly.
            try:
                delay = float(retry_after) if retry_after else 2**attempt
            except ValueError:
                try:
                    delay = (
                        parsedate_to_datetime(retry_after) - datetime.now(timezone.utc)
                    ).total_seconds()
                except (TypeError, ValueError, OverflowError):
                    raise DiscoveryError(
                        f"{host}: HTTP {status}; unrecognized Retry-After header"
                    ) from None
            if delay > 10:
                raise DiscoveryError(
                    f"{host}: HTTP {status}; Retry-After exceeds this demo's 10-second retry allowance"
                ) from None
            if on_retry:
                on_retry(f"{host}: HTTP {status}; retry {attempt + 1}/2")
            _wait(delay, remaining_seconds)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            if attempt == 2:
                raise DiscoveryError(
                    f"{host}: network timeout or connection failure ({type(exc).__name__})"
                ) from None
            if on_retry:
                on_retry(f"{host}: connection failure; retry {attempt + 1}/2")
            _wait(2**attempt, remaining_seconds)
    raise AssertionError("unreachable")


def _read_response(
    url: str,
    headers: dict[str, str],
    timeout: float,
    max_bytes: int,
    on_bytes: Callable[[int], None] | None,
    remaining_seconds: Callable[[], float] | None,
    before_request: Callable[[], None] | None,
) -> dict[str, Any]:
    if timeout <= 0:
        raise DiscoveryError("remaining retrieval time is exhausted")
    deadline = time.monotonic() + timeout

    def time_left():
        return min(
            deadline - time.monotonic(), remaining_seconds() if remaining_seconds else timeout
        )

    request = urllib.request.Request(url, headers=headers)
    with urllib.request.build_opener(_AllowedRedirects(before_request, time_left)).open(
        request, timeout=timeout
    ) as response:
        if urllib.parse.urlsplit(response.url).hostname not in {
            "export.arxiv.org",
            "api.openalex.org",
            "arxiv.org",
        }:
            raise DiscoveryError("provider redirected outside the allowed scholarly hosts")
        parts = []
        total = 0
        read_block = getattr(response, "read1", response.read)
        while True:
            if time_left() <= 0:
                raise DiscoveryError("bounded retrieval time is exhausted")
            block = read_block(min(65_536, max_bytes - total + 1))
            if not block:
                break
            total += len(block)
            if on_bytes:
                on_bytes(len(block))
            if total > max_bytes:
                raise DiscoveryError("provider response exceeds configured byte limit")
            parts.append(block)
        return {
            "body": b"".join(parts).decode("utf-8", errors="replace"),
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "url": response.url,
            "content_type": response.headers.get("Content-Type", ""),
            "usage": {
                name: response.headers[name]
                for name in (
                    "X-RateLimit-Limit",
                    "X-RateLimit-Remaining",
                    "X-RateLimit-Credits-Used",
                    "X-RateLimit-Reset",
                )
                if name in response.headers
            },
        }


def search_papers(
    query: str, provider: str, limit: int = 5, **request_options: Any
) -> list[Source]:
    """Fetch at most ``limit`` provider records and preserve discovery context."""
    query = query.strip()
    if not 3 <= len(query) <= 500 or not 1 <= limit <= 20:
        raise ValueError("query must have 3..500 characters; limit must be 1..20")
    if provider == "arxiv":
        # Natural-language queries become explicit AND terms, not raw API syntax.
        terms = re.findall(r'"[^"\n]+"|[\w-]+', query)[:30]
        expression = " AND ".join("all:" + term for term in terms)
        url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode(
            {
                "search_query": expression,
                "start": 0,
                "max_results": limit,
                "sortBy": "relevance",
                "sortOrder": "descending",
            }
        )
    elif provider == "openalex":
        url = "https://api.openalex.org/works?" + urllib.parse.urlencode(
            {"search": query, "per_page": limit}
        )
    else:
        raise ValueError("provider must be arxiv or openalex")
    response = _get(url, **request_options)
    retrieval = Retrieval(
        provider=provider,
        query=query,
        url=url,
        retrieved_at=response["retrieved_at"],
        cache_hit=response["cache_hit"],
    )
    try:
        if provider == "arxiv":
            return _arxiv_sources(response["body"], retrieval)[:limit]
        return _openalex_sources(response["body"], retrieval)[:limit]
    except (ET.ParseError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise DiscoveryError(
            f"{provider}: invalid provider response ({type(exc).__name__})"
        ) from None


def _arxiv_sources(body: str, retrieval: Retrieval) -> list[Source]:
    ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    sources = []
    for entry in ET.fromstring(body).findall("atom:entry", ns):
        url = entry.findtext("atom:id", "", ns).replace("http://", "https://")
        identifier = url.split("/abs/")[-1]
        if not _ARXIV_ID.fullmatch(identifier):
            raise DiscoveryError("arxiv: returned an error entry or invalid paper identifier")
        identifiers = {"arxiv": identifier, "arxiv_unversioned": re.sub(r"v\d+$", "", identifier)}
        doi = entry.findtext("arxiv:doi", "", ns).strip()
        if doi:
            identifiers["doi"] = _normalize_doi(doi)
        abstract = " ".join(entry.findtext("atom:summary", "", ns).split()) or None
        sources.append(
            Source(
                source_id="arxiv:" + identifiers["arxiv_unversioned"],
                title=" ".join(entry.findtext("atom:title", "", ns).split()),
                authors=[
                    author.findtext("atom:name", "", ns)
                    for author in entry.findall("atom:author", ns)
                ],
                year=int(entry.findtext("atom:published", "0000", ns)[:4]) or None,
                identifiers=identifiers,
                url=url,
                abstract=abstract,
                providers=["arxiv"],
                retrievals=[retrieval],
                content_level="abstract" if abstract else "metadata",
                content=abstract or "",
                content_url=url,
                access_note="Provider-supplied abstract; the full paper has not been read.",
            )
        )
    return sources


def _openalex_sources(body: str, retrieval: Retrieval) -> list[Source]:
    sources = []
    for work in json.loads(body)["results"]:
        identifiers = {"openalex": work["id"].rsplit("/", 1)[-1]}
        if work.get("doi"):
            identifiers["doi"] = _normalize_doi(work["doi"])
        for key in ("pmid", "pmcid"):
            if work.get("ids", {}).get(key):
                identifiers[key] = work["ids"][key]
        locations = work.get("locations") or []
        for location in locations:
            for key in ("landing_page_url", "pdf_url"):
                value = location.get(key) or ""
                match = re.search(r"arxiv\.org/(?:abs|pdf|html)/([^?#]+)", value)
                if match and _ARXIV_ID.fullmatch(match[1]):
                    identifiers["arxiv"] = match[1]
                    identifiers["arxiv_unversioned"] = re.sub(r"v\d+$", "", match[1])
        index = work.get("abstract_inverted_index") or {}
        # Inverted abstracts map each word to the positions where it occurs.
        positions = {int(position): word for word, offsets in index.items() for position in offsets}
        abstract = " ".join(positions[p] for p in sorted(positions)) or None
        best = work.get("best_oa_location") or work.get("primary_location") or {}
        url = best.get("landing_page_url") or work.get("doi") or work["id"]
        sources.append(
            Source(
                source_id="openalex:" + identifiers["openalex"],
                title=work.get("title") or work.get("display_name") or "Untitled scholarly work",
                authors=[
                    author["author"]["display_name"]
                    for author in work.get("authorships", [])
                    if author.get("author", {}).get("display_name")
                ],
                year=work.get("publication_year"),
                identifiers=identifiers,
                url=url,
                abstract=abstract,
                providers=["openalex"],
                retrievals=[retrieval],
                citations=work.get("cited_by_count"),
                content_level="abstract" if abstract else "metadata",
                content=abstract or "",
                content_url=url,
                access_note="Reconstructed provider abstract; full paper not read."
                if abstract
                else "Provider metadata only; no abstract was supplied.",
            )
        )
    return sources


def _normalize_doi(value: str) -> str:
    return re.sub(
        r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", value.strip(), flags=re.I
    ).lower()


def citation_identity(source: Source) -> bool:
    """Check retained identifier consistency and discovery provenance.

    This establishes a source record's internal identity, not the truth of its
    claims or independent verification of a publisher's metadata.
    """
    identifiers = source.identifiers
    doi = identifiers.get("doi")
    if doi and (doi != _normalize_doi(doi) or not re.fullmatch(r"10\.\d{4,9}/\S+", doi)):
        return False
    namespace, separator, canonical = source.source_id.partition(":")
    if not separator:
        return False
    if namespace == "synthetic":
        return (
            identifiers.get("synthetic") == canonical
            and bool(re.fullmatch(r"[a-z0-9][a-z0-9_-]*", canonical))
            and "synthetic" in source.providers
            and any(
                r.provider == "synthetic" and r.url == "local:offline-corpus"
                for r in source.retrievals
            )
        )
    if namespace == "arxiv":
        versioned = identifiers.get("arxiv", "")
        valid = bool(_ARXIV_ID.fullmatch(versioned)) and canonical == re.sub(
            r"v\d+$", "", versioned
        )
        valid = valid and identifiers.get("arxiv_unversioned") == canonical
        host = "export.arxiv.org"
    elif namespace == "openalex":
        valid = bool(re.fullmatch(r"W\d+", canonical)) and identifiers.get("openalex") == canonical
        host = "api.openalex.org"
    else:
        return False
    provenance = any(
        retrieval.provider == namespace
        and urllib.parse.urlsplit(retrieval.url).scheme == "https"
        and urllib.parse.urlsplit(retrieval.url).hostname == host
        for retrieval in source.retrievals
    )
    return bool(valid and namespace in source.providers and provenance)


def deduplicate_sources(sources: list[Source]) -> list[Source]:
    """Merge shared DOI/arXiv/OpenAlex IDs, or exact title+first-author matches.

    Conflicting durable IDs prevent a title-only merge. Existing source IDs stay
    stable so resume and retained evidence references are not silently renamed.
    """
    result: list[Source] = []
    for source in sources:
        matches: list[Source] = []
        for existing in result:
            shared_id = any(
                existing.identifiers.get(key) == value
                for key, value in source.identifiers.items()
                if key in {"doi", "arxiv_unversioned", "openalex"}
            )
            conflict = any(
                existing.identifiers[key] != value
                for key, value in source.identifiers.items()
                if key in {"doi", "arxiv_unversioned"} and key in existing.identifiers
            )
            title_match = re.sub(r"\W", "", existing.title.casefold()) == re.sub(
                r"\W", "", source.title.casefold()
            )
            author_match = bool(
                existing.authors
                and source.authors
                and existing.authors[0].casefold() == source.authors[0].casefold()
            )
            if shared_id or (title_match and author_match and not conflict):
                matches.append(existing)
        if not matches:
            result.append(source.model_copy(deep=True))
            continue
        match = matches[0]
        # A new record can bridge two earlier records through different IDs.
        for incoming in [source, *matches[1:]]:
            for key, value in incoming.identifiers.items():
                if key in match.identifiers and match.identifiers[key] != value:
                    match.identifiers[f"alternate:{key}:{value}"] = value
                else:
                    match.identifiers[key] = value
            match.providers = list(dict.fromkeys(match.providers + incoming.providers))
            retained = {(r.provider, r.query, r.url, r.retrieved_at) for r in match.retrievals}
            match.retrievals.extend(
                r
                for r in incoming.retrievals
                if (r.provider, r.query, r.url, r.retrieved_at) not in retained
            )
            if not match.abstract and incoming.abstract:
                match.abstract = incoming.abstract
            levels = {"metadata": 0, "abstract": 1, "full_text": 2}
            if levels[incoming.content_level] > levels[match.content_level] or (
                incoming.content_level == match.content_level
                and len(incoming.content) > len(match.content)
            ):
                match.content = incoming.content
                match.content_level = incoming.content_level
                match.content_url = incoming.content_url
                match.access_note = incoming.access_note
            if match.citations is None:
                match.citations = incoming.citations
        result = [item for item in result if item not in matches[1:]]
    return result


class _ArticleText(HTMLParser):
    """Extract visible article text without executing page code."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.article = False
        self.skip = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "article":
            self.article = True
        if tag in {"script", "style", "nav"}:
            self.skip += 1
        if (
            self.article
            and not self.skip
            and tag in {"p", "h1", "h2", "h3", "h4", "li", "tr", "section"}
        ):
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "nav"}:
            self.skip = max(0, self.skip - 1)
        if tag == "article":
            self.article = False

    def handle_data(self, data: str) -> None:
        if self.article and not self.skip:
            self.parts.append(data)


def read_source(source: Source, **request_options: Any) -> Source:
    """Read available arXiv HTML, otherwise retain the honest abstract fallback."""
    result = source.model_copy(deep=True)
    if result.content_level == "full_text":
        return result
    identifier = result.identifiers.get("arxiv")
    if not identifier or not _ARXIV_ID.fullmatch(identifier):
        return result
    url = "https://arxiv.org/html/" + identifier
    try:
        response = _get(url, **request_options)
        if "html" not in response["content_type"]:
            raise DiscoveryError("arxiv: expected HTML source content")
        parser = _ArticleText()
        parser.feed(response["body"])
        content = "\n".join(
            " ".join(line.split()) for line in "".join(parser.parts).splitlines() if line.strip()
        )
        if len(content) < 500:
            raise DiscoveryError("arxiv: accessible HTML article text was unavailable")
        result.content = content[:120_000]
        result.content_level = "full_text"
        result.content_url = response["url"]
        result.access_note = "Visible text from freely accessible arXiv HTML; math, figures, and table structure may be lost."
        if len(content) > 120_000:
            result.access_note += " Retained first 120,000 characters only."
        result.retrievals.append(
            Retrieval(
                provider="arxiv",
                query="full-text HTML",
                url=url,
                retrieved_at=response["retrieved_at"],
                cache_hit=response["cache_hit"],
            )
        )
    except DiscoveryError as exc:
        result.access_note += f" HTML fallback: {exc}."
    return result


def offline_sources(query: str, round_number: int = 1) -> list[Source]:
    """Synthetic classroom excerpts, never represented as real publications."""
    excerpts = [
        (
            "quantization",
            "SYNTHETIC: Calibrated Quantization of a Vision Transformer",
            "This synthetic classroom example studies post-training quantization of a vision transformer. On the fictional Edge-A GPU, INT8 quantization reduced batch-one inference latency compared with the FP32 baseline. Representative calibration inputs reduced accuracy loss. The example holds model architecture, image resolution, and batch size fixed. It does not measure energy use or evaluate deployment under distribution shift.",
        ),
        (
            "pruning",
            "SYNTHETIC: Structured Pruning for Edge Inference",
            "This synthetic classroom example evaluates structured channel pruning of a vision transformer on the fictional Edge-A GPU. Removing complete channels reduced model size. Sparse weight pruning alone did not reduce batch-one inference latency on the dense kernel used in this example. Fine-tuning recovered some accuracy. Results apply to the stated kernel and hardware; energy consumption was not measured.",
        ),
        (
            "setup",
            "SYNTHETIC: Precision and Batch Size on a Desktop GPU",
            "This synthetic classroom follow-up evaluates mixed precision on the fictional Desktop-B GPU at batch size thirty-two. FP16 increased throughput compared with FP32 for the same vision transformer. The experiment did not measure batch-one latency on Edge-A, so its result is not directly comparable with the edge quantization example. No energy measurement was reported. Hardware, batch size, and kernel support affect the practical speed benefit.",
        ),
    ]
    chosen = excerpts[:2] if round_number == 1 else excerpts[2:]
    return [
        Source(
            source_id="synthetic:" + slug,
            title=title,
            authors=["Synthetic classroom fixture"],
            year=None,
            identifiers={"synthetic": slug},
            url="https://example.invalid/synthetic/" + slug,
            abstract=abstract,
            providers=["synthetic"],
            retrievals=[
                Retrieval(
                    provider="synthetic",
                    query=query,
                    url="local:offline-corpus",
                    retrieved_at="2026-10-03T00:00:00+00:00",
                )
            ],
            content_level="abstract",
            content=abstract,
            content_url="local:offline-corpus#" + slug,
            access_note="Synthetic educational excerpt and deterministic model substitute; not real research evidence.",
        )
        for slug, title, abstract in chosen
    ]
