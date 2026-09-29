def filter_candidates(items, preferences):

    filtered = []

    for item in items:


        # -------------------------------------------------
        # Price
        # -------------------------------------------------

        price = item.get("price", {})

        if isinstance(price, dict):
            price_amount = price.get("amount")
            currency = price.get("currency", "INR")
        else:
            price_amount = price
            currency = "INR"

        # We only support INR for now
        if currency != "INR":
            continue

        # Maximum price
        max_price = preferences.get("max_price")

        if max_price is not None:

            if price_amount is None:
                continue

            if price_amount > max_price:
                continue

        # Minimum price
        min_price = preferences.get("min_price")

        if min_price is not None:

            if price_amount is None:
                continue

            if price_amount < min_price:
                continue

        # -------------------------------------------------
        # Dietary
        # -------------------------------------------------

        dietary = item.get("dietary", {})

        # Vegan
        if preferences.get("vegan") is True:

            if dietary.get("vegan") is not True:
                continue

        # Dairy-free
        if preferences.get("dairy_free") is True:

            if dietary.get("dairy_free") is not True:
                continue

        # Sugar-free
        if preferences.get("sugar_free") is True:

            if dietary.get("sugar_free") is not True:
                continue

        # -------------------------------------------------
        # Calories
        # -------------------------------------------------

        nutrition = item.get("nutrition", {})

        max_calories = preferences.get("max_calories")

        if max_calories is not None:

            calories = nutrition.get("calories")

            # Unknown calories cannot satisfy
            # a strict calorie limit.
            if calories is None:
                continue

            if calories > max_calories:
                continue

        # -------------------------------------------------
        # Category
        # -------------------------------------------------

        category = preferences.get("category")

        if category is not None:

            item_category = item.get("category")

            if item_category != category:
                continue

        # -------------------------------------------------
        # Temperature
        # -------------------------------------------------

        temperature = preferences.get("temperature")

        if temperature is not None:

            item_temperature = (
                item.get("serving", {})
                .get("temperature")
            )

            if item_temperature != temperature:
                continue

        # -------------------------------------------------
        # All hard filters passed
        # -------------------------------------------------

        filtered.append(item)

    return filtered