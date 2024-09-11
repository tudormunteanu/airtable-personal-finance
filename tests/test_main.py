import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from main import upload_csv_to_airtable
import csv
import tempfile
import os


@pytest.fixture
def csv_file():
    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, newline="", suffix=".csv"
    ) as temp_file:
        writer = csv.DictWriter(temp_file, fieldnames=["name", "age"])
        writer.writeheader()
        writer.writerow({"name": "Alice", "age": "30"})
        writer.writerow({"name": "Bob", "age": "25"})
    yield temp_file.name
    os.unlink(temp_file.name)


@pytest.fixture
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("INTERNAL_AIRTABLE_API_KEY", "fake_api_key")


@patch("main.Api")
def test_upload_csv_to_airtable(mock_api, csv_file, mock_env_vars):
    mock_table = MagicMock()
    mock_api_instance = MagicMock()
    mock_api_instance.table.return_value = mock_table
    mock_api.return_value = mock_api_instance

    runner = CliRunner()
    result = runner.invoke(
        upload_csv_to_airtable,
        [
            "--csv-file",
            csv_file,
            "--base-id",
            "fake_base_id",
            "--table-name",
            "fake_table_name",
        ],
    )

    assert result.exit_code == 0
    assert (
        f"CSV file '{csv_file}' uploaded to Airtable base 'fake_base_id', table 'fake_table_name'"
        in result.output
    )

    mock_api.assert_called_once_with("fake_api_key")
    mock_api_instance.table.assert_called_once_with("fake_base_id", "fake_table_name")
    mock_table.batch_create.assert_called_once_with(
        [{"name": "Alice", "age": "30"}, {"name": "Bob", "age": "25"}]
    )


@patch.dict(os.environ, {}, clear=True)
def test_upload_csv_to_airtable_missing_api_key(csv_file):
    runner = CliRunner()
    result = runner.invoke(
        upload_csv_to_airtable,
        [
            "--csv-file",
            csv_file,
            "--base-id",
            "fake_base_id",
            "--table-name",
            "fake_table_name",
        ],
    )

    assert result.exit_code != 0
    assert "INTERNAL_AIRTABLE_API_KEY not found in .env file" in result.output


def test_upload_csv_to_airtable_file_not_found(mock_env_vars):
    runner = CliRunner()
    result = runner.invoke(
        upload_csv_to_airtable,
        [
            "--csv-file",
            "non_existent_file.csv",
            "--base-id",
            "fake_base_id",
            "--table-name",
            "fake_table_name",
        ],
    )

    assert result.exit_code != 0
    assert "Path 'non_existent_file.csv' does not exist." in result.output


def test_on_live_api():
    runner = CliRunner()
    result = runner.invoke(
        upload_csv_to_airtable,
        [
            "--data-source",
            "natwest",
            "--csv-file",
            "/Users/tudor/Downloads/MUNTEANUT85193275-20240911.csv",
            "--airtable-url",
            "https://airtable.com/appO9bi5ZHMSWDiEh/tblyVC1fMLkehAy7N/viwYtnOXAKqQ3rlWk",
            "--table-name",
            "natwest",
        ],
    )

    assert result.exit_code == 0
