#!/usr/bin/env python3
"""
Generate high-quality vector figures for the document from CSV data.
Outputs SVG format for optimal quality in HTML and PDF via AsciiDoc.
"""

from typing import Tuple
import polars as pl
import matplotlib.pyplot as plt
import numpy as np
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


def figure_capital_social(df: pl.DataFrame) -> None:
    """Generate bar chart of capital social by company."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    companies = df['Empresa'].to_list()
    capital = df['Capital Social (€)'].cast(pl.Int64) / 1_000_000  # Convert to millions
    
    ax.bar(companies, capital, color='steelblue', edgecolor='navy', alpha=0.8)
    ax.set_xlabel('Empresa')
    ax.set_ylabel('Capital Social (M€)')
    ax.set_title('Capital Social das Empresas em 2024')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    output_path = OUTPUT_DIR / 'capital_social.svg'
    fig.savefig(output_path, format='svg', bbox_inches='tight')
    plt.close(fig)
    print(f"✓ Generated: {output_path}")


def figure_ebitda_margin(df: pl.DataFrame) -> None:
    """Generate bar chart of EBITDA margins."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    companies = df['Empresa'].to_list()
    margins = df['Margem EBITDA (%)'].cast(pl.Float64).to_list()
    
    colors = ['green' if m >= 25 else 'orange' if m >= 20 else 'red' for m in margins]
    ax.bar(companies, margins, color=colors, edgecolor='black', alpha=0.7)
    ax.axhline(y=25, color='green', linestyle='--', alpha=0.5, label='25% (Bom)')
    ax.axhline(y=20, color='orange', linestyle='--', alpha=0.5, label='20% (Médio)')
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


def figure_waste_collection(df: pl.DataFrame) -> None:
    """Generate stacked bar chart of waste collection."""
    fig, ax = plt.subplots(figsize=(11, 6))
    
    companies = df['Empresa'].to_list()
    indiferenciados = df['Total RU Indiferenciados (ton)'].cast(pl.Int64) / 1000
    seletivos = df['Total Recolha Seletiva (ton)'].cast(pl.Int64) / 1000
    
    x = np.arange(len(companies))
    width = 0.6
    
    p1 = ax.bar(x, indiferenciados, width, label='Indiferenciados', color='gray', alpha=0.8)
    p2 = ax.bar(x, seletivos, width, bottom=indiferenciados, label='Recolha Seletiva', color='green', alpha=0.8)
    
    ax.set_xlabel('Empresa')
    ax.set_ylabel('Resíduos (mil toneladas)')
    ax.set_title('Resíduos Urbanos Recebidos em 2024')
    ax.set_xticks(x)
    ax.set_xticklabels(companies, rotation=45, ha='right')
    ax.legend()
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    plt.tight_layout()
    
    output_path = OUTPUT_DIR / 'waste_collection.svg'
    fig.savefig(output_path, format='svg', bbox_inches='tight')
    plt.close(fig)
    print(f"✓ Generated: {output_path}")


def figure_waste_per_capita(df: pl.DataFrame) -> None:
    """Generate bar chart of waste per capita."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    companies = df['Empresa'].to_list()
    population = df['População Servida (hab)'].cast(pl.Int64)
    total_waste = df['Total RU Recebidos (ton)'].cast(pl.Int64)
    
    # Calculate kg per habitant per year
    waste_per_capita = (total_waste * 1000 / population).to_list()
    
    # Sort by waste per capita for better visualization
    sorted_data = sorted(zip(companies, waste_per_capita), key=lambda x: x[1], reverse=True)
    companies_sorted, waste_sorted = zip(*sorted_data)
    
    # Color code: red for high, orange for medium, green for low
    colors = ['red' if w > 600 else 'orange' if w > 450 else 'green' for w in waste_sorted]
    ax.bar(companies_sorted, waste_sorted, color=colors, edgecolor='black', alpha=0.7)
    
    # Add reference lines
    ax.axhline(y=526, color='blue', linestyle='--', alpha=0.5, label='Média Nacional (~526 kg/hab)')
    
    ax.set_xlabel('Empresa')
    ax.set_ylabel('Resíduos por Habitante (kg/hab/ano)')
    ax.set_title('Produção de Resíduos per Capita em 2024')
    ax.legend()
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    output_path = OUTPUT_DIR / 'waste_per_capita.svg'
    fig.savefig(output_path, format='svg', bbox_inches='tight')
    plt.close(fig)
    print(f"✓ Generated: {output_path}")


def figure_employees_vs_revenue(df: pl.DataFrame) -> None:
    """Generate scatter plot of employees vs revenue."""
    fig, ax = plt.subplots(figsize=(10, 7))
    
    # Convert to numeric, handling any potential issues
    employees = df['Nº Médio Trabalhadores'].cast(pl.Int64).to_list()
    revenue = (df['Vendas e Serviços Prestados (€)'].cast(pl.Int64) / 1_000_000).to_list()
    companies = df['Empresa'].to_list()
    
    ax.scatter(employees, revenue, s=100, alpha=0.6, c='steelblue', edgecolors='navy')
    
    # Add labels for each point
    for i, company in enumerate(companies):
        ax.annotate(company, (employees[i], revenue[i]), 
                   xytext=(5, 5), textcoords='offset points', fontsize=8)
    
    ax.set_xlabel('Número Médio de Trabalhadores')
    ax.set_ylabel('Vendas e Serviços Prestados (M€)')
    ax.set_title('Relação entre Número de Trabalhadores e Receitas em 2024')
    ax.grid(True, alpha=0.3, linestyle='--')
    plt.tight_layout()
    
    output_path = OUTPUT_DIR / 'employees_vs_revenue.svg'
    fig.savefig(output_path, format='svg', bbox_inches='tight')
    plt.close(fig)
    print(f"✓ Generated: {output_path}")


def figure_financial_autonomy(df: pl.DataFrame) -> None:
    """Generate bar chart of financial autonomy."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    companies = df['Empresa'].to_list()
    autonomy = df['Autonomia Financeira (%)'].cast(pl.Float64).to_list()
    
    colors = ['green' if a >= 40 else 'orange' if a >= 25 else 'red' for a in autonomy]
    ax.bar(companies, autonomy, color=colors, edgecolor='black', alpha=0.7)
    ax.axhline(y=40, color='green', linestyle='--', alpha=0.5, label='40% (Bom)')
    ax.axhline(y=25, color='orange', linestyle='--', alpha=0.5, label='25% (Médio)')
    ax.set_xlabel('Empresa')
    ax.set_ylabel('Autonomia Financeira (%)')
    ax.set_title('Autonomia Financeira das Empresas em 2024')
    ax.legend()
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    output_path = OUTPUT_DIR / 'financial_autonomy.svg'
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
    ax.axhline(y=10, color='darkred', linestyle='--', alpha=0.5, label='10% (Limite Adequado)')
    
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


def main() -> None:
    """Generate all figures."""
    print("Loading data...")
    capital_social, indicadores, residuos = load_data()
    
    print(f"\nGenerating figures to {OUTPUT_DIR}/\n")
    
    figure_capital_social(capital_social)
    figure_ebitda_margin(indicadores)
    figure_waste_collection(residuos)
    figure_waste_per_capita(residuos)
    figure_employees_vs_revenue(indicadores)
    figure_financial_autonomy(indicadores)
    figure_roe_distribution(capital_social, indicadores)
    
    print(f"\n✓ All figures generated successfully!")


if __name__ == '__main__':
    main()
