import streamlit as st
import pandas as pd
from datetime import date, timedelta
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="Solar Finance", page_icon="💳", layout="centered", initial_sidebar_state="collapsed")

# 💎 PROFESSIONAL FINTECH CSS (Stable Streamlit Version)
st.markdown("""
    <style>
    /* Font & Background */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    .stApp {
        background-color: #F8FAFC; /* Slate-50 */
        font-family: 'Inter', sans-serif;
    }
    
    /* Mobile Container Constraint */
    .main .block-container {
        max-width: 480px;
        padding-top: 1rem;
        padding-bottom: 5rem;
        padding-left: 1rem;
        padding-right: 1rem;
        background-color: #FFFFFF;
        min-height: 100vh;
        margin: 0 auto;
        box-shadow: 0 0 20px rgba(0,0,0,0.03);
    }

    /* Hide Streamlit Bloat */
    #MainMenu, footer, header {visibility: hidden;}
    div[data-testid="stToolbar"] { display: none; }

    /* --- WIDGETS --- */
    
    /* Balance Card */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #4F46E5 0%, #6366F1 100%);
        padding: 20px;
        border-radius: 20px;
        color: white !important;
        box-shadow: 0 10px 25px -5px rgba(79, 70, 229, 0.4);
    }
    div[data-testid="stMetric"] label { color: rgba(255,255,255,0.8) !important; font-size: 14px !important; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: white !important; font-size: 32px !important; font-weight: 700 !important; }
    div[data-testid="stMetric"] div[data-testid="stMetricDelta"] { color: rgba(255,255,255,0.9) !important; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #F1F5F9;
        padding: 4px;
        border-radius: 12px;
        gap: 0;
        margin-top: 20px;
        margin-bottom: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px; border-radius: 8px; border: none;
        color: #64748B; font-weight: 600; font-size: 14px; flex: 1;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF; color: #4F46E5; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    /* Inputs */
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        height: 48px;
        color: #1E293B;
    }

    /* Buttons */
    div.stButton > button {
        border-radius: 12px;
        height: 48px;
        font-weight: 600;
        border: none;
        width: 100%;
        transition: all 0.2s;
    }
    
    /* Primary Action Button (FAB) */
    .element-container:has(button[title="Add"]) {
        position: fixed;
        bottom: 24px;
        right: 24px;
        z-index: 999;
        width: auto !important;
    }
    button[title="Add"] {
        width: 60px !important;
        height: 60px !important;
        border-radius: 30px !important;
        background: #0F172A !important; /* Dark Slate */
        color: white !important;
        font-size: 28px !important;
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.3) !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. CONSTANTS ---
TRN_TYPES = ["EXPENSE", "CREDIT", "ADV-IN", "ADV-OUT", "ADV-PEN"]
CATEGORIES = [
    "TEA / SNACKS / WATERCAN", "COURIER / MAILING", "XEROX / PRINT / OFFICE STATIONERY",
    "STAFF FOOD / BUS FARE / TRAVEL EXPENSE", "PLANT MAINTENANCE", 
    "FUEL ALLOWANCE / BUS FARE / TRAVEL ALLOWANCES", "GRASS CUTTER - SPARES / SUPPLIES & SERVICE",
    "MODULE CLEANING - ACCESSORIES & PLUMBING ITEMS", "PETROL PURCHASE", "DIESEL PURCHASE",
    "OFFICE & WASHROOM - HOUSEKEEPING MATERIALS", "POOJA ITEMS / WEEKLY POOJA EXPENSES",
    "CREDIT", "ADV-IN", "ADV-OUT", "ADV-PEN", "OTHERS"
]
MODES = ["CASH", "E-TRANSACTION"]
DOC_TYPES = ["BILL", "VOUCHER", "NA"]

# --- 3. HELPER FUNCTIONS ---
def clean_currency(val):
    if pd.isnull(val): return 0.0
    if isinstance(val, (int, float)): return float(val)
    val = str(val).replace('₹', '').replace(',', '').replace(' ', '')
    try: return float(val)
    except: return 0.0

def load_data(conn):
    try:
        df = conn.read(ttl=0)
        df.columns = df.columns.str.strip()
        df['DATE'] = pd.to_datetime(df['DATE'], dayfirst=True, errors='coerce')
        if 'AMOUNT' in df.columns: df['AMOUNT'] = df['AMOUNT'].apply(clean_currency)
        if 'BALANCE' in df.columns: df['BALANCE'] = df['BALANCE'].apply(clean_currency)
        return df
    except:
        return pd.DataFrame(columns=["DATE", "TRN. ID", "TRN. TYPE", "CATEGORY", "DESCRIPTION", "AMOUNT", "TRN. MODE", "BILL/VOUCHER", "BALANCE", "REMARKS"])

def recalculate_and_save(conn, df):
    with st.spinner("Processing..."):
        if 'TRN. ID' in df.columns: df['TRN. ID'] = pd.to_numeric(df['TRN. ID'], errors='coerce').fillna(0)
        if 'AMOUNT' in df.columns: df['AMOUNT'] = df['AMOUNT'].apply(clean_currency)
        df = df.sort_values(by=['DATE', 'TRN. ID'], ascending=[True, True]).reset_index(drop=True)
        
        bal = 0.0
        bals = []
        # Calculate running balance (oldest to newest)
        calc_df = df.copy()
        for _, row in calc_df.iterrows():
            amt = row['AMOUNT']
            t = row['TRN. TYPE']
            if t in ["CREDIT", "ADV-IN"]: bal += amt
            elif t in ["EXPENSE", "ADV-OUT"]: bal -= amt
            bals.append(bal)
        calc_df['BALANCE'] = bals
        
        conn.update(data=calc_df)
        return calc_df

# --- 4. INIT ---
conn = st.connection("gsheets", type=GSheetsConnection)
if "df" not in st.session_state: st.session_state.df = load_data(conn)
df = st.session_state.df

# --- DIALOGS ---
@st.dialog("New Entry")
def add_dialog():
    with st.form("add_form", clear_on_submit=True):
        amt = st.number_input("Amount (₹)", min_value=0.0, step=100.0)
        c1, c2 = st.columns(2)
        with c1: dte = st.date_input("Date", value=date.today())
        with c2: typ = st.selectbox("Type", TRN_TYPES)
        
        # Smart Category
        def_cat_idx = 0
        if typ in CATEGORIES: def_cat_idx = CATEGORIES.index(typ)
        cat = st.selectbox("Category", CATEGORIES, index=def_cat_idx)
        
        desc = st.text_input("Description", placeholder="e.g. Fuel")
        c3, c4 = st.columns(2)
        with c3: mod = st.selectbox("Mode", MODES)
        with c4: doc = st.selectbox("Proof", DOC_TYPES)
        rem = st.text_input("Remarks")
        
        if st.form_submit_button("Save", type="primary"):
            nid = 1
            if not df.empty:
                try: nid = int(df['TRN. ID'].max()) + 1
                except: nid = len(df) + 1
            new_row = {"DATE": pd.to_datetime(dte), "TRN. ID": nid, "TRN. TYPE": typ, "CATEGORY": cat, "DESCRIPTION": desc, "AMOUNT": amt, "TRN. MODE": mod, "BILL/VOUCHER": doc, "BALANCE": 0, "REMARKS": rem}
            st.session_state.df = recalculate_and_save(conn, pd.concat([df, pd.DataFrame([new_row])], ignore_index=True))
            st.rerun()

@st.dialog("Edit Entry")
def edit_dialog(row, rid):
    with st.form("edit_form"):
        st.caption(f"ID: #{rid}")
        dte = st.date_input("Date", value=row['DATE'])
        amt = st.number_input("Amount", value=clean_currency(row['AMOUNT']))
        typ = st.selectbox("Type", TRN_TYPES, index=TRN_TYPES.index(row['TRN. TYPE']) if row['TRN. TYPE'] in TRN_TYPES else 0)
        cat = st.selectbox("Category", CATEGORIES, index=CATEGORIES.index(row['CATEGORY']) if row['CATEGORY'] in CATEGORIES else 0)
        desc = st.text_input("Description", value=str(row['DESCRIPTION']))
        mod = st.selectbox("Mode", MODES, index=MODES.index(row['TRN. MODE']) if row['TRN. MODE'] in MODES else 0)
        
        b1, b2 = st.columns(2)
        if b1.form_submit_button("Update"):
            idx = df[df['TRN. ID'] == rid].index[0]
            df.at[idx, 'DATE'] = pd.to_datetime(dte)
            df.at[idx, 'TRN. TYPE'] = typ
            df.at[idx, 'CATEGORY'] = cat
            df.at[idx, 'AMOUNT'] = amt
            df.at[idx, 'DESCRIPTION'] = desc
            df.at[idx, 'TRN. MODE'] = mod
            st.session_state.df = recalculate_and_save(conn, df)
            st.rerun()
        if b2.form_submit_button("Delete", type="primary"):
            st.session_state.df = recalculate_and_save(conn, df[df['TRN. ID'] != rid])
            st.rerun()

# --- 5. UI LAYOUT ---

# Top Bar
c_top1, c_top2 = st.columns([3, 1])
with c_top1:
    st.markdown("<h3 style='margin:0; padding-top:10px;'>Solar Finance</h3>", unsafe_allow_html=True)
with c_top2:
    if st.button("🔄", help="Sync"):
        st.cache_data.clear()
        st.session_state.df = recalculate_and_save(conn, conn.read(ttl=0))
        st.rerun()

st.write("")

# Balance Widget (Clean Card Style)
curr_bal = df.iloc[-1]['BALANCE'] if not df.empty and 'BALANCE' in df.columns else 0.0
st.metric("Current Balance", f"₹ {curr_bal:,.0f}")

# Tabs
tab1, tab2 = st.tabs(["Transactions", "Analytics"])

# === TAB 1: TRANSACTIONS ===
with tab1:
    if not df.empty:
        # Search
        search = st.text_input("Search...", placeholder="Filter transactions", label_visibility="collapsed")
        
        # Sort & Filter
        view_df = df.sort_values(by=['DATE', 'TRN. ID'], ascending=False)
        if search:
            view_df = view_df[view_df.apply(lambda row: search.lower() in str(row).lower(), axis=1)]

        # Interactive Table
        st.caption("Tap row to edit")
        sel = st.dataframe(
            view_df,
            column_config={
                "DATE": st.column_config.DateColumn("Date", format="DD MMM"),
                "AMOUNT": st.column_config.NumberColumn("Amt", format="₹ %.0f"),
                "CATEGORY": st.column_config.TextColumn("Category", width="medium"),
                "DESCRIPTION": st.column_config.TextColumn("Desc", width="medium"),
                "TRN. ID": st.column_config.NumberColumn("ID", format="%d"),
            },
            use_container_width=True,
            hide_index=True,
            height=500,
            on_select="rerun",
            selection_mode="single-row"
        )
        
        if sel.selection.rows:
            rid = view_df.iloc[sel.selection.rows[0]]['TRN. ID']
            edit_dialog(df[df['TRN. ID'] == rid].iloc[0], rid)
    else:
        st.info("No transactions found.")

# === TAB 2: ANALYTICS ===
with tab2:
    if not df.empty:
        # 1. Monthly Filter
        dates_df = df[['DATE']].copy()
        dates_df['M'] = dates_df['DATE'].dt.strftime('%B %Y')
        dates_df['YM'] = dates_df['DATE'].dt.to_period('M')
        months = dates_df.drop_duplicates('YM').sort_values('YM', ascending=False)['M'].tolist()
        
        sel_month = st.selectbox("Select Month", months, label_visibility="collapsed")
        
        if sel_month:
            mask = df['DATE'].dt.strftime('%B %Y') == sel_month
            m_df = df.loc[mask]
            
            # 2. Stats Grid (2x2)
            grp = m_df.groupby('TRN. TYPE')['AMOUNT'].sum()
            
            c_a1, c_a2 = st.columns(2)
            with c_a1:
                st.container(border=True).metric("Credit", f"₹ {grp.get('CREDIT', 0):,.0f}")
                st.container(border=True).metric("Adv In", f"₹ {grp.get('ADV-IN', 0):,.0f}")
            with c_a2:
                st.container(border=True).metric("Expense", f"₹ {grp.get('EXPENSE', 0):,.0f}")
                st.container(border=True).metric("Adv Out", f"₹ {grp.get('ADV-OUT', 0):,.0f}")
                
            # 3. Pivot Breakdown
            st.write("")
            st.subheader("Category Breakdown")
            piv = m_df.groupby('CATEGORY')['AMOUNT'].sum().reset_index().sort_values('AMOUNT', ascending=False)
            st.dataframe(piv, column_config={"AMOUNT": st.column_config.NumberColumn("Total", format="₹ %.0f")}, use_container_width=True, hide_index=True)

# --- FAB (Add Button) ---
if st.button("➕", key="fab_add", help="Add"):
    add_dialog()
