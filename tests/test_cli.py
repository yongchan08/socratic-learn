from typer.testing import CliRunner

from socratic_tutor.cli import app


def test_cli_accepts_output_language_option():
    runner = CliRunner()

    result = runner.invoke(app, ["start", "--help"])

    assert result.exit_code == 0
    assert "--output-language" in result.output


def test_cli_exposes_concept_review_without_changing_start():
    runner = CliRunner()

    root_help = runner.invoke(app, ["--help"])
    start_help = runner.invoke(app, ["start", "--help"])

    assert root_help.exit_code == 0
    assert "concept-review" in root_help.output
    assert start_help.exit_code == 0
