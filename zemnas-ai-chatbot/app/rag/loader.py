from pathlib import Path

from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import SitemapLoader, WebBaseLoader

from app.config import settings
from app.core.logging import get_logger


logger = get_logger(__name__)


def load_from_text_file():
    """
    Load Zemnas knowledge from data/zemnas.txt
    """

    file_path = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "zemnas.txt"
    )

    try:
        logger.info("Loading Zemnas knowledge file: %s", file_path)

        if not file_path.exists():
            raise FileNotFoundError(
                f"Knowledge file not found: {file_path}"
            )

        loader = TextLoader(
            str(file_path),
            encoding="utf-8"
        )

        documents = loader.load()

        logger.info(
            "Loaded %s knowledge document(s)",
            len(documents)
        )

        return documents

    except Exception:
        logger.exception("Zemnas text file loading failed")
        return []


def load_from_sitemap():
    sitemap_url = (
        settings.WEBSITE_URL.rstrip("/")
        + "/sitemap.xml"
    )

    try:
        logger.info("Loading sitemap: %s", sitemap_url)

        loader = SitemapLoader(
            web_path=sitemap_url
        )

        documents = loader.load()

        return documents

    except Exception:
        logger.exception("Sitemap loading failed")
        return []


def load_urls(urls: list[str]):
    if not urls:
        return []

    try:
        return WebBaseLoader(
            web_paths=urls
        ).load()

    except Exception as error:
        raise RuntimeError(
            "Website URL loading failed"
        ) from error