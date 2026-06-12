def transform_rows(rows):
    result = []
    for row in rows:
        item = {
            "id": row["id"],
            "name": row["name"].strip(),
        }
        result.append(item)
    return result
