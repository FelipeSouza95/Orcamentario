import numpy as np
import os
import pandas as pd
from openpyxl import load_workbook

def carregar_dados_excel(caminho_arquivo, aba=None, nome_aba=None):
    """Lê planilhas .xls e .xlsx e retorna (headers, dados)"""
    if not caminho_arquivo:
        raise FileNotFoundError("⚠️ caminho_arquivo não foi informado (None).")

    if not os.path.exists(caminho_arquivo):
        raise FileNotFoundError(f"⚠️ Arquivo não encontrado: {caminho_arquivo}")

    extensao = os.path.splitext(caminho_arquivo)[1].lower()

    if extensao == ".xlsx":
        df = pd.read_excel(caminho_arquivo, sheet_name=nome_aba or 0, engine="openpyxl")
    elif extensao == ".xls":
        try:
            df = pd.read_excel(caminho_arquivo, sheet_name=nome_aba or 0, engine="xlrd")
        except ImportError:
            raise ImportError("⚠️ Instale o pacote 'xlrd': pip install xlrd")
    else:
        raise ValueError(f"❌ Formato não suportado: {extensao}")

    df = df.fillna("")
    df.columns = [str(c).strip() for c in df.columns]
    headers = list(df.columns)
    dados = df.astype(str).values

    return headers, dados
