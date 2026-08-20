"""Executable NSP mutation probes for the OpenAI provider boundary."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

import pytest

from yggdrasil.llm.base import LLMError, LLMMessage

if TYPE_CHECKING:
    from collections.abc import Callable

_ADAPTER_PATH = Path(__file__).parents[1] / "adapters" / "openai.py"
_REPO_ROOT = Path(__file__).parents[4]
_CONTRACT_PATH = _REPO_ROOT / "docs" / "contracts" / "openai-llm-provider.boundary.json"
_COMPILER_PATH = (
    _REPO_ROOT
    / ".agents"
    / "skills"
    / "negative-space-programming"
    / "scripts"
    / "compile_contract.py"
)


class _ResponseAPI:
    def __init__(self, outcomes: list[object]) -> None:
        self._outcomes = list(outcomes)
        self.calls = 0

    def create(self, **_payload: object) -> object:
        self.calls += 1
        outcome = self._outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class _SDKClient:
    def __init__(self, outcomes: list[object]) -> None:
        self.responses = _ResponseAPI(outcomes)


class _AuthenticationError(Exception):
    status_code = 401


def _response(text: str = "ok") -> SimpleNamespace:
    return SimpleNamespace(output_text=text, model="gpt-test", status="completed")


def _load_mutant(replacement: tuple[str, str]) -> Any:
    source = _ADAPTER_PATH.read_text(encoding="utf-8")
    old, new = replacement
    assert source.count(old) == 1, f"mutation anchor is not unique: {old!r}"
    module_name = "openai_adapter_mutant"
    spec = importlib.util.spec_from_loader(module_name, loader=None)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    exec(compile(source.replace(old, new), str(_ADAPTER_PATH), "exec"), module.__dict__)
    return module.OpenAIClient


def _scenario_rejects_blank_key(client_type: Any) -> bool:
    try:
        client_type(model="gpt-test", api_key="", sdk_client=object())
    except LLMError:
        return True
    return False


def _scenario_does_not_fallback(client_type: Any) -> bool:
    sdk = _SDKClient([_AuthenticationError(), _response()])
    try:
        client_type(model="gpt-test", api_key="sk-test", sdk_client=sdk).complete(
            [LLMMessage(role="user", content="hello")]
        )
    except LLMError:
        return True
    return False


def _scenario_does_not_retry_permanent(client_type: Any) -> bool:
    sdk = _SDKClient([_AuthenticationError(), _AuthenticationError()])
    try:
        client_type(model="gpt-test", api_key="sk-test", sdk_client=sdk).complete(
            [LLMMessage(role="user", content="hello")]
        )
    except LLMError:
        return sdk.responses.calls == 1
    return False


def _scenario_hides_reasoning(client_type: Any) -> bool:
    result = client_type(
        model="gpt-test", api_key="sk-test", sdk_client=_SDKClient([_response()])
    ).complete([LLMMessage(role="user", content="hello")])
    return result.thinking == ""


def _scenario_rejects_empty_output(client_type: Any) -> bool:
    try:
        client_type(
            model="gpt-test",
            api_key="sk-test",
            sdk_client=_SDKClient([_response("")]),
        ).complete([LLMMessage(role="user", content="hello")])
    except LLMError:
        return True
    return False


def _scenario_rejects_unsafe_endpoint(client_type: Any) -> bool:
    try:
        client_type(
            model="gemma-local",
            api_key="local-test",
            base_url="http://example.test/v1",
            sdk_client=object(),
        )
    except LLMError:
        return True
    return False


@pytest.mark.parametrize(
    ("mutant", "scenario"),
    [
        (
            ("if not self._api_key:", "if False:"),
            _scenario_rejects_blank_key,
        ),
        (
            (
                "raise self._as_llm_error(exc) from exc",
                "return self._client.responses.create(**payload)",
            ),
            _scenario_does_not_fallback,
        ),
        (
            (
                "if not self._is_transient(exc) or attempt == _MAX_ATTEMPTS:",
                "if attempt == _MAX_ATTEMPTS:",
            ),
            _scenario_does_not_retry_permanent,
        ),
        (
            ('thinking="",', "thinking=self._extract_output_text(raw),"),
            _scenario_hides_reasoning,
        ),
        (
            ("if not content:", "if False:"),
            _scenario_rejects_empty_output,
        ),
        (
            ("self._base_url = resolve_openai_base_url(base_url)", "self._base_url = None"),
            _scenario_rejects_unsafe_endpoint,
        ),
    ],
    ids=["IM-KEY", "IM-FALLBACK", "IM-RETRY-ALL", "IM-RAW-REASONING", "IM-COVERAGE", "IM-ENDPOINT"],
)
def test_implementation_mutant_is_killed(
    mutant: tuple[str, str], scenario: Callable[[Any], bool]
) -> None:
    """Each declared implementation weakening violates an executable oracle."""
    mutant_client = _load_mutant(mutant)
    assert not scenario(mutant_client), "implementation mutant survived its boundary oracle"


def _load_compiler() -> Any:
    module_name = "nsp_compile_contract_for_openai_tests"
    spec = importlib.util.spec_from_file_location(module_name, _COMPILER_PATH)
    assert spec is not None and spec.loader is not None
    compiler = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = compiler
    spec.loader.exec_module(compiler)
    return compiler


def _contract() -> dict[str, Any]:
    return json.loads(_CONTRACT_PATH.read_text(encoding="utf-8"))


@pytest.mark.parametrize("mutant", ["SM-BOUNDARY", "SM-ENDPOINT", "SM-NEGATIVE", "SM-GRAPH"])
def test_specification_mutant_is_rejected(mutant: str) -> None:
    """Removing a declared boundary obligation fails the design compiler."""
    document = copy.deepcopy(_contract())
    if mutant == "SM-BOUNDARY":
        document["boundary"]["supported"] = [
            item for item in document["boundary"]["supported"] if item["id"] != "SUP-STRUCTURED"
        ]
    elif mutant == "SM-ENDPOINT":
        document["boundary"]["supported"] = [
            item for item in document["boundary"]["supported"] if item["id"] != "SUP-ENDPOINT"
        ]
    elif mutant == "SM-NEGATIVE":
        document["boundary"]["forbidden"] = [
            item for item in document["boundary"]["forbidden"] if item["id"] != "FORBID-FALLBACK"
        ]
    else:
        document["graph"]["edges"] = []

    report = _load_compiler().ContractCompiler(document, "design").validate()
    assert not report["valid"], f"specification mutant {mutant} survived the design gate"
