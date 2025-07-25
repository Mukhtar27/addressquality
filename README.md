# 🌍 Address Point Quality Checker (AI Agent)

This web-based Streamlit AI Agent helps in validating the quality of address point datasets (.shp and .gpkg) using country-specific rules.

## 🚀 Features
- Upload `.shp.zip` or `.gpkg` files
- Enter 3-digit ISO code (e.g., ARE, IND, SAU)
- Dynamically loads validation rules for completeness, correctness, accuracy, etc.
- Web-based interface (no CLI)

## 🛠️ Setup Instructions

```bash
git clone https://github.com/yourusername/address-quality-agent.git
cd address-quality-agent
pip install -r requirements.txt
streamlit run app.py
