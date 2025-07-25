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

# --- Fallback Rule Inference ---
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

        # If no static rules, attempt to infer
        if not rules:
            st.warning(f"⚠️ No predefined rules for `{country_code}`. Attempting auto-rule generation...")
            inferred_rules = infer_country_rules_from_columns(gdf.columns, country_code)
            st.info("🧠 Inferred Rule:")
            st.json(inferred_rules)

            if st.checkbox("✅ Use inferred rule for validation?"):
                rules = inferred_rules
            else:
                st.stop()

        # --- AI Agent Validation Logic ---
        if rules:
            st.info("🔍 Ready to run address quality checks...")
            if st.button("▶️ Run Address Quality Checks"):
                st.success("🚀 Running with the following rules:")
                st.json(rules)

                results = []
                gdf["Remark"] = ""  # Init empty remark field

                # Mandatory Fields Present in Schema
                mandatory_fields = rules.get("mandatory_fields", [])
                missing_fields = [field for field in mandatory_fields if field not in gdf.columns.str.lower()]
                if missing_fields:
                    results.append(f"❌ Missing mandatory fields: {', '.join(missing_fields)}")
                else:
                    results.append("✅ All mandatory fields are present.")

                # Row-level missing values in mandatory fields
                for field in mandatory_fields:
                    matches = [col for col in gdf.columns if col.lower() == field]
                    if matches:
                        col = matches[0]
                        missing_mask = gdf[col].isna() | (gdf[col].astype(str).str.strip() == "")
                        gdf.loc[missing_mask, "Remark"] += f"{col} is missing|"
                        results.append(f"⚠️ {missing_mask.sum()} missing values in `{col}`.")

                # Postal Code Length Check
                if "postal_code" in [f.lower() for f in rules.get("expected_attributes", [])]:
                    postal_cols = [col for col in gdf.columns if "postal" in col.lower() or "zip" in col.lower()]
                    if postal_cols:
                        postal_col = postal_cols[0]
                        gdf[postal_col] = gdf[postal_col].astype(str)
                        wrong_length_mask = ~gdf[postal_col].str.len().eq(rules["postal_code_length"])
                        gdf.loc[wrong_length_mask, "Remark"] += f"{postal_col} wrong length|"
                        results.append(f"📮 Postal code length errors: {wrong_length_mask.sum()} rows (expected {rules['postal_code_length']} digits)")
                    else:
                        results.append("⚠️ No postal code column found for length check.")

                # Geometry checks
                null_geom_mask = gdf.geometry.isnull()
                gdf.loc[null_geom_mask, "Remark"] += "Null geometry|"
                if null_geom_mask.any():
                    results.append(f"❌ {null_geom_mask.sum()} null geometries found.")
                else:
                    results.append("✅ No null geometries.")

                invalid_geom_mask = ~gdf.is_valid
                gdf.loc[invalid_geom_mask, "Remark"] += "Invalid geometry|"
                if invalid_geom_mask.any():
                    results.append(f"❌ {invalid_geom_mask.sum()} invalid geometries found.")
                else:
                    results.append("✅ All geometries are valid.")

                # CRS check
                crs = gdf.crs
                if crs:
                    results.append(f"🧭 CRS detected: `{crs}`")
                else:
                    results.append("⚠️ CRS not set in the data.")

                # Final clean-up of trailing pipes
                gdf["Remark"] = gdf["Remark"].str.rstrip("|")

                # --- Display Results ---
                st.subheader("🧪 Quality Check Summary")
                for res in results:
                    st.write(res)

                error_rows = gdf[gdf["Remark"] != ""]
                if not error_rows.empty:
                    st.subheader(f"🚨 {len(error_rows)} Rows with Issues")
                    st.dataframe(error_rows)
                else:
                    st.success("🎉 No row-level issues found!")

else:
    st.info("📥 Please upload a file and enter a valid 3-digit ISO country code.")
