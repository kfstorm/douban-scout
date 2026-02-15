"""Data import service with singleton pattern."""

import contextlib
import json
import logging
import shutil
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import ClassVar

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app import database
from app.cache import cache_manager
from app.database import (
    FTS_CREATE_TABLE_SQL,
    FTS_INSERT_ALL_SQL,
    FTS_TABLE_NAME,
    Base,
    Genre,
    Movie,
    MovieGenre,
    MoviePoster,
    MovieRegion,
    Region,
    get_db_path,
)
from app.schemas import ImportStatus

# Configure logger
logger = logging.getLogger("douban.import")


class ImportService:
    """Singleton service for importing movie data."""

    _instance: "ImportService | None" = None
    _lock = threading.Lock()
    _status: ImportStatus

    _MAX_ERROR_LOGS = 10  # Maximum number of errors to log with full traceback

    # Valid genres
    VALID_GENRES: ClassVar[set[str]] = {
        "剧情",
        "喜剧",
        "爱情",
        "动作",
        "惊悚",
        "犯罪",
        "恐怖",
        "动画",
        "纪录片",
        "短片",
        "悬疑",
        "冒险",
        "科幻",
        "奇幻",
        "家庭",
        "音乐",
        "历史",
        "战争",
        "歌舞",
        "传记",
        "古装",
        "真人秀",
        "同性",
        "运动",
        "西部",
        "情色",
        "儿童",
        "武侠",
        "脱口秀",
        "黑色电影",
        "戏曲",
        "灾难",
    }

    # Valid regions (hard-coded list as requested)
    VALID_REGIONS: ClassVar[set[str]] = {
        "美国",
        "中国大陆",
        "日本",
        "英国",
        "法国",
        "中国香港",
        "韩国",
        "德国",
        "加拿大",
        "意大利",
        "中国台湾",
        "西班牙",
        "印度",
        "澳大利亚",
        "俄罗斯",
        "巴西",
        "墨西哥",
        "泰国",
        "瑞典",
        "阿根廷",
        "比利时",
        "荷兰",
        "丹麦",
        "波兰",
        "土耳其",
        "菲律宾",
        "瑞士",
        "奥地利",
        "苏联",
        "芬兰",
        "挪威",
        "西德",
        "葡萄牙",
        "匈牙利",
        "以色列",
        "捷克",
        "希腊",
        "罗马尼亚",
        "爱尔兰",
        "新加坡",
        "伊朗",
        "捷克斯洛伐克",
        "印度尼西亚",
        "南斯拉夫",
        "越南",
        "乌克兰",
        "智利",
        "新西兰",
        "保加利亚",
        "南非",
        "马来西亚",
        "哥伦比亚",
        "冰岛",
        "爱沙尼亚",
        "克罗地亚",
        "埃及",
        "古巴",
        "塞尔维亚",
        "拉脱维亚",
        "立陶宛",
        "黎巴嫩",
        "尼日利亚",
        "秘鲁",
        "Canada",
        "斯洛文尼亚",
        "卢森堡",
        "格鲁吉亚",
        "斯洛伐克",
        "乌拉圭",
        "阿尔巴尼亚",
        "委内瑞拉",
        "USA",
        "卡塔尔",
        "摩洛哥",
        "哈萨克斯坦",
        "巴基斯坦",
        "巴勒斯坦",
        "朝鲜",
        "孟加拉国",
        "突尼斯",
        "波黑",
        "阿尔及利亚",
        "波多黎各",
        "多米尼加",
        "UK",
        "India",
        "东德",
        "中国",
        "阿联酋",
        "厄瓜多尔",
        "白俄罗斯",
        "亚美尼亚",
        "尼泊尔",
        "叙利亚",
        "沙特阿拉伯",
        "Australia",
        "柬埔寨",
        "中国澳门",
        "玻利维亚",
        "斯里兰卡",
        "塞内加尔",
        "蒙古",
        "伊拉克",
        "缅甸",
        "Turkey",
        "哥斯达黎加",
        "塞浦路斯",
        "肯尼亚",
        "阿塞拜疆",
        "阿富汗",
        "北马其顿",
        "约旦",
        "蘇聯",
        "科索沃",
        "印尼",
        "危地马拉",
        "Russia",
        "乌兹别克斯坦",
        "布基纳法索",
        "吉尔吉斯斯坦",
        "前苏联",
        "巴拉圭",
        "巴拿马",
        "黑山",
        "摩纳哥",
        "马其顿",
        "Germany",
        "Indonesia",
        "尼加拉瓜",
        "Netherlands",
        "加纳",
        "Poland",
        "Sweden",
        "Mexico",
        "俄国",
        "埃塞俄比亚",
        "Austria",
        "刚果",
        "马耳他",
        "喀麦隆",
        "Greece",
        "France",
        "Denmark",
        "Belgium",
        "老挝",
        "Ireland",
        "Argentina",
        "Soviet",
        "科威特",
        "Portugal",
        "Singapore",
        "Union",
        "Brazil",
        "波斯尼亚和黑塞哥维那",
        "孟加拉",
        "Philippines",
        "Indian",
        "马里",
        "Switzerland",
        "Hungary",
        "Norway",
        "不丹",
        "New",
        "俄羅斯",
        "Finland",
        "香港",
        "塞黑",
        "Republic",
        "圣马力诺",
        "津巴布韦",
        "Czech",
        "澳洲",
        "Zealand",
        "South",
        "Italy",
        "摩尔多瓦",
        "Israel",
        "Kazakhstan",
        "West",
        "Romania",
        "Ukraine",
        "塔吉克斯坦",
        "英國",
        "Vietnam",
        "台灣",
        "Cyprus",
        "BBC",
        "Chile",
        "Czechoslovakia",
        "Africa",
        "Spain",
        "Iran",
        "Iceland",
        "Palestine",
        "多米尼加共和国",
        "加拿大Canada",
        "乍得",
        "尼日尔",
        "联邦德国",
        "列支敦士登",
        "海地",
        "苏丹",
        "萨尔瓦多",
        "索马里",
        "Lebanon",
        "Bulgaria",
        "Senegal",
        "Peru",
        "China",
        "卢旺达",
        "india",
        "丹麥",
        "洪都拉斯",
        "Lithuania",
        "Cambodia",
        "安哥拉",
        "Cuba",
        "Venezuela",
        "Egypt",
        "Taiwan",
        "莫桑比克",
        "原西德",
        "Belarus",
        "Colombia",
        "Croatia",
        "佛得角",
        "US",
        "argentina",
        "Kenya",
        "牙买加",
        "科特迪瓦",
        "毛里塔尼亚",
        "Japan",
        "坦桑尼亚",
        "法罗群岛",
        "乌干达",
        "格陵兰",
        "Guatemala",
        "几内亚比绍",
        "Malaysia",
        "uk",
        "Armenia",
        "United",
        "brasil",
        "Syria",
        "Philippine",
        "Jamaica",
        "Arab",
        "巴林",
        "也门",
        "德國",
        "Bolivia",
        "Russian",
        "台灣Taiwan",
        "Serbia",
        "Myanmar",
        "Pakistan",
        "刚果（金）",  # noqa: RUF001
        "利比亚",
        "博茨瓦纳",
        "美國",
        "巴哈马",
        "Emirates",
        "usa",
        "Haiti",
        "canada",
        "比利時",
        "纳米比亚",
        "阿拉伯联合酋长国",
        "poland",
        "阿鲁巴",
        "加蓬",
        "赞比亚",
        "The",
        "Korea",
        "Burkina",
        "Faso",
        "捷克共和国",
        "Slovakia",
        "Netherland",
        "Uruguay",
        "马达加斯加",
        "Nepal",
        "Qatar",
        "苏里南",
        "菲律宾Philippine",
        "Estonia",
        "Cameroon",
        "贝宁",
        "安道尔",
        "and",
        "奧地利",
        "of",
        "前西德",
        "几内亚",
        "巴布亚新几内亚",
        "Ecuador",
        "Paraguay",
        "印度India",
        "Mainland",
        "塞拉利昂",
        "荷蘭",
        "南极洲",
        "马其顿共和国",
        "Guinea",
        "Bangladesh",
        "印度尼西亞",
        "萨摩亚",
        "荷兰Netherlands",
        "Mongolia",
        "Macedonia",
        "Columbia",
        "新加坡Singapore",
        "斐济",
        "Ghana",
        "U.S.",
        "Panama",
        "North",
        "澳大利亚Australia",
        "the",
        "菲律賓",
        "Jordan",
        "库克群岛",
        "利比里亚",
        "Kyrgyzstan",
        "Bahamas",
        "Thailand",
        "中非",
        "Islands",
        "Turkmenistan",
        "Iraq",
        "澳大利亞",
        "Morocco",
        "蒙古国",
        "美國USA",
        "刚果(布)",
        "莱索托",
        "brazil",
        "阿曼",
        "East",
        "Luxembourg",
        "西撒哈拉",
        "Danmark",
        "泰國",
        "Papua",
        "Honduras",
        "Madagascar",
        "El",
        "Salvador",
        "English",
        "伯利兹",
        "塞尔维亚和黑山",
        "Virgin",
        "USSR",
        "Albania",
        "Yugoslavia",
        "Brasil",
        "芬蘭",
        "特立尼达和多巴哥",
        "英國UK",
        "丹麦Denmark",
        "Holland",
        "巴巴多斯",
        "Nigeria",
        "Saudi",
        "Arabia",
        "阿根廷Argentina",
        "波兰Poland",
        "俄羅斯Russia",
    }

    def __new__(cls) -> "ImportService":
        """Create singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._status = ImportStatus(status="idle")
        return cls._instance

    @property
    def status(self) -> ImportStatus:
        """Get current import status."""
        return self._status

    def start_import(self, source_path: str) -> ImportStatus:
        """Start the import process in a background thread."""
        with self._lock:
            if self._status.status == "running":
                logger.warning("Import already in progress, cannot start new import")
                raise RuntimeError("Import already in progress")

            logger.info(f"Starting import from: {source_path}")
            self._status = ImportStatus(
                status="running",
                processed=0,
                total=0,
                percentage=0.0,
                started_at=datetime.now(),
            )

            thread = threading.Thread(target=self._import_data, args=(source_path,))
            thread.daemon = True
            thread.start()

            return self._status

    def _import_data(self, source_path: str) -> None:  # noqa: PLR0912, PLR0915
        """Internal method to perform the import."""
        target_db_path = Path(get_db_path())
        temp_db_path = target_db_path.with_suffix(".db.tmp")
        try:
            logger.info(f"Connecting to source database: {source_path}")
            if not Path(source_path).exists():
                raise FileNotFoundError(f"Source file not found: {source_path}")

            # Connect to source database
            source_conn = sqlite3.connect(source_path)
            source_cursor = source_conn.cursor()

            # Get total count of items to import (movie and tv).
            # Note: Items with empty type are placeholders that only have douban_id set
            # and should be ignored.
            source_cursor.execute("SELECT COUNT(*) FROM item WHERE type IN ('movie', 'tv')")
            total = source_cursor.fetchone()[0]
            logger.info(f"Found {total} total records to import")

            with self._lock:
                self._status.total = total

            # Ensure data directory exists
            temp_db_path.parent.mkdir(parents=True, exist_ok=True)
            if temp_db_path.exists():
                temp_db_path.unlink()

            # Create fresh temp DB with high-speed settings for import
            logger.info(f"Creating temporary database at {temp_db_path}")
            temp_engine = create_engine(
                f"sqlite:///{temp_db_path}",
                connect_args={"check_same_thread": False},
            )

            # Set performance pragmas for the import session
            with temp_engine.connect() as conn:
                # Use DELETE mode for the temp DB to avoid leaving -wal files behind
                conn.execute(text("PRAGMA journal_mode = DELETE"))
                conn.execute(text("PRAGMA synchronous = OFF"))
                conn.execute(text("PRAGMA cache_size = -100000"))  # 100MB cache

            Base.metadata.create_all(bind=temp_engine)  # type: ignore[attr-defined]

            with Session(temp_engine) as db:
                # Pre-populate Genres
                logger.info("Populating genres table...")
                genre_map = {}
                for g_name in sorted(self.VALID_GENRES):
                    genre = Genre(name=g_name)
                    db.add(genre)
                db.flush()

                genres_list = db.query(Genre).all()
                genre_map = {g.name: g.id for g in genres_list}

                # Pre-populate Regions
                logger.info("Populating regions table...")
                for r_name in sorted(self.VALID_REGIONS):
                    region = Region(name=r_name)
                    db.add(region)
                db.flush()

                regions_list = db.query(Region).all()
                region_map = {r.name: r.id for r in regions_list}
                db.commit()

                # Import in batches
                batch_size = 1000
                processed = 0
                batch: list[dict] = []
                error_count = 0

                logger.info("Starting data import...")
                source_cursor.execute(
                    "SELECT douban_id, imdb_id, douban_title, year, rating, raw_data, "
                    "type, update_time FROM item WHERE type IN ('movie', 'tv')"
                )

                for row in source_cursor:
                    douban_id = None
                    try:
                        (
                            douban_id,
                            _,
                            title,
                            year,
                            rating,
                            raw_data,
                            item_type,
                            update_time,
                        ) = row

                        # Initialize defaults
                        rating_count = 0
                        poster_urls: set[str] = set()
                        movie_genre_names: set[str] = set()
                        movie_region_names: set[str] = set()

                        # Parse raw_data JSON
                        if raw_data:
                            try:
                                data = json.loads(raw_data)
                                detail = data.get("detail", {})
                                if isinstance(detail, dict):
                                    # Extract rating count
                                    rating_info = detail.get("rating", {})
                                    if isinstance(rating_info, dict):
                                        rating_count = rating_info.get("count", 0)

                                    # Extract poster URLs
                                    pic = detail.get("pic", {})
                                    if isinstance(pic, dict):
                                        for key in ["normal", "large"]:
                                            if pic.get(key):
                                                poster_urls.add(pic[key])

                                    cover_url = detail.get("cover_url")
                                    if cover_url:
                                        poster_urls.add(cover_url)

                                    # Extract regions from countries list
                                    countries = detail.get("countries", [])
                                    if isinstance(countries, list):
                                        for country in countries:
                                            if country in self.VALID_REGIONS:
                                                movie_region_names.add(country)

                                    # Extract genres from card_subtitle or subtitle
                                    card_subtitle = detail.get("card_subtitle") or detail.get(
                                        "subtitle", ""
                                    )
                                    if card_subtitle:
                                        # card_subtitle example: "2000 / 美国 / 剧情 喜剧"
                                        # Split by any whitespace and "/" to get tokens
                                        tokens = card_subtitle.replace("/", " ").split()
                                        for token in tokens:
                                            if token in self.VALID_GENRES:
                                                movie_genre_names.add(token)
                                            if (
                                                not movie_region_names
                                                and token in self.VALID_REGIONS
                                            ):
                                                movie_region_names.add(token)
                            except json.JSONDecodeError as e:
                                logger.warning(
                                    f"Failed to parse raw_data for douban_id {douban_id}: {e}"
                                )

                        # Build movie dictionary
                        movie = {
                            "id": int(douban_id),
                            "title": title or "",
                            "year": year,
                            "rating": rating,
                            "rating_count": rating_count,
                            "type": item_type,
                            "genre_ids": [genre_map[gn] for gn in movie_genre_names],
                            "region_ids": [region_map[rn] for rn in movie_region_names],
                            "posters": list(poster_urls),
                            "updated_at": int(update_time) if update_time else None,
                        }

                        batch.append(movie)

                        if len(batch) >= batch_size:
                            self._insert_batch(db, batch)
                            processed += len(batch)
                            batch = []

                            with self._lock:
                                self._status.processed = processed
                                if total > 0:
                                    self._status.percentage = (processed / total) * 100
                                else:
                                    self._status.percentage = 100.0

                            if processed % 10000 == 0:
                                pct = self._status.percentage
                                logger.info(f"Imported {processed}/{total} records ({pct:.1f}%)")

                    except Exception as e:
                        error_count += 1
                        logger.error(f"Error processing row {douban_id}: {e}", exc_info=True)
                        if error_count <= self._MAX_ERROR_LOGS:
                            continue
                        else:
                            logger.warning(
                                f"Suppressing detailed error logs after {error_count} errors"
                            )

                # Insert remaining
                if batch:
                    logger.info(f"Inserting final batch of {len(batch)} records...")
                    self._insert_batch(db, batch)
                    processed += len(batch)

                # Commit the entire transaction
                logger.info("Committing transaction...")
                db.commit()

            source_conn.close()

            # Post-import optimization
            self._optimize_db(temp_db_path)

            # Atomic swap
            logger.info(f"Swapping {temp_db_path} to {target_db_path}")

            # Dispose existing connections to ensure they stop using the old file handles
            database.engine.dispose()

            # Remove associated SQLite sidecars if they exist for the target
            for suffix in ["-wal", "-shm"]:
                sidecar = target_db_path.with_name(target_db_path.name + suffix)
                if sidecar.exists():
                    try:
                        sidecar.unlink()
                    except Exception as e:
                        logger.warning(f"Could not remove sidecar {sidecar}: {e}")

            if target_db_path.exists():
                # On Linux we can rename over an existing file
                shutil.move(temp_db_path, target_db_path)
            else:
                shutil.move(temp_db_path, target_db_path)

            # Clear application cache after successful swap
            cache_manager.clear()

            logger.info(
                f"Import completed successfully. "
                f"Processed {processed} records with {error_count} errors"
            )
            with self._lock:
                self._status.status = "completed"
                self._status.processed = processed
                self._status.percentage = 100.0
                self._status.completed_at = datetime.now()

        except Exception as e:
            logger.exception(f"Import failed: {e}")
            if temp_db_path.exists():
                with contextlib.suppress(Exception):
                    temp_db_path.unlink()
            with self._lock:
                self._status.status = "failed"
                self._status.message = str(e)
                self._status.completed_at = datetime.now()

    def _insert_batch(self, db: Session, movies: list[dict]) -> None:
        """Insert a batch of movies and their associations."""
        try:
            for movie_data in movies:
                genre_ids = movie_data.pop("genre_ids", [])
                region_ids = movie_data.pop("region_ids", [])
                posters = movie_data.pop("posters", [])

                movie = Movie(**movie_data)
                db.add(movie)
                db.flush()

                for gid in genre_ids:
                    db.add(MovieGenre(movie_id=movie.id, genre_id=gid))

                for rid in region_ids:
                    db.add(MovieRegion(movie_id=movie.id, region_id=rid))

                for poster_url in posters:
                    db.add(MoviePoster(movie_id=movie.id, url=poster_url))

            db.flush()
            db.expunge_all()
        except Exception as e:
            logger.exception(f"Failed to insert batch: {e}")
            raise

    def _optimize_db(self, db_path: Path) -> None:
        """Run post-import optimizations."""
        logger.info("Running post-import optimizations...")
        # Use isolation_level=None for autocommit mode, required for VACUUM
        conn = sqlite3.connect(db_path, isolation_level=None)
        try:
            cursor = conn.cursor()

            # Create FTS5 table
            logger.info("Creating FTS5 virtual table for search...")
            cursor.execute(f"DROP TABLE IF EXISTS {FTS_TABLE_NAME}")
            cursor.execute(FTS_CREATE_TABLE_SQL)
            cursor.execute(FTS_INSERT_ALL_SQL)

            # ANALYZE for query planner
            logger.info("Running ANALYZE...")
            cursor.execute("ANALYZE")

            # VACUUM to shrink and defragment
            logger.info("Running VACUUM...")
            cursor.execute("VACUUM")

            conn.commit()
            logger.info("Optimizations complete")
        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            # Don't re-raise, we still want the DB to be usable even if not perfectly optimized
        finally:
            conn.close()


import_service = ImportService()
