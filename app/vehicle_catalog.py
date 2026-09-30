"""Year-specific US vehicle menus from the EPA/DOE FuelEconomy.gov catalog."""
from functools import lru_cache
from time import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError
from xml.etree import ElementTree

from fastapi import APIRouter, HTTPException, Query

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
    try:
        options = fetch_menu(menus[field], year, make if field != "makes" else "",
                             model if field == "engines" else "", int(time() // 86400))
    except (URLError, TimeoutError, OSError, ElementTree.ParseError, ValueError):
        raise HTTPException(503, "Vehicle catalog is temporarily unavailable. You can enter the details manually.")
    return {"options": options, "source": "FuelEconomy.gov"}
