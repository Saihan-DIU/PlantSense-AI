"""Public site settings used for search engines and link previews.

SITE_URL: the live address (no trailing slash). Used for canonical links,
hreflang, the sitemap and Open Graph tags.
GOOGLE_SITE_VERIFICATION: the content="..." value of the HTML tag from Google
Search Console (Settings > Ownership verification > HTML tag). Leave empty to
omit the tag.
"""
import os

SITE_URL = os.environ.get("SITE_URL", "https://plantsense-ai.vercel.app").rstrip("/")
GOOGLE_SITE_VERIFICATION = os.environ.get("GOOGLE_SITE_VERIFICATION", "")
