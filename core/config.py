from pydantic import BaseModel, Field, model_validator


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
    include_paths: list[str] = []
    exclude_paths: list[str] = []

    @model_validator(mode="after")
    def check_pause_values(self):
        """Ensures that min_pause is not greater than max_pause."""
        if self.min_pause > self.max_pause:
            raise ValueError("Min pause cannot be greater than max pause")
        return self
