"""
Módulo de Serviços do APBIA
feito de ultima hora pois vi que é o indicado para organizar serviços
"""
from services.gemini_stats import GeminiStats, gemini_stats
from services.gemini_service import GeminiService
from services.pdf_service import BragantecPDFGenerator

# Exporta para facilitar importações
__all__ = [
    'GeminiService',
    'GeminiStats',
    'BragantecPDFGenerator'
]