from pydantic import BaseModel, Field, root_validator
from typing import List


class CrawlerConfig(BaseModel):
    """Configuration model for the web crawler, using Pydantic for validation."""

    start_url: str
    output_dir: str
    max_pages: int = Field(..., gt=0)
    min_pause: float = Field(..., ge=0)
    max_pause: float = Field(..., ge=0)
    crawl_depth: int
    stay_on_subdomain: bool
    ignore_queries: bool
    user_agent: str
    include_paths: List[str] = []
    exclude_paths: List[str] = []

    @root_validator(skip_on_failure=True)
    def check_pause_values(cls, values):
        """Ensures that min_pause is not greater than max_pause."""
        min_p, max_p = values.get("min_pause"), values.get("max_pause")
        if min_p > max_p:
            raise ValueError("Min pause cannot be greater than max pause")
        return values
