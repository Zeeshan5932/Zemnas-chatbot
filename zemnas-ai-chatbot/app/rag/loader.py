from langchain_community.document_loaders import (
    SitemapLoader,
    WebBaseLoader
)

from app.config import settings
from app.core.logging import get_logger


logger = get_logger(__name__)


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

    except Exception as error:

        logger.exception("Sitemap loading failed")

        return []


def load_urls(urls: list[str]):
    if not urls:
        return []
    try:
        return WebBaseLoader(web_paths=urls).load()
    except Exception as error:
        raise RuntimeError("Website URL loading failed") from error