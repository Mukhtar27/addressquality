# Install dependencies (commented out to avoid reinstallation)
# !pip install --quiet streamlit geopandas ollama

import streamlit as st
import geopandas as gpd
import tempfile
import zipfile
import os
import re
import ollama
from rule_engine import get_country_rules

# --- Page Setup ---
st.set_page_config(page_title="Address Point Quality Checker (AI Agent)", layout="wide")
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

# --- LLM Helpers ---
def analyze_value_anomalies(row_data):
    prompt = (
        "You are a data quality assistant. Given address data values, identify spelling errors or strange entries. "
        "Only report anomalies. Do NOT suggest corrections. "
        "Format response as: 'ColumnName: issue' (multiple issues separated by '|').\n\n"
        f"Example row:\n{row_data}\n\nAnomalies:"
    )
    response = ollama.chat(model="llama3", messages=[{"role": "user", "content": prompt}])
    return response['message']['content'].strip()

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

                # Begin quality checks
                remarks = []
                mandatory_fields = rules["mandatory_fields"]
                expected_attributes = rules["expected_attributes"]

                for _, row in gdf.iterrows():
                    row_remark = []

                    # Mandatory field check
                    for field in mandatory_fields:
                        matched = next((col for col in gdf.columns if re.fullmatch(field, col, flags=re.IGNORECASE)), None)
                        if matched and pd.isna(row[matched]):
                            row_remark.append(f"{field}: missing")

                    # LLM value anomaly check
                    subset = row[expected_attributes].dropna().astype(str).to_dict()
                    if subset:
                        issues = analyze_value_anomalies(subset)
                        if issues and issues.lower() != "none":
                            row_remark.append(issues)

                    remarks.append(" | ".join(row_remark) if row_remark else "")

                gdf["Remark"] = remarks

                st.subheader("✅ Final Output Sample")
                st.dataframe(gdf.head(10))
                st.download_button("📥 Download Checked File (GeoJSON)", gdf.to_json(), file_name="checked_output.geojson", mime="application/json")

else:
    st.info("📥 Please upload a file and enter a valid 3-digit ISO country code.")
