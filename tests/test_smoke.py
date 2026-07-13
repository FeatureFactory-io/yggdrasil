import pytest
from django.test import Client


@pytest.mark.django_db
def test_health_endpoint():
    client = Client()
    response = client.get("/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.django_db
def test_welcome_page():
    from django.test import RequestFactory

    from web.views import welcome

    request = RequestFactory().get("/")
    response = welcome(request)
    assert response.status_code == 200
    assert b"Yggdrasil" in response.content


@pytest.mark.django_db
def test_welcome_page_content():
    """Avoid template render instrumentation issues on Python 3.14."""
    from django.test import RequestFactory

    from web.views import welcome

    request = RequestFactory().get("/")
    response = welcome(request)
    assert response.status_code == 200


@pytest.mark.django_db
def test_llm_factory_qwen(settings):
    from core.llm import QwenLLM, get_llm

    settings.LLM_PROVIDER = "qwen"
    llm = get_llm()
    assert isinstance(llm, QwenLLM)
