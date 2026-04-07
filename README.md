# Análise Comparativa do Sector de Gestão de Resíduos Urbanos em Portugal

[![Deploy to GitHub Pages](https://github.com/jorgecarleitao/relatorio-residuos-urbanos-portugal/actions/workflows/deploy-pages.yml/badge.svg?branch=main)](https://github.com/jorgecarleitao/relatorio-residuos-urbanos-portugal/actions/workflows/deploy-pages.yml)

## 📄 Relatório

**Aceder ao relatório:** [https://jorgecarleitao.github.io/relatorio-residuos-urbanos-portugal/](https://jorgecarleitao.github.io/relatorio-residuos-urbanos-portugal/)

- **Versão latest (desenvolvimento):** [/main/](https://jorgecarleitao.github.io/relatorio-residuos-urbanos-portugal/main/)
- **Versões estáveis:** Ver índice acima ou [Releases](https://github.com/jorgecarleitao/relatorio-residuos-urbanos-portugal/releases)
- **Descarregar PDF:** [Releases](https://github.com/jorgecarleitao/relatorio-residuos-urbanos-portugal/releases)

## 📊 Sobre

Análise comparativa baseada em dados públicos dos relatórios e contas de 2024 de 10 sistemas multimunicipais de gestão de resíduos urbanos em Portugal.

**Principais conclusões:**

- Rentabilidade sobre capital próprio (ROE) varia de -22% (ALGAR) a +33% (VALORSUL/VALORLIS)
- Infraestrutura de valorização energética é o principal determinante da rentabilidade
- Sistemas com incineração moderna apresentam rentabilidades 3-4x superiores ao esperado para utilities reguladas
- Heterogeneidade de 55 pontos percentuais indica falha na função equalizadora da regulação

## 🛠️ Construir Localmente

### Requisitos

- Python 3.11+
- Ruby 3.2+ (para AsciiDoctor)
- Make

### Instalação

```bash
# Instalar dependências Python
python -m venv venv
source venv/bin/activate
pip install -r src/requirements.txt

# Instalar AsciiDoctor
gem install asciidoctor
```

### Gerar Relatório

```bash
# Gerar tabelas a partir dos dados CSV
make tables

# Gerar figuras (gráficos SVG)
make figures

# Gerar HTML
make html

# Gerar PDF (opcional)
make pdf
```

O relatório HTML será gerado em `build/index.html`.

## 📁 Estrutura do Projeto

```
.
├── data/2024/
│   ├── raw/          # PDFs e OCR dos relatórios originais
│   └── extracted/    # Dados extraídos em CSV
├── src/
│   ├── tables.py     # Geração de tabelas AsciiDoc
│   └── figures.py    # Geração de gráficos SVG
├── build/            # Saída (HTML, tabelas, figuras)
└── index.adoc        # Documento principal
```

## 📖 Dados

Todas as análises baseiam-se exclusivamente em dados públicos oficiais:

- **Fonte primária:** Relatórios e Contas Anuais de 2024 das empresas multimunicipais
- **Sistemas analisados:** VALORSUL, ALGAR, ERSUC, RESINORTE, AMARSUL, SULDOURO, VALORLIS, RESIESTRELA, RESULIMA, VALORMINHO

## 📝 Licença

Dados: públicos (Relatórios e Contas oficiais)  
Código de análise: MIT

## ✍️ Autor

Jorge C. Leitão
