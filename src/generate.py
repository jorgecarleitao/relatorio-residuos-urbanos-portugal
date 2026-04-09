#!/usr/bin/env python3
"""
Generate both tables and figures from the same data.
Ensures perfect consistency between visual and text representations.
"""

from pathlib import Path
from typing import Dict, List, Optional, Union
import polars as pl
import matplotlib.pyplot as plt
from calculations import (
    calculate_sistemas_analisados,
    calculate_ebitda_margins,
    calculate_roe,
    calculate_net_debt_ebitda,
    calculate_rentability_per_ton,
    load_fontes
)

# Configure matplotlib for high-quality output
plt.rcParams['svg.fonttype'] = 'none'  # Preserve text as text, not paths
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
        col_align: Column alignment spec (e.g., "1,>1,>1" or "1,1,1")
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
    
    if threshold_lines and any(line.get('label') for line in threshold_lines):
        ax.legend()
    
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    # Write to file
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
        headers=['Sistema', 'Região', 'Acionista Maioritário'],
        column_specs=[
            {'col': 'Empresa', 'title_case': True},
            {'col': 'Região'},
            {'col': 'Acionista'}
        ],
        col_align='1,1,2'
    )


def generate_ebitda_margins() -> None:
    """Generate EBITDA margins table and figure."""
    df = calculate_ebitda_margins()
    
    # Table
    write_table(
        'ebitda_margins',
        df,
        headers=['Empresa', 'Margem EBITDA (%)'],
        column_specs=[
            {'col': 'Empresa', 'title_case': True},
            {'col': 'Margem EBITDA (%)', 'decimals': 1}
        ],
        col_align='1,>1'
    )
    
    # Figure
    def color_fn(margin):
        return 'green' if margin >= 20 else 'red'
    
    write_bar_plot(
        'ebitda_margins',
        df,
        x_col='Empresa',
        y_col='Margem EBITDA (%)',
        title='Margem EBITDA por Empresa em 2024',
        xlabel='Empresa',
        ylabel='Margem EBITDA (%)',
        color_fn=color_fn,
        threshold_lines=[
            {'y': 20, 'color': 'green', 'linestyle': '--', 'alpha': 0.5, 'label': '20% (Bom)'}
        ]
    )


def generate_roe() -> None:
    """Generate ROE table and figure."""
    df = calculate_roe()
    
    # Table
    write_table(
        'roe',
        df,
        headers=['Empresa', 'ROE (%)'],
        column_specs=[
            {'col': 'Empresa', 'title_case': True},
            {'col': 'ROE', 'decimals': 1}
        ],
        col_align='1,>1'
    )
    
    # Figure
    def color_fn(roe):
        if roe < 0:
            return 'red'
        elif roe < 10:
            return 'green'
        else:
            return 'red'
    
    write_bar_plot(
        'roe',
        df,
        x_col='Empresa',
        y_col='ROE',
        title='Rentabilidade sobre Capital Próprio (ROE) em 2024',
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
    df = calculate_net_debt_ebitda()
    
    # Table
    write_table(
        'net_debt_ebitda',
        df,
        headers=['Empresa', 'Dívida Líquida / EBITDA (x)'],
        column_specs=[
            {'col': 'Empresa', 'title_case': True},
            {'col': 'Endividamento Líquido / EBITDA (x)', 'decimals': 2}
        ],
        col_align='1,>1'
    )
    
    # Figure
    def color_fn(ratio):
        if ratio < 1:
            return 'red'
        elif ratio <= 4:
            return 'green'
        else:
            return 'red'
    
    write_bar_plot(
        'net_debt_ebitda',
        df,
        x_col='Empresa',
        y_col='Endividamento Líquido / EBITDA (x)',
        title='Dívida Líquida / EBITDA por Empresa em 2024',
        xlabel='Empresa',
        ylabel='Dívida Líquida / EBITDA (x)',
        color_fn=color_fn,
        threshold_lines=[
            {'y': 1, 'color': 'red', 'linestyle': '--', 'alpha': 0.6, 'label': '1x'},
            {'y': 4, 'color': 'red', 'linestyle': '--', 'alpha': 0.6, 'label': '4x'}
        ]
    )


def generate_rentability_per_ton() -> None:
    """Generate rentability per ton table and figure."""
    df = calculate_rentability_per_ton()
    
    # Table
    write_table(
        'rentability_per_ton',
        df,
        headers=['Empresa', 'Rentabilidade por Tonelada (€/t)'],
        column_specs=[
            {'col': 'Empresa', 'title_case': True},
            {'col': 'Lucro_por_Ton', 'decimals': 1}
        ],
        col_align='1,>1'
    )
    
    # Figure
    def color_fn(rent):
        if rent < 0:
            return 'red'
        elif rent <= 5:
            return 'green'
        else:
            return 'orange'
    
    write_bar_plot(
        'rentability_per_ton',
        df,
        x_col='Empresa',
        y_col='Lucro_por_Ton',
        title='Rentabilidade por Tonelada de Resíduo em 2024',
        xlabel='Empresa',
        ylabel='Rentabilidade por Tonelada (€/t)',
        color_fn=color_fn,
        threshold_lines=[
            {'y': 0, 'color': 'black', 'linestyle': '-', 'alpha': 0.8},
            {'y': 5, 'color': 'orange', 'linestyle': '--', 'alpha': 0.5, 'label': '5 €/t (Rentabilidade Moderada)'}
        ]
    )


def generate_referencias() -> None:
    """Generate references table from fontes.csv (no figure)."""
    df = load_fontes()
    
    output = []
    output.append('[cols="1,1"]')
    output.append('|===')
    output.append('|Sistema |Relatório & Contas 2024')
    output.append('')
    
    for row in df.iter_rows(named=True):
        empresa = row['Empresa']
        link = row['Link Relatório & Contas 2024']
        # Format as AsciiDoc link: link:URL[text]
        link_formatted = f'link:{link}[PDF]'
        output.append(f'|{empresa} |{link_formatted}')
    
    output.append('|===')
    
    # Write to file
    filepath = TABLES_DIR / 'referencias.adoc'
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))
    print(f"✓ Table: {filepath}")


# ============================================================================
# MAIN
# ============================================================================

def main() -> None:
    """Generate all tables and figures."""
    print("Generating tables and figures...\n")
    
    generate_sistemas_analisados()
    generate_ebitda_margins()
    generate_roe()
    generate_net_debt_ebitda()
    generate_rentability_per_ton()
    generate_referencias()
    
    print("\n✓ All tables and figures generated successfully!")


if __name__ == '__main__':
    main()
