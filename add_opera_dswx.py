"""Add the OPERA DSWX S1 water-classification layer from OPERA.ipynb to datasets.tsv."""

import time

import ee
import pandas as pd
from geemap.ee_tile_layers import _get_tile_url_format, _validate_palette

from auto_update import ensure_uid_column, initialize_earth_engine, make_uid

DATASETS_PATH = "datasets.tsv"

DATASET = {
    "id": "OPERA/DSWX/L3_V1/S1",
    "type": "Image",
    "snippet": (
        'ee.ImageCollection("OPERA/DSWX/L3_V1/S1").filterDate("2026-04-01", '
        '"2026-06-01").map(lambda image: image.select("BWTR_Binary_water").'
        'updateMask(image.select("BWTR_Binary_water").eq(1))).reduce('
        'ee.Reducer.sum()).rename("BWTR_Binary_water")'
    ),
    "vis": "{'min': 0, 'max': 10, 'palette': ['ffffff', 'ffbbbb', '0000ff']}",
    "source": (
        "https://developers.google.com/earth-engine/datasets/catalog/"
        "OPERA_DSWX_L3_V1_S1"
    ),
}


def build_opera_dswx_image():
    """Build the masked OPERA DSWX S1 water-frequency image from OPERA.ipynb."""
    collection = ee.ImageCollection("OPERA/DSWX/L3_V1/S1").filterDate(
        "2026-04-01", "2026-06-01"
    )

    def mask_water(image):
        water = image.select("BWTR_Binary_water")
        return water.updateMask(water.eq(1))

    return (
        collection.map(mask_water).reduce(ee.Reducer.sum()).rename("BWTR_Binary_water")
    )


def generate_tile_url(ee_object, vis_params):
    """Generate an Earth Engine tile URL for an image and visualization parameters."""
    vis = dict(vis_params)
    if "palette" in vis:
        vis["palette"] = _validate_palette(vis["palette"])
    return _get_tile_url_format(ee_object, vis)


def append_dataset(path=DATASETS_PATH):
    """Generate the OPERA DSWX tile URL and append or update its datasets.tsv record."""
    initialize_earth_engine()

    ee_object = build_opera_dswx_image()
    vis_params = eval(DATASET["vis"])
    url = generate_tile_url(ee_object, vis_params)
    modified = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    df = pd.read_csv(path, sep="\t")
    df = ensure_uid_column(df)

    uid = make_uid(DATASET["id"])
    row = {
        "uid": uid,
        "id": DATASET["id"],
        "type": DATASET["type"],
        "snippet": DATASET["snippet"],
        "vis": DATASET["vis"],
        "url": url,
        "modified": modified,
        "source": DATASET["source"],
    }

    if uid in df["uid"].values:
        index = df.index[df["uid"] == uid][0]
        for column, value in row.items():
            df.at[index, column] = value
        print(f"Updated existing dataset: {DATASET['id']}")
    else:
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        print(f"Appended dataset: {DATASET['id']}")

    df.to_csv(path, sep="\t", index=False)
    print(url)


def main():
    """Initialize Earth Engine and append the OPERA DSWX dataset record."""
    append_dataset()


if __name__ == "__main__":
    main()
