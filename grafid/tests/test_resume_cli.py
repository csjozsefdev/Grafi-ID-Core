"""CLI tests for resume command invocation (Typer option ordering)."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from grafid.cli.main import app
from grafid.config.manager import ConfigManager

runner = CliRunner()


@pytest.fixture
def cli_env(config_manager: ConfigManager, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point CLI runtime at the isolated test config directory."""
    monkeypatch.setenv("GRAFID_DATA_DIR", str(config_manager.config_dir))


def _output(result) -> str:
    return f"{result.stdout}\n{result.stderr}"


def test_resume_help_lists_project_and_options() -> None:
    result = runner.invoke(app, ["resume", "--help"])
    assert result.exit_code == 0
    assert "IDENTIFIER" in result.stdout
    assert "--short" in result.stdout
    assert "--detailed" in result.stdout


def test_resume_project_then_short_option(cli_env, project_id: int) -> None:
    """Natural order: graf-id resume <project> --short"""
    result = runner.invoke(app, ["resume", "test-project", "--short"])
    assert result.exit_code == 0, _output(result)
    assert "resume_id:" in result.stdout
    assert "history:" in result.stdout


def test_resume_short_option_before_project(cli_env, project_id: int) -> None:
    """Also valid: graf-id resume --short <project>"""
    result = runner.invoke(app, ["resume", "--short", "test-project"])
    assert result.exit_code == 0, _output(result)
    assert "resume_id:" in result.stdout


def test_resume_default_is_short_mode(cli_env, project_id: int) -> None:
    result = runner.invoke(app, ["resume", "test-project"])
    assert result.exit_code == 0, _output(result)
    assert "resume_id:" in result.stdout


def test_resume_latest_command(cli_env, project_id: int) -> None:
    runner.invoke(app, ["resume", "test-project", "--short"])
    result = runner.invoke(app, ["resume-latest", "test-project", "--short"])
    assert result.exit_code == 0, _output(result)
    assert "resume_id:" in result.stdout


def test_resume_missing_project_shows_error() -> None:
    result = runner.invoke(app, ["resume"])
    assert result.exit_code != 0
    combined = _output(result)
    assert "IDENTIFIER" in combined or "Missing" in combined
