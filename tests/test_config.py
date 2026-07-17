import pytest
from pydantic import ValidationError

from socratic_tutor.config import DEFAULT_MODEL, AppConfig


def test_config_default_model_is_gpt_5_mini():
    config = AppConfig()

    assert DEFAULT_MODEL == "gpt-5-mini"
    assert config.model == "gpt-5-mini"


def test_config_default_output_language_is_ko():
    config = AppConfig()

    assert config.output_language == "ko"


def test_config_rejects_unknown_output_language():
    with pytest.raises(ValidationError):
        AppConfig(output_language="fr")
