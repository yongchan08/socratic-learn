import pytest
from pydantic import ValidationError

from socratic_tutor.config import DEFAULT_MODEL, AppConfig


def test_config_default_model_is_gpt_4_1():
    config = AppConfig()

    assert DEFAULT_MODEL == "gpt-4.1"
    assert config.model == "gpt-4.1"


def test_config_default_output_language_is_ko():
    config = AppConfig()

    assert config.output_language == "ko"


def test_config_rejects_unknown_output_language():
    with pytest.raises(ValidationError):
        AppConfig(output_language="fr")
