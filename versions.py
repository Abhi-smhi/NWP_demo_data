# UrbanAir data versions
from dataclasses import dataclass
import json


@dataclass
class UrbanAirData():
    data_info = {
        "Antwerpen": {"nx": 139, "ny": 139, "dx": 500},
        "Paris": {"nx": 989, "ny": 989, "dx": 500},
        "Paris_7.1": {
            "desc": "HARMONIE-AROME",
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
                "ts_none": True,
            },
        },
        "Paris_8.0": {
            "desc": "HARMONIE-AROME",
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
                "ts_none": False,
            },
        },
        "Paris_9.0": {
            "desc": "HARMONIE-AROME",
            "nx": 989,
            "ny": 989,
            "dx": 500,
            "date": "2023-08-20T15:00:00Z",
            "forecast_range": "PT36H",
            "output_frequency": "PT15M",
            "fdb": {
                "expver": "aagp",
                "georef": "u09tvk",
            },
            "json": "json/aagp.json",
            "polytope": {
                "collection": "deode",
                "url": "polytope.ecmwf.int",
                "ts_none": True,
            },
        },
        "Paris_10.0": {
            "desc": "HARMONIE-AROME",
            "nx": 1013,
            "ny": 1013,
            "dx": 200,
            "date": "2023-08-20T18:00:00Z",
            "forecast_range": "PT30H",
            "output_frequency": "PT15M",
            "fdb": {
                "expver": "aagw",
                "georef": "u09tvk",
            },
            "json": "json/aagw.json",
            "polytope": {
                "collection": "deode",
                "url": "polytope.ecmwf.int",
                "ts_none": True,
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
        "10.0": {
            "name": "Paris 10.0",
            "url": "polytope.ecmwf.int",
            "metadata": data_info["Paris_10.0"],
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
        import pydoc
        if version is None:
            version = self.current_version

        txt = self.dict_print(self.urls[version], 1, prefix="\n")
        json_file = self.urls[version]["metadata"]["json"]
        with open(json_file, "r", encoding="utf-8") as f:
            toc = json.load(f)

        title = f'\t\t ---- Data available from polytope ( from {json_file} ) --- \n'
        formatted_json = title + json.dumps(toc, indent=4)
        pydoc.pager(formatted_json)



    def url_version(self, version=None):
        if version is None:
            version = self.current_version
        try:
            if not isinstance(version, str):
                version = str(version)
            url = self.urls[version]["url"]
            if 'liu.se' not in url:
                print(f"Version {version} does not have an lie.se url.")
                print(f"Run 'python download.py -l' for available versions")
                url = None
        except KeyError:
            print(f"KeyError: {version} is not listed")
            print(self)
            url = None

        return url

    def print_url_versions(self):
        import pprint
        print("\n\t\t -- Data versions available for direct (url) download  --\n")
        for url in self.urls:
            if 'exporter.nsc.liu.se' in self.urls[url]['url']:
                print(f"version : {url} \n")
                pprint.pprint(self.urls[url])

if __name__ == "__main__":

    uad = UrbanAirData()
    uad.show()
