import sys
from pathlib import Path


backend_root = str(Path(__file__).parent.parent)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from services.product_parse_service import _extract_cover_urls


def test_extract_cover_urls_prefers_original_image_from_media_list() -> None:
    html = """
    <html>
      <body>
        <script id="__NEXT_DATA__" type="application/json">
        {
          "props": {
            "pageProps": {
              "metaOGInfo": {
                "data": [
                  {
                    "content": {
                      "cover": {
                        "mediaType": "img",
                        "url": "https://image-cdn.dewu.com/app/thumb.jpg"
                      },
                      "media": {
                        "list": [
                          {
                            "mediaType": "img",
                            "url": "https://image-cdn.poizon.com/app/original.jpg"
                          },
                          {
                            "mediaType": "blur",
                            "url": "https://image-cdn.poizon.com/app/blur.jpg"
                          }
                        ]
                      }
                    }
                  }
                ]
              }
            }
          }
        }
        </script>
      </body>
    </html>
    """

    assert _extract_cover_urls(html) == ["https://image-cdn.poizon.com/app/original.jpg"]


def test_extract_cover_urls_falls_back_to_thumbnail_when_original_missing() -> None:
    html = """
    <html>
      <body>
        <script id="__NEXT_DATA__" type="application/json">
        {
          "props": {
            "pageProps": {
              "metaOGInfo": {
                "data": [
                  {
                    "content": {
                      "cover": {
                        "mediaType": "img",
                        "url": "https://image-cdn.dewu.com/app/thumb.jpg"
                      },
                      "media": {
                        "list": [
                          {
                            "mediaType": "blur",
                            "url": "https://image-cdn.poizon.com/app/blur.jpg"
                          }
                        ]
                      }
                    }
                  }
                ]
              }
            }
          }
        }
        </script>
      </body>
    </html>
    """

    assert _extract_cover_urls(html) == ["https://image-cdn.dewu.com/app/thumb.jpg"]
