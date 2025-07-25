import streamlit as st
import geopandas as gpd
import tempfile
import zipfile
import os

# Page config
st.set_page_config(page_title="Address Point Quality Checker", layout="wide")
st.title("🌍 Address Point Quality Checker (AI Agent)")

# File upload
uploaded_file = st.file_uploader("📂 Upload Address File (.shp.zip or .gpkg)", type=["zip", "gpkg"])

# Country input
country_code = st.text_input("🌐 Enter 3-digit ISO Country Code (e.g., ARE, IND, SAU)").upper()

# Function to read uploaded geodata
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
                shp_path = os.path.join(tmpdir, shp_files[0])
                return gpd.read_file(shp_path)
    elif uploaded_file.name.endswith(".gpkg"):
        return gpd.read_file(uploaded_file)
    else:
        st.error("Unsupported file type.")
        return None

# Load geodata and trigger rule engine
if uploaded_file and country_code:
    st.success(f"📌 File uploaded and country set to: `{country_code}`")
    
    with st.spinner("🧠 Reading geospatial data..."):
        gdf = load_geodata(uploaded_file)
        if gdf is not None:
            st.subheader("📊 Data Sample Preview")
            st.dataframe(gdf.head(10))

            # Placeholder for AI Agent
            st.info("🔍 Ready to run AI Agent checks with country-specific rules...")
            if st.button("▶️ Run Address Quality Checks"):
                st.warning("🚧 Checks coming in Step 2. Stay tuned!")
else:
    st.info("📥 Please upload a file and provide country ISO code to proceed.")
