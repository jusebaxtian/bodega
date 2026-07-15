"""Capa de IA: interpreta el resumen del motor de reglas y redacta el
diagnóstico. Nunca calcula métricas — solo las explica y decide qué
recomendar en base a lo que el resumen ya trae."""

import json
from typing import Protocol

from pydantic import BaseModel, ValidationError

from app.core.config import get_settings
from app.services.ai.prompts import SYSTEM_PROMPT, build_user_prompt

FALLBACK_MODEL_NAME = "fallback-no-ai"


class AIExplanationResult(BaseModel):
    main_problem: str
    severity: str
    diagnosis: str
    immediate_actions: list[str]
    actions_72h: list[str]
    confidence: int
    explanation_simple: str


class LLMClient(Protocol):
    """Interfaz mínima para poder cambiar de proveedor (o mockear en tests)
    sin tocar AIExplainer."""

    def complete(self, system: str, user: str) -> str: ...


class AnthropicLLMClient:
    """Implementación real contra la API de Anthropic (Claude)."""

    def __init__(self, model: str = "claude-sonnet-4-5"):
        import anthropic  # import perezoso: solo se necesita si de verdad se usa

        settings = get_settings()
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = model

    def complete(self, system: str, user: str) -> str:
        response = self._client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return response.content[0].text


def _fallback_explanation(reason: str) -> AIExplanationResult:
    return AIExplanationResult(
        main_problem="No se pudo generar un diagnóstico automático",
        severity="baja",
        diagnosis=f"La IA no devolvió una respuesta interpretable ({reason}). Revisa las "
        "recomendaciones del motor de reglas mientras tanto.",
        immediate_actions=["Revisar las recomendaciones activas de esta campaña"],
        actions_72h=["Reintentar el diagnóstico de IA más tarde"],
        confidence=0,
        explanation_simple="No pudimos generar la explicación en texto simple en este momento.",
    )


class AIExplainer:
    def __init__(self, llm_client: LLMClient, model_name: str = "claude"):
        self._llm = llm_client
        self._model_name = model_name

    def explain(self, summary: dict) -> tuple[AIExplanationResult, str]:
        user_prompt = build_user_prompt(summary)

        for _attempt in range(2):
            raw = self._llm.complete(SYSTEM_PROMPT, user_prompt)
            try:
                data = json.loads(raw)
                return AIExplanationResult(**data), self._model_name
            except (json.JSONDecodeError, ValidationError):
                continue

        return _fallback_explanation("respuesta no parseable tras reintento"), FALLBACK_MODEL_NAME
