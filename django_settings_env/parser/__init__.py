from typing import Optional
from dataclasses import dataclass
from yarl import URL


__all__ = (
    "URLParser",
    "ParsedUrl",
    "default_parser",
)

_none = object()


@dataclass
class ParsedUrl:
    scheme: str
    username: Optional[str] = None
    password: Optional[str] = None
    hostname: Optional[str] = None
    port: Optional[str | int] = None
    path: Optional[str] = None
    qs: Optional[dict] = None

    def to_url(
        self,
        scheme: Optional[str] = _none,
        name: Optional[str] = _none,
        port: Optional[str] = _none,
        qs: bool = False,
    ) -> str:
        scheme = scheme if scheme is not _none else self.scheme or "https"
        scheme = f"{scheme}://" if scheme else ""
        if self.username:
            userpass = (
                f"{self.username}:{self.password}@"
                if self.password
                else f"{self.username}@"
            )
        elif self.password:
            userpass = f":{self.password}@"
        else:
            userpass = ""
        url = f"{scheme}{userpass}{self.hostname or ''}"
        port = port if port is not _none else self.port
        if port:
            url += f":{port}"
        name = name if name is not _none else self.path
        if name:
            url += name
        if self.qs and qs:
            url += "?" + "&".join(f"{k}={v}" for k, v in self.qs.items())
        return url

    def __str__(self) -> str:
        return f"<ParsedUrl: {self.to_url()}"


class URLParser:
    """
    Base class for URL parsers. Subclasses must implement the __call__ method to parse URLs.
    Parsers normalise the given URL and return ParsedUrl objects.
    """

    DEFAULT_SCHEME = None

    @property
    def default_scheme(self) -> str:
        """
        Returns the default scheme for the parser.

        Returns:
            The default scheme.
        """
        return self.DEFAULT_SCHEME or "https"

    def __call__(self, url: str, **kwargs) -> ParsedUrl:
        """
        Parses the given URL and returns a ParsedUrl object.

        Args:
            url: The URL to be parsed.
            kwargs: Additional arguments for the parser.

        Returns:
            A ParsedUrl object
        Throws:
            ValueError: If the URL can't be parsed.
        """
        if "://" not in url and "/" in url:
            url = f"https://{url}"
        parsed = URL(url)
        if parsed.scheme or parsed.host or parsed.path:
            return ParsedUrl(
                scheme=parsed.scheme,
                username=parsed.user,
                password=parsed.password,
                hostname=parsed.host,
                port=parsed.port,
                path=parsed.path,
                qs=parsed.query or None,
            )
        else:
            raise ValueError(f"Invalid URL: {url}")


default_parser = URLParser()
