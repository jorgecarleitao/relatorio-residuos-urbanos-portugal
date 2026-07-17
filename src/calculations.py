#!/usr/bin/env python3
"""
Shared data loading and calculation functions.
Used by generate.py to ensure consistency.
"""

from pathlib import Path
from typing import Tuple
import polars as pl

def _data_dir(year: str = '2024') -> Path:
    return Path(__file__).parent.parent / 'data' / year / 'extracted'


def _load_companies(year: str = '2024') -> pl.DataFrame:
    """Load all per-company JSONs into a single flat DataFrame."""
    data_dir = _data_dir(year)
    json_files = sorted(data_dir.glob("*.json"))

    import json
    records = []
    for f in json_files:
        with open(f) as fh:
            data = json.load(fh)
        empresa_name = data.get("empresa", "")
        assert empresa_name and isinstance(empresa_name, str), f"{f.name}: 'empresa' field is missing or empty"
        flat = {"empresa": empresa_name, "ano": data.get("ano"), "regiao": data.get("regiao")}
        for group in ("indicadores", "waste", "operations", "debt", "capital", "revenue"):
            for k, v in data.get(group, {}).items():
                flat[k] = v
        records.append(flat)

    df = pl.DataFrame(records)
    assert df['empresa'].is_not_null().all(), f"{year}: Null values found in empresa column after loading"
    return df


def load_fontes(year: str = '2024') -> pl.DataFrame:
    """Load sources/references data for a given year."""
    fontes_path = _data_dir(year).parent / 'raw' / 'fontes.csv'
    df = pl.read_csv(fontes_path)
    assert df['Empresa'].is_not_null().all(), f"{year}: Null values found in Empresa column in fontes.csv"
    return df.sort('Empresa')


# ============================================================================
# CALCULATION FUNCTIONS
# ============================================================================

def calculate_sistemas_analisados(year: str = '2024') -> pl.DataFrame:
    """Calculate systems analysis data."""
    df = _load_companies(year)

    # Sort by population descending
    df = df.sort('populacao_servida', descending=True)

    result = df.select([
        pl.col('empresa').alias('Empresa'),
        pl.col('regiao').alias('Região'),
        pl.col('municipios_servidos').alias('Municípios'),
        pl.col('populacao_servida').alias('População')
    ])
    assert result['Empresa'].is_not_null().all(), "Null values found in Empresa in calculate_sistemas_analisados"
    return result


def calculate_ebitda_margins(year: str = '2024') -> pl.DataFrame:
    """Calculate EBITDA margins."""
    df = _load_companies(year)

    result = df.select([
        pl.col('empresa').alias('Empresa'),
        (pl.col('ebitda') / pl.col('vendas') * 100).alias('Margem EBITDA (%)')
    ]).sort('Margem EBITDA (%)', descending=True)
    assert result['Empresa'].is_not_null().all(), "Null values found in Empresa in calculate_ebitda_margins"
    return result


def calculate_roe(year: str = '2024') -> pl.DataFrame:
    """Calculate ROE (Return on Equity)."""
    df = _load_companies(year)

    # Calculate ROE from existing data
    df = df.with_columns([
        pl.when(pl.col('capital_proprio') > 0)
        .then((pl.col('resultado_liquido') / pl.col('capital_proprio')) * 100)
        .otherwise(0.0)
        .alias('ROE')
    ])

    result = df.select([
        pl.col('empresa').alias('Empresa'),
        'ROE'
    ]).sort('ROE', descending=True)
    assert result['Empresa'].is_not_null().all(), "Null values found in Empresa in calculate_roe"
    return result


def calculate_net_debt_ebitda(year: str = '2024') -> pl.DataFrame:
    """Calculate Net Debt / EBITDA ratio."""
    df = _load_companies(year)

    assert df['endividamento_liquido'].is_not_null().all(), "Null values found in endividamento_liquido"
    assert df['ebitda'].is_not_null().all(), "Null values found in ebitda"

    result = df.select([
        pl.col('empresa').alias('Empresa'),
        (pl.col('endividamento_liquido') / pl.col('ebitda')).alias('Endividamento Líquido / EBITDA (x)')
    ]).sort('Endividamento Líquido / EBITDA (x)', descending=False)
    assert result['Empresa'].is_not_null().all(), "Null values found in Empresa in calculate_net_debt_ebitda"
    return result


def calculate_dividend_per_tariff(year: str = '2024') -> pl.DataFrame:
    """Calculate dividends as % of municipality fee revenue.
    
    Uses: dividendos / (tarifa_regulada * ru_indiferenciados_municipais) * 100
    Only undifferentiated municipal waste is tariffed; selective collection is excluded.
    This measures what % of what municipalities pay ends up as dividends.
    """
    df = _load_companies(year)

    result = df.with_columns([
        (pl.col('tarifa_regulada') * pl.col('ru_indiferenciados_municipais')).alias('municipio_receita'),
    ]).with_columns([
        pl.when(
            pl.col('municipio_receita').is_not_null() & 
            (pl.col('municipio_receita') > 0) &
            pl.col('dividendos').is_not_null()
        )
        .then((pl.col('dividendos') / pl.col('municipio_receita') * 100))
        .otherwise(None)
        .alias('Dividendos / Tarifa (%)')
    ]).filter(
        pl.col('Dividendos / Tarifa (%)').is_not_null()
    ).select([
        pl.col('empresa').alias('Empresa'),
        'Dividendos / Tarifa (%)'
    ]).sort('Dividendos / Tarifa (%)', descending=True)

    return result


def calculate_rentability_per_ton(year: str = '2024') -> pl.DataFrame:
    """Calculate profitability per ton of waste."""
    df = _load_companies(year)

    df = df.filter(pl.col('total_ru_recebidos').is_not_null())

    df = df.with_columns([
        (pl.col('resultado_liquido') / pl.col('total_ru_recebidos')).alias('Lucro_por_Ton')
    ])

    result = df.select([
        pl.col('empresa').alias('Empresa'),
        'Lucro_por_Ton'
    ]).sort('Lucro_por_Ton', descending=True)
    assert result['Empresa'].is_not_null().all(), "Null values found in Empresa in calculate_rentability_per_ton"
    return result


def calculate_roe_vs_debt(year: str = '2024') -> pl.DataFrame:
    """Calculate ROE vs Net Debt/EBITDA for scatter plot."""
    df = _load_companies(year)

    assert df['endividamento_liquido'].is_not_null().all(), "Null values found in endividamento_liquido"
    assert df['ebitda'].is_not_null().all(), "Null values found in ebitda"

    result = df.select([
        pl.col('empresa').alias('Empresa'),
        pl.when(pl.col('capital_proprio') > 0)
        .then((pl.col('resultado_liquido') / pl.col('capital_proprio')) * 100)
        .otherwise(0.0).alias('ROE'),
        (pl.col('endividamento_liquido') / pl.col('ebitda')).alias('Debt_EBITDA')
    ])
    assert result['Empresa'].is_not_null().all(), "Null values found in Empresa in calculate_roe_vs_debt"
    return result


# Continental Portugal population (INE, 2023)
CONTINENTAL_POPULATION = 10_344_802


def calculate_total_coverage() -> dict:
    """Calculate total population and municipalities covered."""
    df = _load_companies()

    total_population = df['populacao_servida'].sum()
    total_municipalities = df['municipios_servidos'].sum()
    num_systems = len(df)
    pct_continental = round(total_population / CONTINENTAL_POPULATION * 100)

    return {
        'population': total_population,
        'municipalities': total_municipalities,
        'systems': num_systems,
        'pct_continental': pct_continental
    }
