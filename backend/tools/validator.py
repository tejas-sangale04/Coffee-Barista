def validate_recommendations(recommendations, valid_candidates):

    valid_items = {
        item["name"]: item
        for item in valid_candidates
        if item.get("name")
    }

    invalid_items = []

    for recommendation in recommendations:

        name = recommendation.get("name")
        price = recommendation.get("price")

        # Check whether item exists
        if name not in valid_items:
            invalid_items.append({
                "name": name,
                "reason": "Item was not present in valid candidates"
            })
            continue

        # Check price
        actual_price = valid_items[name].get("price", {}).get("amount")

        if price != actual_price:
            invalid_items.append({
                "name": name,
                "reason": "Price does not match menu data"
            })

    return {
        "valid": len(invalid_items) == 0,
        "invalid_items": invalid_items
    }