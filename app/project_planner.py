from __future__ import annotations

from typing import Any


def build_project_plan(
    description: str,
    answers: dict[str, Any] | None = None,
    media_count: int = 0,
) -> dict[str, Any]:
    answers = answers or {}
    text = (
        description
        + " "
        + " ".join(str(value) for value in answers.values())
    ).lower()

    media_note = ""
    if media_count == 1:
        media_note = " One attachment was included."
    elif media_count > 1:
        media_note = f" {media_count} attachments were included."

    if any(word in text for word in (
        "tile",
        "porcelain",
        "ceramic",
        "thinset",
        "grout",
    )):
        return {
            "title": "12x24 tile installation plan",
            "confidence": 0.94,
            "summary": (
                "Pocket Mechanic created a tile-installation project plan."
                + media_note
            ),
            "safety_message": (
                "Wear eye protection, gloves, hearing protection, knee "
                "protection, and suitable respiratory protection when cutting."
            ),
            "why": (
                "Large-format tile requires a flat and stable surface, careful "
                "layout, proper mortar coverage, and regular lippage checks."
            ),
            "checks": [
                "Measure the room and calculate the total square footage.",
                "Add approximately 10–15% for cuts, waste, and future repairs.",
                "Verify the floor is solid, clean, dry, and suitable for tile.",
                "Check the entire surface for high areas, low areas, and movement.",
                "Plan the layout before mixing mortar.",
                "Avoid narrow tile strips at visible walls and doorways.",
                "Dry-fit several tiles with the intended grout-joint spacing.",
                "Use mortar approved for the tile and the underlying surface.",
                "Key mortar into the surface and comb ridges in one direction.",
                "Back-butter each 12x24 tile before setting it.",
                "Move the tile across the mortar ridges to collapse them.",
                "Lift occasional tiles to confirm adequate mortar coverage.",
                "Check alignment, spacing, level, and lippage continuously.",
                "Allow the mortar to cure before walking on or grouting the tile.",
            ],
            "repair": [
                "Materials: tile, approved mortar, spacers or leveling clips, grout, and any required membrane or backer board.",
                "Tools: tape measure, level, straightedge, chalk line, notched trowel, margin trowel, buckets, mixer, wet saw, grout float, and sponges.",
                "Difficulty: intermediate.",
                "Complete all surface preparation and layout work before setting the first tile.",
                "Follow the mortar and grout manufacturers' curing instructions.",
            ],
        }

    if any(word in text for word in (
        "laminate",
        "vinyl plank",
        "hardwood",
        "flooring",
    )):
        return {
            "title": "Flooring installation plan",
            "confidence": 0.90,
            "summary": (
                "Pocket Mechanic created a flooring installation plan."
                + media_note
            ),
            "safety_message": (
                "Wear eye, knee, hearing, and respiratory protection while "
                "cutting and installing flooring."
            ),
            "why": (
                "Flooring installation depends on subfloor preparation, layout, "
                "expansion spacing, moisture control, and proper transitions."
            ),
            "checks": [
                "Measure the room and calculate the required flooring.",
                "Add the product manufacturer's recommended waste allowance.",
                "Confirm whether the flooring is floating, glued, nailed, or stapled.",
                "Verify the subfloor is clean, dry, flat, and securely fastened.",
                "Check whether acclimation is required.",
                "Plan the plank direction and stagger pattern.",
                "Install the required underlayment or vapor barrier.",
                "Maintain the required expansion gap around the perimeter.",
                "Plan door jamb cuts, transitions, and final-row width.",
            ],
            "repair": [
                "Materials: flooring, underlayment or vapor barrier, spacers, transitions, and trim.",
                "Tools: tape measure, square, saw, utility knife, tapping block, pull bar, and spacers.",
                "Do not fasten trim through a floating floor.",
            ],
        }

    if any(word in text for word in (
        "faucet",
        "toilet",
        "sink",
        "shower",
        "pex",
        "plumbing",
    )):
        return {
            "title": "Plumbing installation plan",
            "confidence": 0.86,
            "summary": (
                "Pocket Mechanic created a plumbing installation plan."
                + media_note
            ),
            "safety_message": (
                "Shut off the correct water supply and control nearby "
                "electrical hazards before opening plumbing connections."
            ),
            "why": (
                "A reliable plumbing installation requires compatible fittings, "
                "correct sealing, secure support, and complete leak testing."
            ),
            "checks": [
                "Identify the existing pipe material and size.",
                "Confirm the new fixture and fittings are compatible.",
                "Shut off and relieve the water supply.",
                "Protect nearby surfaces and prepare for residual water.",
                "Use thread sealant only where the fitting design requires it.",
                "Support pipes and fixtures without stressing connections.",
                "Restore water slowly and inspect every connection.",
                "Test fixture operation and drainage before closing the work area.",
            ],
            "repair": [
                "Prepare all fittings and tools before disconnecting the existing fixture.",
                "Use a licensed professional for gas piping, major drain alterations, or permit-required work.",
            ],
        }

    if any(word in text for word in (
        "paint",
        "painting",
        "primer",
    )):
        return {
            "title": "Painting project plan",
            "confidence": 0.88,
            "summary": (
                "Pocket Mechanic created a painting project plan."
                + media_note
            ),
            "safety_message": (
                "Ventilate the area and use proper ladder, eye, and respiratory protection."
            ),
            "why": (
                "Surface preparation, compatible primer, even application, and "
                "adequate drying time determine the finished appearance."
            ),
            "checks": [
                "Protect floors, furniture, fixtures, and adjacent surfaces.",
                "Clean the surface and remove loose paint, dust, grease, and mildew.",
                "Repair holes and cracks.",
                "Sand repairs and glossy areas as needed.",
                "Prime bare, stained, repaired, or incompatible surfaces.",
                "Cut in edges before rolling broad surfaces.",
                "Apply thin and even coats while maintaining a wet edge.",
                "Allow the required drying time before recoating.",
            ],
            "repair": [
                "Materials: cleaner, patching compound, primer, paint, tape, and protective coverings.",
                "Tools: brushes, rollers, tray, extension pole, scraper, sanding supplies, and ladder.",
            ],
        }

    return {
        "title": "DIY project plan",
        "confidence": 0.76,
        "summary": (
            "Pocket Mechanic created a general project plan."
            + media_note
        ),
        "safety_message": (
            "Identify electrical, structural, chemical, cutting, lifting, and "
            "tool hazards before beginning."
        ),
        "why": (
            "Providing dimensions, material types, existing conditions, and "
            "pictures will allow a more precise plan."
        ),
        "checks": [
            "Describe exactly what is being installed, built, removed, or refinished.",
            "Measure and record the complete work area.",
            "Identify the existing surface or structure.",
            "List the materials and tools already available.",
            "Choose the desired finished appearance.",
            "Check permits and manufacturer instructions.",
            "Create a measured layout before cutting materials.",
            "Perform a small test fit before permanent installation.",
        ],
        "repair": [
            "Add dimensions, material details, and pictures for a more detailed plan.",
            "Pocket Mechanic can then calculate quantities and produce an ordered installation guide.",
        ],
    }
