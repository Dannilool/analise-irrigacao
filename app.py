"""
API FastAPI do Sistema de Análise de Irrigação.

Execução local:
    python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload

Documentação interativa:
    http://127.0.0.1:8000/docs

Dashboard:
    http://127.0.0.1:8000/
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sklearn.linear_model import LinearRegression
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import train_test_split

# =============================================================================
# CAMINHOS E CONFIGURAÇÕES
# =============================================================================
BASE_DIR = Path(__file__).resolve().parent
ARQUIVO_DADOS = BASE_DIR / "Arquivos" / "dados_de_irrigacao.csv"
PASTA_RESULTADOS = BASE_DIR / "resultados"
PASTA_FIGURAS = PASTA_RESULTADOS / "figuras"
PASTA_TEMPLATES = BASE_DIR / "templates"
PASTA_STATIC = BASE_DIR / "static"
GITHUB_URL = os.getenv(
    "GITHUB_URL", "https://github.com/Dannilool/analise-irrigacao"
).strip()

NOMES = {
    "horas_irrigacao": "Horas de irrigação",
    "area_irrigada": "Área irrigada",
    "area_irrigada_angulo": "Área irrigada por ângulo",
}

FIGURAS = [
    {
        "arquivo": "01_dispersao_horas_area.png",
        "titulo": "Horas de irrigação × Área irrigada",
        "grupo": "Dispersão",
        "descricao": "Relação linear entre as horas de irrigação e a área total.",
    },
    {
        "arquivo": "02_dispersao_horas_area_angulo.png",
        "titulo": "Horas de irrigação × Área por ângulo",
        "grupo": "Dispersão",
        "descricao": "Variável independente e variável dependente do modelo.",
    },
    {
        "arquivo": "03_dispersao_area_area_angulo.png",
        "titulo": "Área irrigada × Área por ângulo",
        "grupo": "Dispersão",
        "descricao": "As duas medidas de área crescem de forma proporcional.",
    },
    {
        "arquivo": "04_mapa_calor_correlacao.png",
        "titulo": "Mapa de calor das correlações",
        "grupo": "Correlação",
        "descricao": "Coeficientes de Pearson entre todas as variáveis.",
    },
    {
        "arquivo": "05_reais_vs_preditos.png",
        "titulo": "Valores reais × preditos",
        "grupo": "Avaliação",
        "descricao": "Comparação no conjunto de teste; pontos sobre a reta ideal.",
    },
    {
        "arquivo": "06_residuos_vs_preditos.png",
        "titulo": "Resíduos × valores preditos",
        "grupo": "Resíduos",
        "descricao": "Resíduos na ordem de 10⁻¹², sem padrão sistemático.",
    },
    {
        "arquivo": "07_histograma_residuos.png",
        "titulo": "Distribuição dos resíduos",
        "grupo": "Resíduos",
        "descricao": "Histograma dos resíduos do conjunto de teste.",
    },
    {
        "arquivo": "08_qq_plot_residuos.png",
        "titulo": "Gráfico Q-Q dos resíduos",
        "grupo": "Normalidade",
        "descricao": "Comparação dos quantis dos resíduos com a normal teórica.",
    },
    {
        "arquivo": "09_predicoes.png",
        "titulo": "Previsões do modelo",
        "grupo": "Predição",
        "descricao": "Previsões para 10, 15, 20, 24 e 48 horas de irrigação.",
    },
]

CHECKLIST = [
    {"numero": 1, "tarefa": "Carregar os dados de irrigação a partir de um CSV", "onde": "Script §1 · Relatório §1"},
    {"numero": 2, "tarefa": "Visualizar os dados e as variáveis disponíveis", "onde": "Script §1 e §3 · Relatório §1 e §3"},
    {"numero": 3, "tarefa": "Calcular as estatísticas descritivas", "onde": "Script §2 · Relatório §2"},
    {"numero": 4, "tarefa": "Criar gráficos de dispersão", "onde": "Script §3 · Relatório §3"},
    {"numero": 5, "tarefa": "Analisar a correlação entre as variáveis", "onde": "Script §4 · Relatório §4"},
    {"numero": 6, "tarefa": "Dividir os dados em conjuntos de treino e teste", "onde": "Script §5 · Relatório §5"},
    {"numero": 7, "tarefa": "Treinar a regressão linear (X = horas, Y = área por ângulo)", "onde": "Script §6 · Relatório §5"},
    {"numero": 8, "tarefa": "Imprimir a equação da reta obtida", "onde": "Script §6 · Relatório §5"},
    {"numero": 9, "tarefa": "Avaliar a precisão com MSE e MAE", "onde": "Script §7 · Relatório §6"},
    {"numero": 10, "tarefa": "Visualizar resultados reais e preditos em um gráfico", "onde": "Script §8 · Relatório §6"},
    {"numero": 11, "tarefa": "Calcular e analisar os resíduos do modelo", "onde": "Script §9 · Relatório §7"},
    {"numero": 12, "tarefa": "Verificar a normalidade dos resíduos", "onde": "Script §10 · Relatório §8"},
    {"numero": 13, "tarefa": "Fazer predições (exemplo: 15 horas de irrigação)", "onde": "Script §11 · Relatório §9"},
]


# =============================================================================
# FORMATAÇÃO
# =============================================================================
def fmt_numero(valor, casas: int = 4) -> str:
    """Formata números no padrão brasileiro, com notação científica quando útil."""
    if valor is None:
        return "—"
    if isinstance(valor, (float, np.floating)) and (math.isnan(valor) or math.isinf(valor)):
        return "—"
    if isinstance(valor, (int, np.integer)):
        return f"{int(valor):,}".replace(",", ".")

    valor = float(valor)
    if valor != 0 and (abs(valor) < 10 ** (-casas) or abs(valor) >= 1e6):
        texto = f"{valor:.{casas}e}"
        mantissa, expoente = texto.split("e")
        sobrescritos = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")
        return f"{mantissa.replace('.', ',')} × 10{str(int(expoente)).translate(sobrescritos)}"

    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_p(p: float) -> str:
    if p is None or (isinstance(p, float) and math.isnan(p)):
        return "—"
    if p < 0.001:
        return "< 0,001"
    return f"= {fmt_numero(p, 4)}"


# =============================================================================
# DADOS E MODELO
# =============================================================================
def carregar_dados() -> pd.DataFrame:
    if not ARQUIVO_DADOS.exists():
        raise RuntimeError(f"Arquivo de dados não encontrado: {ARQUIVO_DADOS}")

    df = pd.read_csv(ARQUIVO_DADOS, encoding="utf-8-sig")
    if df.shape[1] != 3:
        raise ValueError(
            f"Esperadas 3 colunas, mas o arquivo possui {df.shape[1]}: {list(df.columns)}"
        )
    df.columns = ["horas_irrigacao", "area_irrigada", "area_irrigada_angulo"]
    return df


def resumo_dataset(df: pd.DataFrame) -> dict:
    return {
        "registros": int(len(df)),
        "variaveis": int(df.shape[1]),
        "ausentes": int(df.isna().sum().sum()),
        "duplicadas": int(df.duplicated().sum()),
        "negativos": int((df < 0).sum().sum()),
        "correlacao": float(df["horas_irrigacao"].corr(df["area_irrigada_angulo"])),
        "horas_min": float(df["horas_irrigacao"].min()),
        "horas_max": float(df["horas_irrigacao"].max()),
    }


def calcular_estatisticas(df: pd.DataFrame) -> list[dict]:
    linhas = []
    for coluna, nome in NOMES.items():
        serie = df[coluna]
        linhas.append(
            {
                "variavel": nome,
                "n": int(serie.count()),
                "media": float(serie.mean()),
                "desvio_padrao": float(serie.std()),
                "minimo": float(serie.min()),
                "q1": float(serie.quantile(0.25)),
                "mediana": float(serie.median()),
                "q3": float(serie.quantile(0.75)),
                "maximo": float(serie.max()),
                "cv": float(serie.std() / serie.mean() * 100),
            }
        )
    return linhas


@dataclass
class Estado:
    df: pd.DataFrame
    resumo: dict
    estatisticas: list[dict]
    modelo_angulo: LinearRegression
    modelo_area: LinearRegression
    coef_angulo: float
    intercepto_angulo: float
    coef_area: float
    intercepto_area: float
    equacao: str
    metricas: dict


def criar_estado() -> Estado:
    df = carregar_dados()
    resumo = resumo_dataset(df)
    estatisticas = calcular_estatisticas(df)

    X = df[["horas_irrigacao"]]
    y_angulo = df["area_irrigada_angulo"]
    y_area = df["area_irrigada"]

    # Métricas de generalização: treino/teste com a mesma semente da análise.
    X_treino, X_teste, y_treino, y_teste = train_test_split(
        X, y_angulo, test_size=0.20, random_state=42, shuffle=True
    )
    modelo_avaliacao = LinearRegression().fit(X_treino, y_treino)
    y_pred = modelo_avaliacao.predict(X_teste)

    mse = float(mean_squared_error(y_teste, y_pred))
    mae = float(mean_absolute_error(y_teste, y_pred))
    rmse = float(np.sqrt(mse))
    r2 = float(r2_score(y_teste, y_pred))
    mape = float(mean_absolute_percentage_error(y_teste, y_pred) * 100)
    erro_maximo = float(np.max(np.abs(y_teste.to_numpy() - y_pred)))

    metricas = {
        "mse": mse,
        "mae": mae,
        "rmse": rmse,
        "r2": r2,
        "mape": mape,
        "erro_maximo": erro_maximo,
        "n_treino": int(len(X_treino)),
        "n_teste": int(len(X_teste)),
        "semente": 42,
    }

    # Modelo de produção: treinado em todos os registros disponíveis.
    modelo_angulo = LinearRegression().fit(X, y_angulo)
    modelo_area = LinearRegression().fit(X, y_area)

    coef_angulo = float(modelo_angulo.coef_[0])
    intercepto_angulo = float(modelo_angulo.intercept_)
    coef_area = float(modelo_area.coef_[0])
    intercepto_area = float(modelo_area.intercept_)

    equacao = (
        f"Área irrigada por ângulo = {fmt_numero(coef_angulo, 4)} × "
        f"Horas de irrigação + ({fmt_numero(intercepto_angulo, 6)})"
    )

    return Estado(
        df=df,
        resumo=resumo,
        estatisticas=estatisticas,
        modelo_angulo=modelo_angulo,
        modelo_area=modelo_area,
        coef_angulo=coef_angulo,
        intercepto_angulo=intercepto_angulo,
        coef_area=coef_area,
        intercepto_area=intercepto_area,
        equacao=equacao,
        metricas=metricas,
    )


ESTADO = criar_estado()


# =============================================================================
# APLICAÇÃO
# =============================================================================
app = FastAPI(
    title="API do Sistema de Análise de Irrigação",
    description=(
        "API para consultar os dados de irrigação, as métricas do modelo de "
        "regressão linear e simular a área irrigada a partir das horas de irrigação."
    ),
    version="1.0.0",
    contact={
        "name": "Projeto de Ciência de Dados — Irrigação",
        "url": GITHUB_URL,
    },
    openapi_tags=[
        {"name": "Dashboard", "description": "Interface web e relatório."},
        {"name": "Dados", "description": "Resumo, estatísticas e qualidade da base."},
        {"name": "Modelo", "description": "Equação, coeficientes e métricas."},
        {"name": "Predição", "description": "Simulação de área irrigada."},
        {"name": "Sistema", "description": "Saúde e informações técnicas."},
    ],
)

app.mount("/static", StaticFiles(directory=PASTA_STATIC), name="static")
app.mount(
    "/figuras",
    StaticFiles(directory=PASTA_FIGURAS, check_dir=False),
    name="figuras",
)

templates = Jinja2Templates(directory=str(PASTA_TEMPLATES))
templates.env.filters["numero"] = fmt_numero
templates.env.filters["pvalor"] = fmt_p


def prever(horas: float) -> dict:
    entrada = pd.DataFrame({"horas_irrigacao": [horas]})
    area_angulo = round(float(ESTADO.modelo_angulo.predict(entrada)[0]), 4)
    area_total = round(float(ESTADO.modelo_area.predict(entrada)[0]), 4)
    return {
        "horas": horas,
        "area_angulo_prevista": area_angulo,
        "area_total_estimada": area_total,
        "equacao": ESTADO.equacao,
        "observacao": (
            "A base é determinística; a previsão é exata para o padrão aprendido "
            "e deve ser validada em condições de campo."
        ),
    }


class PrevisaoEntrada(BaseModel):
    horas: float = Field(
        ...,
        ge=0,
        le=1000,
        description="Horas de irrigação (0 a 1000). A base original cobre 1 a 299 horas.",
    )


# -----------------------------------------------------------------------------
# Rotas de interface
# -----------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse, tags=["Dashboard"], summary="Dashboard web")
def dashboard(request: Request):
    predicao_15h = prever(15)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request,
            "resumo": ESTADO.resumo,
            "estatisticas": ESTADO.estatisticas,
            "metricas": ESTADO.metricas,
            "modelo": {
                "coeficiente": ESTADO.coef_angulo,
                "intercepto": ESTADO.intercepto_angulo,
                "coef_area": ESTADO.coef_area,
                "intercepto_area": ESTADO.intercepto_area,
            },
            "equacao": ESTADO.equacao,
            "predicao_15h": predicao_15h["area_angulo_prevista"],
            "area_15h": predicao_15h["area_total_estimada"],
            "figuras": FIGURAS,
            "checklist": CHECKLIST,
            "github_url": GITHUB_URL or None,
        },
    )


@app.get(
    "/relatorio",
    tags=["Dashboard"],
    summary="Relatório completo em HTML",
    response_class=FileResponse,
)
def relatorio():
    caminho = PASTA_RESULTADOS / "relatorio.html"
    if not caminho.exists():
        raise HTTPException(
            status_code=404,
            detail="Relatório não encontrado. Execute 'python analise_irrigacao.py' primeiro.",
        )
    return FileResponse(caminho, media_type="text/html")


# -----------------------------------------------------------------------------
# Rotas de dados
# -----------------------------------------------------------------------------
@app.get("/api/resumo", tags=["Dados"], summary="Resumo do dataset e do modelo")
def api_resumo():
    return {
        "dataset": ESTADO.resumo,
        "modelo": {
            "equacao": ESTADO.equacao,
            "variavel_independente": "horas_irrigacao",
            "variavel_dependente": "area_irrigada_angulo",
            "coeficiente_angular": ESTADO.coef_angulo,
            "intercepto": ESTADO.intercepto_angulo,
            "treinamento": "todos os registros",
        },
        "metricas_teste": ESTADO.metricas,
        "predicao_15h": prever(15),
        "figuras": FIGURAS,
    }


@app.get("/api/estatisticas", tags=["Dados"], summary="Estatísticas descritivas")
def api_estatisticas():
    return {"estatisticas": ESTADO.estatisticas}


@app.get("/api/checklist", tags=["Dados"], summary="Checklist do projeto")
def api_checklist():
    return {"total": len(CHECKLIST), "itens": CHECKLIST}


@app.get("/api/figuras", tags=["Dados"], summary="Lista de figuras geradas")
def api_figuras():
    return {"figuras": FIGURAS}


# -----------------------------------------------------------------------------
# Rotas de modelo e predição
# -----------------------------------------------------------------------------
@app.get("/api/modelo", tags=["Modelo"], summary="Coeficientes e métricas do modelo")
def api_modelo():
    return {
        "equacao": ESTADO.equacao,
        "coeficiente_angular": ESTADO.coef_angulo,
        "intercepto": ESTADO.intercepto_angulo,
        "coeficiente_area_total": ESTADO.coef_area,
        "intercepto_area_total": ESTADO.intercepto_area,
        "metricas_teste": ESTADO.metricas,
    }


@app.post("/api/prever", tags=["Predição"], summary="Prever área irrigada (JSON)")
def api_prever(payload: PrevisaoEntrada):
    return prever(payload.horas)


@app.get(
    "/api/prever/{horas}",
    tags=["Predição"],
    summary="Prever área irrigada (URL)",
)
def api_prever_url(horas: float):
    if horas < 0 or horas > 1000:
        raise HTTPException(
            status_code=422,
            detail="O valor de horas deve estar entre 0 e 1000.",
        )
    return prever(horas)


# -----------------------------------------------------------------------------
# Sistema
# -----------------------------------------------------------------------------
@app.get("/health", tags=["Sistema"], summary="Verificação de saúde")
def health():
    return {
        "status": "ok",
        "registros": len(ESTADO.df),
        "modelo": "regressao_linear",
        "versao": "1.0.0",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
