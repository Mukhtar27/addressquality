# app.py

import streamlit as st
import geopandas as gpd
import tempfile
import os
import json
import pandas as pd
from rule_engine import get_country_rules
from difflib import get_close_matches
import ollama

st.set_page_config(page_title="Address Point Quality Checker", layout="wide")

st.title("📍 Address Point Data Quality AI Agent")

uploaded_file = st.file_uploader("Upload address point file (.shp or .gpkg)", type=["shp", "gpkg"])
iso_code = st.text_input("Enter 3-digit ISO country code (e.g., IND, ARE, SAU):").upper()

if uploaded_file and iso_code:
    # Save uploaded file to a temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Load data
        if uploaded_file.name.endswith(".shp"):
            gdf = gpd.read_file(file_path)
        else:
            gdf = gpd.read_file(file_path)

        st.success("✅ File successfully loaded.")
        st.write(f"CRS detected: {gdf.crs}")

        rules = get_country_rules(iso_code)

        if not rules:
            st.error("❌ No rules found for the given ISO code.")
        else:
            st.info(f"🧠 Loaded rules for **{rules['country_name']}**")
            expected_attributes = rules["expected_attributes"]
            mandatory_fields = rules["mandatory_fields"]

            # ---------- LLM-BASED COLUMN MAPPING ----------
            def get_column_mapping_with_llm(expected, actual):
                prompt = f"""
You are an expert in address data validation.

Map the following expected address fields to the actual column names found in a geospatial dataset. The mapping should only include best guesses if the actual name closely resembles the expected one.

Respond ONLY with a JSON dictionary.

Expected: {expected}
Actual: {actual}
"""
                response = ollama.chat(
                    model="llama3",
                    messages=[{"role": "user", "content": prompt}]
                )
                try:
                    mapping = json.loads(response['message']['content'])
                    return mapping
                except Exception as e:
                    st.error("❌ LLM failed to infer column mappings.")
                    return {}

            actual_columns = list(gdf.columns)
            mapping = get_column_mapping_with_llm(expected_attributes, actual_columns)
            st.write("🧩 Inferred Column Mapping (without renaming):")
            st.json(mapping)

            # Quality Checks
            quality_issues = []
            gdf["Remark"] = ""

            for idx, row in gdf.iterrows():
                row_remarks = []

                # Check for missing mandatory fields (based on mapping)
                for expected_field in mandatory_fields:
                    actual_col = mapping.get(expected_field)
                    if actual_col and pd.isna(row.get(actual_col, None)):
                        row_remarks.append(f"Missing `{expected_field}`")

                # Optional: Spelling anomaly check (naive approach using basic heuristics)
                for expected_field in expected_attributes:
                    actual_col = mapping.get(expected_field)
                    if actual_col in gdf.columns and isinstance(row[actual_col], str):
                        val = row[actual_col]
                        if len(val) > 3 and not val.replace(" ", "").isalpha():
                            row_remarks.append(f"Suspicious content in `{expected_field}`")

                gdf.at[idx, "Remark"] = " | ".join(row_remarks)

            # Final summary
            st.subheader("🧪 Quality Check Summary")
            missing_mandatory = [f for f in mandatory_fields if f not in mapping or mapping[f] not in gdf.columns]
            if missing_mandatory:
                st.error(f"❌ Missing mapped mandatory fields: {', '.join(missing_mandatory)}")
            else:
                st.success("✅ All mapped mandatory fields present.")

            if gdf.geometry.isna().any():
                st.error("❌ Null geometries detected.")
            else:
                st.success("✅ No null geometries.")

            if not gdf.is_valid.all():
                st.warning("⚠️ Some geometries are invalid.")
            else:
                st.success("✅ All geometries are valid.")

            # Show preview
            st.subheader("🔍 Data Preview with Remarks")
            st.dataframe(gdf[[*gdf.columns.difference(['geometry']), 'Remark']].head(50))
