# Sistema de Análise de Irrigação

Projeto de Ciência de Dados aplicado à irrigação: análise exploratória, visualização,
correlação e regressão linear para prever a **área irrigada por ângulo** a partir das
**horas de irrigação**.

O projeto foi construído para cumprir as **13 tarefas da checklist**.

**Repositório:** <https://github.com/Dannilool/analise-irrigacao>

---

## Resultado em uma linha

A base é **perfeitamente linear**: `Área irrigada por ângulo = 66,6667 × Horas de irrigação`.
O modelo tem **R² = 1,000000**, erros praticamente nulos e prevê **1.000,00** para
**15 horas** de irrigação.

> **Importante:** como a base é determinística (sem ruído), o ajuste perfeito não deve ser
> interpretado como garantia de desempenho em campo. O relatório discute essa limitação.

---

## Dashboard e API

O projeto também pode ser explorado como uma aplicação web:

- **Dashboard:** <http://127.0.0.1:8000>
- **Swagger UI:** <http://127.0.0.1:8000/docs>
- **ReDoc:** <http://127.0.0.1:8000/redoc>
- **Relatório HTML:** <http://127.0.0.1:8000/relatorio>
- **Health check:** <http://127.0.0.1:8000/health>

O dashboard permite simular a área irrigada em tempo real, consultar as estatísticas,
as métricas do modelo, os nove gráficos e o checklist das 13 tarefas.

### Endpoints principais

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/` | Dashboard web |
| `GET` | `/relatorio` | Relatório completo em HTML |
| `GET` | `/api/resumo` | Resumo do dataset e do modelo |
| `GET` | `/api/estatisticas` | Estatísticas descritivas |
| `GET` | `/api/modelo` | Coeficientes e métricas |
| `GET` | `/api/checklist` | Itens da checklist |
| `GET` | `/api/figuras` | Lista das figuras |
| `GET` | `/api/prever/15` | Previsão via URL |
| `POST` | `/api/prever` | Previsão via JSON: `{"horas": 15}` |
| `GET` | `/health` | Status do sistema |

---

## Estrutura do projeto

```
Projeto/
├── Arquivos/
│   └── dados_de_irrigacao.csv          # base original (299 registros)
├── analise_irrigacao.py                # análise completa (13 etapas)
├── analise_irrigacao.ipynb             # mesma análise em notebook
├── app.py                              # API FastAPI e dashboard
├── templates/
│   └── index.html                      # interface do dashboard
├── static/
│   ├── style.css                       # estilos da interface
│   └── app.js                          # previsão e interações
├── executar_analise.bat                # atalho da análise no Windows
├── iniciar_api.bat                     # atalho da API no Windows
├── requirements.txt
├── README.md
└── resultados/
    ├── relatorio.md                    # relatório com tabelas, figuras e conclusões
    ├── relatorio.html                  # mesma versão para navegador/impressão em PDF
    ├── relatorio.pdf                   # versão pronta para entrega/impressão
    ├── figuras/                        # 9 gráficos em PNG
    │   ├── 01_dispersao_horas_area.png
    │   ├── 02_dispersao_horas_area_angulo.png
    │   ├── 03_dispersao_area_area_angulo.png
    │   ├── 04_mapa_calor_correlacao.png
    │   ├── 05_reais_vs_preditos.png
    │   ├── 06_residuos_vs_preditos.png
    │   ├── 07_histograma_residuos.png
    │   ├── 08_qq_plot_residuos.png
    │   └── 09_predicoes.png
    └── tabelas/
        ├── qualidade_dados.csv
        ├── estatisticas_descritivas.csv
        ├── correlacao_pearson.csv
        ├── correlacao_spearman.csv
        ├── divisao_treino_teste.csv
        ├── metricas_desempenho.csv
        ├── residuos_teste.csv
        ├── testes_normalidade.csv
        ├── previsoes.csv
        └── resumo_modelo.txt
```

---

## Como executar

### 1. Instalar as dependências

No terminal, dentro da pasta `Projeto`:

```powershell
python -m pip install -r requirements.txt
```

### 2. Rodar o dashboard FastAPI

```powershell
python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

Ou dê um duplo clique em `iniciar_api.bat`. Depois abra
<http://127.0.0.1:8000> no navegador.

A documentação interativa fica em <http://127.0.0.1:8000/docs>.
Para encerrar o servidor, use `Ctrl+C`.

### 3. Executar a análise (script)

```powershell
python analise_irrigacao.py
```

Ou dê um duplo clique em `executar_analise.bat`.

### 4. Abrir o notebook

Abra `analise_irrigacao.ipynb` no VS Code, JupyterLab ou Google Colab e execute todas as
células. O notebook deve ser aberto a partir da pasta `Projeto` para localizar a base
`Arquivos/dados_de_irrigacao.csv`.

> **Windows:** o script força saída UTF-8. Se os acentos aparecerem estranhos no terminal,
> execute `chcp 65001` antes ou use o `executar_analise.bat`.

### Versão em PDF

O arquivo `resultados/relatorio.pdf` já está pronto para entrega/impressão.
Para atualizá-lo depois de uma nova execução, abra `resultados/relatorio.html` no Chrome ou
Edge e use **Imprimir → Salvar como PDF**.

---

## Checklist — onde cada tarefa foi cumprida

| # | Tarefa | Script | Relatório |
|---|--------|--------|-----------|
| 1 | Carregar os dados do CSV 
| 2 | Visualizar estrutura e variáveis 
| 3 | Estatísticas descritivas 
| 4 | Gráficos de dispersão 
| 5 | Correlação entre variáveis 
| 6 | Divisão treino/teste
| 7 | Treinar regressão linear (X = horas, Y = área por ângulo) 
| 8 | Imprimir a equação da reta 
| 9 | MSE e MAE 
| 10 | Gráfico de reais × preditos 
| 11 | Cálculo e análise dos resíduos 
| 12 | Normalidade dos resíduos (testes e Q-Q) 
| 13 | Predição para 15 horas 

O mapeamento também aparece no fim de `resultados/relatorio.md`.

---

## Principais resultados

| Item | Valor |
|------|-------|
| Registros | 299 |
| Variáveis | 3 |
| Dados ausentes / duplicados / negativos | 0 / 0 / 0 |
| Correlação (horas × área por ângulo) | 1,0000 |
| Equação | `Y = 66,6667·X + 1,818989 × 10⁻¹²` |
| R² (teste) | 1,000000 |
| MSE | 6,8942 × 10⁻²⁴ |
| MAE | 2,4310 × 10⁻¹² |
| Previsão para 15 h | **1.000,00** |

### Sobre a normalidade dos resíduos

Os resíduos estão na ordem de **10⁻¹²**, ou seja, são ruído de ponto flutuante. Nessa escala,
os testes de normalidade perdem sentido prático:

- **Shapiro-Wilk:** p ≈ 0,000002 → rejeita a normalidade;
- **D'Agostino-Pearson:** p ≈ 0,1866 → não rejeita;
- **Jarque-Bera:** p ≈ 0,2519 → não rejeita.

O conflito é consequência da **quantização numérica**, não de uma distribuição real. O
relatório explica por que não se deve concluir "resíduos normais" ou "não normais" a partir
dessa base.

---

## Limitações e próximos passos

1. A base é **determinística/simulada**: `área = 100 × horas` e `área por ângulo = (2/3) × área`.
2. Um R² = 1 em dados sem ruído **não garante** generalização para o campo.
3. Para evoluir o projeto:
   - coletar dados reais com variabilidade (clima, solo, umidade, vazão, eficiência);
   - incluir novas variáveis explicativas;
   - usar validação cruzada e teste independente;
   - avaliar resíduos em escala real e testar robustez a outliers;
   - comparar com modelos não lineares e séries temporais, se fizer sentido.

---

## Tecnologias

- Python 3.10+
- pandas, NumPy
- Matplotlib
- SciPy (testes estatísticos)
- scikit-learn (regressão linear e métricas)
- tabulate (tabelas Markdown)
- Markdown (versão HTML do relatório)
- FastAPI + Uvicorn (API e dashboard)
- Jinja2 (templates HTML)
- HTML, CSS e JavaScript (interface)
