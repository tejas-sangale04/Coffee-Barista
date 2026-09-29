def filter_candidates(items, preferences):

    filtered = []

    for item in items:

        nutrition = item.get("nutrition", {})
        dietary = item.get("dietary", {})

        # Budget
        max_price = preferences.get("max_price")

        if max_price is not None:
            if item["price"] > max_price:
                continue

        # Calories
        max_calories = preferences.get("max_calories")

        if max_calories is not None:
            if nutrition.get("calories", 999999) > max_calories:
                continue

        # Dairy-free
        if preferences.get("dairy_free"):

            if not dietary.get("dairy_free", False):
                continue

        # Vegan
        if preferences.get("vegan"):

            if not dietary.get("vegan", False):
                continue

        # Availability
        if not item.get("availability", {}).get("available", True):
            continue

        filtered.append(item)

    return filtered
def rank_candidates(items, preferences):

    ranked = []

    for item in items:

        score = 0

        tags = set(item.get("tags", []))
        nutrition = item.get("nutrition", {})

        # Temperature
        temperature = preferences.get("temperature")

        if temperature and temperature in tags:
            score += 25

        # Strength
        strength = preferences.get("strength")

        if strength and strength in tags:
            score += 25

        # Sweetness
        sweetness = preferences.get("sweetness")

        if sweetness == "low":
            if "sugar-free" in tags:
                score += 20
            elif nutrition.get("sugar_g", 999) < 5:
                score += 10

        # High caffeine
        if preferences.get("high_caffeine"):

            if nutrition.get("caffeine_mg", 0) >= 150:
                score += 20

        # Price preference
        max_price = preferences.get("max_price")

        if max_price:
            if item["price"] <= max_price:
                score += 10

        ranked.append({
            "item": item,
            "score": score
        })

    ranked.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return ranked