"""Tests for year range filter."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import Movie


def test_get_movies_filter_by_year_range(client: TestClient, db_session: Session):
    """Test filtering movies by year range."""
    # Add movies with different years and one with NULL year
    movies = [
        Movie(id=1, title="1990 Movie", year=1990, type="movie"),
        Movie(id=2, title="2000 Movie", year=2000, type="movie"),
        Movie(id=3, title="2010 Movie", year=2010, type="movie"),
        Movie(id=4, title="No Year Movie", year=None, type="movie"),
    ]
    for m in movies:
        db_session.add(m)
    db_session.commit()

    # 1. min_year only (should exclude NULL)
    response = client.get("/api/movies?min_year=2000")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2  # 2000, 2010
    assert all(m["year"] >= 2000 for m in data["items"])
    assert all(m["year"] is not None for m in data["items"])

    # 2. max_year only (should include NULL)
    response = client.get("/api/movies?max_year=2000")
    assert response.status_code == 200
    data = response.json()
    # Should include 1990, 2000 and NULL
    assert len(data["items"]) == 3
    years = [m["year"] for m in data["items"]]
    assert None in years
    assert 1990 in years
    assert 2000 in years

    # 3. Both min_year and max_year (should exclude NULL)
    response = client.get("/api/movies?min_year=1995&max_year=2005")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1  # 2000
    assert data["items"][0]["year"] == 2000

    # 4. No year filter (should include all)
    response = client.get("/api/movies")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 4
    years = [m["year"] for m in data["items"]]
    assert None in years
