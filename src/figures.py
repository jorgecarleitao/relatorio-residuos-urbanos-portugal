#!/usr/bin/env python3
"""
Generate high-quality vector figures for the document from CSV data.
Outputs SVG format for optimal quality in HTML and PDF via AsciiDoc.
"""

from typing import Tuple
import polars as pl
import matplotlib.pyplot as plt
from pathlib import Path

# Configure matplotlib for high-quality output
plt.rcParams['svg.fonttype'] = 'none'  # Preserve text as text, not paths
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9
plt.rcParams['legend.fontsize'] = 9
plt.rcParams['figure.dpi'] = 100

# Paths
DATA_DIR = Path(__file__).parent.parent / 'data' / '2024' / 'extracted'
OUTPUT_DIR = Path(__file__).parent.parent / 'build' / 'figures'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_data() -> Tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    """Load all CSV files."""
    capital_social = pl.read_csv(DATA_DIR / 'capital_social.csv')
    indicadores = pl.read_csv(DATA_DIR / 'indicadores_financeiros.csv')
    residuos = pl.read_csv(DATA_DIR / 'receção_residuos.csv')
    return capital_social, indicadores, residuos


def figure_ebitda_margin(df: pl.DataFrame) -> None:
    """Generate bar chart of EBITDA margins."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    companies = df['Empresa'].to_list()
    margins = df['Margem EBITDA (%)'].cast(pl.Float64).to_list()
    
    colors = ['green' if m >= 20 else 'red' for m in margins]
    ax.bar(companies, margins, color=colors, edgecolor='black', alpha=0.7)
    ax.axhline(y=20, color='green', linestyle='--', alpha=0.5, label='20% (Bom)')
    ax.set_xlabel('Empresa')
    ax.set_ylabel('Margem EBITDA (%)')
    ax.set_title('Margem EBITDA por Empresa em 2024')
    ax.legend()
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    output_path = OUTPUT_DIR / 'ebitda_margins.svg'
    fig.savefig(output_path, format='svg', bbox_inches='tight')
    plt.close(fig)
    print(f"✓ Generated: {output_path}")


def figure_roe_distribution(capital_df: pl.DataFrame, indicadores_df: pl.DataFrame) -> None:
    """Generate bar chart of ROE (Return on Equity) by company with color-coded categories."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Join datasets and calculate ROE
    merged = capital_df.join(indicadores_df, on='Empresa', how='inner')
    
    # Calculate ROE = (Resultado Líquido / Capital Próprio) * 100
    merged = merged.with_columns([
        ((pl.col('Resultado Líquido (€)') / pl.col('Capital Próprio (€)')) * 100).alias('ROE')
    ])
    
    # Sort by ROE descending
    merged = merged.sort('ROE', descending=True)
    
    companies = merged['Empresa'].to_list()
    roe_values = merged['ROE'].to_list()
    
    # Color coding: red for loss (<0), green for adequate (0-10%), red for excessive (>10%)
    colors = []
    for roe in roe_values:
        if roe < 0:
            colors.append('red')
        elif roe < 10:
            colors.append('green')
        else:
            colors.append('red')
    
    bars = ax.bar(companies, roe_values, color=colors, edgecolor='black', alpha=0.7)
    
    # Add threshold lines
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    ax.axhline(y=10, color='red', linestyle='--', alpha=0.5, label='')
    ax.axhline(y=-10, color='red', linestyle='--', alpha=0.5, label='')
    
    ax.set_xlabel('Empresa')
    ax.set_ylabel('ROE - Rentabilidade sobre Capital Próprio (%)')
    ax.set_title('Rentabilidade sobre Capital Próprio (ROE) em 2024')
    ax.legend(loc='upper right')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    output_path = OUTPUT_DIR / 'roe_distribution.svg'
    fig.savefig(output_path, format='svg', bbox_inches='tight')
    plt.close(fig)
    print(f"✓ Generated: {output_path}")


def figure_net_debt_ebitda(indicadores_df: pl.DataFrame) -> None:
    """Generate bar chart of Net Debt / EBITDA by company with color-coded leverage categories."""
    fig, ax = plt.subplots(figsize=(10, 6))

    # Sort by ratio ascending (lower leverage is better)
    df = indicadores_df.sort('Endividamento Líquido / EBITDA (x)', descending=False)

    companies = df['Empresa'].to_list()
    values = df['Endividamento Líquido / EBITDA (x)'].cast(pl.Float64).to_list()

    # Color coding: green < 2x (low), orange 2–4x (moderate), red > 4x (high)
    colors = []
    for v in values:
        if v < 1:
            colors.append('red')
        elif v <= 4:
            colors.append('green')
        else:
            colors.append('red')

    ax.bar(companies, values, color=colors, edgecolor='black', alpha=0.7)

    ax.axhline(y=1, color='red', linestyle='--', alpha=0.6, label='1x')
    ax.axhline(y=4, color='red', linestyle='--', alpha=0.6, label='4x')

    ax.set_xlabel('Empresa')
    ax.set_ylabel('Dívida Líquida / EBITDA (x)')
    ax.set_title('Dívida Líquida / EBITDA por Empresa em 2024')
    ax.legend(loc='upper left')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    output_path = OUTPUT_DIR / 'net_debt_ebitda.svg'
    fig.savefig(output_path, format='svg', bbox_inches='tight')
    plt.close(fig)
    print(f"✓ Generated: {output_path}")


def figure_rentability_per_ton(indicadores_df: pl.DataFrame, residuos_df: pl.DataFrame) -> None:
    """Generate bar chart of rentability per ton by company with color-coded categories."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Join datasets and calculate rentability per ton
    merged = indicadores_df.join(residuos_df, on='Empresa', how='inner')
    
    # Calculate Rentability per ton = (Resultado Líquido / Total RU Recebidos)
    merged = merged.with_columns([
        (pl.col('Resultado Líquido (€)') / pl.col('Total RU Recebidos (ton)')).alias('Rentabilidade_por_Ton')
    ])
    
    # Sort by rentability per ton descending
    merged = merged.sort('Rentabilidade_por_Ton', descending=True)
    
    companies = merged['Empresa'].to_list()
    rent_per_ton = merged['Rentabilidade_por_Ton'].to_list()
    
    # Color coding: red for loss (<0), green for positive (0-5€/t), orange for high (>5€/t)
    colors = []
    for rent in rent_per_ton:
        if rent < 0:
            colors.append('red')
        elif rent <= 5:
            colors.append('green')
        else:
            colors.append('orange')
    
    bars = ax.bar(companies, rent_per_ton, color=colors, edgecolor='black', alpha=0.7)
    
    # Add threshold lines
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    ax.axhline(y=5, color='orange', linestyle='--', alpha=0.5, label='5 €/t (Rentabilidade Moderada)')
    
    ax.set_xlabel('Empresa')
    ax.set_ylabel('Rentabilidade por Tonelada (€/t)')
    ax.set_title('Rentabilidade por Tonelada de Resíduo em 2024')
    ax.legend(loc='upper right')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    output_path = OUTPUT_DIR / 'rentability_per_ton.svg'
    fig.savefig(output_path, format='svg', bbox_inches='tight')
    plt.close(fig)
    print(f"✓ Generated: {output_path}")


def main() -> None:
    """Generate all figures."""
    print("Loading data...")
    capital_social, indicadores, residuos = load_data()
    
    print(f"\nGenerating figures to {OUTPUT_DIR}/\n")
    
    figure_ebitda_margin(indicadores)
    figure_roe_distribution(capital_social, indicadores)
    figure_net_debt_ebitda(indicadores)
    figure_rentability_per_ton(indicadores, residuos)
    
    print(f"\n✓ All figures generated successfully!")


if __name__ == '__main__':
    main()
