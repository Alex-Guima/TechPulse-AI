"""Testes unitários do contrato `BaseCollector`."""
import pytest

from techpulse_ai.collectors.base import BaseCollector


class DummyCollector(BaseCollector):
    """Implementação mínima usada apenas para testar o contrato."""

    def collect(self):
        return [{"title": "item de teste"}]


def test_base_collector_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        BaseCollector()


def test_subclass_implements_collect_contract():
    collector = DummyCollector()
    result = collector.collect()

    assert isinstance(result, list)
    assert result[0]["title"] == "item de teste"


def test_subclass_without_collect_cannot_be_instantiated():
    class IncompleteCollector(BaseCollector):
        pass

    with pytest.raises(TypeError):
        IncompleteCollector()
