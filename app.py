import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="Wallet", page_icon="💳", layout="centered", initial_sidebar_state="collapsed")

# 💎 PROFESSIONAL FINTECH CSS
st.markdown("""
    <style>
    /* Global Font & Background */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    .stApp {
        background-color: #F2F4F7;
        font-family: 'Inter', sans-serif;
    }
    
    /* Mobile Container */
    .main .block-container {
        max-width: 480px;
        padding: 0;
        margin: 0 auto;
        background-color: #F2F4F7;
        min-height: 100vh;
    }

    /* Hide Defaults */
    #MainMenu, footer, header {visibility: hidden;}
    div[data-testid="stToolbar"] { display: none; }

    /* --- COMPONENTS --- */
    
    /* 1. Header */
    .nav-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px 24px;
        background: transparent;
    }
    .nav-title { font-size: 16px; font-weight: 600; color: #101828; }
    
    /* 2. Balance Card (White) */
    .bal-card {
        background: white;
        margin: 0 20px;
        padding: 40px 20px;
        border-radius: 24px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(16, 24, 40, 0.1);
    }
    .bal-lbl { color: #667085; font-size: 13px; font-weight: 500; margin-bottom: 8px; }
    .bal-val { color: #101828; font-size: 36px; font-weight: 800; letter-spacing: -1px; }
    
    /* 3. Action Buttons */
    .action-grid {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        gap: 12px;
        padding: 24px;
    }
    
    /* Streamlit Button Overrides to look like Icons */
    div.stButton > button {
        background-color: white !important;
        border: 1px solid #EAECF0 !important;
        border-radius: 16px !important;
        height: 64px !important;
        width: 100% !important;
        color: #101828 !important;
        font-size: 20px !important;
        box-shadow: 0 1px 2px rgba(16, 24, 40, 0.05) !important;
        margin: 0 auto !important;
        display: block !important;
    }
    div.stButton > button:hover {
        background-color: #F9FAFB !important;
        border-color: #D0D5DD !important;
    }
    div.stButton p { font-size: 24px; line-height: 1; } /* Icon Size */

    .action-lbl {
        text-align: center;
        font-size: 12px;
        color: #475467;
        font-weight: 500;
        margin-top: -10px; /* Pull label closer to button */
        margin-bottom: 10px;
    }

    /* 4. Transaction List */
    .list-header {
        display: flex; justify-content: space-between; align-items: center;
        padding: 0 24px 16px 24px;
    }
    .list-title { font-size: 16px; font-weight: 600; color: #101828; }
    
    .txn-item {
        background: white;
        padding: 16px;
        margin: 0 20px 12px 20px;
        border-radius: 16px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 1px 2px rgba(16, 24, 40, 0.03);
    }
    .txn-left { display: flex; align-items: center; gap: 12px; }
    .txn-icon {
        width: 40px; height: 40px; border-radius: 20px;
        display: flex; align-items: center; justify-content: center;
        font-size: 18px;
    }
    .bg-green { background: #ECFDF3; color: #027A48; }
    .bg-red { background: #FEF3F2; color: #B42318; }
    
    .txn-info { display: flex; flex-direction: column; }
    .txn-cat { font-size: 14px; font-weight: 600; color: #101828; }
    .txn-meta { font-size: 12px; color: #667085; }
    
    .txn-right { text-align: right; }
    .txn-amt { font-size: 14px; font-weight: 700; color: #101828; }
    .txn-bal { font-size: 11px; color: #98A2B3; }

    /* Input Fields for Modal */
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
        border-radius: 12px !important;
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
        # Note: We sort strictly by Date ASC for calculation, then flip for display
        calc_df = df.sort_values(by=['DATE', 'TRN. ID'], ascending=[True, True])
        for _, row in calc_df.iterrows():
            amt = row['AMOUNT']
            t = row['TRN. TYPE']
            if t in ["CREDIT", "ADV-IN"]: bal += amt
            elif t in ["EXPENSE", "ADV-OUT"]: bal -= amt
            bals.append(bal)
        calc_df['BALANCE'] = bals
        
        # Save back to sheet
        conn.update(data=calc_df)
        return calc_df

# --- 4. INIT ---
conn = st.connection("gsheets", type=GSheetsConnection)
if "df" not in st.session_state: st.session_state.df = load_data(conn)
df = st.session_state.df

# --- DIALOGS ---
@st.dialog("Add Transaction")
def add_dialog():
    with st.form("add_form", clear_on_submit=True):
        amt = st.number_input("Amount (₹)", min_value=0.0, step=100.0)
        c1, c2 = st.columns(2)
        with c1: dte = st.date_input("Date", value=date.today())
        with c2: typ = st.selectbox("Type", TRN_TYPES)
        cat = st.selectbox("Category", CATEGORIES, index=CATEGORIES.index(typ) if typ in CATEGORIES else 0)
        desc = st.text_input("Description", placeholder="e.g. Fuel")
        c3, c4 = st.columns(2)
        with c3: mod = st.selectbox("Mode", MODES)
        with c4: doc = st.selectbox("Proof", DOC_TYPES)
        rem = st.text_input("Remarks")
        if st.form_submit_button("Save Entry", type="primary"):
            nid = 1
            if not df.empty:
                try: nid = int(df['TRN. ID'].max()) + 1
                except: nid = len(df) + 1
            new_row = {"DATE": pd.to_datetime(dte), "TRN. ID": nid, "TRN. TYPE": typ, "CATEGORY": cat, "DESCRIPTION": desc, "AMOUNT": amt, "TRN. MODE": mod, "BILL/VOUCHER": doc, "BALANCE": 0, "REMARKS": rem}
            st.session_state.df = recalculate_and_save(conn, pd.concat([df, pd.DataFrame([new_row])], ignore_index=True))
            st.rerun()

@st.dialog("Edit Transaction")
def edit_dialog(row, rid):
    with st.form("edit_form"):
        st.caption(f"ID #{rid}")
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

# --- 5. UI RENDER ---

# Determine View Mode
if 'view_mode' not in st.session_state: st.session_state.view_mode = 'home'

# --- HOME VIEW ---
if st.session_state.view_mode == 'home':
    # 1. Header
    st.markdown('<div class="nav-header"><div class="nav-title">Welcome back</div><div style="font-size:20px;">🔔</div></div>', unsafe_allow_html=True)
    
    # 2. Balance Card
    curr_bal = df.iloc[-1]['BALANCE'] if not df.empty and 'BALANCE' in df.columns else 0.0
    st.markdown(f"""
        <div class="bal-card">
            <div class="bal-lbl">Account balance</div>
            <div class="bal-val">₹ {curr_bal:,.2f}</div>
        </div>
    """, unsafe_allow_html=True)
    
    # 3. Actions Grid
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("↻", key="sync"):
            st.cache_data.clear()
            st.session_state.df = recalculate_and_save(conn, conn.read(ttl=0))
            st.rerun()
        st.markdown('<div class="action-lbl">Sync</div>', unsafe_allow_html=True)
    with c2:
        if st.button("＋", key="add"): add_dialog()
        st.markdown('<div class="action-lbl">Add</div>', unsafe_allow_html=True)
    with c3:
        if st.button("📄", key="report"): 
            st.session_state.view_mode = 'table'
            st.rerun()
        st.markdown('<div class="action-lbl">Edit</div>', unsafe_allow_html=True)

    # 4. Transactions List
    col_t1, col_t2 = st.columns([3,1])
    with col_t1: st.markdown('<div style="padding-left:24px; font-weight:600; color:#101828;">Transactions</div>', unsafe_allow_html=True)
    with col_t2: 
        if st.button("See all"): 
            st.session_state.view_mode = 'table'
            st.rerun()

    if not df.empty:
        # Show recent 5
        recent = df.sort_values(by=['DATE', 'TRN. ID'], ascending=False).head(5)
        for _, row in recent.iterrows():
            is_out = row['TRN. TYPE'] in ["EXPENSE", "ADV-OUT"]
            icon = "↓" if is_out else "↑"
            cls = "bg-red" if is_out else "bg-green"
            amt_fmt = f"- ₹{row['AMOUNT']:,.0f}" if is_out else f"+ ₹{row['AMOUNT']:,.0f}"
            cat = row['CATEGORY'].split('/')[0].title()
            date_str = row['DATE'].strftime("%b %d")
            
            # Pure HTML rendering without indentation issues
            st.markdown(f"""
            <div class="txn-item">
                <div class="txn-left">
                    <div class="txn-icon {cls}">{icon}</div>
                    <div class="txn-info">
                        <div class="txn-cat">{cat}</div>
                        <div class="txn-meta">{date_str}</div>
                    </div>
                </div>
                <div class="txn-right">
                    <div class="txn-amt">{amt_fmt}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No transactions yet.")

# --- TABLE VIEW (EDIT MODE) ---
else:
    c_b1, c_b2 = st.columns([1, 4])
    with c_b1:
        if st.button("←"): 
            st.session_state.view_mode = 'home'
            st.rerun()
    with c_b2:
        st.markdown("<div style='padding-top:10px; font-weight:600;'>Manage Transactions</div>", unsafe_allow_html=True)
        
    if not df.empty:
        view_df = df.sort_values(by=['DATE', 'TRN. ID'], ascending=False)
        sel = st.dataframe(
            view_df,
            column_config={
                "DATE": st.column_config.DateColumn("Date", format="DD MMM"),
                "AMOUNT": st.column_config.NumberColumn("Amt", format="₹ %.0f"),
                "CATEGORY": st.column_config.TextColumn("Category"),
                "DESCRIPTION": st.column_config.TextColumn("Desc"),
                "TRN. ID": st.column_config.NumberColumn("ID", format="%d"),
            },
            use_container_width=True,
            hide_index=True,
            height=600,
            on_select="rerun",
            selection_mode="single-row"
        )
        if sel.selection.rows:
            rid = view_df.iloc[sel.selection.rows[0]]['TRN. ID']
            edit_dialog(df[df['TRN. ID'] == rid].iloc[0], rid)
