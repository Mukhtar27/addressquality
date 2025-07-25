# rule_engine.py

country_rules = {
    "IND": {
        "country_name": "India",
        "expected_attributes": ["street_name", "house_number", "postal_code", "state", "city"],
        "postal_code_length": 6,
        "language_support": ["en", "hi"],
        "accuracy_expectation": "parcel",
        "mandatory_fields": ["street_name", "house_number", "postal_code"],
        "notes": "Dependent Locality often not used; region-specific scripts may apply."
    },
    "ARE": {
        "country_name": "United Arab Emirates",
        "expected_attributes": ["street_name", "building_name", "zone", "emirate"],
        "postal_code_length": 0,
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
    },
    "OMN": {
        "country_name": "Oman",
        "expected_attributes": ["street_name", "building_number", "wilayat", "governorate", "postal_code"],
        "postal_code_length": 3,
        "language_support": ["en", "ar"],
        "accuracy_expectation": "building",
        "mandatory_fields": ["street_name", "building_number", "postal_code"],
        "notes": "Addresses are linked to municipality systems; building number and locality are essential."
    },
    "QAT": {
        "country_name": "Qatar",
        "expected_attributes": ["zone", "street_number", "building_number", "municipality"],
        "postal_code_length": 0,
        "language_support": ["en", "ar"],
        "accuracy_expectation": "building",
        "mandatory_fields": ["zone", "street_number", "building_number"],
        "notes": "Postcodes are not commonly used. Zone and building number are mandatory for delivery."
    },
    "BHR": {
        "country_name": "Bahrain",
        "expected_attributes": ["building_number", "road", "block", "area"],
        "postal_code_length": 0,
        "language_support": ["en", "ar"],
        "accuracy_expectation": "rooftop",
        "mandatory_fields": ["building_number", "road", "block"],
        "notes": "Block and road-based addressing; rooftop-level accuracy preferred."
    },
    "KWT": {
        "country_name": "Kuwait",
        "expected_attributes": ["building_number", "street", "block", "governorate"],
        "postal_code_length": 5,
        "language_support": ["en", "ar"],
        "accuracy_expectation": "building",
        "mandatory_fields": ["building_number", "street", "block"],
        "notes": "Postal code is usually known by area. Building and block are key."
    }
}

def get_country_rules(iso3_code: str):
    """
    Fetch address point quality rules for a given country ISO3 code.
    """
    iso3_code = iso3_code.strip().upper()
    return country_rules.get(iso3_code)
