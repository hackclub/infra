"""
File that interacts with the airtable API and gets the results
"""
import pyairtable, pandas as pd, requests
import csv


def get_airtable_records(apikey, base, table, output):
    """
    Get's all of the airtables records and returns them into a Pandas DataFrame

    :param apikey: The Airtable API ket
    :param base: The Airtable Base
    :param table: The Airtable Table

    :return dataframe: The dataframe with the table data
    """

    API = pyairtable.Api(apikey)  # Setup the API key
    TABLE = API.table(base, table)  # Init the Table x Airtable connection

    # Get all the columns of the table
    data = requests.get(
        f"https://api.airtable.com/v0/meta/bases/{base}/tables",
        headers={"Authorization": f"Bearer {apikey}"},
    ).json()

    fields = []

    for t in data["tables"]:
        if t["name"] == table:
            for f in t["fields"]:
                fields.append(f["name"])

    # Open THE CSV File
    file = open(output, "w")
    csvfile = csv.writer(file)

    csvfile.writerow(fields)  # Write header
    for row in TABLE.all():
        data = []
        for field in fields:
            if field in row["fields"]:
                data.append(row["fields"][field])
            else:
                data.append(None)

        csvfile.writerow(data)

    file.close()
