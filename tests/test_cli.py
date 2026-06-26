from typer.testing import CliRunner

from socratic_tutor.cli import app


def test_cli_accepts_output_language_option():
    runner = CliRunner()

    result = runner.invoke(app, ["start", "--help"])

    assert result.exit_code == 0
    assert "--output-language" in result.output
