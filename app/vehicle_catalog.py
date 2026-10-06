"""Year-specific US vehicle menus from the EPA/DOE FuelEconomy.gov catalog."""
from functools import lru_cache
from time import time
import json
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen
from urllib.error import URLError
from xml.etree import ElementTree

from fastapi import APIRouter, HTTPException, Query
from app.farm_catalog import FARM_MODELS

router = APIRouter(prefix="/api/vehicles")


@lru_cache(maxsize=512)
def fetch_menu(menu: str, year: int, make: str, model: str, day: int) -> tuple[str, ...]:
    params = {"year": year}
    if make:
        params["make"] = make
    if model:
        params["model"] = model
    url = "https://www.fueleconomy.gov/ws/rest/vehicle/menu/" + menu + "?" + urlencode(params)
    request = Request(url, headers={"Accept": "application/xml", "User-Agent": "PocketGuru/1.0"})
    # A brief upstream failure must not force the user to abandon the picker.
    # Bound both attempts so the browser's 30-second deadline has room to spare.
    for attempt, timeout in enumerate((8, 12)):
        try:
            with urlopen(request, timeout=timeout) as response:
                document = ElementTree.fromstring(response.read(2_000_000))
            break
        except (URLError, TimeoutError, OSError, ElementTree.ParseError, ValueError):
            if attempt == 1:
                raise
    # Engine menus include the transmission so similar configurations remain distinguishable.
    return tuple(sorted({item.findtext("text", "").strip()
                         for item in document.findall("menuItem")
                         if item.findtext("text", "").strip()}))


@router.get("/{field}")
def vehicle_menu(
    field: str,
    category: str = Query("automotive", pattern="^(automotive|motorcycle|equipment)$"),
    year: int = Query(..., ge=1900, le=2100),
    make: str = Query("", max_length=100),
    model: str = Query("", max_length=150),
) -> dict:
    menus = {"makes": "make", "models": "model", "engines": "options"}
    if field not in menus:
        raise HTTPException(404, "Vehicle menu not found")
    make, model = make.strip(), model.strip()
    if field in {"models", "engines"} and not make:
        raise HTTPException(422, "Choose a make first")
    if field == "engines" and not model:
        raise HTTPException(422, "Choose a model first")
    if category == "equipment":
        if field != "models":
            raise HTTPException(404, "Farm equipment menu not found")
        options = sorted({row["model"] for row in FARM_MODELS
                          if row["make"].casefold() == make.casefold() and row["start"] <= year <= row["end"]})
        return {"options":options, "source":"Documented tractor production years (partial catalog)"}
    if category == "motorcycle":
        if field != "models":
            raise HTTPException(404, "Motorcycle menu not found")
        try:
            options, source = motorcycle_models(year, make, int(time() // 86400))
        except (URLError, TimeoutError, OSError, ValueError, KeyError, TypeError):
            raise HTTPException(503, "Motorcycle catalog is temporarily unavailable. Try again or enter the exact model manually.")
        return {"options": options, "source": source}
    try:
        options = fetch_menu(menus[field], year, make if field != "makes" else "",
                             model if field == "engines" else "", int(time() // 86400))
    except (URLError, TimeoutError, OSError, ElementTree.ParseError, ValueError):
        raise HTTPException(503, "Vehicle catalog is temporarily unavailable. You can enter the details manually.")
    return {"options": options, "source": "FuelEconomy.gov"}


@lru_cache(maxsize=512)
def motorcycle_models(year: int, make: str, day: int) -> tuple[tuple[str, ...], str]:
    # Verified manufacturer parts pages for this pre-vPIC model year.
    # https://www.kawasaki.com/en-us/owner-center/parts/134936/1980/KZ550-A1
    # https://www.kawasaki.com/en-us/owner-center/parts/135264/1980/KZ440-A1
    # https://www.kawasaki.com/en-us/owner-center/parts/135041/1980/KZ550-C1
    # https://www.kawasaki.com/en-us/owner-center/parts/143186/1980/KZ650-E1
    # https://www.kawasaki.com/en-us/owner-center/parts/1980/KDX175-A1
    # https://www.kawasaki.com/en-us/ownercenter/downloaddiagrampdf/144079?modelcode=KZ750-G1&modelyear=1980
    if year == 1980 and make.casefold() == "kawasaki":
        return ("KDX175-A1", "KZ440-A1", "KZ550-A1", "KZ550-C1", "KZ650-E1", "KZ750-G1"), "Kawasaki owner parts catalog (partial)"
    if year <= 1995:
        return (), "No verified historical catalog matches"
    url = ("https://vpic.nhtsa.dot.gov/api/vehicles/GetModelsForMakeYear/make/"
           + quote(make, safe="") + "/modelyear/" + str(year)
           + "/vehicletype/motorcycle?format=json")
    request = Request(url, headers={"Accept":"application/json", "User-Agent":"PocketGuru/1.0"})
    with urlopen(request, timeout=12) as response:
        data = json.loads(response.read(2_000_000))
    motorcycle_names = {row["Model_Name"].strip().casefold() for row in data["Results"]
                        if isinstance(row.get("Model_Name"), str) and row["Model_Name"].strip()
                        and row.get("Make_Name", "").casefold() == make.casefold()}
    # vPIC can return models from other years even for a year query. Intersect
    # with year-tagged safety records instead of labeling those as verified.
    url = "https://api.nhtsa.gov/products/vehicle/models?" + urlencode({"modelYear":year,"make":make,"issueType":"r"})
    with urlopen(Request(url, headers={"Accept":"application/json"}), timeout=8) as response:
        records = json.loads(response.read(2_000_000))["results"]
    return tuple(sorted({row["model"].strip() for row in records
                         if str(row.get("modelYear")) == str(year)
                         and row.get("make", "").casefold() == make.casefold()
                         and row.get("model", "").strip().casefold() in motorcycle_names})), "NHTSA year-specific motorcycle safety records (partial)"
