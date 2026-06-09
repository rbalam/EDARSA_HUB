"""Módulo Benchmark Interno de Grupo (SQL-first, NO-LIVE, confidencialidad backend)."""
from modules.comercial_benchmark.routes import router as comercial_benchmark_router

__all__ = ["comercial_benchmark_router"]
