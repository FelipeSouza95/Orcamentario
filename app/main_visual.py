# ==============================================================
# 📺 Painel Acompanhamento Orçamentário — Atualização Automática (hashlib)
# ==============================================================
# - Detecta alterações no arquivo da planilha
# - Atualiza automaticamente sem reiniciar o app
# - Visual limpo e ideal para TV
# ==============================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import os
import hashlib
from dotenv import load_dotenv
import datetime

# --------------------------------------------------------------
# CONFIGURAÇÃO GERAL
# --------------------------------------------------------------
st.set_page_config(
    page_title="Painel Orçamentário - SES",
    page_icon="assets/favicon.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Remove completamente a margem superior automática do Streamlit
st.markdown(
    """
    <style>
        div.block-container {
            padding-top: 0rem !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# --------------------------------------------------------------
# CSS
# --------------------------------------------------------------
def aplicar_estilo(css_path: str):
    if os.path.exists(css_path):
        with open(css_path, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

aplicar_estilo("assets/style.css")

# --------------------------------------------------------------
# CABEÇALHO
# --------------------------------------------------------------
st.markdown("""
    <div class="header-topo">
        <div class="header-title">
            Secretaria de Estado de Saúde - RJ
        </div>
    </div>
""", unsafe_allow_html=True)

# --------------------------------------------------------------
# FUNÇÃO PARA VERIFICAR ALTERAÇÕES NA PLANILHA
# --------------------------------------------------------------
def calcular_hash_arquivo(caminho):
    """Gera um hash (MD5) do conteúdo do arquivo para detectar mudanças."""
    hash_md5 = hashlib.md5()
    with open(caminho, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

# --------------------------------------------------------------
# CARREGAMENTO DA PLANILHA
# --------------------------------------------------------------
load_dotenv()
CAMINHO_ARQUIVO = os.getenv("ENV_PLANILHA_ACOMPANHAMENTO_ORCAMENTARIO")

if not CAMINHO_ARQUIVO or not os.path.exists(CAMINHO_ARQUIVO):
    st.error(f"⚠️ Arquivo não encontrado: {CAMINHO_ARQUIVO}")
    st.stop()

# Cálculo do hash atual
hash_atual = calcular_hash_arquivo(CAMINHO_ARQUIVO)

# Verifica se houve mudança desde a última leitura
if "hash_ultimo" not in st.session_state or st.session_state["hash_ultimo"] != hash_atual:
    st.session_state["hash_ultimo"] = hash_atual  # Atualiza hash salvo
    st.session_state["dados_carregados"] = None   # Força recarregamento

# --------------------------------------------------------------
# LEITURA DA PLANILHA (CACHE CONTROLADO)
# --------------------------------------------------------------
@st.cache_data(ttl=60)
def carregar_dados(caminho):
    extensao = os.path.splitext(caminho)[1].lower()
    if extensao == ".xlsx":
        df = pd.read_excel(caminho, header=2, engine="openpyxl")
    elif extensao == ".xls":
        df = pd.read_excel(caminho, header=2, engine="xlrd")
    else:
        raise ValueError("Formato de planilha não suportado.")
    return df

df = carregar_dados(CAMINHO_ARQUIVO)

# --------------------------------------------------------------
# AJUSTE DE NOMES E TIPOS
# --------------------------------------------------------------
df.columns = [str(c).strip() for c in df.columns]
df = df.fillna("")

def procurar_coluna(padrao):
    for col in df.columns:
        if padrao.lower() in col.lower():
            return col
    return None

col_acao = procurar_coluna("AÇÃO") or procurar_coluna("PT")
col_loa = procurar_coluna("LOA") or procurar_coluna("DOT")
col_decl = procurar_coluna("DECLARADO")
col_emp = procurar_coluna("EMPENHADO")

for col in [col_loa, col_decl, col_emp]:
    if col and col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# --------------------------------------------------------------
# FORMATAÇÃO EM MILHÕES
# --------------------------------------------------------------
def formatar_milhoes(valor):
    if pd.isna(valor):
        return "R$ 0,00 mi"
    return f"R$ {valor/1_000_000:,.2f} mi"

# --------------------------------------------------------------
# CÁLCULOS
# --------------------------------------------------------------
valor_loa = df[col_loa].sum(skipna=True) if col_loa else 0
valor_decl = df[col_decl].sum(skipna=True) if col_decl else 0
valor_emp = df[col_emp].sum(skipna=True) if col_emp else 0

# --------------------------------------------------------------
# CARDS SUPERIORES
# --------------------------------------------------------------
st.markdown("<div class='cards-container'>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"<div class='metric-card'><div class='metric-label-left'>Valor da LOA</div><div class='metric-value-right'>{formatar_milhoes(valor_loa)}</div></div>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<div class='metric-card'><div class='metric-label-left'>Declarado na ASSPLO</div><div class='metric-value-right'>{formatar_milhoes(valor_decl)}</div></div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div class='metric-card highlight'><div class='metric-label-left'>Empenhado</div><div class='metric-value-right'>{formatar_milhoes(valor_emp)}</div></div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# --------------------------------------------------------------
# GRÁFICO TOP 5 EMPENHADO
# --------------------------------------------------------------
if col_acao and col_emp:
    # Cria um container Streamlit que será estilizado via HTML
    with st.container():
        # Início do container HTML com bordas arredondadas
        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
        st.markdown("### 💰 Top 5 Ações com Maior Empenho")

        # Prepara os dados
        top5 = (
            df[[col_acao, col_emp]]
            .dropna(subset=[col_emp])
            .sort_values(by=col_emp, ascending=False)
            .head(5)
        )

        fator_reducao = 0.75
        top5["VALOR_GRAFICO"] = top5[col_emp] * fator_reducao

        color_scale = ["#0077b6", "#0096c7", "#00b4d8", "#48cae4", "#2744e9"]

        # Cria o gráfico
        fig = px.bar(
            top5,
            x="VALOR_GRAFICO",
            y=col_acao,
            orientation="h",
            text=top5[col_emp].apply(lambda x: f"{x/1_000_000:.2f} mi"),
            color=col_emp,
            color_continuous_scale=color_scale,
            labels={"VALOR_GRAFICO": "", col_acao: ""},
            height=480
        )

        fig.update_traces(
            textfont_size=25,
            textfont_color="white",
            textposition="inside",
            marker_line_color="white",
            marker_line_width=1.2,
            hoverinfo="none",
            hovertemplate=None
        )

        fig.update_layout(
            yaxis=dict(
                autorange="reversed",
                tickfont=dict(size=22, family="Segoe UI Semibold")
            ),
            xaxis=dict(visible=False),
            coloraxis_showscale=False,
            showlegend=False,
            margin=dict(l=25, r=25, t=25, b=0),
            plot_bgcolor="rgba(0,0,0,0)",  # 🔹 Fundo transparente
            paper_bgcolor="rgba(0,0,0,0)"  # 🔹 Fundo transparente
        )

        # Renderiza o gráfico dentro do container
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        # Fecha o container HTML
        st.markdown("</div>", unsafe_allow_html=True)

# --------------------------------------------------------------
# TABELA (TOP 10)
# --------------------------------------------------------------
st.markdown("### 📋 Acompanhamento Orçamentário (Top 10) - Detalhado")
tabela = df.head(10).astype(str)
st.dataframe(tabela, use_container_width=True, height=None)