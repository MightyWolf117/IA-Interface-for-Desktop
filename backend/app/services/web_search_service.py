import re
import json
import urllib.request
import urllib.parse
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup


class WebSearchService:
    """
    Servicio de acceso a internet en tiempo real para el modelo de lenguaje (RAG Web).
    - Modo por defecto: DuckDuckGo Search (sin coste, sin registros ni API keys obligatorias).
    - Modo ampliado: Soporte para APIs externas con clave (Tavily, SerpAPI, Brave Search).
    - Procesa y sintetiza los resultados en bloques contextuales estructurados con citas clicables.
    """

    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )

    @classmethod
    def search_duckduckgo(cls, query: str, max_results: int = 4) -> List[Dict[str, str]]:
        """
        Ejecuta una búsqueda en DuckDuckGo Lite / HTML y extrae títulos, snippets y URLs.
        """
        results: List[Dict[str, str]] = []
        encoded_query = urllib.parse.urlencode({"q": query})
        url = f"https://html.duckduckgo.com/html/?{encoded_query}"

        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": cls.USER_AGENT,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
                    "Referer": "https://html.duckduckgo.com/"
                }
            )

            with urllib.request.urlopen(req, timeout=6.0) as resp:
                html = resp.read().decode("utf-8", errors="ignore")

            soup = BeautifulSoup(html, "html.parser")
            result_nodes = soup.find_all("div", class_=re.compile(r"result\s+results_links"))

            for node in result_nodes[:max_results]:
                title_node = node.find("a", class_="result__a")
                snippet_node = node.find("a", class_="result__snippet")
                url_node = node.find("a", class_="result__url")

                if not title_node:
                    continue

                title = title_node.get_text(strip=True)
                raw_href = title_node.get("href", "")

                # DuckDuckGo HTML links wrap external targets inside /l/?uddg=<url>
                clean_url = raw_href
                if "uddg=" in raw_href:
                    try:
                        parsed = urllib.parse.parse_qs(urllib.parse.urlparse(raw_href).query)
                        clean_url = parsed.get("uddg", [raw_href])[0]
                    except Exception:
                        clean_url = raw_href

                snippet = snippet_node.get_text(strip=True) if snippet_node else ""
                if not snippet and url_node:
                    snippet = url_node.get_text(strip=True)

                if title and clean_url:
                    results.append({
                        "title": title,
                        "url": clean_url,
                        "snippet": snippet
                    })

        except Exception as e:
            print(f"[WebSearchService] Aviso en búsqueda DuckDuckGo HTML: {e}")
            # Fallback a DuckDuckGo Instant Answer API JSON
            try:
                api_url = f"https://api.duckduckgo.com/?{encoded_query}&format=json&no_html=1&skip_disambig=1"
                req_api = urllib.request.Request(api_url, headers={"User-Agent": cls.USER_AGENT})
                with urllib.request.urlopen(req_api, timeout=4.0) as resp_api:
                    data = json.loads(resp_api.read().decode("utf-8"))
                    abstract = data.get("AbstractText", "")
                    heading = data.get("Heading", query)
                    abstract_url = data.get("AbstractURL", "")

                    if abstract:
                        results.append({
                            "title": heading,
                            "url": abstract_url,
                            "snippet": abstract
                        })

                    for topic in data.get("RelatedTopics", [])[:max_results - len(results)]:
                        if "Text" in topic and "FirstURL" in topic:
                            results.append({
                                "title": topic.get("Text", "")[:60] + "...",
                                "url": topic.get("FirstURL", ""),
                                "snippet": topic.get("Text", "")
                            })
            except Exception as e_api:
                print(f"[WebSearchService] Fallback API DuckDuckGo falló: {e_api}")

        return results

    @classmethod
    def search_tavily(cls, query: str, api_key: str, max_results: int = 4) -> List[Dict[str, str]]:
        """
        Búsqueda opcional mediante la API dedicada de Tavily Search.
        """
        results = []
        payload = json.dumps({
            "api_key": api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": "basic",
            "include_answer": False
        }).encode("utf-8")

        try:
            req = urllib.request.Request(
                "https://api.tavily.com/search",
                data=payload,
                headers={"Content-Type": "application/json", "User-Agent": cls.USER_AGENT}
            )
            with urllib.request.urlopen(req, timeout=6.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for item in data.get("results", []):
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "snippet": item.get("content", "")
                    })
        except Exception as e:
            print(f"[WebSearchService] Error en búsqueda Tavily API: {e}")

        return results

    @classmethod
    def execute_search(cls, query: str, max_results: int = 4, api_key: Optional[str] = None, provider: str = "duckduckgo") -> List[Dict[str, str]]:
        """
        Punto de entrada de búsqueda con despacho por proveedor.
        """
        if provider == "tavily" and api_key:
            return cls.search_tavily(query, api_key, max_results)
        return cls.search_duckduckgo(query, max_results)

    @classmethod
    def format_search_context(cls, results: List[Dict[str, str]]) -> str:
        """
        Convierte los resultados en un bloque de contexto markdown optimizado para RAG e inyección al LLM.
        """
        if not results:
            return ""

        lines = [
            "---",
            "### [INFORMACIÓN ACTUALIZADA DE INTERNET (BÚSQUEDA WEB EN VIVO)]",
            "Utiliza los siguientes datos web recientes para responder a la consulta del usuario si es relevante. "
            "Cita siempre las fuentes indicando el título o la URL correspondiente.",
            ""
        ]

        for i, res in enumerate(results, start=1):
            title = res.get("title", f"Fuente {i}").strip()
            url = res.get("url", "").strip()
            snippet = res.get("snippet", "").strip()
            lines.append(f"[{i}] **{title}**")
            lines.append(f"    - URL: {url}")
            if snippet:
                lines.append(f"    - Resumen: {snippet}")
            lines.append("")

        lines.append("---")
        return "\n".join(lines)

