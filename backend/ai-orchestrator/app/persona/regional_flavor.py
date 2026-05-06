"""Regional flavor packs for seed cities. Spec §7 persona flavor.

For unknown cities, Gemini's general knowledge fills the gap.
"""

FLAVOR_PACKS: dict[str, dict] = {
    "Gurgaon": {
        "neighborhoods": [
            "Cyber Hub", "Galleria", "Sector 29", "Golf Course Road",
            "Sohna Road", "Ambience Mall area", "Leisure Valley",
        ],
        "slang": ["yaar", "scene kya hai", "proper", "bhai"],
        "food": [
            "butter chicken", "chole bhature", "momos", "galouti kebab",
            "parathas", "street chaat", "biryani", "sushi (Cyber Hub)",
        ],
        "do_notes": [
            "traffic on Golf Course Road peaks 8-10am and 6-8pm",
            "monsoon season July-September, roads can flood",
            "winter fog December-January, visibility drops sharply",
            "Sector 29 is the nightlife hub but gets loud weekends",
        ],
    },
    "Goa": {
        "neighborhoods": [
            "Panjim", "Calangute", "Anjuna", "Assagao", "Morjim",
            "Palolem", "Vagator", "Candolim", "Fontainhas",
        ],
        "slang": ["boss", "na", "re", "susegad", "dev bare koro"],
        "food": [
            "fish curry rice", "pork vindaloo", "bebinca", "goan sausage",
            "prawn balchao", "xacuti", "kingfish rawa fry", "feni",
            "sorpotel", "poee bread",
        ],
        "do_notes": [
            "suggest beach shacks not chain restaurants",
            "mention sunset timing — it matters here",
            "north Goa is lively, south Goa is quiet",
            "beach cleanliness varies — weekday mornings are best",
            "monsoon June-September: shacks close, but the state is lush green",
        ],
    },
    "Bangalore": {
        "neighborhoods": [
            "Indiranagar", "Koramangala", "JP Nagar", "Whitefield",
            "Malleshwaram", "Basavanagudi", "Church Street", "MG Road",
            "Jayanagar", "HSR Layout",
        ],
        "slang": ["machaa", "boss", "ya", "da", "super", "one plate"],
        "food": [
            "filter coffee", "masala dosa", "idli", "biryani", "vada pav",
            "butter chicken", "craft beer", "paddu", "obattu",
        ],
        "do_notes": [
            "traffic is heavy most hours — always note the ETAs",
            "weather is mild year-round, mention it casually",
            "Indiranagar and Koramangala for nightlife and food",
            "Cubbon Park area is the green lung — good for walking",
            "mention Nandi Hills for morning drives",
        ],
    },
}


def get_flavor_pack(city_name: str) -> dict | None:
    """Return flavor pack for a known seed city, or None for unknown cities."""
    return FLAVOR_PACKS.get(city_name)


def format_flavor_text(city_name: str, flavor: dict | None) -> str:
    """Produce the local flavor sentence injected into the persona prompt."""
    if flavor is None:
        return (
            f"You have general knowledge of {city_name}. "
            f"Use your knowledge of its neighborhoods, food, culture, and character "
            f"to make the user feel like a local is guiding them."
        )

    parts = []
    neighborhoods = flavor.get("neighborhoods", [])
    if neighborhoods:
        parts.append(f"Key neighborhoods: {', '.join(neighborhoods[:6])}.")

    food = flavor.get("food", [])
    if food:
        parts.append(f"Local food: {', '.join(food[:6])}.")

    slang = flavor.get("slang", [])
    if slang:
        parts.append(f"Use these local terms naturally where it fits: {', '.join(slang)}.")

    do_notes = flavor.get("do_notes", [])
    if do_notes:
        parts.append("Local notes: " + " | ".join(do_notes))

    return " ".join(parts)
