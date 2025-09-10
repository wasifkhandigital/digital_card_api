def generate_vcard(data: dict) -> str:
    vcard = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"N:{data['name']}",
        f"TEL:{data['phone']}",
        f"EMAIL:{data['email']}",
    ]

    # Optional fields
    if data.get("job_title"):
        vcard.append(f"TITLE:{data['job_title']}")
    if data.get("company"):
        vcard.append(f"ORG:{data['company']}")
    if data.get("website"):
        vcard.append(f"URL:{data['website']}")

    vcard.append("END:VCARD")
    return "\n".join(vcard)
