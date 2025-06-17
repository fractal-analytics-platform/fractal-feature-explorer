from fractal_feature_explorer.utils.ngio_io_caches import _url_belongs_to_base


def test_url_belongs_to_base():
    base_url = "https://example.com/base/"
    test_urls = [
        "https://example.com/base/resource",
        "https://example.com/base/resource/subresource",
        "https://example.com/base/resource/subresource?query=param#fragment",
    ]

    for url in test_urls:
        assert _url_belongs_to_base(url, base_url)

    negative_test_urls = [
        "https://example.com/other/resource",
        "http://example.com/base/resource",
    ]

    for url in negative_test_urls:
        assert not _url_belongs_to_base(url, base_url)
