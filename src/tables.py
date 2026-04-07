#!/usr/bin/env python3
"""
Generate AsciiDoc tables from CSV data files.
"""

import csv
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Data directory path
DATA_DIR = Path('data/2024/extracted')


def read_csv(filepath: Path) -> List[Dict[str, str]]:
    """Read CSV file and return list of dictionaries."""
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


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
        return value


def generate_sistemas_analisados() -> str:
    """Generate 'Sistemas Analisados' table."""
    filepath = DATA_DIR / 'capital_social_2024.csv'
    data = read_csv(filepath)
    
    # Load regions mapping from CSV
    regions_path = DATA_DIR / 'empresa_regioes.csv'
    regions_data = read_csv(regions_path)
    regions = {r['Empresa']: r['Região'] for r in regions_data}
    
    output = []
    output.append('[cols="1,1,2"]')
    output.append('|===')
    output.append('|Sistema |Região |Acionista Maioritário')
    output.append('')
    
    # Sort by EGF percentage descending
    sorted_data = sorted([r for r in data if r['Empresa'] in regions],
                         key=lambda x: float(x['EGF % (acionista maioritário)']), 
                         reverse=True)
    
    for row in sorted_data:
        empresa = row['Empresa'].title()
        regiao = regions[row['Empresa']]
        egf_percent = row['EGF % (acionista maioritário)']
        output.append(f'|{empresa} |{regiao} |EGF ({egf_percent}%)')
    
    output.append('|===')
    return '\n'.join(output)


def generate_waste_collection_table() -> str:
    """Generate 'Indicadores de Escala e Operação' table."""
    filepath = DATA_DIR / 'receção_residuos_2024.csv'
    data = read_csv(filepath)
    
    # Filter valid rows and sort by population
    valid_data = [r for r in data if r['População Servida (hab)'] and r['População Servida (hab)'] != 'N/D']
    sorted_data = sorted(valid_data, 
                        key=lambda x: int(x['População Servida (hab)']), 
                        reverse=True)
    
    output = []
    output.append('[cols="1,1,1,1,1,1"]')
    output.append('|===')
    output.append('|Empresa |População (hab) |RU Total (ton) |Indiferenciados (ton) |Seletiva (ton) |Energia (GWh)')
    output.append('')
    
    for row in sorted_data:
        empresa = row['Empresa'].title()
        pop = format_number(row['População Servida (hab)'])
        total = format_number(row['Total RU Recebidos (ton)'])
        indif = format_number(row['Total RU Indiferenciados (ton)'])
        seletiva = format_number(row['Total Recolha Seletiva (ton)'])
        energia = format_number(row['Energia Vendida (GWh)'], decimals=1)
        
        output.append(f'|{empresa} |{pop} |{total} |{indif} |{seletiva} |{energia}')
    
    output.append('|===')
    return '\n'.join(output)


def generate_financial_performance_table() -> str:
    """Generate 'Desempenho Financeiro Comparativo' table."""
    filepath = DATA_DIR / 'indicadores_financeiros_2024.csv'
    data = read_csv(filepath)
    
    # Filter valid rows and sort by revenue
    valid_data = [r for r in data if r['Vendas e Serviços Prestados (€)'] and r['Vendas e Serviços Prestados (€)'] != 'N/D']
    sorted_data = sorted(valid_data, 
                        key=lambda x: float(x['Vendas e Serviços Prestados (€)']), 
                        reverse=True)
    
    output = []
    output.append('[cols="1,1,1,1,1,1,1"]')
    output.append('|===')
    output.append('|Empresa |Volume Negócios (M€) |EBITDA (M€) |Resultado Líquido (M€) |Margem EBITDA (%) |Margem Líquida (%) |Dív. Líq./EBITDA (x)')
    output.append('')
    
    for row in sorted_data:
        empresa = row['Empresa'].title()
        vn = format_number(float(row['Vendas e Serviços Prestados (€)']) / 1_000_000, decimals=1)
        ebitda = format_number(float(row['EBITDA (€)']) / 1_000_000, decimals=1)
        rl = format_number(float(row['Resultado Líquido (€)']) / 1_000_000, decimals=1)
        marg_ebitda = format_number(row['Margem EBITDA (%)'], decimals=1)
        marg_liq = format_number(row['Margem Líquida (%)'], decimals=1)
        divida = format_number(row['Endividamento Líquido / EBITDA (x)'], decimals=2)
        
        output.append(f'|{empresa} |{vn} |{ebitda} |{rl} |{marg_ebitda} |{marg_liq} |{divida}')
    
    output.append('|===')
    return '\n'.join(output)


def generate_rentability_per_ton_table() -> str:
    """Generate 'Rentabilidade por Tonelada' table."""
    waste_path = DATA_DIR / 'receção_residuos_2024.csv'
    finance_path = DATA_DIR / 'indicadores_financeiros_2024.csv'
    
    waste_data = {r['Empresa']: r for r in read_csv(waste_path)}
    finance_data = {r['Empresa']: r for r in read_csv(finance_path)}
    
    # Merge data and calculate per-ton metrics
    merged = []
    for empresa in waste_data:
        if empresa in finance_data and waste_data[empresa]['Total RU Recebidos (ton)'] != 'N/D':
            tons = float(waste_data[empresa]['Total RU Recebidos (ton)'])
            vn = float(finance_data[empresa]['Vendas e Serviços Prestados (€)'])
            ebitda = float(finance_data[empresa]['EBITDA (€)'])
            rl = float(finance_data[empresa]['Resultado Líquido (€)'])
            energia = waste_data[empresa]['Energia Vendida (GWh)']
            
            # Skip if N/D
            if energia == 'N/D':
                continue
                
            energia_kwh = float(energia) * 1_000_000 / tons
            
            merged.append({
                'Empresa': empresa,
                'Receita': vn / tons,
                'EBITDA': ebitda / tons,
                'Lucro': rl / tons,
                'Energia': energia_kwh
            })
    
    # Sort by profit per ton descending
    sorted_data = sorted(merged, key=lambda x: x['Lucro'], reverse=True)
    
    output = []
    output.append('[cols="1,1,1,1,1"]')
    output.append('|===')
    output.append('|Empresa |Receita (€/t) |EBITDA (€/t) |Lucro (€/t) |Energia (kWh/t)')
    output.append('')
    
    for row in sorted_data:
        empresa = row['Empresa'].title()
        receita = format_number(row['Receita'], decimals=1)
        ebitda = format_number(row['EBITDA'], decimals=1)
        lucro = format_number(row['Lucro'], decimals=1)
        energia = format_number(row['Energia'], decimals=0)
        
        output.append(f'|{empresa} |{receita} |{ebitda} |{lucro} |{energia}')
    
    output.append('|===')
    return '\n'.join(output)


def generate_capital_social_roe_table() -> str:
    """Generate 'Retorno sobre Capital Social' table."""
    capital_path = DATA_DIR / 'capital_social_2024.csv'
    finance_path = DATA_DIR / 'indicadores_financeiros_2024.csv'
    
    capital_data = {r['Empresa']: r for r in read_csv(capital_path)}
    finance_data = {r['Empresa']: r for r in read_csv(finance_path)}
    
    # Merge and calculate ROE
    merged = []
    for empresa in capital_data:
        if empresa in finance_data:
            cs = capital_data[empresa]['Capital Social (€)']
            rl = finance_data[empresa]['Resultado Líquido (€)']
            
            if cs == 'N/D' or rl == 'N/D':
                continue
            
            cs_val = float(cs) / 1_000_000
            rl_val = float(rl) / 1_000_000
            roe = (rl_val / cs_val) * 100 if cs_val > 0 else 0
            
            merged.append({
                'Empresa': empresa,
                'Capital': cs_val,
                'Lucro': rl_val,
                'ROE': roe
            })
    
    # Sort by ROE descending
    sorted_data = sorted(merged, key=lambda x: x['ROE'], reverse=True)
    
    output = []
    output.append('[cols="1,1,1,1"]')
    output.append('|===')
    output.append('|Empresa |Capital Social (M€) |Resultado Líquido (M€) |ROE sobre Capital (%)')
    output.append('')
    
    for row in sorted_data:
        empresa = row['Empresa'].title()
        capital = format_number(row['Capital'], decimals=1)
        lucro = format_number(row['Lucro'], decimals=2)
        roe = format_number(row['ROE'], decimals=0)
        
        output.append(f'|{empresa} |{capital} |{lucro} |{roe}%')
    
    output.append('|===')
    return '\n'.join(output)


def generate_algar_valorsul_comparison() -> str:
    """Generate ALGAR vs Valorsul comparison table."""
    waste_path = DATA_DIR / 'receção_residuos_2024.csv'
    finance_path = DATA_DIR / 'indicadores_financeiros_2024.csv'
    
    waste_data = {r['Empresa']: r for r in read_csv(waste_path)}
    finance_data = {r['Empresa']: r for r in read_csv(finance_path)}
    
    def get_values(empresa: str) -> Dict[str, str]:
        w = waste_data[empresa]
        f = finance_data[empresa]
        tons = float(w['Total RU Recebidos (ton)'])
        energia_gwh = float(w['Energia Vendida (GWh)'])
        
        return {
            'pop': format_number(w['População Servida (hab)']),
            'tons': format_number(w['Total RU Recebidos (ton)']),
            'energia_gwh': format_number(energia_gwh, decimals=1),
            'energia_kwh_t': format_number((energia_gwh * 1_000_000) / tons, decimals=0),
            'reciclaveis': format_number(float(w['Recicláveis Vendidos - Embalagem (ton)']) + 
                                        (float(w['Recicláveis Vendidos - Não Embalagem (ton)']) 
                                         if w['Recicláveis Vendidos - Não Embalagem (ton)'] != 'N/D' else 0)),
            'vn': format_number(float(f['Vendas e Serviços Prestados (€)']) / 1_000_000, decimals=1),
            'ebitda': format_number(float(f['EBITDA (€)']) / 1_000_000, decimals=1),
            'ebitda_pct': format_number(f['Margem EBITDA (%)'], decimals=1),
            'rl': format_number(float(f['Resultado Líquido (€)']) / 1_000_000, decimals=1),
            'rl_pct': format_number(f['Margem Líquida (%)'], decimals=1),
            'lucro_t': format_number(float(f['Resultado Líquido (€)']) / tons, decimals=1),
            'divida': format_number(f['Endividamento Líquido / EBITDA (x)'], decimals=2),
        }
    
    algar = get_values('ALGAR')
    valorsul = get_values('VALORSUL')
    
    output = []
    output.append('[cols="1h,1,1"]')
    output.append('|===')
    output.append('|Indicador |ALGAR (Algarve) |Valorsul (Lisboa)')
    output.append('')
    output.append(f'|População servida |{algar["pop"]} hab |{valorsul["pop"]} hab')
    output.append(f'|RU total |{algar["tons"]} t |{valorsul["tons"]} t')
    output.append(f'|Energia produzida |{algar["energia_gwh"]} GWh |{valorsul["energia_gwh"]} GWh')
    output.append(f'|Energia por tonelada |{algar["energia_kwh_t"]} kWh/t |{valorsul["energia_kwh_t"]} kWh/t')
    output.append(f'|Recicláveis vendidos |~{algar["reciclaveis"]} t |~{valorsul["reciclaveis"]} t')
    output.append(f'|Volume de negócios |{algar["vn"]} M€ |{valorsul["vn"]} M€')
    output.append(f'|EBITDA |{algar["ebitda"]} M€ ({algar["ebitda_pct"]}%) |{valorsul["ebitda"]} M€ ({valorsul["ebitda_pct"]}%)')
    output.append(f'|Resultado líquido |{algar["rl"]} M€ ({algar["rl_pct"]}%) |{valorsul["rl"]} M€ ({valorsul["rl_pct"]}%)')
    output.append(f'|Lucro por tonelada |{algar["lucro_t"]} €/t |+{valorsul["lucro_t"]} €/t')
    output.append(f'|Dívida Líq./EBITDA |{algar["divida"]}x |{valorsul["divida"]}x')
    output.append('|===')
    return '\n'.join(output)


def generate_rentability_distribution_table() -> str:
    """Generate rentability distribution summary table."""
    filepath = DATA_DIR / 'rentability_categories.csv'
    data = read_csv(filepath)
    
    output = []
    output.append('[cols="1,1"]')
    output.append('|===')
    output.append('|Situação |Sistemas')
    output.append('')
    
    for row in data:
        categoria = row['Categoria']
        descricao = row['Descrição']
        empresas = row['Empresas'].split(',')
        empresas_formatted = ', '.join([e.strip().title() for e in empresas])
        situacao = f"{categoria} ({descricao})" if descricao else categoria
        output.append(f'|{situacao} |{empresas_formatted}')
    
    output.append('|===')
    return '\n'.join(output)


def generate_valorsul_investment_table() -> str:
    """Generate Valorsul CAPEX vs profit table."""
    filepath = DATA_DIR / 'valorsul_investment_history.csv'
    data = read_csv(filepath)
    
    output = []
    output.append('[cols="1h,1,1,1"]')
    output.append('|===')
    output.append('|Ano |Investimento (M€) |Resultado Líquido (M€) |CAPEX/Lucro')
    output.append('')
    
    for row in data:
        ano = row['Ano']
        investimento = format_number(row['Investimento (M€)'], decimals=1)
        resultado = format_number(row['Resultado Líquido (M€)'], decimals=1)
        capex_lucro = format_number(row['CAPEX/Lucro'], decimals=1)
        output.append(f'|{ano} |{investimento} |{resultado} |{capex_lucro}x')
    
    output.append('|===')
    return '\n'.join(output)


def main() -> None:
    """Generate all tables and save to build/tables/ directory."""
    # Create output directory
    output_dir = Path('build/tables')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    tables = {
        'sistemas_analisados.adoc': generate_sistemas_analisados(),
        'waste_collection.adoc': generate_waste_collection_table(),
        'financial_performance.adoc': generate_financial_performance_table(),
        'rentability_per_ton.adoc': generate_rentability_per_ton_table(),
        'capital_social_roe.adoc': generate_capital_social_roe_table(),
        'algar_valorsul_comparison.adoc': generate_algar_valorsul_comparison(),
        'rentability_distribution.adoc': generate_rentability_distribution_table(),
        'valorsul_investment.adoc': generate_valorsul_investment_table(),
    }
    
    for filename, content in tables.items():
        filepath = output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Generated: {filepath}")
    
    print(f"\nAll {len(tables)} tables generated successfully!")


if __name__ == '__main__':
    main()
