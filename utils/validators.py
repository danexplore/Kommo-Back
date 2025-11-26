"""
Funções de validação de dados
"""
import pandas as pd
from typing import List, Any, Optional
from datetime import datetime, date


def validate_date_range(start_date: date, end_date: date) -> bool:
    """Valida se o range de datas é válido"""
    if start_date is None or end_date is None:
        return False
    return start_date <= end_date


def validate_dataframe(df: pd.DataFrame, required_columns: List[str]) -> bool:
    """Valida se DataFrame possui as colunas requeridas"""
    if df is None or df.empty:
        return False
    return all(col in df.columns for col in required_columns)


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitiza input de texto para prevenir injeção"""
    if not isinstance(text, str):
        return ""
    # Remove caracteres potencialmente perigosos
    sanitized = text.strip()
    # Limita tamanho
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    return sanitized


def is_valid_email(email: str) -> bool:
    """Valida formato básico de email"""
    if not email or not isinstance(email, str):
        return False
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_lead_id(lead_id: Any) -> Optional[int]:
    """Valida e converte ID de lead para inteiro"""
    if pd.isna(lead_id):
        return None
    try:
        return int(lead_id)
    except (ValueError, TypeError):
        return None


def is_positive_number(value: Any) -> bool:
    """Verifica se valor é número positivo"""
    if pd.isna(value):
        return False
    try:
        return float(value) > 0
    except (ValueError, TypeError):
        return False
