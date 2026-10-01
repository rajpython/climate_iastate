"""Write the audit5 per-cell threshold layout (theta90 + mu_clim per zone, long parquet, identity JSON) from a
producer climatology directory. Usage: build_audit5_layout.py <climatology_dir> <out_dir> <vintage_id> <manifest_keys.json> zone ..."""
import hashlib, json, sys
from pathlib import Path
import numpy as np, pandas as pd, xarray as xr
clim, out, vid, keyfile, zones = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5:]
keys = json.load(open(keyfile))
out.mkdir(parents=True, exist_ok=True)
RECIPE = "transpose(doy,lat,lon);sortby asc;<f4 C-contiguous;sha256(values)"
def field(store, z):
    ds = xr.open_zarr(str(clim / f"{store}_{z}.zarr"), consolidated=False)
    v = ds[list(ds.data_vars)[0]]
    d = [x for x in v.dims if x not in ("lat", "lon")][0]
    v = v.rename({d: "doy"}).transpose("doy", "lat", "lon").sortby(["lat", "lon"]).astype("float32")
    return v.assign_coords(doy=np.arange(1, v.sizes["doy"] + 1, dtype="int32"),
                           lat=v.lat.values.astype("float32"), lon=v.lon.values.astype("float32")), dict(v.attrs)
ident = {"recipe": RECIPE, "vintage_id": vid, "zones": {}}
longs = []
for z in zones:
    th, tha = field("theta90", z); mu, mua = field("mu", z)
    assert np.array_equal(th.lat, mu.lat) and np.array_equal(th.lon, mu.lon)
    a = np.ascontiguousarray(th.values.astype("<f4"))
    k = hashlib.sha256(a.tobytes()).hexdigest()
    ds = xr.Dataset({"theta90": (("doy", "lat", "lon"), a, tha), "mu_clim": (("doy", "lat", "lon"), mu.values.astype("<f4"), mua)},
                    coords={"doy": th.doy.values, "lat": th.lat.values, "lon": th.lon.values})
    ds.attrs = {"title": f"Per-cell MHW theta90 threshold + mu climatology ({z})", "zone": z, "vintage_id": vid,
                "vintage_theta90_identity_sha256": keys[z], "canonical_theta90_sha256": k, "baseline": "1991-2020",
                "recipe": "Hobday et al. (2016): 90th pct, 11-day centered DOY window (wrap), 31-day circular DOY smoothing (nan-aware); 15% ice mask on baseline and detection; ice-field-outage rule (interpolated ice, open above 2 degC) on the 171 OISST outage days; no detrend",
                "source": "NOAA OISST v2.1 (ncdcOisst21Agg, PFEG CoastWatch ERDDAP, + NCEI per-day files for the repaired, extension and re-issued days), DOI 10.25921/RE9P-PT57",
                "provenance": "dashboard producer climatology of vintage " + vid + "; theta90 canonical-SHA-identical to the vintage identity key",
                "generating_script": "build_audit5_layout.py (shipped)"}
    enc = {v: {"zlib": True, "complevel": 4, "_FillValue": np.float32(np.nan), "dtype": "float32", "chunksizes": a.shape} for v in ("theta90", "mu_clim")}
    ds.to_netcdf(out / f"theta90_{z}.nc", encoding=enc)
    ident["zones"][z] = {"canonical_sha256": k, "vintage_identity_sha256": keys[z], "match": k == keys[z],
                         "shape_doy_lat_lon": list(a.shape), "nan_count": int(np.isnan(a).sum()),
                         "lat_min": float(th.lat.min()), "lat_max": float(th.lat.max()), "lon_min": float(th.lon.min()), "lon_max": float(th.lon.max()),
                         "theta90_attrs": {k2: (str(v2) if not isinstance(v2, (int, float, str)) else v2) for k2, v2 in tha.items()}}
    D, LA, LO = np.meshgrid(th.doy.values, th.lat.values, th.lon.values, indexing="ij")
    df = pd.DataFrame({"zone": z, "lat": LA.ravel().astype("float32"), "lon": LO.ravel().astype("float32"), "doy": D.ravel().astype("int16"),
                       "mhw_threshold": a.ravel(), "mu_clim": mu.values.astype("float32").ravel()})
    assert (df.mhw_threshold.isna() == df.mu_clim.isna()).all(), z
    longs.append(df[df.mhw_threshold.notna()])
ident["all_zones_match_vintage_identity"] = all(v["match"] for v in ident["zones"].values())
json.dump(ident, open(out / "THETA90-IDENTITY-VERIFICATION.json", "w"), indent=2)
L = pd.concat(longs, ignore_index=True)
L.to_parquet(out / "theta90_percell_long.parquet", index=False)
print("wrote", len(zones), "zones; long rows", len(L), "; all match:", ident["all_zones_match_vintage_identity"])
