# -*- coding: utf-8 -*-
import streamlit as st
import gspread
import pandas as pd
import altair as alt
import numpy as np
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
from gspread.exceptions import SpreadsheetNotFound
import warnings
import time

# Suprimir warnings específicos do pandas
warnings.filterwarnings('ignore', category=FutureWarning, message='.*observed=False.*')

# --- Configurações Globais e Constantes ---
SPREADSHEET_ID = '1NTScbiIna-iE7roQ9XBdjUOssRihTFFby4INAAQNXTg'
WORKSHEET_NAME = 'Vendas'
COMPRAS_WORKSHEET_NAME = 'Compras'

# Lista de fornecedores por categoria
FORNECEDORES_CATEGORIAS = {
    "FRIOS": ["MMP FRIOS"],
    "BEBIDAS": ["PRACA DA BIBLIA"],
    "HAMBURGER": ["MAX"],
    "SUPERMERCADO": ["NOVA JERUSALEM", "RAIO"],
    "PAO": ["DI ROMA"]
}

# Configuração da página Streamlit
st.set_page_config(
    page_title="Clips Burger", 
    layout="wide", 
    page_icon="🍔",
    initial_sidebar_state="expanded"
)

# Configuração de tema para gráficos mais bonitos
alt.data_transformers.enable('json')

# Paleta de cores otimizada para modo escuro
CORES_MODO_ESCURO = ['#4c78a8', '#54a24b', '#f58518', '#e45756', '#72b7b2', '#ff9da6', '#9d755d', '#bab0ac']

# Define a ordem correta dos dias da semana e meses
dias_semana_ordem = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
meses_ordem = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

# CSS para melhorar a aparência e adicionar background
def inject_css():
    # Base CSS styles com background cyberpunk
    base_css = """
    /* Background principal cyberpunk com efeito inset */
    .stApp {
        background: linear-gradient(135deg, #0c0c0c 0%, #1a0033 50%, #000000 100%);
        box-shadow: inset 0 0 100px rgba(138, 43, 226, 0.1);
        background-attachment: fixed;
    }
    
    /* Header transparente */
    .stApp > header {
        background-color: transparent;
    }
    
    /* Sidebar com fundo semi-transparente */
    .css-1d391kg {
        background: rgba(30, 60, 114, 0.8);
        backdrop-filter: blur(10px);
    }
    
    /* Containers com fundo semi-transparente */
    .stContainer {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        backdrop-filter: blur(5px);
    }
    
    .stSelectbox label, .stNumberInput label {
        font-weight: bold;
        color: #87CEEB;
    }
    .stNumberInput input::placeholder {
        color: #888;
        font-style: italic;
    }
    .stButton > button {
        height: 3rem;
        font-size: 1.2rem;
        font-weight: bold;
        width: 100%;
        background: linear-gradient(45deg, #4c78a8, #87CEEB);
        border: none;
        color: white;
    }
    .stButton > button:hover {
        background: linear-gradient(45deg, #87CEEB, #4c78a8);
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }
    .element-container {
        margin-bottom: 0.5rem;
    }
    .stMetric {
        background-color: rgba(135, 206, 235, 0.1);
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
        min-height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        border: 1px solid rgba(135, 206, 235, 0.3);
    }
    
    /* Rodapé */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background: linear-gradient(90deg, rgba(76, 120, 168, 0.9), rgba(84, 162, 75, 0.9));
        color: white;
        text-align: center;
        padding: 10px 0;
        font-size: 14px;
        z-index: 999;
        backdrop-filter: blur(10px);
        border-top: 1px solid rgba(255, 255, 255, 0.2);
    }
    """
    
    # CSS da logo animada (integrado)
    fire_logo_css = """
    /* Logo Container com Efeito de Fogo */
    .logo-fire-container {
        position: relative;
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 2rem auto;
        height: 280px;
        width: 100%;
        max-width: 400px;
        overflow: visible !important;
        z-index: 1;
    }
    
    /* Logo Principal - Z-INDEX ALTO E ANIMADA */
    .fire-logo {
        position: relative;
        z-index: 50;
        max-width: 200px;
        width: auto;
        height: auto;
        object-fit: contain;
        filter: drop-shadow(0 0 20px rgba(255, 69, 0, 0.8));
        animation: logoFloat 3s ease-in-out infinite;
        display: block;
        margin: 0 auto;
    }
    
    /* Animação de Flutuação da Logo */
    @keyframes logoFloat {
        0%, 100% {
            transform: translateY(0px) scale(1);
            filter: drop-shadow(0 0 20px rgba(255, 69, 0, 0.8));
        }
        50% {
            transform: translateY(-10px) scale(1.05);
            filter: drop-shadow(0 0 30px rgba(255, 140, 0, 1));
        }
    }
    
    /* Container das Chamas */
    .fire-container {
        position: absolute;
        bottom: -30px;
        left: 50%;
        transform: translateX(-50%);
        width: 300px;
        height: 800px;
        z-index: 1;
        pointer-events: none;
        overflow: visible !important;
    }
    
    /* Chamas Individuais */
    .flame {
        position: absolute;
        bottom: 0;
        border-radius: 50% 50% 50% 50% / 60% 60% 40% 40%;
        transform-origin: center bottom;
        animation: flicker 0.5s ease-in-out infinite alternate;
        z-index: 10;
    }
    
    /* Chama Principal (Vermelha) */
    .flame-red {
        left: 50%;
        transform: translateX(-50%);
        width: 80px;
        height: 120px;
        background: radial-gradient(circle, #ff4500 0%, #ff6347 30%, #dc143c 70%, #8b0000 100%);
        box-shadow: 0 0 30px #ff4500, 0 0 60px #ff6347, 0 0 90px #dc143c;
        animation: flicker 0.8s ease-in-out infinite alternate;
    }
    
    /* Chama Laranja */
    .flame-orange {
        left: 45%;
        transform: translateX(-50%);
        width: 60px;
        height: 90px;
        background: radial-gradient(circle, #ffa500 0%, #ff8c00 50%, #ff4500 100%);
        box-shadow: 0 0 25px #ffa500, 0 0 50px #ff8c00;
        animation: flicker 0.6s ease-in-out infinite alternate;
        animation-delay: 0.2s;
    }
    
    /* Chama Amarela */
    .flame-yellow {
        left: 55%;
        transform: translateX(-50%);
        width: 40px;
        height: 70px;
        background: radial-gradient(circle, #ffff00 0%, #ffd700 50%, #ffa500 100%);
        box-shadow: 0 0 20px #ffff00, 0 0 40px #ffd700;
        animation: flicker 0.4s ease-in-out infinite alternate;
        animation-delay: 0.4s;
    }
    
    /* Chama Branca (Centro) */
    .flame-white {
        left: 50%;
        transform: translateX(-50%);
        width: 25px;
        height: 50px;
        background: radial-gradient(circle, #ffffff 0%, #ffff99 50%, #ffd700 100%);
        box-shadow: 0 0 15px #ffffff, 0 0 30px #ffff99;
        animation: flicker 0.3s ease-in-out infinite alternate;
        animation-delay: 0.1s;
    }
    
    /* Partículas de Fogo */
    .fire-particle {
        position: absolute;
        bottom: 0;
        border-radius: 50%;
        animation: particle-rise-high linear infinite;
        pointer-events: none;
        z-index: 5;
        opacity: 1;
    }
    
    /* Animação das Partículas */
    @keyframes particle-rise-high {
        0% {
            bottom: 0px;
            opacity: 1;
            transform: translateX(0) scale(1);
        }
        10% {
            bottom: 50px;
            opacity: 1;
            transform: translateX(calc(var(--random-x, 0) * 0.2)) scale(0.95);
        }
        25% {
            bottom: 150px;
            opacity: 0.9;
            transform: translateX(calc(var(--random-x, 0) * 0.5)) scale(0.85);
        }
        40% {
            bottom: 250px;
            opacity: 0.7;
            transform: translateX(calc(var(--random-x, 0) * 0.7)) scale(0.7);
        }
        60% {
            bottom: 400px;
            opacity: 0.6;
            transform: translateX(var(--random-x, 0)) scale(0.6);
        }
        80% {
            bottom: 600px;
            opacity: 0.3;
            transform: translateX(calc(var(--random-x, 0) * 1.2)) scale(0.4);
        }
        100% {
            bottom: 800px;
            opacity: 0;
            transform: translateX(calc(var(--random-x, 0) * 1.5)) scale(0.1);
        }
    }
    
    /* Estilos das Partículas */
    .fire-particle.small {
        width: 4px;
        height: 4px;
        background: radial-gradient(circle, #ff6347 0%, #ff4500 100%);
        box-shadow: 0 0 8px #ff6347;
    }
    
    .fire-particle.medium {
        width: 6px;
        height: 6px;
        background: radial-gradient(circle, #ffa500 0%, #ff6347 100%);
        box-shadow: 0 0 10px #ffa500;
    }
    
    .fire-particle.large {
        width: 8px;
        height: 8px;
        background: radial-gradient(circle, #ffff00 0%, #ffa500 100%);
        box-shadow: 0 0 12px #ffff00;
    }
    
    /* Configuração das Partículas */
    .fire-particle:nth-child(1) { 
        left: 5%; 
        animation-delay: 0.2s; 
        animation-duration: 4.5s;
        --random-x: -12px;
    }
    .fire-particle:nth-child(2) { 
        left: 15%; 
        animation-delay: 0.7s; 
        animation-duration: 4.8s;
        --random-x: 18px;
    }
    .fire-particle:nth-child(3) { 
        left: 25%; 
        animation-delay: 1.2s; 
        animation-duration: 4.2s;
        --random-x: -8px;
    }
    .fire-particle:nth-child(4) { 
        left: 35%; 
        animation-delay: 1.7s; 
        animation-duration: 5.1s;
        --random-x: 14px;
    }
    .fire-particle:nth-child(5) { 
        left: 10%; 
        animation-delay: 0s; 
        animation-duration: 5.0s;
        --random-x: -20px;
    }
    .fire-particle:nth-child(6) { 
        left: 20%; 
        animation-delay: 0.5s; 
        animation-duration: 4.8s;
        --random-x: 25px;
    }
    .fire-particle:nth-child(7) { 
        left: 30%; 
        animation-delay: 1.0s; 
        animation-duration: 5.2s;
        --random-x: -15px;
    }
    .fire-particle:nth-child(8) { 
        left: 40%; 
        animation-delay: 1.5s; 
        animation-duration: 4.6s;
        --random-x: 18px;
    }
    .fire-particle:nth-child(9) { 
        left: 50%; 
        animation-delay: 2.0s; 
        animation-duration: 5.1s;
        --random-x: -22px;
    }
    .fire-particle:nth-child(10) { 
        left: 60%; 
        animation-delay: 2.5s; 
        animation-duration: 4.9s;
        --random-x: 16px;
    }
    .fire-particle:nth-child(11) { 
        left: 70%; 
        animation-delay: 3.0s; 
        animation-duration: 5.3s;
        --random-x: -18px;
    }
    .fire-particle:nth-child(12) { 
        left: 80%; 
        animation-delay: 3.5s; 
        animation-duration: 4.7s;
        --random-x: 24px;
    }
    .fire-particle:nth-child(13) { 
        left: 90%; 
        animation-delay: 4.0s; 
        animation-duration: 5.0s;
        --random-x: -14px;
    }
    .fire-particle:nth-child(14) { 
        left: 45%; 
        animation-delay: 0.8s; 
        animation-duration: 4.4s;
        --random-x: -10px;
    }
    .fire-particle:nth-child(15) { 
        left: 55%; 
        animation-delay: 1.3s; 
        animation-duration: 4.9s;
        --random-x: 20px;
    }
    .fire-particle:nth-child(16) { 
        left: 65%; 
        animation-delay: 1.8s; 
        animation-duration: 4.3s;
        --random-x: -16px;
    }
    .fire-particle:nth-child(17) { 
        left: 75%; 
        animation-delay: 2.3s; 
        animation-duration: 5.2s;
        --random-x: 12px;
    }
    .fire-particle:nth-child(18) { 
        left: 85%; 
        animation-delay: 2.8s; 
        animation-duration: 4.6s;
        --random-x: -19px;
    }
    .fire-particle:nth-child(19) { 
        left: 95%; 
        animation-delay: 3.3s; 
        animation-duration: 4.8s;
        --random-x: 15px;
    }
    .fire-particle:nth-child(20) { 
        left: 12%; 
        animation-delay: 0.3s; 
        animation-duration: 5.0s;
        --random-x: -13px;
    }
    
    /* Animações das Chamas */
    @keyframes flicker {
        0% {
            transform: translateX(-50%) rotate(-2deg) scaleY(1);
            opacity: 0.8;
        }
        25% {
            transform: translateX(-50%) rotate(1deg) scaleY(1.1);
            opacity: 0.9;
        }
        50% {
            transform: translateX(-50%) rotate(-1deg) scaleY(0.95);
            opacity: 1;
        }
        75% {
            transform: translateX(-50%) rotate(2deg) scaleY(1.05);
            opacity: 0.85;
        }
        100% {
            transform: translateX(-50%) rotate(-1deg) scaleY(1);
            opacity: 0.9;
        }
    }

    /* Responsividade para logo */
    @media screen and (max-width: 768px) {
        .logo-fire-container {
            height: 240px;
            max-width: 350px;
        }
        
        .fire-logo {
            max-width: 180px;
        }
        
        .fire-container {
            width: 250px;
            height: 150px;
            bottom: -20px;
        }
    }

    @media screen and (max-width: 480px) {
        .logo-fire-container {
            height: 200px;
            max-width: 300px;
            margin: 1rem auto;
        }
        
        .fire-logo {
            max-width: 150px;
        }
        
        .fire-container {
            width: 200px;
            height: 120px;
            bottom: -15px;
        }
        
        .flame-red {
            width: 60px;
            height: 90px;
        }
        
        .flame-orange {
            width: 45px;
            height: 70px;
        }
        
        .flame-yellow {
            width: 30px;
            height: 50px;
        }
        
        .flame-white {
            width: 20px;
            height: 35px;
        }
    }
    """

    # Combine and inject CSS
    st.markdown(f"<style>{base_css}\n{fire_logo_css}</style>", unsafe_allow_html=True)

inject_css()

# --- Funções de Cache para Acesso ao Google Sheets ---
@st.cache_resource
def get_google_auth():
    """Autoriza o acesso ao Google Sheets e retorna o cliente gspread."""
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
              'https://www.googleapis.com/auth/spreadsheets.readonly',
              'https://www.googleapis.com/auth/drive.readonly']
    try:
        if "google_credentials" not in st.secrets:
            st.error("Credenciais do Google ('google_credentials') não encontradas em st.secrets. Configure o arquivo .streamlit/secrets.toml")
            return None
        
        credentials_dict = st.secrets["google_credentials"]
        if not credentials_dict:
            st.error("As credenciais do Google em st.secrets estão vazias.")
            return None
            
        creds = Credentials.from_service_account_info(credentials_dict, scopes=SCOPES)
        gc = gspread.authorize(creds)
        return gc
    except Exception as e:
        st.error(f"Erro de autenticação com Google: {e}")
        return None

@st.cache_resource
def get_worksheet():
    """Retorna o objeto worksheet da planilha especificada."""
    gc = get_google_auth()
    if gc:
        try:
            spreadsheet = gc.open_by_key(SPREADSHEET_ID)
            worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
            return worksheet
        except SpreadsheetNotFound:
            st.error(f"Planilha com ID '{SPREADSHEET_ID}' não encontrada.")
            return None
        except Exception as e:
            st.error(f"Erro ao acessar a planilha '{WORKSHEET_NAME}': {e}")
            return None
    return None

@st.cache_resource
def get_compras_worksheet():
    """Retorna o objeto worksheet da planilha de compras."""
    gc = get_google_auth()
    if gc:
        try:
            spreadsheet = gc.open_by_key(SPREADSHEET_ID)
            try:
                worksheet = spreadsheet.worksheet(COMPRAS_WORKSHEET_NAME)
                return worksheet
            except:
                # Se a aba não existir, criar uma nova
                worksheet = spreadsheet.add_worksheet(title=COMPRAS_WORKSHEET_NAME, rows="1000", cols="10")
                # Adicionar cabeçalhos CORRETOS
                worksheet.append_row(['DATA', 'PRODUTO', 'QUANTIDADE', 'VALOR', 'FORNECEDOR'])
                return worksheet
        except SpreadsheetNotFound:
            st.error(f"Planilha com ID '{SPREADSHEET_ID}' não encontrada.")
            return None
        except Exception as e:
            st.error(f"Erro ao acessar a planilha '{COMPRAS_WORKSHEET_NAME}': {e}")
            return None
    return None

@st.cache_data
def read_sales_data():
    """Lê todos os registros da planilha de vendas e retorna como DataFrame."""
    worksheet = get_worksheet()
    if worksheet:
        try:
            rows = worksheet.get_all_records()
            if not rows:
                st.info("A planilha de vendas está vazia.")
                return pd.DataFrame()

            df = pd.DataFrame(rows)
            
            for col in ['Cartão', 'Dinheiro', 'Pix']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                else:
                    df[col] = 0
            
            if 'Data' not in df.columns:
                df['Data'] = pd.NaT

            return df
        except Exception as e:
            st.error(f"Erro ao ler dados da planilha: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

@st.cache_data
def read_compras_data():
    """Lê todos os registros da planilha de compras e retorna como DataFrame."""
    worksheet = get_compras_worksheet()
    if worksheet:
        try:
            rows = worksheet.get_all_records()
            if not rows:
                return pd.DataFrame(columns=['DATA', 'PRODUTO', 'QUANTIDADE', 'VALOR', 'FORNECEDOR'])

            df = pd.DataFrame(rows)
            
            # Verificar se as colunas essenciais existem
            required_columns = ['DATA', 'PRODUTO', 'QUANTIDADE', 'VALOR', 'FORNECEDOR']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.error(f"❌ Colunas ausentes na planilha de compras: {missing_columns}")
                return pd.DataFrame(columns=required_columns)
            
            # Converter valores para numérico
            if 'VALOR' in df.columns:
                df['VALOR'] = pd.to_numeric(df['VALOR'], errors='coerce').fillna(0)
            else:
                df['VALOR'] = 0
                
            if 'QUANTIDADE' in df.columns:
                df['QUANTIDADE'] = pd.to_numeric(df['QUANTIDADE'], errors='coerce').fillna(0)
            else:
                df['QUANTIDADE'] = 0
            
            # Processar data
            if 'DATA' in df.columns and not df['DATA'].isnull().all():
                df['Data'] = pd.to_datetime(df['DATA'], dayfirst=True, errors='coerce')
                df.dropna(subset=['Data'], inplace=True)
                
                if not df.empty:
                    df['DataFormatada'] = df['Data'].dt.strftime('%d/%m/%Y')
                    df['Ano'] = df['Data'].dt.year
                    df['Mês'] = df['Data'].dt.month
                    df['MêsNome'] = df['Mês'].map(lambda x: meses_ordem[int(x)-1] if pd.notna(x) and 1 <= int(x) <= 12 else "Inválido")

            return df
        except Exception as e:
            st.error(f"Erro ao ler dados da planilha de compras: {e}")
            return pd.DataFrame(columns=['DATA', 'PRODUTO', 'QUANTIDADE', 'VALOR', 'FORNECEDOR'])
    return pd.DataFrame(columns=['DATA', 'PRODUTO', 'QUANTIDADE', 'VALOR', 'FORNECEDOR'])

# --- Funções de Manipulação de Dados ---
def add_data_to_sheet(date, cartao, dinheiro, pix, worksheet_obj):
    """Adiciona uma nova linha de dados à planilha Google Sheets."""
    if worksheet_obj is None:
        st.error("Não foi possível acessar a planilha para adicionar dados.")
        return False
    try:
        cartao_val = float(cartao) if cartao else 0.0
        dinheiro_val = float(dinheiro) if dinheiro else 0.0
        pix_val = float(pix) if pix else 0.0
        
        new_row = [date, cartao_val, dinheiro_val, pix_val]
        worksheet_obj.append_row(new_row)
        st.success("Dados registrados com sucesso! ✅")
        return True
    except ValueError as ve:
        st.error(f"Erro ao converter valores para número: {ve}. Verifique os dados de entrada.")
        return False
    except Exception as e:
        st.error(f"Erro ao adicionar dados na planilha: {e}")
        return False

def add_compras_to_sheet(date, produtos_list, worksheet_obj):
    """Adiciona múltiplas compras à planilha Google Sheets."""
    if worksheet_obj is None:
        st.error("Não foi possível acessar a planilha para adicionar as compras.")
        return False
    
    try:
        success_count = 0
        for produto_data in produtos_list:
            produto = produto_data['produto']
            quantidade = float(produto_data['quantidade']) if produto_data['quantidade'] else 0.0
            valor = float(produto_data['valor']) if produto_data['valor'] else 0.0
            fornecedor = produto_data['fornecedor']
            
            # Nova ordem: DATA, PRODUTO, QUANTIDADE, VALOR, FORNECEDOR
            new_row = [date, produto, quantidade, valor, fornecedor]
            worksheet_obj.append_row(new_row)
            success_count += 1
        
        st.success(f"✅ {success_count} compra(s) registrada(s) com sucesso!")
        return True
    except ValueError as ve:
        st.error(f"Erro ao converter valores para número: {ve}")
        return False
    except Exception as e:
        st.error(f"Erro ao adicionar compras na planilha: {e}")
        return False

@st.cache_data
def process_data(df_input):
    """Processa e prepara os dados de vendas para análise."""
    df = df_input.copy()
    
    cols_to_ensure_numeric = ['Cartão', 'Dinheiro', 'Pix', 'Total']
    cols_to_ensure_date_derived = ['Ano', 'Mês', 'MêsNome', 'AnoMês', 'DataFormatada', 'DiaSemana', 'DiaDoMes']
    
    if df.empty:
        all_expected_cols = ['Data'] + cols_to_ensure_numeric + cols_to_ensure_date_derived
        empty_df = pd.DataFrame(columns=all_expected_cols)
        for col in cols_to_ensure_numeric:
            empty_df[col] = pd.Series(dtype='float')
        for col in cols_to_ensure_date_derived:
            empty_df[col] = pd.Series(dtype='object' if col in ['MêsNome', 'AnoMês', 'DataFormatada', 'DiaSemana'] else 'float')
        empty_df['Data'] = pd.Series(dtype='datetime64[ns]')
        return empty_df

    for col in ['Cartão', 'Dinheiro', 'Pix']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        else:
            df[col] = 0

    df['Total'] = df['Cartão'] + df['Dinheiro'] + df['Pix']

    if 'Data' in df.columns and not df['Data'].isnull().all():
        try:
            if pd.api.types.is_string_dtype(df['Data']):
                df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
                if df['Data'].isnull().all():
                    df['Data'] = pd.to_datetime(df_input['Data'], errors='coerce')
            elif not pd.api.types.is_datetime64_any_dtype(df['Data']):
                df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
            
            df.dropna(subset=['Data'], inplace=True)

            if not df.empty:
                df['Ano'] = df['Data'].dt.year
                df['Mês'] = df['Data'].dt.month

                try:
                    df['MêsNome'] = df['Data'].dt.strftime('%B').str.capitalize()
                    if not df['MêsNome'].dtype == 'object' or df['MêsNome'].str.isnumeric().any():
                        df['MêsNome'] = df['Mês'].map(lambda x: meses_ordem[int(x)-1] if pd.notna(x) and 1 <= int(x) <= 12 else "Inválido")
                except Exception:
                    df['MêsNome'] = df['Mês'].map(lambda x: meses_ordem[int(x)-1] if pd.notna(x) and 1 <= int(x) <= 12 else "Inválido")

                df['AnoMês'] = df['Data'].dt.strftime('%Y-%m')
                df['DataFormatada'] = df['Data'].dt.strftime('%d/%m/%Y')
                
                day_map = {0: "Segunda-feira", 1: "Terça-feira", 2: "Quarta-feira", 3: "Quinta-feira", 4: "Sexta-feira", 5: "Sábado", 6: "Domingo"}
                df['DiaSemana'] = df['Data'].dt.dayofweek.map(day_map)
                df['DiaDoMes'] = df['Data'].dt.day

                df['DiaSemana'] = pd.Categorical(df['DiaSemana'], categories=[d for d in dias_semana_ordem if d in df['DiaSemana'].unique()], ordered=True)
            else:
                for col in cols_to_ensure_date_derived:
                    df[col] = pd.Series(dtype='object' if col in ['MêsNome', 'AnoMês', 'DataFormatada', 'DiaSemana'] else 'float')
        except Exception as e:
            st.error(f"Erro crítico ao processar a coluna 'Data': {e}. Verifique o formato das datas na planilha.")
            for col in cols_to_ensure_date_derived:
                df[col] = pd.Series(dtype='object' if col in ['MêsNome', 'AnoMês', 'DataFormatada', 'DiaSemana'] else 'float')
    else:
        if 'Data' not in df.columns:
            st.warning("Coluna 'Data' não encontrada no DataFrame. Algumas análises temporais não estarão disponíveis.")
            df['Data'] = pd.NaT
        for col in cols_to_ensure_date_derived:
            df[col] = pd.Series(dtype='object' if col in ['MêsNome', 'AnoMês', 'DataFormatada', 'DiaSemana'] else 'float')
            
    return df

# --- Funções de Gráficos Interativos em Altair ---
def create_radial_plot(df):
    """Cria um gráfico radial plot substituindo o gráfico de pizza."""
    if df.empty or not any(col in df.columns for col in ['Cartão', 'Dinheiro', 'Pix']):
        return None
    
    payment_data = pd.DataFrame({
        'Método': ['Cartão', 'Dinheiro', 'PIX'],
        'Valor': [df['Cartão'].sum(), df['Dinheiro'].sum(), df['Pix'].sum()]
    })
    payment_data = payment_data[payment_data['Valor'] > 0]
    
    if payment_data.empty:
        return None

    # Criar gráfico radial plot usando Altair
    base = alt.Chart(payment_data).encode(
        theta=alt.Theta('Valor:Q', stack=True),
        radius=alt.Radius('Valor:Q', scale=alt.Scale(type='sqrt', zero=True, rangeMin=20)),
        color=alt.Color(
            'Método:N', 
            scale=alt.Scale(range=CORES_MODO_ESCURO[:3]),
            legend=None
        ),
        tooltip=[
            alt.Tooltip('Método:N', title='Método'),
            alt.Tooltip('Valor:Q', title='Valor (R$)', format=',.2f')
        ]
    )

    radial_plot = base.mark_arc(
        innerRadius=20, 
        stroke='white', 
        strokeWidth=2
    ).properties(
        height=500,
        padding={'bottom': 100}
    ).configure_view(
        stroke=None
    ).configure(
        background='transparent'
    )

    return radial_plot

def create_cumulative_area_chart(df):
    """Cria gráfico de área ACUMULADO com gradiente."""
    if df.empty or 'Data' not in df.columns or 'Total' not in df.columns:
        st.warning("Dados insuficientes ou colunas 'Data'/'Total' ausentes para gerar o gráfico de evolução acumulada.")
        return None

    df_copy = df.copy()
    try:
        df_copy['Data'] = pd.to_datetime(df_copy['Data'])
    except Exception as e:
        st.error(f"Erro ao converter a coluna 'Data' para datetime: {e}")
        return None

    df_sorted = df_copy.sort_values('Data')

    if df_sorted.empty:
        st.warning("DataFrame vazio após ordenação para o gráfico de evolução acumulada.")
        return None

    df_sorted['Total_Acumulado'] = df_sorted['Total'].cumsum()

    area_chart = alt.Chart(df_sorted).mark_area(
        interpolate='monotone',
        line={'color': CORES_MODO_ESCURO[0], 'strokeWidth': 2},
        color=alt.Gradient(
            gradient='linear',
            stops=[
                alt.GradientStop(color=CORES_MODO_ESCURO[0], offset=0),
                alt.GradientStop(color=CORES_MODO_ESCURO[4], offset=1)
            ],
            x1=1, x2=1, y1=1, y2=0
        )
    ).encode(
        x=alt.X(
            'Data:T',
            axis=alt.Axis(format='%d/%m', labelAngle=-45, labelFontSize=12)
        ),
        y=alt.Y(
            'Total_Acumulado:Q',
            axis=alt.Axis(labelFontSize=12)
        ),
        tooltip=[
            alt.Tooltip('Data:T', title='Data', format='%d/%m/%Y'),
            alt.Tooltip('Total:Q', title='Venda do Dia (R$)', format=',.2f'),
            alt.Tooltip('Total_Acumulado:Q', title='Total Acumulado (R$)', format=',.2f')
        ]
    ).properties(
        height=500,
    ).configure(
        background='transparent'
    )

    return area_chart

def create_advanced_daily_sales_chart(df):
    """Cria um gráfico de vendas diárias sem animação."""
    if df.empty or 'Data' not in df.columns:
        return None
    
    df_sorted = df.sort_values('Data').copy()
    
    if df_sorted.empty:
        return None
    
    df_melted = df_sorted.melt(
        id_vars=['Data', 'DataFormatada', 'Total'],
        value_vars=['Cartão', 'Dinheiro', 'Pix'],
        var_name='Método',
        value_name='Valor'
    )
    
    df_melted = df_melted[df_melted['Valor'] > 0]
    
    if df_melted.empty:
        return None
    
    bars = alt.Chart(df_melted).mark_bar(
        size=20,
        stroke='white',
        strokeWidth=2
    ).encode(
        x=alt.X(
            'Data:T',
            title='Data',
            axis=alt.Axis(format='%d/%m', labelAngle=-45, labelFontSize=12)
        ),
        y=alt.Y(
            'Valor:Q',
            title='Valor (R$)',
            stack='zero',
            axis=alt.Axis(labelFontSize=12)
        ),
        color=alt.Color(
            'Método:N',
            scale=alt.Scale(range=CORES_MODO_ESCURO[:3]),
            legend=None
        ),
        tooltip=[
            alt.Tooltip('DataFormatada:N', title='Data'),
            alt.Tooltip('Método:N', title='Método'),
            alt.Tooltip('Valor:Q', title='Valor (R$)', format=',.2f')
        ]
    ).properties(
        height=500,
        padding={'bottom': 100}
    ).configure_view(
        stroke=None
    ).configure(
        background='transparent'
    )
    
    return bars

def create_enhanced_weekday_analysis(df):
    """Cria análise de vendas por dia da semana sem animação."""
    if df.empty or 'DiaSemana' not in df.columns or 'Total' not in df.columns:
        return None, None
    
    df_copy = df.copy()
    df_copy['Total'] = pd.to_numeric(df_copy['Total'], errors='coerce')
    df_copy.dropna(subset=['Total', 'DiaSemana'], inplace=True)
    
    if df_copy.empty:
        return None, None
    
    weekday_stats = df_copy.groupby('DiaSemana', observed=True).agg({
        'Total': ['mean', 'sum', 'count']
    }).round(2)
    
    weekday_stats.columns = ['Média', 'Total', 'Dias_Vendas']
    weekday_stats = weekday_stats.reindex([d for d in dias_semana_ordem if d in weekday_stats.index])
    weekday_stats = weekday_stats.reset_index()
    
    total_media_geral = weekday_stats['Média'].sum()
    if total_media_geral > 0:
        weekday_stats['Percentual_Media'] = (weekday_stats['Média'] / total_media_geral * 100).round(1)
    else:
        weekday_stats['Percentual_Media'] = 0
    
    chart = alt.Chart(weekday_stats).mark_bar(
        color=CORES_MODO_ESCURO[0],
        cornerRadiusTopLeft=5,
        cornerRadiusTopRight=5
    ).encode(
        x=alt.X(
            'DiaSemana:O',
            title='Dia da Semana',
            sort=dias_semana_ordem,
            axis=alt.Axis(labelAngle=-45, labelFontSize=12)
        ),
        y=alt.Y(
            'Média:Q',
            title='Média de Vendas (R$)',
            axis=alt.Axis(labelFontSize=12)
        ),
        tooltip=[
            alt.Tooltip('DiaSemana:N', title='Dia'),
            alt.Tooltip('Média:Q', title='Média (R$)', format=',.2f'),
            alt.Tooltip('Percentual_Media:Q', title='% da Média Total', format='.1f'),
            alt.Tooltip('Dias_Vendas:Q', title='Dias com Vendas')
        ]
    ).properties(
        title=alt.TitleParams(
            text="Média de Vendas por Dia da Semana",
            fontSize=18,
            anchor='start'
        ),
        height=500,
        padding={'bottom': 100}
    ).configure_view(
        stroke=None
    ).configure(
        background='transparent'
    )
    
    best_day = weekday_stats.loc[weekday_stats['Média'].idxmax(), 'DiaSemana'] if not weekday_stats.empty else "N/A"
    
    return chart, best_day

def create_sales_histogram(df, title="Distribuição dos Valores de Venda Diários"):
    """Histograma sem animação."""
    if df.empty or 'Total' not in df.columns or df['Total'].isnull().all():
        return None
    
    df_filtered_hist = df[df['Total'] > 0].copy()
    if df_filtered_hist.empty:
        return None
    
    histogram = alt.Chart(df_filtered_hist).mark_bar(
        color=CORES_MODO_ESCURO[0],
        opacity=0.8,
        cornerRadiusTopLeft=5,
        cornerRadiusTopRight=5
    ).encode(
        x=alt.X(
            "Total:Q",
            bin=alt.Bin(maxbins=20),
            title="Faixa de Valor da Venda Diária (R$)",
            axis=alt.Axis(labelFontSize=12)
        ),
        y=alt.Y(
            'count():Q',
            title='Número de Dias (Frequência)',
            axis=alt.Axis(labelFontSize=12)
        ),
        tooltip=[
            alt.Tooltip("Total:Q", bin=True, title="Faixa de Valor (R$)", format=",.0f"),
            alt.Tooltip("count():Q", title="Número de Dias")
        ]
    ).properties(
        title=alt.TitleParams(
            text=title,
            fontSize=18,
            anchor='start'
        ),
        height=600,
        padding={'bottom': 100}
    ).configure_view(
        stroke=None
    ).configure(
        background='transparent'
    )
    
    return histogram

def analyze_sales_by_weekday(df):
    """Analisa vendas por dia da semana."""
    if df.empty or 'DiaSemana' not in df.columns or 'Total' not in df.columns or df['DiaSemana'].isnull().all() or df['Total'].isnull().all():
        return None, None
    
    try:
        df_copy = df.copy()
        df_copy['Total'] = pd.to_numeric(df_copy['Total'], errors='coerce')
        df_copy.dropna(subset=['Total', 'DiaSemana'], inplace=True)
        
        if df_copy.empty:
            return None, None
        
        avg_sales_weekday = df_copy.groupby('DiaSemana', observed=True)['Total'].mean().reindex(dias_semana_ordem).dropna()
        
        if not avg_sales_weekday.empty:
            best_day = avg_sales_weekday.idxmax()
            return best_day, avg_sales_weekday
        else:
            return None, avg_sales_weekday
    except Exception as e:
        st.error(f"Erro ao analisar vendas por dia da semana: {e}")
        return None, None

def create_daily_purchases_histogram(df_compras, title="Histograma de Compras por Dia"):
    """Cria histograma de compras diárias agrupadas por faixas de valor."""
    if df_compras.empty or 'VALOR' not in df_compras.columns or df_compras['VALOR'].isnull().all():
        return None
    
    # Filtrar apenas compras > 0
    df_filtered = df_compras[df_compras['VALOR'] > 0].copy()
    if df_filtered.empty:
        return None
    
    # Agrupar por data e somar valores
    if 'Data' in df_filtered.columns:
        df_daily = df_filtered.groupby('Data')['VALOR'].sum().reset_index()
        df_daily.columns = ['Data', 'Total_Compras']
    else:
        return None
    
    # Criar faixas de valores para o histograma
    df_daily['Faixa_Valor'] = pd.cut(
        df_daily['Total_Compras'], 
        bins=[0, 100, 300, 500, 800, 1200, float('inf')],
        labels=['R$ 0-100', 'R$ 100-300', 'R$ 300-500', 'R$ 500-800', 'R$ 800-1200', 'R$ 1200+']
    )
    
    # Contar frequência por faixa
    faixa_counts = df_daily['Faixa_Valor'].value_counts().sort_index()
    
    # Preparar dados para o gráfico
    chart_data = pd.DataFrame({
        'Faixa_Valor': faixa_counts.index,
        'Frequencia': faixa_counts.values
    })
    
    # Criar histograma com Altair
    histogram = alt.Chart(chart_data).mark_bar(
        color=CORES_MODO_ESCURO[4],
        opacity=0.8,
        cornerRadiusTopLeft=8,
        cornerRadiusTopRight=8,
        stroke='white',
        strokeWidth=2
    ).encode(
        x=alt.X(
            'Faixa_Valor:O',
            title='Faixa de Valor das Compras Diárias',
            axis=alt.Axis(labelAngle=-45, labelFontSize=12)
        ),
        y=alt.Y(
            'Frequencia:Q',
            title='Número de Dias',
            axis=alt.Axis(labelFontSize=12)
        ),
        tooltip=[
            alt.Tooltip('Faixa_Valor:O', title='Faixa de Valor'),
            alt.Tooltip('Frequencia:Q', title='Dias nesta faixa')
        ]
    ).properties(
        title=alt.TitleParams(
            text=title,
            fontSize=18,
            anchor='start'
        ),
        height=400,
        padding={'bottom': 100}
    ).configure_view(
        stroke=None
    ).configure(
        background='transparent'
    )
    
    return histogram


# --- Funções de Cálculos Financeiros ---
def calculate_financial_results(df, salario_minimo, custo_contadora, custo_fornecedores_percentual):
    """Calcula os resultados financeiros com base nos dados de vendas seguindo normas contábeis."""
    results = {
        'receita_bruta': 0, 'receita_tributavel': 0, 'receita_nao_tributavel': 0,
        'impostos_sobre_vendas': 0, 'receita_liquida': 0, 'custo_produtos_vendidos': 0,
        'lucro_bruto': 0, 'margem_bruta': 0, 'despesas_administrativas': 0,
        'despesas_com_pessoal': 0, 'despesas_contabeis': custo_contadora,
        'total_despesas_operacionais': 0, 'lucro_operacional': 0, 'margem_operacional': 0,
        'lucro_antes_ir': 0, 'lucro_liquido': 0, 'margem_liquida': 0,
        'diferenca_tributavel_nao_tributavel': 0
    }
    
    if df.empty: 
        return results
    
    results['receita_bruta'] = df['Total'].sum()
    results['receita_tributavel'] = df['Cartão'].sum() + df['Pix'].sum()
    results['receita_nao_tributavel'] = df['Dinheiro'].sum()
    results['impostos_sobre_vendas'] = results['receita_tributavel'] * 0.06
    results['receita_liquida'] = results['receita_bruta'] - results['impostos_sobre_vendas']
    results['custo_produtos_vendidos'] = results['receita_bruta'] * (custo_fornecedores_percentual / 100)
    results['lucro_bruto'] = results['receita_liquida'] - results['custo_produtos_vendidos']
    
    if results['receita_liquida'] > 0:
        results['margem_bruta'] = (results['lucro_bruto'] / results['receita_liquida']) * 100
    
    results['despesas_com_pessoal'] = salario_minimo * 1.55
    results['despesas_contabeis'] = custo_contadora
    results['despesas_administrativas'] = 0
    results['total_despesas_operacionais'] = (
        results['despesas_com_pessoal'] + 
        results['despesas_contabeis'] + 
        results['despesas_administrativas']
    )
    
    results['lucro_operacional'] = results['lucro_bruto'] - results['total_despesas_operacionais']
    if results['receita_liquida'] > 0:
        results['margem_operacional'] = (results['lucro_operacional'] / results['receita_liquida']) * 100
    
    results['lucro_antes_ir'] = results['lucro_operacional']
    results['lucro_liquido'] = results['lucro_antes_ir']
    if results['receita_liquida'] > 0:
        results['margem_liquida'] = (results['lucro_liquido'] / results['receita_liquida']) * 100
    
    results['diferenca_tributavel_nao_tributavel'] = results['receita_nao_tributavel']
    
    return results

def create_dre_textual(resultados, df_processed, selected_anos_filter):
    """Cria uma apresentação textual do DRE no estilo tradicional contábil usando dados anuais."""
    def format_val(value):
        return f"{value:,.0f}".replace(",", ".")

    def calc_percent(value, base):
        if base == 0:
            return 0
        return (value / base) * 100

    # Determinar o ano para o DRE
    if selected_anos_filter and len(selected_anos_filter) == 1:
        ano_dre = selected_anos_filter[0]
    else:
        ano_dre = datetime.now().year

    # Filtrar dados APENAS por ano (ignorar filtro de mês)
    if not df_processed.empty and 'Ano' in df_processed.columns:
        df_ano = df_processed[df_processed['Ano'] == ano_dre].copy()
        
        # Recalcular resultados com dados do ano completo
        if not df_ano.empty:
            resultados_ano = calculate_financial_results(
                df_ano, 
                st.session_state.get('salario_tab4', 1550.0), 
                st.session_state.get('contadora_tab4', 316.0) * 12,
                st.session_state.get('fornecedores_tab4', 30.0)
            )
        else:
            resultados_ano = resultados
            st.warning(f"⚠️ Não há dados de vendas registrados para o ano {ano_dre}. O DRE abaixo pode refletir um período diferente.")
    else:
        resultados_ano = resultados

    # Cabeçalho centralizado
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 30px;">
        <h3 style="margin: 0; font-weight: normal;">DEMONSTRAÇÃO DO RESULTADO DO EXERCÍCIO</h3>
        <p style="margin: 5px 0; font-style: italic;">Clips Burger - Exercício {ano_dre}</p>
    </div>
    """, unsafe_allow_html=True)

    # Criar 2 colunas - descrição e valor
    col1, col2 = st.columns([6, 2])
    with col1:
        st.markdown("")
    with col2:
        st.markdown("**Em R$**")
    
    # RECEITA BRUTA
    col1, col2 = st.columns([6, 2])
    with col1:
        st.markdown("**RECEITA BRUTA**")
    with col2:
        st.markdown(f"**{format_val(resultados_ano['receita_bruta'])}**")
    
    # DEDUÇÕES
    col1, col2 = st.columns([6, 2])
    with col1:
        st.markdown("**(-) DEDUÇÕES**")
    with col2:
        st.markdown("")
    
    col1, col2 = st.columns([6, 2])
    with col1:
        st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;Simples Nacional")
    with col2:
        st.markdown(f"({format_val(resultados_ano['impostos_sobre_vendas'])})")
    
    # RECEITA LÍQUIDA
    col1, col2 = st.columns([6, 2])
    with col1:
        st.markdown("**RECEITA LÍQUIDA**")
    with col2:
        st.markdown(f"**{format_val(resultados_ano['receita_liquida'])}**")
    
    # CUSTO DOS PRODUTOS VENDIDOS
    col1, col2 = st.columns([6, 2])
    with col1:
        st.markdown("**(-) CUSTO DOS PRODUTOS VENDIDOS**")
    with col2:
        st.markdown(f"**({format_val(resultados_ano['custo_produtos_vendidos'])})**")
    
    # LUCRO BRUTO
    col1, col2 = st.columns([6, 2])
    with col1:
        st.markdown("**LUCRO BRUTO**")
    with col2:
        st.markdown(f"**{format_val(resultados_ano['lucro_bruto'])}**")
    
    # DESPESAS OPERACIONAIS
    col1, col2 = st.columns([6, 2])
    with col1:
        st.markdown("**(-) DESPESAS OPERACIONAIS**")
    with col2:
        st.markdown("")
    
    col1, col2 = st.columns([6, 2])
    with col1:
        st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;Despesas com Pessoal")
    with col2:
        st.markdown(f"({format_val(resultados_ano['despesas_com_pessoal'])})")
    
    col1, col2 = st.columns([6, 2])
    with col1:
        st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;Serviços Contábeis")
    with col2:
        st.markdown(f"({format_val(resultados_ano['despesas_contabeis'])})")
    
    # LUCRO OPERACIONAL
    col1, col2 = st.columns([6, 2])
    with col1:
        st.markdown("**LUCRO OPERACIONAL**")
    with col2:
        st.markdown(f"**{format_val(resultados_ano['lucro_operacional'])}**")
    
    # RESULTADO ANTES DO IMPOSTO DE RENDA
    col1, col2 = st.columns([6, 2])
    with col1:
        st.markdown("**LUCRO ANTES DO IMPOSTO DE RENDA**")
    with col2:
        st.markdown(f"**{format_val(resultados_ano['lucro_antes_ir'])}**")
    
    col1, col2 = st.columns([6, 2])
    with col1:
        st.markdown("**(-) Provisão para Imposto de Renda**")
    with col2:
        st.markdown("**-**")
    
    # RESULTADO LÍQUIDO - destacado
    col1, col2 = st.columns([6, 2])
    with col1:
        st.markdown("## **RESULTADO LÍQUIDO DO EXERCÍCIO**")
    with col2:
        st.markdown(f"## **{format_val(resultados_ano['lucro_liquido'])}**")
    
    # Nota explicativa
    st.info(f"📅 **Nota:** Este DRE apresenta os resultados consolidados do exercício {ano_dre}, independente do filtro de mês aplicado nas outras análises.")

def create_financial_dashboard_altair(resultados):
    """Dashboard financeiro com legenda corrigida."""
    financial_data = pd.DataFrame({
        'Categoria': [
            'Receita Bruta',
            'Impostos s/ Vendas',
            'Custo Produtos',
            'Despesas Pessoal',
            'Serviços Contábeis',
            'Lucro Líquido'
        ],
        'Valor': [
            resultados['receita_bruta'],
            -resultados['impostos_sobre_vendas'],
            -resultados['custo_produtos_vendidos'],
            -resultados['despesas_com_pessoal'],
            -resultados['despesas_contabeis'],
            resultados['lucro_liquido']
        ],
        'Tipo': [
            'Receita',
            'Dedução',
            'CPV',
            'Despesa',
            'Despesa',
            'Resultado'
        ]
    })
    
    chart = alt.Chart(financial_data).mark_bar(
        cornerRadiusTopRight=8,
        cornerRadiusBottomRight=8
    ).encode(
        x=alt.X(
            'Valor:Q',
            title='Valor (R$)',
            axis=alt.Axis(format=',.0f', labelFontSize=12)
        ),
        y=alt.Y(
            'Categoria:O',
            title=None,
            sort=financial_data['Categoria'].tolist(),
            axis=alt.Axis(labelFontSize=12)
        ),
        color=alt.Color(
            'Tipo:N',
            scale=alt.Scale(
                domain=['Receita', 'Dedução', 'CPV', 'Despesa', 'Resultado'],
                range=[CORES_MODO_ESCURO[1], CORES_MODO_ESCURO[3], CORES_MODO_ESCURO[2], CORES_MODO_ESCURO[4], CORES_MODO_ESCURO[0]]
            ),
            legend=None
        ),
        tooltip=[
            alt.Tooltip('Categoria:N', title='Categoria'),
            alt.Tooltip('Valor:Q', title='Valor (R$)', format=',.2f'),
            alt.Tooltip('Tipo:N', title='Tipo')
        ]
    ).properties(
        title=alt.TitleParams(
            text="Composição do Resultado Financeiro",
            fontSize=20,
            anchor='start'
        ),
        height=500,
        padding={'bottom': 100}
    ).configure_view(
        stroke=None
    ).configure(
        background='transparent'
    )
    
    return chart

def create_activity_heatmap(df_input):
    """Cria um gráfico de heatmap estilo GitHub para a atividade de vendas - IGNORA FILTRO DE MÊS."""
    if df_input.empty or 'Data' not in df_input.columns or 'Total' not in df_input.columns:
        st.info("Dados insuficientes para gerar o heatmap de atividade.")
        return None

    # MODIFICAÇÃO: Recarregar dados completos ignorando filtros
    df_completo = read_sales_data()
    if df_completo.empty:
        st.info("Sem dados disponíveis para o heatmap.")
        return None
    
    # Processar os dados completos
    df_completo = process_data(df_completo)
    
    df = df_completo.copy()
    df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
    df.dropna(subset=['Data'], inplace=True)
    
    if df.empty:
        st.info("Dados insuficientes após processamento para gerar o heatmap de atividade.")
        return None

    # Determinar o ano atual ou mais recente dos dados
    current_year = df['Data'].dt.year.max()
    df = df[df['Data'].dt.year == current_year]

    if df.empty:
        st.info(f"Sem dados para o ano {current_year} para gerar o heatmap.")
        return None

    # Obter o dia da semana do primeiro dia do ano (0=segunda, 6=domingo)
    first_day_of_year = pd.Timestamp(f'{current_year}-01-01')
    first_day_weekday = first_day_of_year.weekday()
    
    # Calcular quantos dias antes do 01/01 precisamos adicionar para começar na segunda
# --- CONTINUAÇÃO DO HEATMAP (completar a função) ---
    # Calcular quantos dias antes do 01/01 precisamos adicionar para começar na segunda-feira
    days_before = first_day_weekday
    
    # Criar range de datas começando na segunda-feira da semana do 01/01
    start_date = first_day_of_year - pd.Timedelta(days=days_before)
    end_date = datetime(current_year, 12, 31)
    
    # Garantir que terminamos no domingo da última semana
    days_after = 6 - end_date.weekday()
    if days_after < 6:
        end_date = end_date + pd.Timedelta(days=days_after)
    
    all_dates = pd.date_range(start=start_date, end=end_date, freq='D')

    # DataFrame com todas as datas (incluindo dias antes do 01/01)
    full_df = pd.DataFrame({'Data': all_dates})
    
    # Marcar quais datas são do ano atual
    full_df['is_current_year'] = full_df['Data'].dt.year == current_year
    
    # Verificar e mapear nomes de colunas corretos
    possible_cartao_names = ['Cartao', 'Cartão', 'cartao', 'cartão', 'CARTAO', 'CARTÃO']
    cartao_col = None
    for col_name in possible_cartao_names:
        if col_name in df.columns:
            cartao_col = col_name
            break
    
    possible_dinheiro_names = ['Dinheiro', 'dinheiro', 'DINHEIRO']
    dinheiro_col = None
    for col_name in possible_dinheiro_names:
        if col_name in df.columns:
            dinheiro_col = col_name
            break
    
    possible_pix_names = ['Pix', 'PIX', 'pix']
    pix_col = None
    for col_name in possible_pix_names:
        if col_name in df.columns:
            pix_col = col_name
            break

    # Certificar que as colunas existem antes de mergear
    cols_to_merge = ['Data', 'Total']
    if cartao_col:
        cols_to_merge.append(cartao_col)
    if dinheiro_col:
        cols_to_merge.append(dinheiro_col)
    if pix_col:
        cols_to_merge.append(pix_col)
    
    cols_present = [col for col in cols_to_merge if col in df.columns]
    full_df = full_df.merge(df[cols_present], on='Data', how='left')
    
    # Preencher NaNs e padronizar nomes das colunas
    if cartao_col and cartao_col in full_df.columns:
        full_df['Cartao'] = full_df[cartao_col].fillna(0)
    else:
        full_df['Cartao'] = 0
    
    if dinheiro_col and dinheiro_col in full_df.columns:
        full_df['Dinheiro'] = full_df[dinheiro_col].fillna(0)
    else:
        full_df['Dinheiro'] = 0
    
    if pix_col and pix_col in full_df.columns:
        full_df['Pix'] = full_df[pix_col].fillna(0)
    else:
        full_df['Pix'] = 0
    
    # Garantir que Total existe
    if 'Total' not in full_df.columns:
        full_df['Total'] = 0
    else:
        full_df['Total'] = full_df['Total'].fillna(0)
    
    # Para dias que não são do ano atual, definir como None apenas para visualização
    full_df['display_total'] = full_df['Total'].copy()
    mask_not_current_year = ~full_df['is_current_year']
    full_df.loc[mask_not_current_year, 'display_total'] = None

    # Mapear os nomes dos dias (ordem fixa)
    full_df['day_of_week'] = full_df['Data'].dt.weekday
    day_name_map = {0: 'Seg', 1: 'Ter', 2: 'Qua', 3: 'Qui', 4: 'Sex', 5: 'Sáb', 6: 'Dom'}
    full_df['day_display_name'] = full_df['day_of_week'].map(day_name_map)
    
    # Ordem fixa dos dias para exibição (sempre a mesma)
    day_display_names = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
    
    full_df['week'] = full_df['Data'].dt.isocalendar().week
    full_df['month'] = full_df['Data'].dt.month
    full_df['month_name'] = full_df['Data'].dt.strftime('%b')

    # Recalcular week baseado na primeira data (que agora é uma segunda-feira)
    full_df['week_corrected'] = ((full_df['Data'] - start_date).dt.days // 7)
    
    # Encontrar a primeira semana de cada mês para os rótulos (apenas para meses do ano atual)
    month_labels = full_df[full_df['is_current_year']].groupby('month').agg(
        week_corrected=('week_corrected', 'min'),
        month_name=('month_name', 'first')
    ).reset_index()

    # Labels dos meses
    months_chart = alt.Chart(month_labels).mark_text(
        align='center',
        baseline='bottom',
        fontSize=12,
        dy=-1,
        dx=-30,
        color='#A9A9A9'
    ).encode(
        x=alt.X('week_corrected:O', axis=None),
        text='month_name:N'
    )

    # Construir tooltip dinamicamente baseado nas colunas disponíveis
    tooltip_fields = [
        alt.Tooltip('Data:T', title='Data', format='%d/%m/%Y'),
        alt.Tooltip('day_display_name:N', title='Dia'),
        alt.Tooltip('Total:Q', title='Total Vendas (R$)', format=',.2f')
    ]
    
    # Adicionar campos de pagamento apenas se existirem
    if 'Cartao' in full_df.columns:
        tooltip_fields.append(alt.Tooltip('Cartao:Q', title='Cartão (R$)', format=',.2f'))
    if 'Dinheiro' in full_df.columns:
        tooltip_fields.append(alt.Tooltip('Dinheiro:Q', title='Dinheiro (R$)', format=',.2f'))
    if 'Pix' in full_df.columns:
        tooltip_fields.append(alt.Tooltip('Pix:Q', title='Pix (R$)', format=',.2f'))

    # Gráfico principal (heatmap)
    heatmap = alt.Chart(full_df).mark_rect(
        stroke='#ffffff',
        strokeWidth=2,
        cornerRadius=0.5
    ).encode(
        x=alt.X('week_corrected:O',
                title=None, 
                axis=None),
        y=alt.Y('day_display_name:N', 
                sort=day_display_names,
                title=None,
                axis=alt.Axis(labelAngle=0, labelFontSize=12, ticks=False, domain=False, grid=False, labelColor='#A9A9A9')),
        color=alt.Color('display_total:Q',
            scale=alt.Scale(
                range=['#f0f0f0', '#9be9a8', '#40c463', '#30a14e', '#216e39'],
                type='threshold',
                domain=[0.01, 1500, 2500, 3500]
            ),
            legend=None),
        tooltip=tooltip_fields
    ).properties(
        height=250
    )

    # Combinar gráfico final
    final_chart = alt.vconcat(
        months_chart,
        heatmap,
        spacing=1
    ).configure_view(
        strokeWidth=0
    ).configure_concat(
        spacing=5
    ).properties(
        title=alt.TitleParams(
            text=f'Atividade de Vendas - {current_year}',
            fontSize=18,
            anchor='start',
            color='white',
            dy=-10
        )
    ).configure(
        background='transparent'
    )

    return final_chart

# Função para formatar valores em moeda brasileira
def format_brl(value):
    return f"R$ {value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")

# Lista de fornecedores por categoria (CORRIGIDA)
FORNECEDORES_CATEGORIAS = {
    "FRIOS": ["MMP Frios"],
    "BEBIDAS": ["Praca da Biblia"],
    "HAMBURGER": ["Max"],
    "SUPERMERCADO": ["Nova Jerusalem", "Raio"],
    "PAO": ["Di Roma"]
}

# --- Interface Principal da Aplicação ---
def main():
    # Carregar dados
    df_raw = read_sales_data()
    df_processed = process_data(df_raw)
    
    # --- NOVA LOGO ANIMADA ---
    LOGO_URL = "https://raw.githubusercontent.com/lucasricardocs/clips_dashboard/main/logo.png"
    st.markdown(f"""
    <div class="logo-fire-container">
        <img src="{LOGO_URL}" class="fire-logo" alt="Clips Burger Logo">
        <div class="fire-container">
            <div class="flame flame-red"></div>
            <div class="flame flame-orange"></div>
            <div class="flame flame-yellow"></div>
            <div class="flame flame-white"></div>
            <!-- Partículas -->
            <div class="fire-particle small"></div>
            <div class="fire-particle medium"></div>
            <div class="fire-particle large"></div>
            <div class="fire-particle small"></div>
            <div class="fire-particle medium"></div>
            <div class="fire-particle large"></div>
            <div class="fire-particle small"></div>
            <div class="fire-particle medium"></div>
            <div class="fire-particle large"></div>
            <div class="fire-particle small"></div>
            <div class="fire-particle medium"></div>
            <div class="fire-particle large"></div>
            <div class="fire-particle small"></div>
            <div class="fire-particle medium"></div>
            <div class="fire-particle large"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Criar as tabs (MODIFICADO PARA INCLUIR A TAB DE COMPRAS)
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Registrar Venda", "🔎 Análise Detalhada", "💡 Estatísticas", "📊 Análise Contábil", "🛒 Gestão de Compras"])

    with tab1:
        st.header("📝 Registrar Nova Venda")
        
        # Inputs FORA do form para atualização em tempo real
        data_input = st.date_input("📅 Data da Venda", value=datetime.now(), format="DD/MM/YYYY")
        
        col1, col2, col3 = st.columns(3)
        with col1: 
            cartao_input = st.number_input(
                "💳 Cartão (R$)", 
                min_value=0.0, 
                value=None,
                format="%.2f", 
                key="cartao_venda",
                placeholder="Digite o valor..."
            )
        with col2: 
            dinheiro_input = st.number_input(
                "💵 Dinheiro (R$)", 
                min_value=0.0, 
                value=None,
                format="%.2f", 
                key="dinheiro_venda",
                placeholder="Digite o valor..."
            )
        with col3: 
            pix_input = st.number_input(
                "📱 PIX (R$)", 
                min_value=0.0, 
                value=None,
                format="%.2f", 
                key="pix_venda",
                placeholder="Digite o valor..."
            )
        
        # Calcular total em tempo real (fora do form)
        cartao_val = cartao_input if cartao_input is not None else 0.0
        dinheiro_val = dinheiro_input if dinheiro_input is not None else 0.0
        pix_val = pix_input if pix_input is not None else 0.0
        total_venda_form = cartao_val + dinheiro_val + pix_val
        
        # Display do total em tempo real
        st.markdown(f"""
        <div style="text-align: center; padding: 0.7rem 1rem; background: linear-gradient(90deg, #4c78a8, #54a24b); border-radius: 10px; color: white; margin: 0.5rem 0; box-shadow: 0 4px 12px rgba(0,0,0,0.2); height: 3rem; display: flex; align-items: center; justify-content: center;">
            <div>
                <span style="font-size: 1.8rem; margin-right: 0.5rem; text-shadow: 1px 1px 3px rgba(0,0,0,0.3);">💰</span>
                <span style="font-size: 2.2rem; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.3);">Total: {format_brl(total_venda_form)}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Botão de registrar (fora do form)
        if st.button("✅ Registrar Venda", type="primary", use_container_width=True):
            if total_venda_form > 0:
                formatted_date = data_input.strftime("%d/%m/%Y")
                worksheet_obj = get_worksheet()
                if worksheet_obj and add_data_to_sheet(formatted_date, cartao_val, dinheiro_val, pix_val, worksheet_obj):
                    # Limpar apenas o cache de dados, não todos
                    read_sales_data.clear()
                    st.success("✅ Venda registrada!")
                    time.sleep(1)
                    st.rerun()
                elif not worksheet_obj: 
                    st.error("❌ Falha ao conectar à planilha. Venda não registrada.")
            else: 
                st.warning("⚠️ O valor total da venda deve ser maior que zero.")
    
    # --- SIDEBAR COM FILTROS ---
    selected_anos_filter, selected_meses_filter = [], []
    
    with st.sidebar:
        st.header("🔍 Filtros de Período")
        st.markdown("---")
        
        # Filtros sempre visíveis
        if not df_processed.empty and 'Ano' in df_processed.columns and not df_processed['Ano'].isnull().all():
            anos_disponiveis = sorted(df_processed['Ano'].dropna().unique().astype(int), reverse=True)
            if anos_disponiveis:
                default_ano = [datetime.now().year] if datetime.now().year in anos_disponiveis else [anos_disponiveis[0]] if anos_disponiveis else []
                selected_anos_filter = st.multiselect("📅 Ano(s):", options=anos_disponiveis, default=default_ano)
                
                if selected_anos_filter:
                    df_para_filtro_mes = df_processed[df_processed['Ano'].isin(selected_anos_filter)]
                    if not df_para_filtro_mes.empty and 'Mês' in df_para_filtro_mes.columns and not df_para_filtro_mes['Mês'].isnull().all():
                        meses_numeros_disponiveis = sorted(df_para_filtro_mes['Mês'].dropna().unique().astype(int))
                        meses_opcoes_dict = {m_num: meses_ordem[m_num-1] for m_num in meses_numeros_disponiveis if 1 <= m_num <= 12}
                        meses_opcoes_display = [f"{m_num} - {m_nome}" for m_num, m_nome in meses_opcoes_dict.items()]
                        
                        # NOVA LÓGICA: Sempre priorizar o mês atual quando o ano atual está selecionado
                        default_meses_selecionados = []
                        ano_atual = datetime.now().year
                        mes_atual = datetime.now().month
                        
                        if ano_atual in selected_anos_filter:
                            mes_atual_str = f"{mes_atual} - {meses_ordem[mes_atual-1]}"
                            
                            # Adicionar mês atual mesmo sem dados
                            if mes_atual_str not in meses_opcoes_display:
                                meses_opcoes_display.append(mes_atual_str)
                                meses_opcoes_display = sorted(meses_opcoes_display, key=lambda x: int(x.split(" - ")[0]))
                            
                            default_meses_selecionados = [mes_atual_str]
                        else:
                            default_meses_selecionados = meses_opcoes_display
                            
                        selected_meses_str = st.multiselect(
                            "📆 Mês(es):", 
                            options=meses_opcoes_display, 
                            default=default_meses_selecionados,
                            help="💡 O mês atual é selecionado automaticamente. Você pode alterar conforme necessário."
                        )
                        selected_meses_filter = [int(m.split(" - ")[0]) for m in selected_meses_str]
            else: 
                st.info("📊 Nenhum ano disponível para filtro.")
        else: 
            st.info("📊 Não há dados processados para aplicar filtros.")
    
    # Aplicar filtros
    df_filtered = df_processed.copy()
    if not df_filtered.empty:
        if selected_anos_filter and 'Ano' in df_filtered.columns: 
            df_filtered = df_filtered[df_filtered['Ano'].isin(selected_anos_filter)]
        if selected_meses_filter and 'Mês' in df_filtered.columns: 
            df_filtered = df_filtered[df_filtered['Mês'].isin(selected_meses_filter)]
    
    # Mostrar informações dos filtros aplicados na sidebar
    if not df_filtered.empty:
        total_registros_filtrados = len(df_filtered)
        total_faturamento_filtrado = df_filtered['Total'].sum()
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📈 Resumo dos Filtros Aplicados")
        st.sidebar.metric("Registros Filtrados", total_registros_filtrados)
        st.sidebar.metric("Faturamento Filtrado", format_brl(total_faturamento_filtrado))
    elif not df_processed.empty:
        st.sidebar.markdown("---")
        st.sidebar.info("Nenhum registro corresponde aos filtros selecionados.")
    
    with tab2:
        st.header("🔎 Análise Detalhada de Vendas")
        if not df_filtered.empty and 'DataFormatada' in df_filtered.columns:
            st.subheader("🧾 Tabela de Vendas Filtradas")
            cols_to_display_tab2 = ['DataFormatada', 'DiaSemana', 'DiaDoMes', 'Cartão', 'Dinheiro', 'Pix', 'Total']
            cols_existentes_tab2 = [col for col in cols_to_display_tab2 if col in df_filtered.columns]
            
            if cols_existentes_tab2: 
                # Ordenar pela data mais recente primeiro
                df_display_tab2 = df_filtered.sort_values(by='Data', ascending=False)
                st.dataframe(df_display_tab2[cols_existentes_tab2], use_container_width=True, height=600, hide_index=True)
            else: 
                st.info("Colunas necessárias para a tabela de dados filtrados não estão disponíveis.")
                
    with tab3:
        st.header("💡 Estatísticas e Tendências de Vendas")
        if not df_filtered.empty and 'Total' in df_filtered.columns and not df_filtered['Total'].isnull().all():
            st.subheader("💰 Resumo Financeiro Agregado")
            total_registros = len(df_filtered)
            total_faturamento = df_filtered['Total'].sum()
            media_por_registro = df_filtered['Total'].mean() if total_registros > 0 else 0
            maior_venda_diaria = df_filtered['Total'].max() if total_registros > 0 else 0
            menor_venda_diaria = df_filtered[df_filtered['Total'] > 0]['Total'].min() if not df_filtered[df_filtered['Total'] > 0].empty else 0
            
            # Layout em colunas para melhor aproveitamento do espaço
            col_metrics1, col_metrics2, col_metrics3 = st.columns(3)
    
            with col_metrics1:
                st.metric("🔢 Total de Registros", f"{total_registros}")
                st.metric("⬆️ Maior Venda Diária", format_brl(maior_venda_diaria))
    
            with col_metrics2:
                st.metric("💵 Faturamento Total", format_brl(total_faturamento))
                st.metric("⬇️ Menor Venda Diária (>0)", format_brl(menor_venda_diaria))
    
            with col_metrics3:
                st.metric("📈 Média por Registro", format_brl(media_por_registro))
            
            # --- INTEGRAÇÃO DO HEATMAP --- 
            st.subheader("📅 Heatmap de Atividade Anual")
            heatmap_chart = create_activity_heatmap(df_filtered)
            if heatmap_chart:
                st.altair_chart(heatmap_chart, use_container_width=True)
            else:
                st.info("Não foi possível gerar o heatmap de atividade para o período/ano selecionado.")
            
            st.subheader("Gráfico de Área Acumulado")
            cumulative_chart = create_cumulative_area_chart(df_filtered)
            if cumulative_chart:
                st.altair_chart(cumulative_chart, use_container_width=True)
            else:
                st.info("Sem dados suficientes para o gráfico de evolução acumulada.")
            
            # Seção de métodos de pagamento com cards lado a lado
            st.subheader("💳 Métodos de Pagamento (Visão Geral)")
            cartao_total = df_filtered['Cartão'].sum() if 'Cartão' in df_filtered else 0
            dinheiro_total = df_filtered['Dinheiro'].sum() if 'Dinheiro' in df_filtered else 0
            pix_total = df_filtered['Pix'].sum() if 'Pix' in df_filtered else 0
            total_pagamentos_geral = cartao_total + dinheiro_total + pix_total
    
            if total_pagamentos_geral > 0:
                cartao_pct = (cartao_total / total_pagamentos_geral * 100)
                dinheiro_pct = (dinheiro_total / total_pagamentos_geral * 100)
                pix_pct = (pix_total / total_pagamentos_geral * 100)
                
                # Layout sempre em 3 colunas lado a lado
                payment_cols = st.columns(3)
                
                with payment_cols[0]:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #4c78a8, #5a8bb8); border-radius: 10px; color: white; margin-bottom: 1rem;">
                        <h3 style="margin: 0; font-size: 1.5rem;">💳 Cartão</h3>
                        <h2 style="margin: 0.5rem 0; font-size: 1.8rem;">{format_brl(cartao_total)}</h2>
                        <p style="margin: 0; font-size: 1.2rem; opacity: 0.9;">{cartao_pct:.1f}% do total</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with payment_cols[1]:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #54a24b, #64b25b); border-radius: 10px; color: white; margin-bottom: 1rem;">
                        <h3 style="margin: 0; font-size: 1.5rem;">💵 Dinheiro</h3>
                        <h2 style="margin: 0.5rem 0; font-size: 1.8rem;">{format_brl(dinheiro_total)}</h2>
                        <p style="margin: 0; font-size: 1.2rem; opacity: 0.9;">{dinheiro_pct:.1f}% do total</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with payment_cols[2]:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #f58518, #ff9528); border-radius: 10px; color: white; margin-bottom: 1rem;">
                        <h3 style="margin: 0; font-size: 1.5rem;">📱 PIX</h3>
                        <h2 style="margin: 0.5rem 0; font-size: 1.8rem;">{format_brl(pix_total)}</h2>
                        <p style="margin: 0; font-size: 1.2rem; opacity: 0.9;">{pix_pct:.1f}% do total</p>
                    </div>
                    """, unsafe_allow_html=True)
            else: 
                st.info("Sem dados de pagamento para exibir o resumo nesta seção.")
            
            # Gráficos lado a lado - 2/3 para análise de dias da semana, 1/3 para radial
            col_chart1, col_chart2 = st.columns([2, 1])
            
            with col_chart1:
                # Análise melhorada de dias da semana (2/3 do espaço)
                weekday_chart, best_day = create_enhanced_weekday_analysis(df_filtered)
                if weekday_chart:
                    st.altair_chart(weekday_chart, use_container_width=True)
                    
                    # Análise detalhada dos dias da semana
                    if not df_filtered.empty and 'DiaSemana' in df_filtered.columns:
                        df_weekday_analysis = df_filtered.copy()
                        df_weekday_analysis['Total'] = pd.to_numeric(df_weekday_analysis['Total'], errors='coerce')
                        df_weekday_analysis = df_weekday_analysis.dropna(subset=['Total', 'DiaSemana'])
                        
                        if not df_weekday_analysis.empty:
                            # Calcular médias por dia da semana (excluindo domingo)
                            dias_trabalho = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado"]
                            df_trabalho = df_weekday_analysis[df_weekday_analysis['DiaSemana'].isin(dias_trabalho)]
                            
                            if not df_trabalho.empty:
                                medias_por_dia = df_trabalho.groupby('DiaSemana', observed=True)['Total'].agg(['mean', 'count']).round(2)
                                medias_por_dia = medias_por_dia.reindex([d for d in dias_trabalho if d in medias_por_dia.index])
                                medias_por_dia = medias_por_dia.sort_values('mean', ascending=False)
                else:
                    st.info("Gráfico de análise de dias da semana indisponível.")
            
            with col_chart2:
                # Gráfico radial (1/3 do espaço)
                radial_chart = create_radial_plot(df_filtered)
                if radial_chart:
                    st.altair_chart(radial_chart, use_container_width=True)
                else:
                    st.info("Gráfico radial de pagamentos indisponível.")
    
            # Gráfico de vendas diárias movido para baixo (largura completa)
            daily_chart = create_advanced_daily_sales_chart(df_filtered)
            if daily_chart:
                st.altair_chart(daily_chart, use_container_width=True)
            else:
                st.info("Gráfico de vendas diárias indisponível.")
            
            st.subheader("📊 Ranking dos Dias da Semana (Seg-Sáb)")
            
            # Criar colunas para o ranking
            col_ranking1, col_ranking2 = st.columns(2)
            
            with col_ranking1:
                st.markdown("### 🏆 **Melhores Dias**")
                if len(medias_por_dia) >= 1:
                    primeiro = medias_por_dia.index[0]
                    st.success(f"🥇 **1º lugar:** {primeiro}")
                    st.write(f"   Média: {format_brl(medias_por_dia.loc[primeiro, 'mean'])} ({int(medias_por_dia.loc[primeiro, 'count'])} dias)")
                
                if len(medias_por_dia) >= 2:
                    segundo = medias_por_dia.index[1]
                    st.info(f"🥈 **2º lugar:** {segundo}")
                    st.write(f"   Média: {format_brl(medias_por_dia.loc[segundo, 'mean'])} ({int(medias_por_dia.loc[segundo, 'count'])} dias)")
            
            with col_ranking2:
                st.markdown("### 📉 **Piores Dias**")
                if len(medias_por_dia) >= 2:
                    penultimo_idx = -2 if len(medias_por_dia) > 1 else -1
                    penultimo = medias_por_dia.index[penultimo_idx]
                    st.warning(f"📊 **Penúltimo:** {penultimo}")
                    st.write(f"   Média: {format_brl(medias_por_dia.loc[penultimo, 'mean'])} ({int(medias_por_dia.loc[penultimo, 'count'])} dias)")
                
                if len(medias_por_dia) >= 1:
                    ultimo = medias_por_dia.index[-1]
                    st.error(f"🔻 **Último lugar:** {ultimo}")
                    st.write(f"   Média: {format_brl(medias_por_dia.loc[ultimo, 'mean'])} ({int(medias_por_dia.loc[ultimo, 'count'])} dias)")

            # Análise de frequência de trabalho
            st.subheader("📅 Análise de Frequência de Trabalho")
            
            # Calcular dias do período filtrado
            if not df_filtered.empty and 'Data' in df_filtered.columns:
                data_inicio = df_filtered['Data'].min()
                data_fim = df_filtered['Data'].max()
                
                if pd.notna(data_inicio) and pd.notna(data_fim):
                    # Calcular total de dias no período
                    total_dias_periodo = (data_fim - data_inicio).days + 1
                    
                    # Calcular domingos no período
                    domingos_periodo = 0
                    data_atual = data_inicio
                    while data_atual <= data_fim:
                        if data_atual.weekday() == 6:  # Domingo = 6
                            domingos_periodo += 1
                        data_atual += timedelta(days=1)
                    
                    # Dias úteis esperados (excluindo domingos)
                    dias_uteis_esperados = total_dias_periodo - domingos_periodo
                    
                    # Dias efetivamente trabalhados (registros únicos por data)
                    dias_trabalhados = df_filtered['Data'].nunique()
                    
                    # Dias de falta
                    dias_falta = max(0, dias_uteis_esperados - dias_trabalhados)
                    
                    # Exibir métricas
                    col_freq1, col_freq2, col_freq3, col_freq4 = st.columns(4)
                    
                    with col_freq1:
                        st.metric(
                            "📅 Período Analisado",
                            f"{total_dias_periodo} dias",
                            help=f"De {data_inicio.strftime('%d/%m/%Y')} até {data_fim.strftime('%d/%m/%Y')}"
                        )
                    
                    with col_freq2:
                        st.metric(
                            "🏢 Dias Trabalhados",
                            f"{dias_trabalhados} dias",
                            help="Dias com registro de vendas"
                        )
                    
                    with col_freq3:
                        st.metric(
                            "🏖️ Domingos (Folga)",
                            f"{domingos_periodo} dias",
                            help="Domingos no período (não trabalhamos)"
                        )
                    
                    with col_freq4:
                        if dias_falta > 0:
                            st.metric(
                                "❌ Dias de Falta",
                                f"{dias_falta} dias",
                                help="Dias úteis sem registro de vendas",
                                delta=f"-{dias_falta}",
                                delta_color="inverse"
                            )
                        else:
                            st.metric(
                                "✅ Frequência",
                                "100%",
                                help="Todos os dias úteis trabalhados!"
                            )
                    
                    # Calcular taxa de frequência
                    if dias_uteis_esperados > 0:
                        taxa_frequencia = (dias_trabalhados / dias_uteis_esperados) * 100
                        
                        if taxa_frequencia >= 95:
                            st.success(f"🎯 **Excelente frequência:** {taxa_frequencia:.1f}% dos dias úteis trabalhados!")
                        elif taxa_frequencia >= 80:
                            st.info(f"👍 **Boa frequência:** {taxa_frequencia:.1f}% dos dias úteis trabalhados")
                        else:
                            st.warning(f"⚠️ **Atenção à frequência:** {taxa_frequencia:.1f}% dos dias úteis trabalhados")
                else:
                    st.info("Não foi possível calcular a frequência (sem dias úteis no período?).")
            else:
                st.info("📊 Dados insuficientes para calcular a análise por dia da semana.")
            
            sales_histogram_chart = create_sales_histogram(df_filtered)
            if sales_histogram_chart: 
                st.altair_chart(sales_histogram_chart, use_container_width=True)
            else: 
                st.info("Dados insuficientes para o Histograma de Vendas.")
        else:
            if df_processed.empty and df_raw.empty and get_worksheet() is None: 
                st.warning("Não foi possível carregar os dados da planilha.")
            elif df_processed.empty: 
                st.info("Não há dados processados para exibir estatísticas.")
            elif df_filtered.empty: 
                st.info("Nenhum dado corresponde aos filtros para exibir estatísticas.")
            else: 
                st.info("Não há dados de 'Total' para exibir nas Estatísticas.")
    
    # --- TAB4: ANÁLISE CONTÁBIL COMPLETA ---
    with tab4:
        st.header("📊 Análise Contábil e Financeira Detalhada")
        
        st.markdown("""
        ### 📋 **Sobre esta Análise**
        
        Esta análise segue as **normas contábeis brasileiras** com estrutura de DRE conforme:
        - **Lei 6.404/76** (Lei das S.A.) | **NBC TG 26** (Apresentação das Demonstrações Contábeis)
        - **Regime Tributário:** Simples Nacional (6% sobre receita tributável)
        - **Metodologia de Margens:** Margem Bruta = (Lucro Bruto ÷ Receita Líquida) × 100
        """)
        
        # Parâmetros Financeiros
        with st.container(border=True):
            st.subheader("⚙️ Parâmetros para Simulação Contábil")
            
            col_param1, col_param2, col_param3 = st.columns(3)
            with col_param1:
                salario_minimo_input = st.number_input(
                    "💼 Salário Base Funcionário (R$)",
                    min_value=0.0, value=st.session_state.get('salario_tab4', 1550.0), format="%.2f",
                    help="Salário base do funcionário. Os encargos (55%) serão calculados automaticamente.",
                    key="salario_tab4"
                )
            with col_param2:
                custo_contadora_input = st.number_input(
                    "📋 Honorários Contábeis Mensais (R$)",
                    min_value=0.0, value=st.session_state.get('contadora_tab4', 316.0), format="%.2f",
                    help="Valor mensal pago pelos serviços contábeis.",
                    key="contadora_tab4"
                )
            with col_param3:
                custo_fornecedores_percentual = st.number_input(
                    "📦 Custo dos Produtos (% da Receita Bruta)",
                    min_value=0.0, max_value=100.0, value=st.session_state.get('fornecedores_tab4', 30.0), format="%.1f",
                    help="Percentual da receita bruta destinado à compra de produtos.",
                    key="fornecedores_tab4"
                )
    
        if df_filtered.empty or 'Total' not in df_filtered.columns:
            st.warning("📊 **Não há dados suficientes para análise contábil.** Ajuste os filtros ou registre vendas.")
        else:
            # Calcular resultados financeiros para o período filtrado
            resultados_filtrados = calculate_financial_results(
                df_filtered, 
                salario_minimo_input, 
                custo_contadora_input,
                custo_fornecedores_percentual
            )
    
            # === DRE TEXTUAL (Anual) ===
            with st.container(border=True):
                create_dre_textual(resultados_filtrados, df_processed, selected_anos_filter)
    
            # === DASHBOARD VISUAL (Período Filtrado) ===
            financial_dashboard = create_financial_dashboard_altair(resultados_filtrados)
            if financial_dashboard:
                st.altair_chart(financial_dashboard, use_container_width=True)
    
            # === ANÁLISE DE MARGENS (Período Filtrado) ===
            with st.container(border=True):
                st.subheader("📈 Análise de Margens e Indicadores (Período Filtrado)")
                
                col_margin1, col_margin2, col_margin3 = st.columns(3)
                
                with col_margin1:
                    st.metric(
                        "📊 Margem Bruta",
                        f"{resultados_filtrados['margem_bruta']:.2f}%",
                        help="(Lucro Bruto / Receita Líquida) * 100"
                    )
                    st.metric(
                        "🏛️ Carga Tributária Efetiva",
                        f"{(resultados_filtrados['impostos_sobre_vendas'] / resultados_filtrados['receita_bruta'] * 100) if resultados_filtrados['receita_bruta'] > 0 else 0:.2f}%",
                        help="(Impostos / Receita Bruta) * 100"
                    )
                
                with col_margin2:
                    st.metric(
                        "💼 Margem Operacional",
                        f"{resultados_filtrados['margem_operacional']:.2f}%",
                        help="(Lucro Operacional / Receita Líquida) * 100"
                    )
                    st.metric(
                        "👥 Custo de Pessoal (% Receita)",
                        f"{(resultados_filtrados['despesas_com_pessoal'] / resultados_filtrados['receita_bruta'] * 100) if resultados_filtrados['receita_bruta'] > 0 else 0:.2f}%",
                        help="(Desp. Pessoal / Receita Bruta) * 100"
                    )
                
                with col_margin3:
                    st.metric(
                        "💰 Margem Líquida",
                        f"{resultados_filtrados['margem_liquida']:.2f}%",
                        help="(Lucro Líquido / Receita Líquida) * 100"
                    )
                    st.metric(
                        "📦 Custo dos Produtos (% Receita)",
                        f"{(resultados_filtrados['custo_produtos_vendidos'] / resultados_filtrados['receita_bruta'] * 100) if resultados_filtrados['receita_bruta'] > 0 else 0:.2f}%",
                        help="(CPV / Receita Bruta) * 100"
                    )
    
            # === RESUMO EXECUTIVO (Período Filtrado) ===
            with st.container(border=True):
                st.subheader("📋 Resumo Executivo (Período Filtrado)")
                
                col_exec1, col_exec2 = st.columns(2)
                
                with col_exec1:
                    st.markdown("**💰 Receitas:**")
                    st.write(f"• Receita Bruta: {format_brl(resultados_filtrados['receita_bruta'])}")
                    st.write(f"• Receita Líquida: {format_brl(resultados_filtrados['receita_liquida'])}")
                    st.write(f"• Receita Tributável: {format_brl(resultados_filtrados['receita_tributavel'])}")
                    st.write(f"• Receita Não Tributável: {format_brl(resultados_filtrados['receita_nao_tributavel'])}")
                    
                    st.markdown("**📊 Resultados:**")
                    st.write(f"• Lucro Bruto: {format_brl(resultados_filtrados['lucro_bruto'])}")
                    st.write(f"• Lucro Operacional: {format_brl(resultados_filtrados['lucro_operacional'])}")
                    st.write(f"• Lucro Líquido: {format_brl(resultados_filtrados['lucro_liquido'])}")
                
                with col_exec2:
                    st.markdown("**💸 Custos e Despesas:**")
                    st.write(f"• Impostos s/ Vendas: {format_brl(resultados_filtrados['impostos_sobre_vendas'])}")
                    st.write(f"• Custo dos Produtos: {format_brl(resultados_filtrados['custo_produtos_vendidos'])}")
                    st.write(f"• Despesas com Pessoal: {format_brl(resultados_filtrados['despesas_com_pessoal'])} (Ref. período)")
                    st.write(f"• Serviços Contábeis: {format_brl(resultados_filtrados['despesas_contabeis'])} (Ref. período)")
                    
                    st.markdown("**🎯 Indicadores-Chave:**")
                    if resultados_filtrados['margem_bruta'] >= 50:
                        st.success(f"✅ Margem Bruta Saudável: {resultados_filtrados['margem_bruta']:.1f}% (Período)")
                    elif resultados_filtrados['margem_bruta'] >= 30:
                        st.warning(f"⚠️ Margem Bruta Moderada: {resultados_filtrados['margem_bruta']:.1f}% (Período)")
                    else:
                        st.error(f"❌ Margem Bruta Baixa: {resultados_filtrados['margem_bruta']:.1f}% (Período)")
                    
                    if resultados_filtrados['lucro_liquido'] > 0:
                        st.success(f"✅ Resultado Positivo: {format_brl(resultados_filtrados['lucro_liquido'])} (Período)")
                    else:
                        st.error(f"❌ Resultado Negativo: {format_brl(resultados_filtrados['lucro_liquido'])} (Período)")
    
            # Nota final
            st.info("""
            💡 **Nota Importante:** A DRE Textual acima é sempre anual. As demais análises (Gráfico Financeiro, Margens, Resumo Executivo) referem-se ao **período selecionado nos filtros**. 
            Para decisões estratégicas, consulte sempre um contador qualificado.
            """)

    # --- TAB5: GESTÃO DE COMPRAS COM MÚLTIPLOS PRODUTOS (CORRIGIDA) ---
    # --- TAB5: GESTÃO DE COMPRAS CORRIGIDA ---
    with tab5:
        st.header("🛒 Gestão de Compras")
        
        # Criar sub-tabs para organizar melhor
        subtab1, subtab2, subtab3 = st.tabs(["📝 Registrar Compras", "📋 Lista de Compras", "📊 Análise de Compras"])
        
        with subtab1:
            st.subheader("📝 Registrar Múltiplas Compras")
            
            # Data da compra
            data_compra = st.date_input("📅 Data da Compra", value=datetime.now(), format="DD/MM/YYYY")
            
            # Inicializar session state para produtos (CORRIGIDO)
            if 'produtos_compra' not in st.session_state:
                st.session_state.produtos_compra = [{'produto': '', 'quantidade': 0.0, 'valor': 0.0, 'categoria': '', 'fornecedor': ''}]
            
            st.markdown("### 🛍️ **Lista de Produtos para Compra**")
            st.markdown("*Preencha os dados de cada produto que você está comprando:*")
            
            # Container para os produtos
            total_geral = 0.0
            produtos_validos = []
            
            for i, produto_data in enumerate(st.session_state.produtos_compra):
                # Card visual para cada produto
                st.markdown(f"""
                <div style="background: rgba(255, 255, 255, 0.05); padding: 1rem; border-radius: 10px; margin: 1rem 0; border-left: 4px solid #4c78a8;">
                    <h4 style="margin: 0; color: #87CEEB;">🛒 Produto {i+1}</h4>
                </div>
                """, unsafe_allow_html=True)
                
                # Layout em colunas com labels claros
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Nome do produto
                    st.markdown("**🍔 Nome do Produto/Item:**")
                    produto = st.text_input(
                        "Digite o nome do produto:",
                        value=produto_data['produto'],
                        placeholder="Ex: Hambúrguer 120g, Batata Congelada 2kg, Refrigerante Coca-Cola...",
                        key=f"produto_{i}",
                        help="Seja específico: inclua marca, peso ou tamanho quando relevante"
                    )
                    st.session_state.produtos_compra[i]['produto'] = produto
                
                with col2:
                    # Botão remover (só aparece se tiver mais de 1 produto)
                    if len(st.session_state.produtos_compra) > 1:
                        st.markdown("**🗑️ Remover:**")
                        if st.button("❌ Remover Produto", key=f"remove_{i}", help="Clique para remover este produto da lista"):
                            st.session_state.produtos_compra.pop(i)
                            st.rerun()
                
                # Segunda linha: Quantidade, Valor e Fornecedor
                col_qty, col_val, col_forn = st.columns([1.5, 1.5, 3])
                
                with col_qty:
                    st.markdown("**📦 Quantidade:**")
                    quantidade = st.number_input(
                        "Quantos itens:",
                        min_value=0.0,
                        value=produto_data['quantidade'],
                        format="%.2f",
                        key=f"quantidade_{i}",
                        help="Quantidade comprada (ex: 2.5 para 2,5kg)"
                    )
                    st.session_state.produtos_compra[i]['quantidade'] = quantidade
                
                with col_val:
                    st.markdown("**💰 Valor Total (R$):**")
                    valor = st.number_input(
                        "Preço pago:",
                        min_value=0.0,
                        value=produto_data['valor'],
                        format="%.2f",
                        key=f"valor_{i}",
                        help="Valor total pago por este item"
                    )
                    st.session_state.produtos_compra[i]['valor'] = valor
                
                with col_forn:
                    st.markdown("**🏪 Categoria e Fornecedor:**")
                    
                    # Selectbox para categoria
                    categoria_selecionada = st.selectbox(
                        "Escolha a categoria:",
                        options=[""] + list(FORNECEDORES_CATEGORIAS.keys()),
                        index=0 if not produto_data.get('categoria') else list(FORNECEDORES_CATEGORIAS.keys()).index(produto_data['categoria']) + 1 if produto_data.get('categoria') in FORNECEDORES_CATEGORIAS.keys() else 0,
                        key=f"categoria_{i}",
                        help="Selecione primeiro a categoria do produto"
                    )
                    
                    # CORREÇÃO: Atualizar categoria no session state
                    st.session_state.produtos_compra[i]['categoria'] = categoria_selecionada
                    
                    # Selectbox para fornecedor baseado na categoria (CORRIGIDO)
                    if categoria_selecionada:
                        fornecedores_da_categoria = FORNECEDORES_CATEGORIAS[categoria_selecionada]
                        
                        # CORREÇÃO: Verificar se o fornecedor atual ainda é válido para a nova categoria
                        current_fornecedor = produto_data.get('fornecedor', '')
                        if current_fornecedor not in fornecedores_da_categoria:
                            current_fornecedor = ""
                            st.session_state.produtos_compra[i]['fornecedor'] = ""
                        
                        fornecedor_index = 0
                        if current_fornecedor and current_fornecedor in fornecedores_da_categoria:
                            fornecedor_index = fornecedores_da_categoria.index(current_fornecedor) + 1
                        
                        fornecedor = st.selectbox(
                            "Escolha o fornecedor:",
                            options=[""] + fornecedores_da_categoria,
                            index=fornecedor_index,
                            key=f"fornecedor_{i}",
                            help=f"Fornecedores disponíveis para {categoria_selecionada}"
                        )
                        st.session_state.produtos_compra[i]['fornecedor'] = fornecedor
                    else:
                        st.session_state.produtos_compra[i]['fornecedor'] = ""
                        st.info("👆 Selecione uma categoria primeiro")
                
                # Validar se o produto está completo
                if (produto.strip() and 
                    st.session_state.produtos_compra[i]['fornecedor'].strip() and 
                    quantidade > 0 and valor > 0):
                    produtos_validos.append({
                        'produto': produto,
                        'quantidade': quantidade,
                        'valor': valor,
                        'fornecedor': st.session_state.produtos_compra[i]['fornecedor']
                    })
                    total_geral += valor
                    
                    # Feedback visual de produto válido
                    st.success(f"✅ Produto válido - Subtotal: {format_brl(valor)}")
                elif produto.strip() or quantidade > 0 or valor > 0:
                    # Produto parcialmente preenchido
                    st.warning("⚠️ Complete todos os campos obrigatórios para este produto")
            
            # Separador visual
            st.markdown("---")
            
            # Botões de ação com layout melhorado
            st.markdown("### ⚙️ **Ações do Formulário**")
            col_btn1, col_btn2, col_btn3 = st.columns([2, 2, 2])
            
            with col_btn1:
                if st.button("➕ **Adicionar Novo Produto**", use_container_width=True, help="Clique para adicionar mais um produto à lista"):
                    # CORREÇÃO: Manter categoria e fornecedor do último produto válido
                    ultimo_produto = st.session_state.produtos_compra[-1] if st.session_state.produtos_compra else {}
                    categoria_anterior = ultimo_produto.get('categoria', '')
                    fornecedor_anterior = ultimo_produto.get('fornecedor', '')
                    
                    novo_produto = {
                        'produto': '', 
                        'quantidade': 0.0, 
                        'valor': 0.0, 
                        'categoria': categoria_anterior,  # Manter categoria anterior
                        'fornecedor': fornecedor_anterior  # Manter fornecedor anterior
                    }
                    st.session_state.produtos_compra.append(novo_produto)
                    st.rerun()
            
            with col_btn2:
                if st.button("🔄 **Limpar Formulário**", use_container_width=True, help="Remove todos os produtos e reinicia o formulário"):
                    st.session_state.produtos_compra = [{'produto': '', 'quantidade': 0.0, 'valor': 0.0, 'categoria': '', 'fornecedor': ''}]
                    st.rerun()
            
            with col_btn3:
                # Mostrar quantidade de produtos válidos
                st.metric("✅ Produtos Válidos", f"{len(produtos_validos)}")
            
            # Display do total melhorado
            if produtos_validos:
                st.markdown(f"""
                <div style="text-align: center; padding: 1.5rem; background: linear-gradient(90deg, #54a24b, #4c78a8); border-radius: 15px; color: white; margin: 2rem 0; box-shadow: 0 8px 16px rgba(0,0,0,0.3);">
                    <div>
                        <span style="font-size: 2rem; margin-right: 1rem;">🛒</span>
                        <span style="font-size: 1.8rem; font-weight: bold;">TOTAL DA COMPRA</span>
                    </div>
                    <div style="margin-top: 0.5rem;">
                        <span style="font-size: 2.5rem; font-weight: bold; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">{format_brl(total_geral)}</span>
                    </div>
                    <div style="margin-top: 0.5rem; font-size: 1.2rem; opacity: 0.9;">
                        {len(produtos_validos)} produto(s) válido(s)
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("💡 **Dica:** Preencha pelo menos um produto completo para ver o total da compra")
            
            # Botão de registrar compras melhorado
            if produtos_validos:
                if st.button("✅ **REGISTRAR TODAS AS COMPRAS**", type="primary", use_container_width=True):
                    formatted_date = data_compra.strftime("%d/%m/%Y")
                    compras_worksheet_obj = get_compras_worksheet()
                    
                    if compras_worksheet_obj and add_compras_to_sheet(formatted_date, produtos_validos, compras_worksheet_obj):
                        # Limpar cache e resetar formulário
                        read_compras_data.clear()
                        st.session_state.produtos_compra = [{'produto': '', 'quantidade': 0.0, 'valor': 0.0, 'categoria': '', 'fornecedor': ''}]
                        st.balloons()  # Efeito visual de sucesso
                        time.sleep(1)
                        st.rerun()
                    elif not compras_worksheet_obj:
                        st.error("❌ Falha ao conectar à planilha de compras.")
            else:
                st.warning("⚠️ **Atenção:** Você precisa ter pelo menos um produto válido para registrar a compra")
                st.info("📝 **Produto válido:** Nome + Categoria/Fornecedor + Quantidade > 0 + Valor > 0")
    
        with subtab2:
            # [Código da subtab2 permanece igual]
            pass
    
        with subtab3:
            st.subheader("📊 Análise de Compras")
            
            df_compras = read_compras_data()
            
            if not df_compras.empty:
                # Aplicar filtros
                df_compras_filtered = df_compras.copy()
                
                if selected_anos_filter and 'Ano' in df_compras_filtered.columns:
                    df_compras_filtered = df_compras_filtered[df_compras_filtered['Ano'].isin(selected_anos_filter)]
                
                if selected_meses_filter and 'Mês' in df_compras_filtered.columns:
                    df_compras_filtered = df_compras_filtered[df_compras_filtered['Mês'].isin(selected_meses_filter)]
                
                if not df_compras_filtered.empty:
                    # NOVO: Histograma de compras por dia
                    st.markdown("### 📊 Histograma de Compras por Dia")
                    daily_purchases_histogram = create_daily_purchases_histogram(df_compras_filtered, "Distribuição de Compras por Faixas de Valor Diário")
                    if daily_purchases_histogram:
                        st.altair_chart(daily_purchases_histogram, use_container_width=True)
                    else:
                        st.info("Dados insuficientes para o histograma de compras diárias.")
                    
                    # Verificar se as colunas necessárias existem para análise (CORRIGIDO)
                    required_columns_analysis = ['FORNECEDOR', 'VALOR', 'PRODUTO']
                    missing_columns_analysis = [col for col in required_columns_analysis if col not in df_compras_filtered.columns]
                    
                    if missing_columns_analysis:
                        st.warning(f"⚠️ Colunas ausentes para análise: {missing_columns_analysis}")
                        st.info("📝 Registre algumas compras primeiro para visualizar as análises.")
                    else:
                        # Análise por fornecedor (CORRIGIDO)
                        st.markdown("### 🏪 Gastos por Fornecedor")
                        gastos_fornecedor = df_compras_filtered.groupby('FORNECEDOR')['VALOR'].agg(['sum', 'count']).round(2)
                        gastos_fornecedor.columns = ['Total_Gasto', 'Qtd_Compras']
                        gastos_fornecedor = gastos_fornecedor.sort_values('Total_Gasto', ascending=False)
                        
                        # Gráfico de gastos por fornecedor
                        chart_data = gastos_fornecedor.reset_index()
                        
                        fornecedor_chart = alt.Chart(chart_data).mark_bar(
                            color=CORES_MODO_ESCURO[3],
                            cornerRadiusTopLeft=5,
                            cornerRadiusTopRight=5
                        ).encode(
                            x=alt.X('Total_Gasto:Q', title='Valor Total Gasto (R$)'),
                            y=alt.Y('FORNECEDOR:N', sort='-x', title='Fornecedor'),
                            tooltip=[
                                alt.Tooltip('FORNECEDOR:N', title='Fornecedor'),
                                alt.Tooltip('Total_Gasto:Q', title='Total Gasto (R$)', format=',.2f'),
                                alt.Tooltip('Qtd_Compras:Q', title='Quantidade de Compras')
                            ]
                        ).properties(
                            height=400
                        ).configure(
                            background='transparent'
                        )
                        
                        st.altair_chart(fornecedor_chart, use_container_width=True)
                        
                        # Top produtos mais comprados (CORRIGIDO)
                        st.markdown("### 🍔 Produtos Mais Comprados")
                        produtos_freq = df_compras_filtered['PRODUTO'].value_counts().head(10)
                        
                        if not produtos_freq.empty:
                            produtos_chart_data = pd.DataFrame({
                                'Produto': produtos_freq.index,
                                'Frequencia': produtos_freq.values
                            })
                            
                            produtos_chart = alt.Chart(produtos_chart_data).mark_bar(
                                color=CORES_MODO_ESCURO[1],
                                cornerRadiusTopLeft=5,
                                cornerRadiusTopRight=5
                            ).encode(
                                x=alt.X('Frequencia:Q', title='Número de Compras'),
                                y=alt.Y('Produto:N', sort='-x', title='Produto'),
                                tooltip=[
                                    alt.Tooltip('Produto:N', title='Produto'),
                                    alt.Tooltip('Frequencia:Q', title='Vezes Comprado')
                                ]
                            ).properties(
                                height=400
                            ).configure(
                                background='transparent'
                            )
                            
                            st.altair_chart(produtos_chart, use_container_width=True)
                        
                        # Resumo estatístico (CORRIGIDO)
                        st.markdown("### 📈 Resumo Estatístico")
                        col_stats1, col_stats2 = st.columns(2)
                        
                        with col_stats1:
                            st.markdown("**💰 Valores:**")
                            st.write(f"• Maior compra: {format_brl(df_compras_filtered['VALOR'].max())}")
                            st.write(f"• Menor compra: {format_brl(df_compras_filtered['VALOR'].min())}")
                            st.write(f"• Compra média: {format_brl(df_compras_filtered['VALOR'].mean())}")
                        
                        with col_stats2:
                            st.markdown("**📊 Frequências:**")
                            st.write(f"• Fornecedor mais usado: {gastos_fornecedor.index[0] if not gastos_fornecedor.empty else 'N/A'}")
                            st.write(f"• Produto mais comprado: {produtos_freq.index[0] if not produtos_freq.empty else 'N/A'}")
                            st.write(f"• Total de itens únicos: {df_compras_filtered['PRODUTO'].nunique()}")
                else:
                    st.info("📊 Nenhuma compra encontrada para análise no período selecionado.")
            else:
                st.info("📊 Registre algumas compras para visualizar as análises.")
    
    
# --- Ponto de Entrada da Aplicação ---
if __name__ == "__main__":
    main()

# --- RODAPÉ PROFISSIONAL ---
st.markdown("""
<div class="footer">
    🍔 <strong>Clips Burger Dashboard</strong> | Desenvolvido com ❤️ usando Streamlit | 
    📊 Sistema de Gestão Completo | 
    🔥 <em>Transformando dados em resultados!</em> | 
    © 2025 - Todos os direitos reservados
</div>
""", unsafe_allow_html=True)
