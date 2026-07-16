#!/usr/bin/env python3
"""
Generate both tables and figures from the same data.
Ensures perfect consistency between visual and text representations.
"""

from pathlib import Path
from typing import Dict, List, Optional, Union
import polars as pl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from calculations import (
    calculate_sistemas_analisados,
    calculate_ebitda_margins,
    calculate_roe,
    calculate_net_debt_ebitda,
    calculate_rentability_per_ton,
    calculate_dividend_per_tariff,
    calculate_roe_vs_debt,
    calculate_total_coverage,
    load_fontes
)

# Configure matplotlib for high-quality output
plt.rcParams['svg.fonttype'] = 'none'  # Preserve text as text, not paths
plt.rcParams['axes.unicode_minus'] = False  # Use ASCII hyphen, not Unicode minus
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9
plt.rcParams['legend.fontsize'] = 9
plt.rcParams['figure.dpi'] = 100

# Output directories
TABLES_DIR = Path('build/tables')
FIGURES_DIR = Path('build/figures')
TABLES_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def format_number(value: Union[str, int, float, None], decimals: Optional[int] = None) -> str:
    """Format numeric values for display."""
    if value is None or value == 'N/D' or value == '':
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
        return str(value) if value is not None else 'N/D'


def write_table(
    name: str,
    df: pl.DataFrame,
    headers: List[str],
    column_specs: List[Dict[str, Union[str, int, bool]]],
    col_align: Optional[str] = None
) -> None:
    """
    Write a polars DataFrame as an AsciiDoc table.
    
    Args:
        name: Output filename (without extension)
        df: Input DataFrame
        headers: List of header labels for the table
        column_specs: List of dicts with keys:
            - 'col': column name in DataFrame
            - 'decimals': optional int for decimal places
            - 'suffix': optional string to append (e.g., '%')
            - 'title_case': optional bool to title case the value
        col_align: Column alignment spec (e.g., "1,1,1" or "1,1,1")
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
    
    # Write to file
    filepath = TABLES_DIR / f'{name}.adoc'
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))
    print(f"✓ Table: {filepath}")


def write_bar_plot(
    name: str,
    df: pl.DataFrame,
    x_col: str,
    y_col: str,
    title: str,
    xlabel: str,
    ylabel: str,
    color_fn,
    threshold_lines: Optional[List[Dict]] = None,
    figsize: tuple = (10, 6)
) -> None:
    """
    Write a bar plot from a DataFrame.
    
    Args:
        name: Output filename (without extension)
        df: Input DataFrame
        x_col: Column name for x-axis (company names)
        y_col: Column name for y-axis (values)
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label
        color_fn: Function that takes a value and returns a color
        threshold_lines: Optional list of dicts with 'y', 'color', 'linestyle', 'label'
        figsize: Figure size tuple
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    companies = df[x_col].to_list()
    values = df[y_col].to_list()
    
    # Apply color function
    colors = [color_fn(v) for v in values]
    
    ax.bar(companies, values, color=colors, edgecolor='black', alpha=0.7)
    
    # Add threshold lines if provided
    if threshold_lines:
        for line in threshold_lines:
            ax.axhline(
                y=line['y'],
                color=line.get('color', 'gray'),
                linestyle=line.get('linestyle', '--'),
                alpha=line.get('alpha', 0.5),
                label=line.get('label', '')
            )
    
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    # Write to file
    output_path = FIGURES_DIR / f'{name}.svg'
    fig.savefig(output_path, format='svg', bbox_inches='tight')
    plt.close(fig)
    print(f"✓ Figure: {output_path}")


def write_bar_plot_2years(
    name: str,
    df_latest: pl.DataFrame,
    df_prior: pl.DataFrame,
    x_col: str,
    y_col: str,
    title_latest: str,
    title_prior: str,
    xlabel: str,
    ylabel: str,
    color_fn,
    threshold_lines: Optional[List[Dict]] = None,
    figsize: tuple = (10, 10)
) -> None:
    """
    Write a two-year bar plot with subplots (top = latest year, bottom = prior year).
    
    Args: same as write_bar_plot but with separate DataFrames and titles for each year.
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize)
    
    for ax, df, title in [(ax1, df_latest, title_latest), (ax2, df_prior, title_prior)]:
        companies = df[x_col].to_list()
        values = df[y_col].to_list()
        colors = [color_fn(v) for v in values]
        
        ax.bar(companies, values, color=colors, edgecolor='black', alpha=0.7)
        
        if threshold_lines:
            for line in threshold_lines:
                ax.axhline(
                    y=line['y'],
                    color=line.get('color', 'gray'),
                    linestyle=line.get('linestyle', '--'),
                    alpha=line.get('alpha', 0.5),
                    label=line.get('label', '')
                )
        
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    
    output_path = FIGURES_DIR / f'{name}.svg'
    fig.savefig(output_path, format='svg', bbox_inches='tight')
    plt.close(fig)
    print(f"✓ Figure: {output_path}")


# ============================================================================
# GENERATION FUNCTIONS
# ============================================================================

def generate_sistemas_analisados() -> None:
    """Generate sistemas analisados table (no figure)."""
    df = calculate_sistemas_analisados()
    
    write_table(
        'sistemas_analisados',
        df,
        headers=['Sistema', 'Região', 'Municípios', 'População (hab)'],
        column_specs=[
            {'col': 'Empresa', 'title_case': True},
            {'col': 'Região'},
            {'col': 'Municípios', 'format': 'int'},
            {'col': 'População', 'format': 'thousands'}
        ],
        col_align='1,1,1,1'
    )


def generate_ebitda_margins() -> None:
    """Generate EBITDA margins table and figure."""
    df_2025 = calculate_ebitda_margins(year='2025')
    df_2024 = calculate_ebitda_margins(year='2024')
    
    # Table (both years)
    tbl = df_2025.join(df_2024, on='Empresa', how='full', suffix='_2024')
    tbl = tbl.with_columns(pl.col('Empresa').fill_null(pl.col('Empresa_2024')))
    assert tbl['Empresa'].is_not_null().all(), "Null Empresa after join in generate_ebitda_margins"
    tbl = tbl.rename({'Margem EBITDA (%)': '2025'})
    tbl = tbl.select([
        pl.col('Empresa'),
        pl.col('2025'),
        pl.col('Margem EBITDA (%)_2024').alias('2024')
    ]).sort('2025', descending=True)
    write_table(
        'ebitda_margins',
        tbl,
        headers=['Empresa', '2025', '2024'],
        column_specs=[
            {'col': 'Empresa', 'title_case': True},
            {'col': '2025', 'decimals': 1},
            {'col': '2024', 'decimals': 1}
        ],
        col_align='1,1,1'
    )
    
    # Figure
    def color_fn(margin):
        return 'green' if margin >= 20 else 'red'
    
    write_bar_plot_2years(
        'ebitda_margins',
        df_2025, df_2024,
        x_col='Empresa',
        y_col='Margem EBITDA (%)',
        title_latest='Margem EBITDA por Empresa em 2025',
        title_prior='Margem EBITDA por Empresa em 2024',
        xlabel='Empresa',
        ylabel='Margem EBITDA (%)',
        color_fn=color_fn,
        threshold_lines=[
            {'y': 20, 'color': 'green', 'linestyle': '--', 'alpha': 0.5}
        ]
    )


def generate_roe() -> None:
    """Generate ROE table and figure."""
    df_2025 = calculate_roe(year='2025')
    df_2024 = calculate_roe(year='2024')
    
    # Table (both years)
    tbl = df_2025.join(df_2024, on='Empresa', how='full', suffix='_2024')
    tbl = tbl.with_columns(pl.col('Empresa').fill_null(pl.col('Empresa_2024')))
    assert tbl['Empresa'].is_not_null().all(), "Null Empresa after join in generate_roe"
    tbl = tbl.rename({'ROE': '2025'})
    tbl = tbl.select([
        pl.col('Empresa'),
        pl.col('2025'),
        pl.col('ROE_2024').alias('2024')
    ]).sort('2025', descending=True)
    write_table(
        'roe',
        tbl,
        headers=['Empresa', '2025', '2024'],
        column_specs=[
            {'col': 'Empresa', 'title_case': True},
            {'col': '2025', 'decimals': 1},
            {'col': '2024', 'decimals': 1}
        ],
        col_align='1,1,1'
    )
    
    # Figure
    def color_fn(roe):
        if roe < 0:
            return 'red'
        elif roe < 10:
            return 'green'
        else:
            return 'red'
    
    write_bar_plot_2years(
        'roe',
        df_2025, df_2024,
        x_col='Empresa',
        y_col='ROE',
        title_latest='Rentabilidade sobre Capital Próprio (ROE) em 2025',
        title_prior='Rentabilidade sobre Capital Próprio (ROE) em 2024',
        xlabel='Empresa',
        ylabel='ROE - Rentabilidade sobre Capital Próprio (%)',
        color_fn=color_fn,
        threshold_lines=[
            {'y': 0, 'color': 'black', 'linestyle': '-', 'alpha': 0.8},
            {'y': 10, 'color': 'red', 'linestyle': '--', 'alpha': 0.5},
            {'y': -10, 'color': 'red', 'linestyle': '--', 'alpha': 0.5}
        ]
    )


def generate_net_debt_ebitda() -> None:
    """Generate Net Debt/EBITDA table and figure."""
    df_2025 = calculate_net_debt_ebitda(year='2025')
    df_2024 = calculate_net_debt_ebitda(year='2024')
    
    # Table (both years)
    col_metric = 'Endividamento Líquido / EBITDA (x)'
    tbl = df_2025.join(df_2024, on='Empresa', how='full', suffix='_2024')
    tbl = tbl.with_columns(pl.col('Empresa').fill_null(pl.col('Empresa_2024')))
    assert tbl['Empresa'].is_not_null().all(), "Null Empresa after join in generate_net_debt_ebitda"
    tbl = tbl.rename({col_metric: '2025'})
    tbl = tbl.select([
        pl.col('Empresa'),
        pl.col('2025'),
        pl.col(f'{col_metric}_2024').alias('2024')
    ]).sort('2025', descending=False)
    write_table(
        'net_debt_ebitda',
        tbl,
        headers=['Empresa', '2025', '2024'],
        column_specs=[
            {'col': 'Empresa', 'title_case': True},
            {'col': '2025', 'decimals': 2},
            {'col': '2024', 'decimals': 2}
        ],
        col_align='1,1,1'
    )
    
    # Figure
    def color_fn(ratio):
        if ratio < 1:
            return 'red'
        elif ratio <= 4:
            return 'green'
        else:
            return 'red'
    
    write_bar_plot_2years(
        'net_debt_ebitda',
        df_2025, df_2024,
        x_col='Empresa',
        y_col='Endividamento Líquido / EBITDA (x)',
        title_latest='Dívida Líquida / EBITDA por Empresa em 2025',
        title_prior='Dívida Líquida / EBITDA por Empresa em 2024',
        xlabel='Empresa',
        ylabel='Dívida Líquida / EBITDA (x)',
        color_fn=color_fn,
        threshold_lines=[
            {'y': 1, 'color': 'red', 'linestyle': '--', 'alpha': 0.6},
            {'y': 4, 'color': 'red', 'linestyle': '--', 'alpha': 0.6}
        ]
    )


def generate_rentability_per_ton() -> None:
    """Generate rentability per ton table and figure."""
    df_2025 = calculate_rentability_per_ton(year='2025')
    df_2024 = calculate_rentability_per_ton(year='2024')
    
    # Table (both years)
    tbl = df_2025.join(df_2024, on='Empresa', how='full', suffix='_2024')
    tbl = tbl.with_columns(pl.col('Empresa').fill_null(pl.col('Empresa_2024')))
    assert tbl['Empresa'].is_not_null().all(), "Null Empresa after join in generate_rentability_per_ton"
    tbl = tbl.rename({'Lucro_por_Ton': '2025'})
    tbl = tbl.select([
        pl.col('Empresa'),
        pl.col('2025'),
        pl.col('Lucro_por_Ton_2024').alias('2024')
    ]).sort('2025', descending=True)
    write_table(
        'rentability_per_ton',
        tbl,
        headers=['Empresa', '2025', '2024'],
        column_specs=[
            {'col': 'Empresa', 'title_case': True},
            {'col': '2025', 'decimals': 1},
            {'col': '2024', 'decimals': 1}
        ],
        col_align='1,1,1'
    )
    
    # Figure
    def color_fn(rent):
        if rent < 0:
            return 'red'
        elif rent <= 5:
            return 'green'
        else:
            return 'orange'
    
    write_bar_plot_2years(
        'rentability_per_ton',
        df_2025, df_2024,
        x_col='Empresa',
        y_col='Lucro_por_Ton',
        title_latest='Rentabilidade por Tonelada de Resíduo em 2025',
        title_prior='Rentabilidade por Tonelada de Resíduo em 2024',
        xlabel='Empresa',
        ylabel='Rentabilidade por Tonelada (€/t)',
        color_fn=color_fn,
        threshold_lines=[
            {'y': 0, 'color': 'black', 'linestyle': '-', 'alpha': 0.8},
            {'y': 5, 'color': 'orange', 'linestyle': '--', 'alpha': 0.5}
        ]
    )


def _scatter_color(roe: float, debt_ebitda: float) -> str:
    roe_good = 0 <= roe < 10
    debt_good = 1 <= debt_ebitda <= 4
    if roe_good and debt_good:
        return 'green'
    elif roe_good or debt_good:
        return 'orange'
    else:
        return 'red'


def generate_dividend_per_tariff() -> None:
    """Generate dividend as % of municipality tariff table."""
    df_2025 = calculate_dividend_per_tariff(year='2025')
    df_2024 = calculate_dividend_per_tariff(year='2024')

    col_metric = 'Dividendos / Tarifa (%)'
    tbl = df_2025.join(df_2024, on='Empresa', how='full', suffix='_2024')
    tbl = tbl.with_columns(pl.col('Empresa').fill_null(pl.col('Empresa_2024')))
    tbl = tbl.rename({col_metric: '2025'})
    tbl = tbl.select([
        pl.col('Empresa'),
        pl.col('2025'),
        pl.col(f'{col_metric}_2024').alias('2024')
    ]).sort('2025', descending=True)
    write_table(
        'dividend_per_tariff',
        tbl,
        headers=['Empresa', '2025', '2024'],
        column_specs=[
            {'col': 'Empresa', 'title_case': True},
            {'col': '2025', 'decimals': 1},
            {'col': '2024', 'decimals': 1}
        ],
        col_align='1,1,1'
    )


def generate_roe_vs_debt_scatter() -> None:
    """Generate scatter plot of ROE vs Net Debt/EBITDA with 2-year arrows."""
    df_2024 = calculate_roe_vs_debt(year='2024')
    df_2025 = calculate_roe_vs_debt(year='2025')
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Merge on company name for common companies
    merged = df_2024.join(df_2025, on='Empresa', suffix='_2025')
    
    # Plot arrows and points for common companies
    for row in merged.iter_rows(named=True):
        x1, y1 = row['Debt_EBITDA'], row['ROE']
        x2, y2 = row['Debt_EBITDA_2025'], row['ROE_2025']
        c1 = _scatter_color(y1, x1)
        c2 = _scatter_color(y2, x2)
        
        # 2024 as square, 2025 as circle
        ax.scatter(x1, y1, marker='s', s=120, c=c1, alpha=0.6, edgecolors='black', zorder=5)
        ax.scatter(x2, y2, marker='o', s=120, c=c2, alpha=0.6, edgecolors='black', zorder=5)
        
        # Arrow from 2024 to 2025
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', color='gray', lw=1.2, alpha=0.7),
                    zorder=4)
        
        # Label at 2025 position
        ax.annotate(row['Empresa'].title(), (x2, y2),
                   xytext=(5, 5), textcoords='offset points',
                   fontsize=8, alpha=0.8)
    
    # Companies only in 2025 (no arrow, just circle)
    only_2025 = df_2025.join(df_2024, on='Empresa', how='anti')
    for row in only_2025.iter_rows(named=True):
        c = _scatter_color(row['ROE'], row['Debt_EBITDA'])
        ax.scatter(row['Debt_EBITDA'], row['ROE'], marker='o', s=120, c=c, alpha=0.6, edgecolors='black', zorder=5)
        ax.annotate(row['Empresa'].title(), (row['Debt_EBITDA'], row['ROE']),
                   xytext=(5, 5), textcoords='offset points',
                   fontsize=8, alpha=0.8)
    
    ax.set_xlabel('Dívida Líquida / EBITDA (x)', fontsize=12)
    ax.set_ylabel('ROE (%)', fontsize=12)
    ax.set_title('ROE vs Dívida Líquida/EBITDA (2024 - 2025)', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Background bands (consistent with ROE and Net Debt/EBITDA bar plot thresholds)
    x_min, x_max = ax.get_xlim()
    y_min, y_max = ax.get_ylim()
    
    # Green center: ROE [0, 10], Debt [1, 4]
    ax.add_patch(Rectangle((1, 0), 3, 10, facecolor='green', alpha=0.12, zorder=0))
    
    # Orange arms: one metric good, the other bad
    ax.add_patch(Rectangle((1, 10), 3, y_max - 10, facecolor='orange', alpha=0.12, zorder=0))   # top
    ax.add_patch(Rectangle((1, y_min), 3, -y_min, facecolor='orange', alpha=0.12, zorder=0))     # bottom
    ax.add_patch(Rectangle((x_min, 0), 1 - x_min, 10, facecolor='orange', alpha=0.12, zorder=0)) # left
    ax.add_patch(Rectangle((4, 0), x_max - 4, 10, facecolor='orange', alpha=0.12, zorder=0))     # right
    
    # Red corners: both metrics bad
    ax.add_patch(Rectangle((x_min, 10), 1 - x_min, y_max - 10, facecolor='red', alpha=0.12, zorder=0))
    ax.add_patch(Rectangle((4, 10), x_max - 4, y_max - 10, facecolor='red', alpha=0.12, zorder=0))
    ax.add_patch(Rectangle((x_min, y_min), 1 - x_min, -y_min, facecolor='red', alpha=0.12, zorder=0))
    ax.add_patch(Rectangle((4, y_min), x_max - 4, -y_min, facecolor='red', alpha=0.12, zorder=0))
    
    # Reference lines
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8, alpha=0.8)
    ax.axvline(x=0, color='black', linestyle='-', linewidth=0.8, alpha=0.8)
    
    # Legend for marker shapes
    legend_elements = [
        Line2D([0], [0], marker='s', color='w', markerfacecolor='gray', markersize=8, label='2024'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='gray', markersize=8, label='2025'),
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=10)
    
    plt.tight_layout()
    
    output_path = FIGURES_DIR / 'roe_vs_debt.svg'
    fig.savefig(output_path, format='svg', bbox_inches='tight')
    plt.close(fig)
    print(f"✓ Figure: {output_path}")


def _fmt_link(link: str) -> str:
    if not link or link == '':
        return 'N/D'
    return f'link:{link}[PDF]'


def generate_referencias() -> None:
    """Generate references table from fontes.csv (no figure)."""
    df_2025 = load_fontes(year='2025')
    df_2024 = load_fontes(year='2024')
    
    tbl = df_2025.join(df_2024, on='Empresa', how='full', suffix='_2024')
    tbl = tbl.with_columns(pl.col('Empresa').fill_null(pl.col('Empresa_2024')))
    assert tbl['Empresa'].is_not_null().all(), "Null Empresa after join in generate_referencias"
    tbl = tbl.select([
        pl.col('Empresa'),
        pl.col('Link Relatório & Contas').alias('Link_2025'),
        pl.col('Link Relatório & Contas_2024').alias('Link_2024')
    ]).sort('Empresa')
    
    output = []
    output.append('[cols="1,1,1"]')
    output.append('|===')
    output.append('|Sistema |2025 |2024')
    output.append('')
    
    for row in tbl.iter_rows(named=True):
        empresa = row['Empresa']
        link_2025 = _fmt_link(row['Link_2025'])
        link_2024 = _fmt_link(row['Link_2024'])
        output.append(f'|{empresa} |{link_2025} |{link_2024}')
    
    output.append('|===')
    
    # Write to file
    filepath = TABLES_DIR / 'referencias.adoc'
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))
    print(f"✓ Table: {filepath}")


def generate_coverage() -> None:
    """Generate coverage attributes file with computed totals."""
    coverage = calculate_total_coverage()

    pop_millions = coverage['population'] / 1_000_000
    pop_text = f"{pop_millions:.1f}".replace('.', ',')
    muni = coverage['municipalities']
    systems = coverage['systems']
    pct = coverage['pct_continental']

    output = [
        f":total_systems: {systems}",
        f":total_population_text: {pop_text} milhões de habitantes",
        f":total_municipalities: {muni}",
        f":coverage_pct: {pct}",
    ]

    filepath = TABLES_DIR / 'coverage-attributes.adoc'
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output) + '\n')
    print(f"✓ Coverage: {filepath}")


# ============================================================================
# MAIN
# ============================================================================

def main() -> None:
    """Generate all tables and figures."""
    print("Generating tables and figures...\n")
    
    generate_coverage()
    generate_sistemas_analisados()
    generate_ebitda_margins()
    generate_roe()
    generate_net_debt_ebitda()
    generate_rentability_per_ton()
    generate_dividend_per_tariff()
    generate_roe_vs_debt_scatter()
    generate_referencias()
    
    print("\n✓ All tables and figures generated successfully!")


if __name__ == '__main__':
    main()
