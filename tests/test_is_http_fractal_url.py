from fractal_explorer.utils.ngio_io_caches import is_http_fractal_url
from fractal_explorer.utils.common import FractalExplorerConfig

def test_is_http_fractal_url(monkeypatch):
    import fractal_explorer.utils.ngio_io_caches

    DOMAIN = "https://example.org"
    BAD_DOMAIN = "https://example.org.bad_domain.org"

    def _mocked_get_config() -> FractalExplorerConfig:
        return FractalExplorerConfig(fractal_token_subdomains=[DOMAIN])

    monkeypatch.setattr(
        fractal_explorer.utils.ngio_io_caches,
        "get_config",
        _mocked_get_config,
    )

    assert is_http_fractal_url(DOMAIN)
    assert is_http_fractal_url(f"{DOMAIN}/subdomain")
    assert not is_http_fractal_url(f"{BAD_DOMAIN}/subdomain")