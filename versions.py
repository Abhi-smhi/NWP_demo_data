# UrbanAir data versions
from dataclasses import dataclass
import json


@dataclass
class UrbanAirData():
    data_info = {
        "Antwerpen": {"nx": 139, "ny": 139, "dx": 500},
        "Paris": {"nx": 989, "ny": 989, "dx": 500},
        "Paris_7.1": {
            "nx": 989,
            "ny": 989,
            "dx": 500,
            "date": "2023-08-20T00:00:00Z",
            "forecast_range": "PT36H",
            "output_frequency": "PT15M",
            "fdb": {
                "expver": "aabg",
                "georef": "u09tvk",
            },
            "json": "json/aabg.json",
            "polytope": {
                "collection": "deode",
                "url": "polytope-test.ecmwf.int",
            },
        },
        "Paris_8.0": {
            "nx": 989,
            "ny": 989,
            "dx": 500,
            "date": "2023-08-20T00:00:00Z",
            "forecast_range": "PT48H",
            "output_frequency": "PT15M",
            "toc": {
                "climate_fields": "http://exporter.nsc.liu.se/aebc1d3690d441cf82818d9893fa9e57/Const.Clim.grib2.toc",
                "surface_fields": "http://exporter.nsc.liu.se/aebc1d3690d441cf82818d9893fa9e57/2023/08/20/GRIBTILEDEOD+0048h00m00s.sfx.toc",
                "atmospheric_fields": "http://exporter.nsc.liu.se/aebc1d3690d441cf82818d9893fa9e57/2023/08/20/GRIBPFDEOD+0048h00m00s.toc",
            },
            "fdb": {
                "expver": "aad4",
                "georef": "u09tvk",
            },
            "json": "json/aad4.json",
            "polytope": {
                "collection": "deode",
                "url": "polytope.ecmwf.int",
            },
        },
        "Paris_9.0": {
            "nx": 989,
            "ny": 989,
            "dx": 500,
            "date": "2023-08-20T15:00:00Z",
            "forecast_range": "PT36",
            "output_frequency": "PT15M",
            "fdb": {
                "expver": "aagp",
                "georef": "u09tvk",
            },
            "json": "json/aagp.json",
            "polytope": {
                "collection": "deode",
                "url": "polytope.ecmwf.int",
            },
        },
    }
    urls = {
        "4": {
            "name": "Antwerpen test",
            "url": "http://exporter.nsc.liu.se/28e80f79cad547988e7a0b64809e0dc3",
            "metadata": data_info["Antwerpen"],
        },
        "5.0": {
            "name": "Antwerpen",
            "url": "http://exporter.nsc.liu.se/1c333ab5ee374ab2acb470b2870cc02e",
            "metadata": data_info["Antwerpen"],
        },
        "6.1": {
            "name": "Paris",
            "url": "http://exporter.nsc.liu.se/284818358def438b8c142f4223c96936",
            "metadata": data_info["Paris"],
        },
        "7.1": {
            "name": "Paris 7.1",
            "url": "http://exporter.nsc.liu.se/f1559d3fb24e47b5b9b3f77905a8bcba",
            "metadata": data_info["Paris_7.1"],
        },
        "8.0": {
            "name": "Paris 8.0",
            "url": "http://exporter.nsc.liu.se/aebc1d3690d441cf82818d9893fa9e57",
            "metadata": data_info["Paris_8.0"],
        },
        "9.0": {
            "name": "Paris 9.0",
            "url": "polytope.ecmwf.int",
            "metadata": data_info["Paris_9.0"],
        },
    }
    current_version = list(urls)[-1]
    base_url = urls[current_version]["url"]

    def __repr__(self):
        return "UrbanAirData"

    def dict_print(self, d, indent=0, prefix=""):
        txt = ""
        for k, v in d.items():
            for i in range(0, indent):
                txt += " "
            if isinstance(v, dict):
                txt += f"{prefix}{k}:\n"
                txt += self.dict_print(v, indent + 1)
            else:
                txt += f"{k}: {v}\n"
        return txt

    def __str__(self):
        txt = "Available versions:\n"
        txt += self.dict_print(self.urls, 1, prefix="\n")

        return txt

    def show(self, version=None):
        if version is None:
            version = self.current_version

        txt = self.dict_print(self.urls[version], 1, prefix="\n")
        json_file = self.urls[version]["metadata"]["json"]
        with open(json_file, "r", encoding="utf-8") as f:
            toc = json.load(f)

        txt +=f"\nData available from polytope ( from {json_file} )\n"
        for levtype, content in toc.items():
          txt += f"\nLevtype:{levtype}\n"
          for i, group in enumerate(content):
            txt += f" group:{i}\n"
            for key, values in group.items():
              txt += f"  {key}: {values}\n"

        #txt += json.dumps(toc#)

        return txt


    def url_version(self, version=None):
        if version is None:
            version = self.current_version
        try:
            if not isinstance(version, str):
                version = str(version)
            url = self.urls[version]["url"]
        except KeyError:
            print(f"Version {version} is not available")
            print(self)
            url = None

        return url

if __name__ == "__main__":

    uad = UrbanAirData()
    print(uad.show())
