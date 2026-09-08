from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class OpenDataSource:
    name: str
    source_type: str
    region: str
    url: str
    license: str
    status: str = "active"
    notes: str = ""
    api: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "source_type": self.source_type,
            "region": self.region,
            "url": self.url,
            "license": self.license,
            "status": self.status,
            "notes": self.notes,
            "api": self.api,
        }


class OpenDataRegistry:
    """Tiny registry for real free/open data sources with evidence-bound metadata."""

    def __init__(self) -> None:
        self._sources: list[OpenDataSource] = [
            OpenDataSource(
                name="Open-Meteo",
                source_type="weather",
                region="Global",
                url="https://open-meteo.com/",
                license="open-license",
                notes="Free weather and climate API without API key for core endpoints.",
                api="https://api.open-meteo.com/v1/forecast",
            ),
            OpenDataSource(
                name="OpenStreetMap Overpass",
                source_type="map",
                region="Global",
                url="https://wiki.openstreetmap.org/wiki/Overpass_API",
                license="odbl",
                notes="Open map and geodata query API.",
                api="https://overpass-api.de/api/interpreter",
            ),
            OpenDataSource(
                name="World Bank Open Data",
                source_type="economy",
                region="Global",
                url="https://data.worldbank.org/",
                license="open-license",
                notes="Development, economy, and demographic datasets.",
                api="https://api.worldbank.org/v2/",
            ),
            OpenDataSource(
                name="GeoNames",
                source_type="geography",
                region="Global",
                url="https://www.geonames.org/",
                license="cc-by",
                notes="Place names, coordinates, and geolocation reference data.",
                api="https://api.geonames.org/",
            ),
            OpenDataSource(
                name="Wikidata",
                source_type="knowledge",
                region="Global",
                url="https://www.wikidata.org/",
                license="cc0",
                notes="Structured linked open knowledge graph.",
                api="https://www.wikidata.org/w/api.php",
            ),
            OpenDataSource(
                name="Data.gov USA",
                source_type="government",
                region="North America",
                url="https://data.gov/",
                license="open-license",
                notes="United States government open datasets.",
                api="https://catalog.data.gov/api/3/action/package_search",
            ),
            OpenDataSource(
                name="Eurostat",
                source_type="economy",
                region="Europe",
                url="https://ec.europa.eu/eurostat/",
                license="eu-odbl",
                notes="Official European Union statistics and indicators.",
                api="https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data",
            ),
            OpenDataSource(
                name="NOAA",
                source_type="environment",
                region="North America",
                url="https://www.noaa.gov/",
                license="public-domain",
                notes="Climate, ocean, weather, and environmental data.",
                api="https://www.ncei.noaa.gov/",
            ),
            OpenDataSource(
                name="OpenAQ",
                source_type="environment",
                region="Global",
                url="https://openaq.org/",
                license="open-license",
                notes="Air quality monitoring and pollution data.",
                api="https://api.openaq.org/v3/",
            ),
            OpenDataSource(
                name="UN Data",
                source_type="government",
                region="Global",
                url="https://data.un.org/",
                license="open-license",
                notes="United Nations statistical datasets.",
                api="https://data.un.org/Explorer.aspx",
            ),
            OpenDataSource(
                name="Open Africa",
                source_type="government",
                region="Africa",
                url="https://africaopendata.org/",
                license="open-license",
                notes="Open data portal for African public datasets.",
                api="https://africaopendata.org/api/3/action/package_search",
            ),
            OpenDataSource(
                name="data.gov.au",
                source_type="government",
                region="Oceania",
                url="https://data.gov.au/",
                license="open-license",
                notes="Australian open government data portal.",
                api="https://data.gov.au/data/api/3/action/package_search",
            ),
        ]

    def list_sources(self) -> list[dict[str, Any]]:
        return [source.as_dict() for source in self._sources]

    def summary(self) -> dict[str, Any]:
        region_counts: dict[str, int] = {}
        for source in self._sources:
            region_counts[source.region] = region_counts.get(source.region, 0) + 1
        return {
            "total_sources": len(self._sources),
            "regions": region_counts,
            "active_sources": sum(1 for source in self._sources if source.status == "active"),
        }

    def find(self, query: str) -> list[dict[str, Any]]:
        lowered = (query or "").casefold()
        matches: list[dict[str, Any]] = []
        for source in self._sources:
            if lowered in source.name.casefold() or lowered in source.source_type.casefold() or lowered in source.region.casefold():
                matches.append(source.as_dict())
        return matches
