from dataclasses import dataclass, field


@dataclass
class CrawlerConfig:
    start_url: str
    output_dir: str
    max_pages: int
    min_pause: float
    max_pause: float
    crawl_depth: int
    stay_on_subdomain: bool
    ignore_queries: bool
    user_agent: str
    include_paths: list[str] = field(default_factory=list)
    exclude_paths: list[str] = field(default_factory=list)
