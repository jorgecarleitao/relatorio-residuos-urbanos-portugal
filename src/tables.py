#!/usr/bin/env python3
"""
Generate AsciiDoc tables from CSV data files.
"""

from pathlib import Path
from typing import Dict, List, Optional, Union
import polars as pl

# Data directory path
DATA_DIR = Path('data/2024/extracted')


def format_number(value: Union[str, int, float, None], decimals: Optional[int] = None) -> str:
    """Format numeric values for display."""
    if not value or value == 'N/D':
        return 'N/D'
    
    try:
        # Handle both string and numeric input
        if isinstance(value, str):
            num = float(value.replace(',', '.'))
        else:
            num = float(value)
        
        if decimals is not None:
            formatted = f"{num:.{decimals}f}"
        else:
            # Auto-detect if it's an integer
            if num.is_integer():
                formatted = f"{int(num)}"
            else:
                formatted = f"{num:.1f}"
        
        # Add thousand separators (European style: 1.000,5)
        if '.' in formatted:
            int_part, dec_part = formatted.split('.')
            int_part = f"{int(int_part):,}".replace(',', '.')
            return f"{int_part},{dec_part}"
        else:
            return f"{int(formatted):,}".replace(',', '.')
            
    except (ValueError, AttributeError):
        return str(value) if value else 'N/D'


def df_to_asciidoc_table(
    df: pl.DataFrame,
    headers: List[str],
    column_specs: List[Dict[str, Union[str, int, bool]]],
    col_align: Optional[str] = None
) -> str:
    """
    Convert a polars DataFrame to an AsciiDoc table.
    
    Args:
        df: Input DataFrame
        headers: List of header labels for the table
        column_specs: List of dicts with keys:
            - 'col': column name in DataFrame
            - 'decimals': optional int for decimal places
            - 'suffix': optional string to append (e.g., '%')
            - 'title_case': optional bool to title case the value
        col_align: Column alignment spec (e.g., "1,>1,>1" or "1,1,1")
    
    Returns:
        AsciiDoc table string
    """
    output = []
    
    # Default column alignment if not specified
    if col_align is None:
        col_align = ','.join(['1'] * len(headers))
    
    output.append(f'[cols="{col_align}"]')
    output.append('|===')
    output.append('|' + ' |'.join(headers))
    output.append('')
    
    for row in df.iter_rows(named=True):
        row_values = []
        for spec in column_specs:
            col_name = spec['col']
            value = row[col_name]
            
            # Apply title case if requested
            if spec.get('title_case', False) and isinstance(value, str):
                value = value.title()
            
            # Format number if not already a string
            if not isinstance(value, str) or col_name != 'Empresa':
                value = format_number(value, decimals=spec.get('decimals'))
            
            # Add suffix if specified
            if spec.get('suffix'):
                value = f"{value}{spec['suffix']}"
            
            row_values.append(str(value))
        
        output.append('|' + ' |'.join(row_values))
    
    output.append('|===')
    return '\n'.join(output)


# ============================================================================
# CALCULATION FUNCTIONS (return polars DataFrames)
# ============================================================================

def calculate_sistemas_analisados() -> pl.DataFrame:
    """Calculate systems analysis data."""
    capital = pl.read_csv(DATA_DIR / 'capital_social.csv')
    regions = pl.read_csv(DATA_DIR / 'empresa_regioes.csv')
    
    # Join and format
    df = capital.join(regions, on='Empresa', how='left')
    df = df.with_columns([
        (pl.lit('EGF (') + pl.col('EGF (%)').cast(pl.Utf8) + pl.lit('%)')).alias('Acionista')
    ])
    
    # Sort before selecting
    df = df.sort('EGF (%)', descending=True)
    
    return df.select([
        'Empresa',
        'Região',
        'Acionista'
    ])


def calculate_rentability_per_ton() -> pl.DataFrame:
    """Calculate profitability per ton of waste."""
    waste = pl.read_csv(DATA_DIR / 'receção_residuos.csv')
    finance = pl.read_csv(DATA_DIR / 'indicadores_financeiros.csv')
    
    # Join datasets
    df = waste.join(finance, on='Empresa', how='inner')
    
    # Filter valid data and calculate per-ton metrics
    df = df.filter(pl.col('Total RU Recebidos (ton)').is_not_null())
    
    df = df.with_columns([
        (pl.col('Vendas e Serviços Prestados (€)') / pl.col('Total RU Recebidos (ton)')).alias('Receita_por_Ton'),
        (pl.col('EBITDA (€)') / pl.col('Total RU Recebidos (ton)')).alias('EBITDA_por_Ton'),
        (pl.col('Resultado Líquido (€)') / pl.col('Total RU Recebidos (ton)')).alias('Lucro_por_Ton')
    ])
    
    return df.select([
        'Empresa',
        'Receita_por_Ton',
        'EBITDA_por_Ton',
        'Lucro_por_Ton'
    ]).sort('Lucro_por_Ton', descending=True)


def calculate_roe() -> pl.DataFrame:
    """Calculate ROE (Return on Equity)."""
    finance = pl.read_csv(DATA_DIR / 'indicadores_financeiros.csv')
    capital = pl.read_csv(DATA_DIR / 'capital_social.csv')
    
    # Join datasets
    df = finance.join(capital, on='Empresa', how='left')
    
    # Convert to millions and calculate ROE
    df = df.with_columns([
        (pl.col('Capital Próprio (€)') / 1_000_000).alias('CP_M'),
        (pl.col('Capital Social (€)') / 1_000_000).alias('CS_M'),
        (pl.col('Resultado Líquido (€)') / 1_000_000).alias('RL_M')
    ])
    
    df = df.with_columns([
        pl.when(pl.col('CP_M') > 0)
        .then((pl.col('RL_M') / pl.col('CP_M')) * 100)
        .otherwise(0.0)
        .alias('ROE')
    ])
    
    return df.select([
        'Empresa',
        'CP_M',
        'CS_M',
        'RL_M',
        'ROE'
    ]).sort('ROE', descending=True)




# ============================================================================
# GENERATION FUNCTIONS (produce AsciiDoc output)
# ============================================================================

def generate_sistemas_analisados() -> str:
    """Generate 'Sistemas Analisados' table."""
    df = calculate_sistemas_analisados()
    
    return df_to_asciidoc_table(
        df,
        headers=['Sistema', 'Região', 'Acionista Maioritário'],
        column_specs=[
            {'col': 'Empresa', 'title_case': True},
            {'col': 'Região'},
            {'col': 'Acionista'}
        ],
        col_align='1,1,2'
    )


def generate_rentability_per_ton_table() -> str:
    """Generate 'Rentabilidade por Tonelada' table."""
    df = calculate_rentability_per_ton()
    
    return df_to_asciidoc_table(
        df,
        headers=['Empresa', 'Receita (€/t)', 'EBITDA (€/t)', 'Lucro (€/t)'],
        column_specs=[
            {'col': 'Empresa', 'title_case': True},
            {'col': 'Receita_por_Ton', 'decimals': 1},
            {'col': 'EBITDA_por_Ton', 'decimals': 1},
            {'col': 'Lucro_por_Ton', 'decimals': 1}
        ],
        col_align='1,1,1,1'
    )


def generate_roe_table() -> str:
    """Generate ROE (Return on Equity) table."""
    df = calculate_roe()
    
    return df_to_asciidoc_table(
        df,
        headers=['Empresa', 'Capital Próprio (M€)', 'Capital Social (M€)', 'Resultado Líquido (M€)', 'ROE (%)'],
        column_specs=[
            {'col': 'Empresa', 'title_case': True},
            {'col': 'CP_M', 'decimals': 1},
            {'col': 'CS_M', 'decimals': 1},
            {'col': 'RL_M', 'decimals': 2},
            {'col': 'ROE', 'decimals': 0, 'suffix': '%'}
        ],
        col_align='1,1,1,1,1'
    )


def main() -> None:
    """Generate all tables and save to build/tables/ directory."""
    output_dir = Path('build/tables')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    tables = {
        'sistemas_analisados.adoc': generate_sistemas_analisados(),
        'rentability_per_ton.adoc': generate_rentability_per_ton_table(),
        'roe.adoc': generate_roe_table(),
    }
    
    for filename, content in tables.items():
        filepath = output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Generated: {filepath}")
    
    print(f"\nAll {len(tables)} tables generated successfully!")


if __name__ == '__main__':
    main()
