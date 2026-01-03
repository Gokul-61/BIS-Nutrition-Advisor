import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
import json
from datetime import datetime
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER

# -------------------------------------------------
# Firebase Initialization
# -------------------------------------------------
if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["FIREBASE_SERVICE_ACCOUNT"]))
    firebase_admin.initialize_app(cred)

db = firestore.client()

# -------------------------------------------------
# Streamlit Page Configuration
# -------------------------------------------------
st.set_page_config(
    page_title="Cattle Nutrition Advisor (BIS/ICAR Standards)",
    layout="wide",
)

# -------------------------------------------------
# Load fodder dataset
# -------------------------------------------------
fodder_df = pd.read_excel("Fodder and Nutrients.xlsx")

# -------------------------------------------------
# Page Header
# -------------------------------------------------
st.markdown("""
# 🐄 Cattle Nutrition Advisor
### Individual Animal Entry System
""")

st.markdown("---")

# -------------------------------------------------
# Nutrient Requirements (ICAR 1998 Standards)
# -------------------------------------------------
MAINTENANCE_REQ = {
    "Calves (0-3 mo)": {"DCP_g": 80, "TDN_kg": 0.40, "ME_Mcal": 1.5, "Water_L": 10},
    "Growing Calves (3-12 mo)": {"DCP_g": 270, "TDN_kg": 2.1, "ME_Mcal": 7.6, "Water_L": 25},
    "Heifers (12-24 mo)": {"DCP_g": 320, "TDN_kg": 3.1, "ME_Mcal": 11.2, "Water_L": 35},
    "Pregnant Heifers (last 2 mo)": {"DCP_g": 350, "TDN_kg": 4.0, "ME_Mcal": 14.1, "Water_L": 45},
    "Dry Cows": {"DCP_g": 300, "TDN_kg": 3.7, "ME_Mcal": 13.2, "Water_L": 40},
    "Lactating Cows": {"DCP_g": 300, "TDN_kg": 3.7, "ME_Mcal": 13.2, "Water_L": 60},
    "Adult Bulls": {"DCP_g": 450, "TDN_kg": 4.5, "ME_Mcal": 16.2, "Water_L": 50},
}

MILK_REQUIREMENTS = {
    3.0: {"DCP_g": 40, "TDN_kg": 0.270, "ME_Mcal": 0.97, "Water_L": 4.0},
    4.0: {"DCP_g": 45, "TDN_kg": 0.315, "ME_Mcal": 1.13, "Water_L": 4.5},
    5.0: {"DCP_g": 51, "TDN_kg": 0.370, "ME_Mcal": 1.28, "Water_L": 5.0},
    6.0: {"DCP_g": 57, "TDN_kg": 0.410, "ME_Mcal": 1.36, "Water_L": 5.0},
    7.0: {"DCP_g": 63, "TDN_kg": 0.460, "ME_Mcal": 1.54, "Water_L": 5.0},
    8.0: {"DCP_g": 69, "TDN_kg": 0.510, "ME_Mcal": 1.80, "Water_L": 5.0},
}

DMI_PERCENT = {
    "Calves (0-3 mo)": 2.0,
    "Growing Calves (3-12 mo)": 2.5,
    "Heifers (12-24 mo)": 2.5,
    "Pregnant Heifers (last 2 mo)": 2.0,
    "Dry Cows": 2.0,
    "Lactating Cows": 3.0,
    "Adult Bulls": 2.0,
}

groups = list(MAINTENANCE_REQ.keys())

DISPLAY_GROUP_NAMES = {
    "Calves (0-3 mo)": "Calves",
    "Growing Calves (3-12 mo)": "Growing Calves",
    "Heifers (12-24 mo)": "Heifers",
    "Pregnant Heifers (last 2 mo)": "Pregnant Heifers",
    "Dry Cows": "Dry Cows",
    "Lactating Cows": "Lactating Cows",
    "Adult Bulls": "Adult Bulls",
}

# -------------------------------------------------
# Initialize session state
# -------------------------------------------------
if 'calculated' not in st.session_state:
    st.session_state.calculated = False
if 'calculation_data' not in st.session_state:
    st.session_state.calculation_data = None

# Initialize animal data storage
for group in groups:
    if f'{group}_data' not in st.session_state:
        st.session_state[f'{group}_data'] = []

# -------------------------------------------------
# Section 1 – Animal Input
# -------------------------------------------------
st.markdown("## 1️⃣ Enter Individual Animal Details")

# Helper function to add animal
def add_animal_to_group(group, data):
    st.session_state[f'{group}_data'].append(data)

# Helper function to remove animal
def remove_animal_from_group(group, index):
    st.session_state[f'{group}_data'].pop(index)

# -------------------------------------------------
# Calves (0-3 months)
# -------------------------------------------------
st.markdown("### 🐮 Calves (0-3 months)")
with st.expander("Add Calves", expanded=False):
    with st.form("calves_form"):
        col1, col2 = st.columns(2)
        with col1:
            calf_weight = st.number_input("Body Weight (kg)", 20, 100, 30, key="calf_wt_input")
        with col2:
            calf_count = st.number_input("Number of calves with this weight", 1, 100, 1, key="calf_count")
        
        if st.form_submit_button("Add Calves", use_container_width=True):
            add_animal_to_group("Calves (0-3 mo)", {
                "weight": calf_weight,
                "count": calf_count
            })
            st.success(f"✅ Added {calf_count} calf(ves) with {calf_weight} kg weight")
            st.rerun()

if st.session_state['Calves (0-3 mo)_data']:
    st.markdown("**Current Calves:**")
    for idx, data in enumerate(st.session_state['Calves (0-3 mo)_data']):
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.write(f"Weight: {data['weight']} kg")
        with col2:
            st.write(f"Count: {data['count']}")
        with col3:
            if st.button("🗑️", key=f"del_calf_{idx}"):
                remove_animal_from_group("Calves (0-3 mo)", idx)
                st.rerun()

st.markdown("---")

# -------------------------------------------------
# Growing Calves (3-12 months)
# -------------------------------------------------
st.markdown("### 🐮 Growing Calves (3-12 months)")
with st.expander("Add Growing Calves", expanded=False):
    with st.form("growing_calves_form"):
        col1, col2 = st.columns(2)
        with col1:
            gcalf_weight = st.number_input("Body Weight (kg)", 50, 300, 100, key="gcalf_wt_input")
        with col2:
            gcalf_count = st.number_input("Number of calves with this weight", 1, 100, 1, key="gcalf_count")
        
        if st.form_submit_button("Add Growing Calves", use_container_width=True):
            add_animal_to_group("Growing Calves (3-12 mo)", {
                "weight": gcalf_weight,
                "count": gcalf_count
            })
            st.success(f"✅ Added {gcalf_count} growing calf(ves)")
            st.rerun()

if st.session_state['Growing Calves (3-12 mo)_data']:
    st.markdown("**Current Growing Calves:**")
    for idx, data in enumerate(st.session_state['Growing Calves (3-12 mo)_data']):
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.write(f"Weight: {data['weight']} kg")
        with col2:
            st.write(f"Count: {data['count']}")
        with col3:
            if st.button("🗑️", key=f"del_gcalf_{idx}"):
                remove_animal_from_group("Growing Calves (3-12 mo)", idx)
                st.rerun()

st.markdown("---")

# -------------------------------------------------
# Heifers (12-24 months)
# -------------------------------------------------
st.markdown("### 🐮 Heifers (12-24 months)")
with st.expander("Add Heifers", expanded=False):
    with st.form("heifers_form"):
        col1, col2 = st.columns(2)
        with col1:
            heifer_weight = st.number_input("Body Weight (kg)", 100, 400, 200, key="heifer_wt_input")
        with col2:
            heifer_count = st.number_input("Number of heifers with this weight", 1, 100, 1, key="heifer_count")
        
        if st.form_submit_button("Add Heifers", use_container_width=True):
            add_animal_to_group("Heifers (12-24 mo)", {
                "weight": heifer_weight,
                "count": heifer_count
            })
            st.success(f"✅ Added {heifer_count} heifer(s)")
            st.rerun()

if st.session_state['Heifers (12-24 mo)_data']:
    st.markdown("**Current Heifers:**")
    for idx, data in enumerate(st.session_state['Heifers (12-24 mo)_data']):
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.write(f"Weight: {data['weight']} kg")
        with col2:
            st.write(f"Count: {data['count']}")
        with col3:
            if st.button("🗑️", key=f"del_heifer_{idx}"):
                remove_animal_from_group("Heifers (12-24 mo)", idx)
                st.rerun()

st.markdown("---")

# -------------------------------------------------
# Pregnant Heifers (last 2 months)
# -------------------------------------------------
st.markdown("### 🤰 Pregnant Heifers (last 2 months)")
with st.expander("Add Pregnant Heifers", expanded=False):
    with st.form("pregnant_heifers_form"):
        col1, col2 = st.columns(2)
        with col1:
            pheifer_weight = st.number_input("Body Weight (kg)", 200, 500, 350, key="pheifer_wt_input")
        with col2:
            pheifer_count = st.number_input("Number of pregnant heifers", 1, 100, 1, key="pheifer_count")
        
        if st.form_submit_button("Add Pregnant Heifers", use_container_width=True):
            add_animal_to_group("Pregnant Heifers (last 2 mo)", {
                "weight": pheifer_weight,
                "count": pheifer_count
            })
            st.success(f"✅ Added {pheifer_count} pregnant heifer(s)")
            st.rerun()

if st.session_state['Pregnant Heifers (last 2 mo)_data']:
    st.markdown("**Current Pregnant Heifers:**")
    for idx, data in enumerate(st.session_state['Pregnant Heifers (last 2 mo)_data']):
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.write(f"Weight: {data['weight']} kg")
        with col2:
            st.write(f"Count: {data['count']}")
        with col3:
            if st.button("🗑️", key=f"del_pheifer_{idx}"):
                remove_animal_from_group("Pregnant Heifers (last 2 mo)", idx)
                st.rerun()

st.markdown("---")

# -------------------------------------------------
# Dry Cows
# -------------------------------------------------
st.markdown("### 🐄 Dry Cows")
with st.expander("Add Dry Cows", expanded=False):
    with st.form("dry_cows_form"):
        col1, col2 = st.columns(2)
        with col1:
            dry_weight = st.number_input("Body Weight (kg)", 250, 700, 400, key="dry_wt_input")
        with col2:
            dry_count = st.number_input("Number of dry cows", 1, 100, 1, key="dry_count")
        
        if st.form_submit_button("Add Dry Cows", use_container_width=True):
            add_animal_to_group("Dry Cows", {
                "weight": dry_weight,
                "count": dry_count
            })
            st.success(f"✅ Added {dry_count} dry cow(s)")
            st.rerun()

if st.session_state['Dry Cows_data']:
    st.markdown("**Current Dry Cows:**")
    for idx, data in enumerate(st.session_state['Dry Cows_data']):
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.write(f"Weight: {data['weight']} kg")
        with col2:
            st.write(f"Count: {data['count']}")
        with col3:
            if st.button("🗑️", key=f"del_dry_{idx}"):
                remove_animal_from_group("Dry Cows", idx)
                st.rerun()

st.markdown("---")

# -------------------------------------------------
# Lactating Cows
# -------------------------------------------------
st.markdown("### 🥛 Lactating Cows")
with st.expander("Add Lactating Cows", expanded=False):
    with st.form("lactating_cows_form"):
        col1, col2 = st.columns(2)
        with col1:
            lac_weight = st.number_input("Body Weight (kg)", 250, 700, 450, key="lac_wt_input")
            lac_milk = st.number_input("Avg Daily Milk (kg/cow)", 0.0, 100.0, 10.0, 0.5, key="lac_milk_input")
        with col2:
            lac_fat = st.selectbox("Milk Fat %", [3.0, 4.0, 5.0, 6.0, 7.0, 8.0], index=2, key="lac_fat_input")
            lac_dim = st.number_input("Days since calving (DIM)", 0, 500, 60, 10, key="lac_dim_input")
        
        lac_count = st.number_input("Number of cows with these parameters", 1, 100, 1, key="lac_count")
        
        if st.form_submit_button("Add Lactating Cows", use_container_width=True):
            add_animal_to_group("Lactating Cows", {
                "weight": lac_weight,
                "milk": lac_milk,
                "fat": lac_fat,
                "dim": lac_dim,
                "count": lac_count
            })
            st.success(f"✅ Added {lac_count} lactating cow(s)")
            st.rerun()

if st.session_state['Lactating Cows_data']:
    st.markdown("**Current Lactating Cows:**")
    for idx, data in enumerate(st.session_state['Lactating Cows_data']):
        col1, col2, col3, col4, col5, col6 = st.columns([1.5, 1.5, 1, 1, 1, 0.5])
        with col1:
            st.write(f"Wt: {data['weight']}kg")
        with col2:
            st.write(f"Milk: {data['milk']}kg/d")
        with col3:
            st.write(f"Fat: {data['fat']}%")
        with col4:
            st.write(f"DIM: {data['dim']}")
        with col5:
            st.write(f"Count: {data['count']}")
        with col6:
            if st.button("🗑️", key=f"del_lac_{idx}"):
                remove_animal_from_group("Lactating Cows", idx)
                st.rerun()

st.markdown("---")

# -------------------------------------------------
# Adult Bulls
# -------------------------------------------------
st.markdown("### 🐂 Breeding Bulls")
with st.expander("Add Bulls", expanded=False):
    with st.form("bulls_form"):
        col1, col2 = st.columns(2)
        with col1:
            bull_weight = st.number_input("Body Weight (kg)", 300, 1000, 500, key="bull_wt_input")
        with col2:
            bull_count = st.number_input("Number of bulls", 1, 50, 1, key="bull_count")
        
        if st.form_submit_button("Add Bulls", use_container_width=True):
            add_animal_to_group("Adult Bulls", {
                "weight": bull_weight,
                "count": bull_count
            })
            st.success(f"✅ Added {bull_count} bull(s)")
            st.rerun()

if st.session_state['Adult Bulls_data']:
    st.markdown("**Current Bulls:**")
    for idx, data in enumerate(st.session_state['Adult Bulls_data']):
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.write(f"Weight: {data['weight']} kg")
        with col2:
            st.write(f"Count: {data['count']}")
        with col3:
            if st.button("🗑️", key=f"del_bull_{idx}"):
                remove_animal_from_group("Adult Bulls", idx)
                st.rerun()

st.markdown("---")

# Display summary
total_animals = sum([
    sum([item['count'] for item in st.session_state[f'{group}_data']])
    for group in groups
])

if total_animals > 0:
    st.info(f"📊 **Total Animals in Farm:** {total_animals}")

st.markdown("---")

# -------------------------------------------------
# Section 2 – Water Supply
# -------------------------------------------------
st.markdown("## 2️⃣ Water Availability")

col_w1, col_w2 = st.columns(2)
with col_w1:
    water_available = st.number_input(
        "Daily Water Available (Liters/day)", 
        min_value=0.0, 
        value=500.0, 
        step=50.0,
        help="Total water available for all animals per day"
    )
with col_w2:
    ambient_temp = st.number_input(
        "Ambient Temperature (°C)", 
        min_value=10.0, 
        max_value=50.0, 
        value=30.0, 
        step=1.0,
        help="Current ambient temperature affects water requirements"
    )

st.markdown("---")

# -------------------------------------------------
# Section 3 – Fodder Selection
# -------------------------------------------------
st.markdown("## 3️⃣ Select Fodders & Daily Quantities")

available_ingredients = fodder_df["Ingredient"].unique()
selected_fodders = st.multiselect("Choose fodders used on your farm:", available_ingredients)

fodder_amounts = {}

if selected_fodders:
    st.markdown("### Enter Daily Feeding Quantity (kg DM basis)")
    
    feed_cols = st.columns(3)
    for idx, f in enumerate(selected_fodders):
        with feed_cols[idx % 3]:
            amt = st.number_input(f"{f} (kg)", min_value=0.0, value=0.0, step=0.5, key=f)
            fodder_amounts[f] = amt

st.markdown("---")

# -------------------------------------------------
# CALCULATE BUTTON
# -------------------------------------------------
calculate_clicked = st.button("🧮 Calculate Nutrition Report", type="primary", use_container_width=True)

if calculate_clicked:
    # Validation
    if total_animals == 0:
        st.error("⚠️ Please enter at least one animal.")
        st.stop()
    
    if len(selected_fodders) == 0:
        st.error("⚠️ Please select at least one fodder.")
        st.stop()
    
    if all(amount == 0 for amount in fodder_amounts.values()):
        st.error("⚠️ Please enter at least one fodder amount greater than 0.")
        st.stop()
    
    # Calculate total nutrients supplied
    total_DCP = 0.0
    total_TDN = 0.0
    total_ME = 0.0
    
    for f, amt_kg in fodder_amounts.items():
        if amt_kg > 0:
            row = fodder_df[fodder_df["Ingredient"] == f].iloc[0]
            actual_dm = amt_kg 
            CP_percent = row["CP"]
            DCP_g = (CP_percent / 100) * actual_dm * 1000 * 0.70
            ME_Mcal = row["ME"]
            TDN_kg = (ME_Mcal * actual_dm) / 4.4
            total_DCP += DCP_g
            total_TDN += TDN_kg
            total_ME += ME_Mcal * actual_dm
    
    # Calculate requirements for each sub-group
    evaluation_data = []
    total_water_req = 0.0
    total_dmi = 0.0
    
    # Process each group
    for group in groups:
        group_data = st.session_state[f'{group}_data']
        
        for sub_idx, sub_group in enumerate(group_data):
            count = sub_group['count']
            if count == 0:
                continue
            
            avg_weight = sub_group['weight']
            
            # Get base requirements
            base_req = MAINTENANCE_REQ[group]
            
            # Calculate total requirements for the sub-group
            if group == "Lactating Cows":
                milk_kg = sub_group['milk']
                fat_pct = sub_group['fat']
                days_in_milk = sub_group['dim']
                
                maint_DCP = base_req["DCP_g"]
                maint_TDN = base_req["TDN_kg"]
                maint_ME = base_req["ME_Mcal"]
                maint_water = base_req["Water_L"]
                
                if fat_pct in MILK_REQUIREMENTS:
                    milk_req = MILK_REQUIREMENTS[fat_pct]
                    prod_DCP = milk_req["DCP_g"] * milk_kg
                    prod_TDN = milk_req["TDN_kg"] * milk_kg
                    prod_ME = milk_req["ME_Mcal"] * milk_kg
                    prod_water = milk_req["Water_L"] * milk_kg
                else:
                    prod_DCP = 51 * milk_kg
                    prod_TDN = 0.370 * milk_kg
                    prod_ME = 1.28 * milk_kg
                    prod_water = 5.0 * milk_kg
                
                parturition_factor = 1.0
                if days_in_milk <= 21:
                    parturition_factor = 1.2
                    
                req_DCP = (maint_DCP + prod_DCP) * count * parturition_factor
                req_TDN = (maint_TDN + prod_TDN) * count * parturition_factor
                req_ME = (maint_ME + prod_ME) * count * parturition_factor
                req_water = (maint_water + prod_water) * count
                
                if ambient_temp > 25:
                    temp_diff = ambient_temp - 25
                    water_increase = (temp_diff / 4) * 6.5 * count
                    req_water += water_increase
                
                dmi_kg = (DMI_PERCENT[group] / 100) * avg_weight * count
                
                group_label = f"{DISPLAY_GROUP_NAMES[group]} #{sub_idx+1} (Wt:{avg_weight}kg, Milk:{milk_kg}kg, Fat:{fat_pct}%, DIM:{days_in_milk})"
            else:
                req_DCP = base_req["DCP_g"] * count
                req_TDN = base_req["TDN_kg"] * count
                req_ME = base_req["ME_Mcal"] * count
                req_water = base_req["Water_L"] * count
                
                if ambient_temp > 25:
                    temp_diff = ambient_temp - 25
                    water_increase = (temp_diff / 4) * 3 * count
                    req_water += water_increase
                
                dmi_kg = (DMI_PERCENT[group] / 100) * avg_weight * count
                
                group_label = f"{DISPLAY_GROUP_NAMES[group]} #{sub_idx+1} (Wt:{avg_weight}kg)"
            
            total_water_req += req_water
            total_dmi += dmi_kg
            
            evaluation_data.append({
                "Group": group_label,
                "Count": count,
                "Avg Weight (kg)": avg_weight,
                "DMI (kg)": round(dmi_kg, 2),
                "DCP Req (g)": round(req_DCP, 0),
                "TDN Req (kg)": round(req_TDN, 2),
                "ME Req (Mcal)": round(req_ME, 2),
                "Water Req (L)": round(req_water, 1),
            })
    
    df_eval = pd.DataFrame(evaluation_data)
    
    # Calculate supplied nutrients proportionally based on DMI
    df_eval["DCP Sup (g)"] = df_eval["DMI (kg)"].apply(lambda x: round((x / total_dmi) * total_DCP, 0))
    df_eval["TDN Sup (kg)"] = df_eval["DMI (kg)"].apply(lambda x: round((x / total_dmi) * total_TDN, 2))
    df_eval["ME Sup (Mcal)"] = df_eval["DMI (kg)"].apply(lambda x: round((x / total_dmi) * total_ME, 2))
    
    # Generate recommendations
    recommendations = []
    
    for _, row in df_eval.iterrows():
        group = row["Group"]
        
        dcp_gap = ((row["DCP Sup (g)"] - row["DCP Req (g)"]) / row["DCP Req (g)"]) * 100
        if dcp_gap < -10:
            dcp_rec = f"⚠️ Deficit {abs(dcp_gap):.1f}% - Add protein-rich concentrate"
        elif dcp_gap > 10:
            dcp_rec = f"⚠️ Excess {dcp_gap:.1f}% - Reduce protein supplements"
        else:
            dcp_rec = "✅ Adequate"
        
        tdn_gap = ((row["TDN Sup (kg)"] - row["TDN Req (kg)"]) / row["TDN Req (kg)"]) * 100
        if tdn_gap < -10:
            tdn_rec = f"⚠️ Deficit {abs(tdn_gap):.1f}% - Add energy-rich feed"
        elif tdn_gap > 10:
            tdn_rec = f"⚠️ Excess {tdn_gap:.1f}% - Reduce grain feeding"
        else:
            tdn_rec = "✅ Adequate"
        
        recommendations.append({
            "Group": group,
            "Protein (DCP)": dcp_rec,
            "Energy (TDN)": tdn_rec,
        })
    
    rec_df = pd.DataFrame(recommendations)
    
    # Save to session state
    st.session_state.calculated = True
    st.session_state.calculation_data = {
        'df_eval': df_eval,
        'rec_df': rec_df,
        'total_DCP': total_DCP,
        'total_TDN': total_TDN,
        'total_ME': total_ME,
        'total_water_req': total_water_req,
        'water_available': water_available,
        'ambient_temp': ambient_temp,
        'total_animals': total_animals,
        'fodder_amounts': fodder_amounts,
    }
    
    # Save to Firebase
    try:
        farmers_ref = db.collection('farmers')
        farmers_docs = farmers_ref.stream()
        farmer_count = len(list(farmers_docs))
        farmer_number = farmer_count + 1
        farmer_id = f"Farmer {farmer_number}"
        
        animal_summary = {}
        for group in groups:
            group_data = st.session_state[f'{group}_data']
            if group_data:
                animal_summary[group] = group_data
        
        data_to_save = {
            "timestamp": datetime.now().isoformat(),
            "total_animals": total_animals,
            "animal_details": animal_summary,
            "fodder_selection": {f: float(amt) for f, amt in fodder_amounts.items() if amt > 0}
        }
        
        db.collection('farmers').document(farmer_id).set(data_to_save)
        st.session_state.farmer_id = farmer_id
    except Exception as e:
        st.error(f"⚠️ Error saving to Firebase: {str(e)}")

# -------------------------------------------------
# Display Results
# -------------------------------------------------
if st.session_state.calculated and st.session_state.calculation_data:
    data = st.session_state.calculation_data
    
    st.success("✅ Nutrition analysis completed successfully!")
    
    # Summary boxes
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total DCP Supplied", f"{data['total_DCP']:.0f} g/day")
    with col2:
        st.metric("Total TDN Supplied", f"{data['total_TDN']:.2f} kg/day")
    with col3:
        st.metric("Total ME Supplied", f"{data['total_ME']:.2f} Mcal/day")
    with col4:
        water_status = "✅" if data['water_available'] >= data['total_water_req'] else "⚠️"
        st.metric(
            f"{water_status} Water Status", 
            f"{data['water_available']:.0f} / {data['total_water_req']:.0f} L",
            delta=f"{data['water_available'] - data['total_water_req']:.0f} L"
        )
    
    if data['water_available'] < data['total_water_req']:
        st.error(f"⚠️ Water Deficit: {data['total_water_req'] - data['water_available']:.0f} L/day. Ensure adequate water supply!")
    else:
        st.success(f"✅ Water supply is adequate with {data['water_available'] - data['total_water_req']:.0f} L surplus.")
    
    if data['ambient_temp'] > 35:
        st.warning(f"🌡️ High Temperature Alert ({data['ambient_temp']:.0f}°C): Heat stress risk. Water requirements have been adjusted upward.")
    
    st.markdown("---")
    
    # Evaluation Table
    st.markdown("## 📊 Nutritional Evaluation by Sub-Group")
    
    df_display = data['df_eval'][["Group", "Count", "DCP Req (g)", "DCP Sup (g)", 
                                   "TDN Req (kg)", "TDN Sup (kg)", "ME Req (Mcal)", "ME Sup (Mcal)", 
                                   "Water Req (L)"]]
    
    def color_row(row):
        styles = [""] * len(row)
        
        dcp_ratio = row["DCP Sup (g)"] / row["DCP Req (g)"] if row["DCP Req (g)"] > 0 else 1
        tdn_ratio = row["TDN Sup (kg)"] / row["TDN Req (kg)"] if row["TDN Req (kg)"] > 0 else 1
        me_ratio = row["ME Sup (Mcal)"] / row["ME Req (Mcal)"] if row["ME Req (Mcal)"] > 0 else 1
        
        if dcp_ratio < 0.9:
            styles[3] = "color: #ff4d4d; font-weight: bold;"
        elif dcp_ratio > 1.1:
            styles[3] = "color: #ffaa00; font-weight: bold;"
        else:
            styles[3] = "color: #33cc33; font-weight: bold;"
        
        if tdn_ratio < 0.9:
            styles[5] = "color: #ff4d4d; font-weight: bold;"
        elif tdn_ratio > 1.1:
            styles[5] = "color: #ffaa00; font-weight: bold;"
        else:
            styles[5] = "color: #33cc33; font-weight: bold;"
        
        if me_ratio < 0.9:
            styles[7] = "color: #ff4d4d; font-weight: bold;"
        elif me_ratio > 1.1:
            styles[7] = "color: #ffaa00; font-weight: bold;"
        else:
            styles[7] = "color: #33cc33; font-weight: bold;"
        
        return styles
    
    styled_df = df_display.style.apply(color_row, axis=1)
    
    st.dataframe(styled_df, use_container_width=True)
    
    st.markdown("""
    🔴 <span style='color:#ff4d4d'>Deficit</span> | 
    🟢 <span style='color:#33cc33'>Adequate</span> | 
    🟡 <span style='color:#ffaa00'>Excess</span>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Recommendations
    st.markdown("## 💡 Recommendations by Sub-Group")
    st.dataframe(data['rec_df'], use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # PDF Generation
    def clean_recommendation(text):
        return (
            text.replace("⚠️", "")
            .replace("✅", "")
            .replace("⚠️", "")
            .strip()
        )

    def generate_pdf_report(df_eval, rec_df, totals):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(name="title", parent=styles["Title"], fontSize=20, 
                                     textColor=colors.HexColor("#1f77b4"), alignment=TA_CENTER)
        
        story = []
        
        story.append(Paragraph("Cattle Nutrition Report (BIS/ICAR Standards)", title_style))
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%d-%m-%Y %H:%M')}", styles["Normal"]))
        story.append(Spacer(1, 20))
        
        # Summary
        story.append(Paragraph(f"<b>Total Animals:</b> {totals['total_animals']}", styles["Normal"]))
        story.append(Paragraph(f"<b>Total DCP:</b> {totals['total_DCP']:.0f} g/day", styles["Normal"]))
        story.append(Paragraph(f"<b>Total TDN:</b> {totals['total_TDN']:.2f} kg/day", styles["Normal"]))
        story.append(Paragraph(f"<b>Total ME:</b> {totals['total_ME']:.2f} Mcal/day", styles["Normal"]))
        story.append(Paragraph(f"<b>Water Required:</b> {totals['total_water_req']:.1f} L/day", styles["Normal"]))
        story.append(Paragraph(f"<b>Water Available:</b> {totals['water_available']:.1f} L/day", styles["Normal"]))
        story.append(Paragraph(f"<b>Ambient Temperature:</b> {totals['ambient_temp']:.1f}°C", styles["Normal"]))
        story.append(Spacer(1, 20))
        
        # Evaluation table
        eval_data = [["Group", "Count", "DCP Req", "DCP Sup", "TDN Req", "TDN Sup", "Water"]]
        for _, row in df_eval.iterrows():
            group_short = row["Group"][:30] + "..." if len(row["Group"]) > 30 else row["Group"]
            eval_data.append([
                group_short,
                str(int(row["Count"])),
                f"{row['DCP Req (g)']:.0f}g",
                f"{row['DCP Sup (g)']:.0f}g",
                f"{row['TDN Req (kg)']:.2f}kg",
                f"{row['TDN Sup (kg)']:.2f}kg",
                f"{row['Water Req (L)']:.1f}L"
            ])
        
        eval_table = Table(eval_data, colWidths=[120, 40, 60, 60, 60, 60, 60])
        eval_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.grey),
            ("GRID", (0,0), (-1,-1), 1, colors.black),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 8),
            ("ALIGN", (1,0), (-1,-1), "CENTER"),
        ]))
        
        story.append(eval_table)
        story.append(Spacer(1, 20))
        
        # Recommendations
        story.append(Paragraph("<b>Recommendations:</b>", styles["Heading2"]))
        for _, row in rec_df.iterrows():
            group_short = row["Group"][:40] + "..." if len(row["Group"]) > 40 else row["Group"]
            story.append(
                Paragraph(
                    f"<b>{group_short}:</b> {clean_recommendation(row['Protein (DCP)'])}",
                    styles["Normal"]
                )
            )
        
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    pdf_buffer = generate_pdf_report(data['df_eval'], data['rec_df'], data)
    
    st.download_button(
        label="📄 Download PDF Report",
        data=pdf_buffer,
        file_name="Cattle_Nutrition_Report_Individual_Groups.pdf",
        mime="application/pdf",
        use_container_width=True
    )
    
    # Rating Section
    st.markdown("---")
    st.markdown("## ⭐ Rate This Tool")
    
    rating_cols = st.columns(5)
    
    if 'selected_rating' not in st.session_state:
        st.session_state.selected_rating = 0
    
    for i in range(5):
        with rating_cols[i]:
            if st.button("⭐" * (i+1), key=f"star_{i+1}", 
                        type="secondary" if st.session_state.selected_rating != i+1 else "primary"):
                st.session_state.selected_rating = i+1
                
                try:
                    if st.session_state.get('farmer_id'):
                        db.collection('farmers').document(st.session_state.farmer_id).update({
                            'rating': i+1,
                            'rating_timestamp': datetime.now().isoformat()
                        })
                        st.success(f"✅ Thank you for your {i+1}-star rating!")
                except Exception as e:
                    st.error(f"⚠️ Error saving rating: {str(e)}")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; margin-top: 40px; padding: 20px; background-color: #f8f9fa; border-radius: 10px;">
    <p style="font-size: 14px; color: #666; margin: 0;">
        <b>Based on:</b> BIS Standards | ICAR Nutrient Requirements
    </p>
    <p style="font-size: 12px; color: #888; margin-top: 5px;">
        Bureau of Indian Standards • Indian Council of Agricultural Research
    </p>
</div>
""", unsafe_allow_html=True)