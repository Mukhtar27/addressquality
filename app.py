import streamlit as st
import geopandas as gpd
import tempfile
import zipfile
import os

from rule_engine import get_country_rules

# UI setup
st.set_page_config(page_title="Address Point Quality Checker", layout="wide")
st.title("🧠 Address Point Quality Checker (AI Agent)")

uploaded_file = st.file_uploader("📂 Upload Address File (.shp.zip or .gpkg)", type=["zip", "gpkg"])
country_code = st.text_input("🌍 Enter 3-digit ISO Country Code (e.g., IND, ARE, SAU)").upper()


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
        st.error("Unsupported file format.")
        return None


def run_quality_checks(gdf, rules):
    result = []

    for field in rules["mandatory_fields"]:
        if field not in gdf.columns:
            result.append({
                "Field": field,
                "Completeness": "nok",
                "Correctness": "nok",
                "Reason": "Missing expected attribute in schema"
            })
        else:
            empty_count = gdf[field].isna().sum() + (gdf[field] == "").sum()
            if empty_count > 0:
                result.append({
                    "Field": field,
                    "Completeness": "nok",
                    "Correctness": "nok",
                    "Reason": f"{empty_count} empty/null values"
                })
            else:
                result.append({
                    "Field": field,
                    "Completeness": "ok",
                    "Correctness": "ok",
                    "Reason": "Field present and populated"
                })

    return result


if uploaded_file and country_code:
    rules = get_country_rules(country_code)

    if rules:
        st.success(f"✅ Rules loaded for `{rules['country_name']}`")
        st.json(rules)

        gdf = load_geodata(uploaded_file)
        if gdf is not None:
            st.subheader("📌 Sample Data Preview")
            st.dataframe(gdf.head(10))

            if st.button("🔎 Run Completeness & Correctness Checks"):
                with st.spinner("Analyzing data..."):
                    check_results = run_quality_checks(gdf, rules)

                st.subheader("✅ Check Results")
                st.dataframe(check_results)

    else:
        st.error("❌ No rules found for this ISO code.")
else:
    st.info("📥 Please upload a file and provide ISO code to begin.")
