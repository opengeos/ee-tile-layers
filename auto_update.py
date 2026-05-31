import json
import os
import time

import ee
import pandas as pd
from geemap.ee_tile_layers import _get_tile_url_format, _validate_palette


def _get_service_account_credentials():
    """Create Earth Engine credentials from the EE_SERVICE_ACCOUNT environment variable.

    Returns:
        A tuple containing service account credentials and the associated project ID.

    Raises:
        ValueError: If EE_SERVICE_ACCOUNT is set but does not contain a valid JSON key.
    """
    service_account = os.environ.get("EE_SERVICE_ACCOUNT")
    if not service_account:
        return None, None

    service_account = service_account.strip()
    if os.path.exists(service_account):
        with open(service_account, encoding="utf-8") as file_obj:
            key_data = file_obj.read()
        key_file = service_account
    else:
        key_data = service_account
        key_file = None

    try:
        key_info = json.loads(key_data)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "EE_SERVICE_ACCOUNT must contain a service account JSON key or a path "
            "to a service account JSON key file."
        ) from exc

    email = key_info.get("client_email")
    if not email:
        raise ValueError("EE_SERVICE_ACCOUNT JSON key is missing client_email.")

    if key_file:
        credentials = ee.ServiceAccountCredentials(email, key_file=key_file)
    else:
        credentials = ee.ServiceAccountCredentials(email, key_data=key_data)

    return credentials, key_info.get("project_id")


def initialize_earth_engine():
    """Initialize the Earth Engine API with service account credentials when available."""
    credentials, project = _get_service_account_credentials()
    if credentials:
        ee.Initialize(credentials=credentials, project=project)
    else:
        ee.Initialize()


def make_uid(dataset_id):
    """Create a dataset UID from an Earth Engine dataset ID.

    Args:
        dataset_id: Earth Engine dataset ID.

    Returns:
        Lowercase dataset UID with slashes and underscores replaced by hyphens.
    """
    return str(dataset_id).replace("/", "-").replace("_", "-").lower()


def ensure_uid_column(df):
    """Add the UID column as the first column of the datasets table.

    Args:
        df: Datasets DataFrame.

    Returns:
        Datasets DataFrame with the UID column first.
    """
    uid_values = df["id"].map(make_uid)
    if "uid" in df.columns:
        df = df.drop(columns=["uid"])
    df.insert(0, "uid", uid_values)
    return df


def update_datasets(path="datasets.tsv"):
    """Update Earth Engine tile URLs in the datasets table.

    Args:
        path: Path to the tab-separated datasets file.
    """
    df = pd.read_csv(path, sep="\t")
    df = ensure_uid_column(df)

    for index, row in df.iterrows():
        print(f"{index}: {row['id']}")
        try:
            ee_object = eval(row["snippet"])
            vis_params = eval(row["vis"])
            if "palette" in vis_params:
                vis_params["palette"] = _validate_palette(vis_params["palette"])
            url = _get_tile_url_format(ee_object, vis_params)
            df.at[index, "url"] = url
            df.at[index, "modified"] = time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime()
            )
        except Exception as e:
            print(e)
            df.at[index, "url"] = None

    df.to_csv(path, sep="\t", index=False)


def main():
    """Initialize Earth Engine and update the datasets table."""
    initialize_earth_engine()
    update_datasets()


if __name__ == "__main__":
    main()
