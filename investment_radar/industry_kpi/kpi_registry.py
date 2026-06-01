from sector_intelligence.sector_kpi_map import SECTOR_KPI_MAP


def get_kpi_registry() -> dict:
    return SECTOR_KPI_MAP


def get_sector_kpis(sector: str) -> list[str]:
    return SECTOR_KPI_MAP.get(sector, [])
