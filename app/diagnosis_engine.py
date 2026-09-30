from typing import Any


def make_cause(
    title: str,
    confidence: float,
    why: str,
    checks: list[str],
    repair: list[str],
    safety: str = "medium",
) -> dict[str, Any]:
    return {
        "title": title,
        "confidence": confidence,
        "why": why,
        "checks": checks,
        "repair": repair,
        "safety": safety,
    }


def contains(text: str, *phrases: str) -> bool:
    return any(phrase in text for phrase in phrases)


def build_diagnostic_causes(
    category: str,
    symptom: str,
    answers: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    answers = answers or {}
    answer_text = " ".join(str(value) for value in answers.values())
    text = f"{symptom} {answer_text}".lower()

    causes: list[dict[str, Any]] = []

    def add(cause: dict[str, Any]) -> None:
        if not any(item["title"] == cause["title"] for item in causes):
            causes.append(cause)

    if category == "automotive":
        if contains(
            text,
            "cranks but",
            "turns over but",
            "crank no start",
        ):
            add(make_cause(
                "Crank-no-start condition",
                0.88,
                "The starter turns the engine, so testing should focus on fuel, spark, injector command, compression, timing, and engine-speed signals.",
                [
                    "Scan for stored and pending trouble codes.",
                    "Check live engine RPM while cranking.",
                    "Test ignition spark with an approved spark tester.",
                    "Measure fuel pressure against specification.",
                    "Check injector pulse and engine compression.",
                ],
                [
                    "Repair the fuel, ignition, sensor, wiring, timing, or compression fault confirmed by testing.",
                    "Do not replace parts until the missing requirement is identified.",
                ],
                "high",
            ))

        elif contains(
            text,
            "won't start",
            "wont start",
            "will not start",
            "no start",
            "not starting",
        ):
            add(make_cause(
                "Starting-system diagnosis required",
                0.79,
                "The first step is separating a no-crank, slow-crank, clicking, and crank-no-start condition.",
                [
                    "State whether the engine cranks, clicks, turns slowly, or does nothing.",
                    "Measure battery voltage before and during a start attempt.",
                    "Inspect terminals, grounds, and starter cables.",
                    "Check the security or immobilizer indicator.",
                    "Scan all available modules for trouble codes.",
                ],
                [
                    "Repair the circuit or system that fails testing.",
                    "Avoid replacing the battery, starter, or fuel pump without confirmation.",
                ],
                "high",
            ))

        if contains(
            text,
            "battery dead",
            "battery dies",
            "dead overnight",
            "not charging",
            "charge light",
        ):
            add(make_cause(
                "Battery, charging-system, or parasitic-draw fault",
                0.86,
                "A discharged battery may be caused by a weak battery, poor connections, alternator trouble, belt trouble, or an electrical draw while parked.",
                [
                    "Fully charge and load-test the battery.",
                    "Measure charging voltage with the engine running.",
                    "Inspect the alternator belt, battery cables, and grounds.",
                    "Perform cable voltage-drop tests.",
                    "Perform a key-off parasitic-current test after modules sleep.",
                ],
                [
                    "Repair poor cable or ground connections.",
                    "Replace a failed battery or alternator only after testing.",
                    "Isolate and repair any excessive key-off draw.",
                ],
                "high",
            ))

        if contains(
            text,
            "overheat",
            "overheating",
            "runs hot",
            "pushing coolant",
            "boiling coolant",
        ):
            add(make_cause(
                "Cooling-system fault",
                0.90,
                "Overheating can result from low coolant, leakage, trapped air, fan failure, thermostat trouble, poor circulation, restriction, or combustion gases.",
                [
                    "Do not open the cooling system while hot.",
                    "Check coolant level only after the engine cools.",
                    "Pressure-test the system and cap.",
                    "Verify cooling-fan operation.",
                    "Check thermostat operation and coolant circulation.",
                    "Test for combustion gases if coolant is expelled.",
                ],
                [
                    "Repair leaks and refill using the correct bleeding procedure.",
                    "Replace failed cooling components only after confirming the fault.",
                    "Stop driving if engine temperature is excessive.",
                ],
                "stop",
            ))

        if contains(
            text,
            "misfire",
            "rough idle",
            "runs rough",
            "shaking",
            "flashing check engine",
            "p030",
        ):
            add(make_cause(
                "Engine misfire",
                0.88,
                "The engine may have an ignition, fuel, intake-air, compression, timing, wiring, or sensor fault.",
                [
                    "Scan codes and review misfire counters.",
                    "Inspect spark plugs, coils, boots, and connectors.",
                    "Check for vacuum and intake leaks.",
                    "Verify injector operation and fuel pressure.",
                    "Perform compression or leak-down testing if needed.",
                ],
                [
                    "Repair the confirmed ignition, fuel, air, electrical, or mechanical fault.",
                    "Do not continue driving with a severe misfire and flashing check-engine light.",
                ],
                "high",
            ))

        if contains(
            text,
            "brake",
            "brakes",
            "pedal soft",
            "pedal to floor",
            "grinding when stopping",
            "no brakes",
        ):
            add(make_cause(
                "Brake-system fault",
                0.92,
                "Grinding, poor stopping, fluid loss, warning lamps, or abnormal pedal travel requires immediate inspection.",
                [
                    "Do not drive if braking ability is reduced.",
                    "Check brake-fluid level and inspect for leakage.",
                    "Inspect pads, rotors, calipers, hoses, and wheel cylinders.",
                    "Check pedal firmness and booster operation.",
                    "Scan the ABS module when warning lamps are present.",
                ],
                [
                    "Repair worn, leaking, seized, or damaged brake components.",
                    "Bleed the hydraulic system correctly after repairs.",
                    "Tow the vehicle when braking performance is unsafe.",
                ],
                "high",
            ))

        if contains(
            text,
            "belt",
            "squeal",
            "chirp",
            "shredding",
            "belt walking",
        ):
            add(make_cause(
                "Accessory-belt tracking or tension fault",
                0.86,
                "Belt noise or edge damage commonly indicates incorrect routing, poor tension, pulley misalignment, bearing drag, contamination, or the wrong belt.",
                [
                    "Verify the correct belt and routing.",
                    "Inspect the belt ribs and edge-damage pattern.",
                    "Spin each pulley and check for roughness or play.",
                    "Observe tensioner movement and pulley alignment.",
                    "Check for oil or coolant contamination.",
                ],
                [
                    "Correct the failed pulley, tensioner, bearing, bracket, or alignment problem.",
                    "Replace the belt only after correcting the root cause.",
                ],
                "high",
            ))

        if contains(
            text,
            "speedometer",
            "odometer",
            "cruise control",
            "vehicle speed",
            "speed gauge",
        ):
            add(make_cause(
                "Vehicle-speed signal fault",
                0.90,
                "The speedometer, odometer, cruise control, ABS, transmission, and engine controller may share vehicle-speed data.",
                [
                    "Scan all modules for speed-sensor and communication codes.",
                    "Compare wheel-speed and vehicle-speed live data.",
                    "Inspect relevant sensor wiring and connectors.",
                    "Inspect tone rings where wheel-speed sensors are used.",
                    "Verify module power, grounds, and communication.",
                ],
                [
                    "Repair damaged wiring, connectors, tone rings, sensors, or module communication.",
                    "Replace a sensor only after testing its circuit and signal.",
                ],
                "medium",
            ))

    elif category == "appliance":
        if contains(
            text,
            "won't drain",
            "wont drain",
            "not draining",
            "standing water",
        ):
            add(make_cause(
                "Drain restriction or drain-pump fault",
                0.88,
                "Standing water is commonly caused by a blocked filter, hose, drain connection, check valve, pump, or control circuit.",
                [
                    "Disconnect power before accessing components.",
                    "Clean the filter and sump.",
                    "Inspect the drain hose for kinks or blockage.",
                    "Verify the household drain connection is open.",
                    "Test whether the pump receives voltage when commanded.",
                ],
                [
                    "Remove restrictions and correct the hose installation.",
                    "Replace the pump only if it receives proper power but cannot operate.",
                ],
                "high",
            ))

        if contains(
            text,
            "no heat",
            "not heating",
            "not drying",
            "cold dryer",
        ):
            add(make_cause(
                "Heating-circuit or airflow fault",
                0.86,
                "The appliance may have a failed heater, igniter, thermostat, thermal fuse, sensor, relay, airflow path, or supply circuit.",
                [
                    "Disconnect power or shut off fuel before service.",
                    "Verify correct supply voltage or gas supply.",
                    "Check airflow and clean restrictions.",
                    "Test thermal protection devices and sensors.",
                    "Test the heating circuit using the wiring diagram.",
                ],
                [
                    "Restore airflow before replacing parts.",
                    "Replace only components that fail testing.",
                ],
                "high",
            ))

    elif category == "equipment":
        if contains(
            text,
            "won't start",
            "wont start",
            "no start",
            "not starting",
        ):
            add(make_cause(
                "Small-engine fuel, spark, compression, or safety-switch fault",
                0.86,
                "A small engine requires fresh fuel, ignition spark, compression, airflow, and enabled safety controls.",
                [
                    "Use fresh fuel and verify the correct mixture.",
                    "Inspect and test the spark plug.",
                    "Check the air filter, choke, primer, and fuel flow.",
                    "Inspect safety switches and the ignition kill wire.",
                    "Test compression if fuel and spark are present.",
                ],
                [
                    "Replace stale fuel and a fouled spark plug.",
                    "Clean or rebuild the carburetor if fuel delivery is restricted.",
                    "Repair failed ignition, safety-switch, or mechanical components based on testing.",
                ],
                "medium",
            ))

        if contains(
            text,
            "starts then dies",
            "runs then dies",
            "only runs on choke",
            "won't stay running",
            "surging",
        ):
            add(make_cause(
                "Restricted carburetor or fuel delivery",
                0.89,
                "An engine that starts but will not remain running commonly has restricted fuel flow, blocked carburetor passages, tank-vent trouble, or an intake leak.",
                [
                    "Briefly loosen the fuel cap to test venting.",
                    "Check continuous fuel flow to the carburetor.",
                    "Inspect fuel lines and the filter.",
                    "Inspect carburetor jets and passages.",
                    "Check intake gaskets for leakage.",
                ],
                [
                    "Clean or rebuild the carburetor.",
                    "Replace damaged fuel lines, filters, primers, or vent parts.",
                ],
                "medium",
            ))

    causes.sort(key=lambda item: item["confidence"], reverse=True)
    return causes[:3]


def fallback_cause(
    category: str,
    media_count: int = 0,
    answers: dict[str, Any] | None = None,
) -> dict[str, Any]:
    checks = {
        "automotive": [
            "Enter the year, make, model, engine size, and mileage.",
            "State whether it cranks, starts, clicks, stalls, overheats, leaks, or displays warning lights.",
            "Enter all trouble codes exactly as displayed.",
            "Describe when the problem occurs.",
        ],
        "motorcycle": [
            "Enter the year, make, model, engine size, and mileage.",
            "State whether it cranks, starts, stalls, misfires, leaks, or loses power.",
            "Include warning lights, codes, battery voltage, and recent repairs.",
        ],
        "appliance": [
            "Enter the appliance type, brand, and complete model number.",
            "Enter the exact error code.",
            "State whether it powers on and which function fails.",
            "Describe when the failure occurs during the cycle.",
        ],
        "equipment": [
            "Enter the equipment type, brand, model, and engine model.",
            "State whether it cranks, starts, runs briefly, smokes, surges, or loses power.",
            "Include fuel age, spark-plug condition, and recent repairs.",
        ],
        "home": [
            "Identify whether this involves electrical, plumbing, HVAC, flooring, roofing, or structure.",
            "Describe the exact location and when the condition occurs.",
            "State whether water, electricity, gas, heat, smoke, or movement is involved.",
        ],
        "diy": [
            "Describe the intended result and current problem.",
            "List materials, measurements, tools, and fasteners.",
            "State whether electrical, gas, structural, chemical, or lifting hazards are present.",
        ],
    }

    item = (answers or {}).get("item")
    if category in {"automotive", "motorcycle"} and isinstance(item, dict):
        # The unified form already supplies these details even for unsaved vehicles.
        missing = [label for key, label in [("year", "year"), ("make", "make"),
                   ("model", "model"), ("engine", "engine size")]
                   if not item.get(key)]
        checks[category] = checks[category][1:]
        if missing:
            checks[category].insert(0, "Add the missing vehicle details: " + ", ".join(missing) + ".")

    if media_count == 1:
        media_note = "One attachment was received. "
    elif media_count > 1:
        media_note = f"{media_count} attachments were received. "
    else:
        media_note = ""

    return make_cause(
        "More specific details needed",
        0.60 if media_count else 0.56,
        media_note
        + "The description does not yet contain enough information for a reliable repair path.",
        checks.get(category, checks["diy"]),
        [
            "Add the requested information and submit the diagnosis again."
        ],
        "medium",
    )
