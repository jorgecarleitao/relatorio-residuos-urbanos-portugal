#!/usr/bin/env python3
"""
Shared data loading and calculation functions.
Used by both figures.py and tables.py to ensure consistency.
"""

from pathlib import Path
from typing import Tuple
import polars as pl

# Data directory path
DATA_DIR = Path(__file__).parent.parent / 'data' / '2024' / 'extracted'


def load_data() -> Tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    """Load all CSV files."""
    capital_social = pl.read_csv(DATA_DIR / 'capital_social.csv')
    indicadores = pl.read_csv(DATA_DIR / 'indicadores_financeiros.csv')
    residuos = pl.read_csv(DATA_DIR / 'receção_residuos.csv')
    return capital_social, indicadores, residuos


def load_regions() -> pl.DataFrame:
    """Load regions data."""
    return pl.read_csv(DATA_DIR / 'empresa_regioes.csv')


# ============================================================================
# CALCULATION FUNCTIONS
# ============================================================================

def calculate_sistemas_analisados() -> pl.DataFrame:
    """Calculate systems analysis data."""
    operacao = pl.read_csv(DATA_DIR / 'empresa_operacao.csv')
    regions = load_regions()
    
    # Join and format
    df = operacao.join(regions, left_on='empresa', right_on='Empresa', how='left')
    
    # Sort by population descending
    df = df.sort('populacao_servida', descending=True)
    
    return df.select([
        pl.col('empresa').alias('Empresa'),
        'Região',
        pl.col('municipios_servidos').alias('Municípios'),
        pl.col('populacao_servida').alias('População')
    ])


def calculate_ebitda_margins() -> pl.DataFrame:
    """Calculate EBITDA margins."""
    finance = pl.read_csv(DATA_DIR / 'indicadores_financeiros.csv')
    
    return finance.select([
        'Empresa',
        'Margem EBITDA (%)'
    ]).sort('Margem EBITDA (%)', descending=True)


def calculate_roe() -> pl.DataFrame:
    """Calculate ROE (Return on Equity)."""
    finance = pl.read_csv(DATA_DIR / 'indicadores_financeiros.csv')
    
    # Calculate ROE from existing data
    df = finance.with_columns([
        pl.when(pl.col('Capital Próprio (€)') > 0)
        .then((pl.col('Resultado Líquido (€)') / pl.col('Capital Próprio (€)')) * 100)
        .otherwise(0.0)
        .alias('ROE')
    ])
    
    return df.select([
        'Empresa',
        'ROE'
    ]).sort('ROE', descending=True)


def calculate_net_debt_ebitda() -> pl.DataFrame:
    """Calculate Net Debt / EBITDA ratio."""
    finance = pl.read_csv(DATA_DIR / 'indicadores_financeiros.csv')
    
    return finance.select([
        'Empresa',
        'Endividamento Líquido / EBITDA (x)'
    ]).sort('Endividamento Líquido / EBITDA (x)', descending=False)


def calculate_rentability_per_ton() -> pl.DataFrame:
    """Calculate profitability per ton of waste."""
    waste = pl.read_csv(DATA_DIR / 'receção_residuos.csv')
    finance = pl.read_csv(DATA_DIR / 'indicadores_financeiros.csv')
    
    # Join datasets
    df = waste.join(finance, on='Empresa', how='inner')
    
    # Filter valid data and calculate per-ton metric
    df = df.filter(pl.col('Total RU Recebidos (ton)').is_not_null())
    
    df = df.with_columns([
        (pl.col('Resultado Líquido (€)') / pl.col('Total RU Recebidos (ton)')).alias('Lucro_por_Ton')
    ])
    
    return df.select([
        'Empresa',
        'Lucro_por_Ton'
    ]).sort('Lucro_por_Ton', descending=True)


def calculate_roe_vs_debt() -> pl.DataFrame:
    """Calculate ROE vs Net Debt/EBITDA for scatter plot."""
    finance = pl.read_csv(DATA_DIR / 'indicadores_financeiros.csv')
    
    # Calculate ROE
    df = finance.with_columns([
        pl.when(pl.col('Capital Próprio (€)') > 0)
        .then((pl.col('Resultado Líquido (€)') / pl.col('Capital Próprio (€)')) * 100)
        .otherwise(0.0)
        .alias('ROE')
    ])
    
    return df.select([
        'Empresa',
        'ROE',
        pl.col('Endividamento Líquido / EBITDA (x)').alias('Debt_EBITDA')
    ])


def load_fontes() -> pl.DataFrame:
    """Load sources/references data."""
    fontes_path = DATA_DIR.parent / 'raw' / 'fontes.csv'
    return pl.read_csv(fontes_path).sort('Empresa')


def calculate_total_coverage() -> dict:
    """Calculate total population and municipalities covered."""
    operacao = pl.read_csv(DATA_DIR / 'empresa_operacao.csv')
    
    total_population = operacao['populacao_servida'].sum()
    total_municipalities = operacao['municipios_servidos'].sum()
    num_systems = len(operacao)
    
    return {
        'population': total_population,
        'municipalities': total_municipalities,
        'systems': num_systems
    }
