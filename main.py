import click
import csv
from pyairtable import Api, Base
import os
from dotenv import load_dotenv

load_dotenv()


@click.command()
@click.option(
    "--csv-file",
    type=click.Path(exists=True),
    required=True,
    help="Path to the CSV file to upload",
)
@click.option(
    "--airtable-url",
    type=str,
    required=True,
    help="URL to the Airtable base",
)
@click.option(
    "--table-name",
    type=str,
    required=True,
    help="Name of the table to create",
)
@click.option(
    "--data-source",
    type=click.Choice(["natwest"], case_sensitive=False),
    required=True,
    help="Data source to use",
)
def upload_csv_to_airtable(csv_file, airtable_url, table_name, data_source):
    api_key = os.getenv("INTERNAL_AIRTABLE_API_KEY")
    if not api_key:
        raise click.ClickException("INTERNAL_AIRTABLE_API_KEY not found in .env file")

    allowed_columns = get_column_keys_from_data_source(data_source)

    base_id, table_id = parse_ids_from_airtable_url(airtable_url)
    api = Api(api_key)
    base = Base(api, base_id)

    tables = base.tables()
    existing_table = next((table for table in tables if table.name == table_name), None)
    if existing_table is None:
        table = create_table_from_csv(base, table_name, csv_file, allowed_columns)
    else:
        table = existing_table

    with open(csv_file, "r") as file:
        csv_reader = csv.DictReader(file)
        records = [
            {key: value for key, value in record.items() if key in allowed_columns}
            for record in csv_reader
        ]
        table.batch_create(records)

    click.echo(
        f"CSV file '{csv_file}' uploaded to Airtable base '{base_id}', table '{table_id}'"
    )


def create_table_from_csv(base, table_name, csv_file, allowed_columns):
    """Create a new table in Airtable based on CSV structure."""
    with open(csv_file, "r") as file:
        csv_reader = csv.reader(file)
        headers = next(csv_reader)

    fields = [
        {"name": header, "type": "singleLineText"}
        for header in headers
        if header in allowed_columns
    ]
    return base.create_table(table_name, fields)


def parse_ids_from_airtable_url(url):
    """Parse the base and table ids from an Airtable URL.
    Example: https://airtable.com/appO9bi5ZHMSWDiEh/tblyVC1fMLkehAy7N/viwYtnOXAKqQ3rlWk
    where base_id is appO9bi5ZHMSWDiEh and table_id is tblyVC1fMLkehAy7N
    """
    parts = url.split("/")

    base_id = parts[-3]
    table_id = parts[-2]
    return base_id, table_id


# Define multiple data sources. A first one is Natwest, in which only the following columns are needed:
# Date, Description, Amount
def get_column_keys_from_data_source(data_source):
    if data_source == "natwest":
        return ["Date", "Description", "Value"]
    else:
        raise ValueError(f"Unsupported data source: {data_source}")


if __name__ == "__main__":
    upload_csv_to_airtable()
