import pytest

from rag.config import ConfigError, load_settings


def test_load_settings_expands_environment_and_dotenv(tmp_path, monkeypatch):
    config_path = tmp_path / "config.yaml"
    env_path = tmp_path / ".env"
    config_path.write_text(
        "components:\n"
        "  database:\n"
        "    class: rag.storage.database:Database\n"
        "    options:\n"
        "      db_url: ${DATABASE_URL}\n",
        encoding="utf-8",
    )
    env_path.write_text("DATABASE_URL=postgresql://local/test\n", encoding="utf-8")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    settings = load_settings(config_path)

    assert settings.components["database"].options["db_url"] == "postgresql://local/test"


def test_load_settings_uses_existing_environment_over_dotenv(tmp_path, monkeypatch):
    config_path = tmp_path / "config.yaml"
    (tmp_path / ".env").write_text("DATABASE_URL=dotenv-value\n", encoding="utf-8")
    config_path.write_text(
        "components:\n"
        "  database:\n"
        "    class: rag.storage.database:Database\n"
        "    options:\n"
        "      db_url: ${DATABASE_URL}\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("DATABASE_URL", "environment-value")

    settings = load_settings(config_path)

    assert settings.components["database"].options["db_url"] == "environment-value"


def test_load_settings_fails_for_unset_environment_variable(tmp_path, monkeypatch):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "components:\n"
        "  database:\n"
        "    class: rag.storage.database:Database\n"
        "    options:\n"
        "      db_url: ${MISSING_DATABASE_URL}\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("MISSING_DATABASE_URL", raising=False)

    with pytest.raises(ConfigError, match="MISSING_DATABASE_URL"):
        load_settings(config_path)


def test_load_settings_rejects_malformed_dependency_reference(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "components:\n"
        "  repository:\n"
        "    class: rag.storage.postgres_file_repo:PostgresFileRepo\n"
        "    dependencies:\n"
        "      database: database\n",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="must contain only a 'ref'"):
        load_settings(config_path)
