"""Application configuration."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # Data directory (contains database and cache)
    data_dir: str = Field(
        default="data",
        description="存储所有持久化数据的根目录, 包括 SQLite 数据库文件和海报图片缓存",
    )

    # Poster Cache
    poster_cache_ttl: int = Field(
        default=365,
        description="本地海报图片的缓存有效期(天), 超过此天数后会尝试重新下载",
    )

    # Security
    import_api_key: str | None = Field(
        default=None,
        description=(
            "调用数据导入 API 时必须在请求头中提供的 X-API-Key 密钥; 若未设置, 导入接口将被禁用"
        ),
    )

    # Rate Limiting
    rate_limit_default: str = Field(
        default="100/minute",
        description="全局默认的接口访问速率限制, 适用于未单独配置限流的接口",
    )
    rate_limit_search: str = Field(
        default="30/minute",
        description="搜索标题、获取电影或电视节目列表等主要查询接口的访问速率限制",
    )
    rate_limit_genres: str = Field(
        default="20/minute", description="获取影视类型标签列表接口的访问速率限制"
    )
    rate_limit_regions: str = Field(
        default="20/minute", description="获取影视地区标签列表接口的访问速率限制"
    )
    rate_limit_stats: str = Field(
        default="10/minute",
        description="获取数据统计信息(如作品总数、年份分布等)接口的访问速率限制",
    )
    rate_limit_poster: str = Field(
        default="200/minute", description="海报图片代理服务接口的访问速率限制"
    )
    rate_limit_import: str = Field(
        default="5/minute",
        description="触发数据导入任务以及查询导入进度接口的访问速率限制",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        """Get the database URL."""
        db_path = Path(self.data_dir) / "db" / "movies.db"
        return f"sqlite:///{db_path}"


settings = Settings()
