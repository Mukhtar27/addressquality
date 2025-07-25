# rule_engine.py

# Country-specific rules for address point quality checks
country_rules = {
    "IND": {
        "country_name": "India",
        "expected_attributes": ["street_name", "house_number", "postal_code", "state", "city"],
        "postal_code_length": 6,
        "language_support": ["en", "hi"],
        "accuracy_expectation": "parcel",  # could be rooftop, parcel, entrance, etc.
        "mandatory_fields": ["street_name", "house_number", "postal_code"],
        "notes": "Dependent Locality often not used; region-specific scripts may apply."
    },
    "ARE": {
        "country_name": "United Arab Emirates",
        "expected_attributes": ["street_name", "building_name", "zone", "emirate"],
        "postal_code_length": 0,  # UAE does not use postal codes
        "language_support": ["en", "ar"],
        "accuracy_expectation": "building",
        "mandatory_fields": ["street_name", "building_name"],
        "notes": "Building names are crucial; postcode not applicable."
    },
    "SAU": {
        "country_name": "Saudi Arabia",
        "expected_attributes": ["street_name", "building_number", "district", "city", "postal_code"],
        "postal_code_length": 5,
        "language_support": ["en", "ar"],
        "accuracy_expectation": "rooftop",
        "mandatory_fields": ["street_name", "building_number", "postal_code"],
        "notes": "Wasel system applies; rooftop accuracy preferred."
    }
    # You can add more countries with similar structure
}

def get_country_rules(iso3_code: str):
    """
    Fetch address point quality rules for a given country ISO3 code.
    """
    iso3_code = iso3_code.strip().upper()
    return country_rules.get(iso3_code)
