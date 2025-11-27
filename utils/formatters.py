"""
Funções utilitárias para formatação de dados
"""
import pandas as pd
from typing import Optional, Union
from datetime import datetime


def format_currency(value: float, symbol: str = "R$") -> str:
    """Formata valor como moeda brasileira"""
    if pd.isna(value):
        return f"{symbol} 0,00"
    return f"{symbol} {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_percentage(value: float, decimals: int = 1) -> str:
    """Formata valor como percentual"""
    if pd.isna(value):
        return "0%"
    return f"{value:.{decimals}f}%"


def format_number(value: Union[int, float], thousands_sep: str = ".") -> str:
    """Formata número com separador de milhares"""
    if pd.isna(value):
        return "0"
    return f"{int(value):,}".replace(",", thousands_sep)


def format_duration(seconds: Union[int, float]) -> str:
    """Formata duração em segundos para MM:SS"""
    if pd.isna(seconds) or seconds <= 0:
        return "0:00"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"


def format_date_br(date: Union[datetime, pd.Timestamp, str], include_time: bool = False) -> str:
    """Formata data no padrão brasileiro"""
    if pd.isna(date):
        return ""
    
    if isinstance(date, str):
        try:
            date = pd.to_datetime(date)
        except (ValueError, TypeError):
            return date  # Retorna string original se não conseguir parsear
    
    if include_time:
        return date.strftime('%d/%m/%Y %H:%M')
    return date.strftime('%d/%m/%Y')


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Divisão segura que retorna default se denominador for zero"""
    if denominator == 0 or pd.isna(denominator) or pd.isna(numerator):
        return default
    return numerator / denominator


def calculate_percentage_change(current: float, previous: float) -> Optional[float]:
    """Calcula variação percentual entre dois valores"""
    if previous == 0 or pd.isna(previous) or pd.isna(current):
        return None
    return ((current - previous) / previous) * 100


def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """Trunca texto se exceder tamanho máximo"""
    if pd.isna(text):
        return ""
    text = str(text)
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix
