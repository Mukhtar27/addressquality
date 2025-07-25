import streamlit as st
import geopandas as gpd
import tempfile
import zipfile
import os
from rule_engine import get_country_rules

# --- Page Setup ---
st.set_page_config(page_title="Address Point Quality Checker", layout="wide")
st.title("🌍 Address Point Quality Checker (AI Agent)")

# --- File Upload ---
uploaded_file = st.file_uploader("📂 Upload Address File (.shp.zip or .gpkg)", type=["zip", "gpkg"])
country_code = st.text_input("🌐 Enter 3-digit ISO Country Code (e.g., ARE, IND, SAU)").upper()

# --- Read Geodata ---
def load_geodata(uploaded_file):
    if uploaded_file.name.endswith(".zip"):
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, "data.zip")
            with open(zip_path, "wb") as f:
                f.write(uploaded_file.read())
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(tmpdir)
                shp_files = [f for f in os.listdir(tmpdir) if f.endswith(".shp")]
                if not shp_files:
                    st.error("No .shp file found inside zip.")
                    return None
                return gpd.read_file(os.path.join(tmpdir, shp_files[0]))
    elif uploaded_file.name.endswith(".gpkg"):
        return gpd.read_file(uploaded_file)
    else:
        st.error("Unsupported file type.")
        return None

# --- Fallback Inference Rule Generator ---
def infer_country_rules_from_columns(columns, iso_code):
    inferred = [col.lower() for col in columns]
    rules = {
        "country_name": "Unknown",
        "expected_attributes": [],
        "postal_code_length": 6,
        "language_support": ["en"],
        "accuracy_expectation": "parcel",
        "mandatory_fields": [],
        "notes": "Auto-generated rule based on column names"
    }

    if any("street" in col for col in inferred):
        rules["expected_attributes"].append("street_name")
        rules["mandatory_fields"].append("street_name")

    if any("house" in col or "building" in col for col in inferred):
        rules["expected_attributes"].append("house_number")
        rules["mandatory_fields"].append("house_number")

    if any("postal" in col or "zip" in col for col in inferred):
        rules["expected_attributes"].append("postal_code")
        rules["mandatory_fields"].append("postal_code")

    if any("state" in col or "province" in col for col in inferred):
        rules["expected_attributes"].append("state")

    if any("city" in col or "town" in col for col in inferred):
        rules["expected_attributes"].append("city")

    return rules

# --- MAIN WORKFLOW ---
if uploaded_file and country_code:
    st.success(f"📌 File uploaded and country set to: `{country_code}`")

    with st.spinner("🧠 Reading geospatial data..."):
        gdf = load_geodata(uploaded_file)

    if gdf is not None:
        st.subheader("📊 Data Sample Preview")
        st.dataframe(gdf.head(10))

        rules = get_country_rules(country_code)

        # If rule not found, try to infer
        if not rules:
            st.warning(f"⚠️ No predefined rules for `{country_code}`. Attempting auto-rule generation...")
            inferred_rules = infer_country_rules_from_columns(gdf.columns, country_code)
            st.info("🧠 Inferred Rule:")
            st.json(inferred_rules)

            if st.checkbox("✅ Use inferred rule for validation?"):
                rules = inferred_rules
            else:
                st.stop()

        # Final AI Agent Check Trigger
        if rules:
            st.info("🔍 Ready to run address quality checks...")
            if st.button("▶️ Run Address Quality Checks"):
                st.success("🚀 Running with the following rules:")
                st.json(rules)
                st.warning("🚧 Quality check logic will be added in next step.")

else:
    st.info("📥 Please upload a file and enter a valid 3-digit ISO country code.")
