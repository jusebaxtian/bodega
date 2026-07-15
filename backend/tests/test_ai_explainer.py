import json

from app.services.ai.explainer import AIExplainer, FALLBACK_MODEL_NAME


class FakeLLMClient:
    def __init__(self, responses: list[str]):
        self._responses = responses
        self.calls = 0

    def complete(self, system: str, user: str) -> str:
        response = self._responses[self.calls]
        self.calls += 1
        return response


VALID_RESPONSE = json.dumps(
    {
        "main_problem": "El anuncio muestra fatiga",
        "severity": "alta",
        "diagnosis": "La frecuencia subió y el CTR cayó fuerte en la última semana.",
        "immediate_actions": ["Pausar el creativo actual", "Subir 2 variaciones de video nuevas"],
        "actions_72h": ["Medir el CTR de los nuevos creativos"],
        "confidence": 85,
        "explanation_simple": "La gente ya vio este anuncio muchas veces y dejó de hacer clic.",
    }
)


def test_explainer_parses_valid_json_response():
    explainer = AIExplainer(llm_client=FakeLLMClient([VALID_RESPONSE]), model_name="fake-model")

    result, model_used = explainer.explain({"ad_name": "Anuncio 1"})

    assert result.main_problem == "El anuncio muestra fatiga"
    assert result.severity == "alta"
    assert result.confidence == 85
    assert model_used == "fake-model"


def test_explainer_retries_once_then_falls_back_on_invalid_json():
    explainer = AIExplainer(llm_client=FakeLLMClient(["esto no es json", "tampoco esto"]), model_name="fake-model")

    result, model_used = explainer.explain({"ad_name": "Anuncio 1"})

    assert model_used == FALLBACK_MODEL_NAME
    assert result.confidence == 0
    assert "No se pudo generar" in result.main_problem


def test_explainer_recovers_if_second_attempt_is_valid():
    explainer = AIExplainer(llm_client=FakeLLMClient(["esto no es json", VALID_RESPONSE]), model_name="fake-model")

    result, model_used = explainer.explain({"ad_name": "Anuncio 1"})

    assert model_used == "fake-model"
    assert result.main_problem == "El anuncio muestra fatiga"
