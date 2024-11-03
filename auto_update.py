import time
import ee
import geemap
import pandas as pd
from geemap.ee_tile_layers import _get_tile_url_format, _validate_palette

geemap.ee_initialize()

df = pd.read_csv("datasets.tsv", sep="\t")

for index, row in df.iterrows():
    print(f"{index}: {row['id']}")
    try:
        ee_object = eval(row["snippet"])
        vis_params = eval(row["vis"])
        if "palette" in vis_params:
            vis_params["palette"] = _validate_palette(vis_params["palette"])
        url = _get_tile_url_format(ee_object, vis_params)
        row["url"] = url
        row["modified"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    except Exception as e:
        print(e)
        row["url"] = None

df.to_csv("datasets.tsv", sep="\t", index=False)
