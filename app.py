import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="Solar Finance", page_icon="☀️", layout="centered", initial_sidebar_state="collapsed")

# Professional Mobile-First CSS (Fintech 2025)
st.markdown("""
    <style>
    /* 1. App Background & Mobile Container */
    .stApp {
        background-color: #F8FAFC; 
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .main .block-container {
        max-width: 480px;
        padding-top: 0.5rem; /* Reduced top padding */
        padding-bottom: 6rem;
        padding-left: 0.5rem;
        padding-right: 0.5rem;
        background-color: #FFFFFF;
        min-height: 100vh;
        margin: 0 auto;
    }

    /* 3. Hide Streamlit Bloat */
    #MainMenu, footer, header {visibility: hidden;}
    
    /* 4. Split Header Card Styling - COMPACTED */
    .card-top {
        background: linear-gradient(135deg, #4F46E5 0%, #6366F1 100%);
        padding: 16px 20px; /* Reduced padding */
        border-top-left-radius: 20px;
        border-top-right-radius: 20px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 20px rgba(79, 70, 229, 0.2);
    }
    .card-mid {
        background-color: #EEF2FF;
        padding: 4px 20px; /* Reduced padding */
        border-left: 1px solid #E0E7FF;
        border-right: 1px solid #E0E7FF;
    }
    .card-bot {
        background-color: #FFFFFF;
        padding: 12px; /* Reduced padding */
        border-bottom-left-radius: 20px;
        border-bottom-right-radius: 20px;
        border: 1px solid #E0E7FF;
        border-top: none;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    
    .header-title { font-size: 10px; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; font-weight: 700; margin-bottom: 2px;}
    .header-balance { font-size: 30px; font-weight: 800; letter-spacing: -0.5px; line-height: 1.2;}
    
    /* Stats Grid - COMPACTED */
    .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; } /* Tighter gap */
    .stat-box { 
        background: #F8FAFC; padding: 8px 10px; border-radius: 10px; /* Smaller box */
        border: 1px solid #F1F5F9; text-align: center; 
    }
    .stat-label { font-size: 9px; color: #64748B; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px; }
    .stat-val { font-size: 13px; color: #0F172A; font-weight: 700; margin-top: 2px; }
    .val-green { color: #10B981; }
    .val-red { color: #EF4444; }

    /* 5. Inputs & Forms */
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        height: 46px;
        font-size: 16px;
        color: #1E293B;
    }
    
    /* 6. Tabs Design */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #F1F5F9;
        padding: 4px;
        border-radius: 14px;
        gap: 0px;
        margin-bottom: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 36px;
        border-radius: 10px;
        border: none;
        color: #64748B;
        font-weight: 600;
        font-size: 13px;
        flex: 1;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF;
        color: #4F46E5;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .stTabs [data-baseweb="tab-highlight"] { display: none; }

    /* 7. General Buttons */
    .stButton button {
        width: 100%;
        border-radius: 12px;
        height: 50px;
        font-weight: 600;
        font-size: 15px;
        border: none;
        background-color: #4F46E5;
        color: white;
        transition: all 0.2s;
    }
    .stButton button:hover { background-color: #4338CA; }

    /* 8. Floating Action Button (FAB) */
    .element-container:has(button[title="Add Transaction"]) {
        position: fixed;
        bottom: 24px;
        right: 24px;
        z-index: 99999;
        width: auto !important;
    }
    
    button[title="Add Transaction"] {
        border-radius: 50% !important;
        width: 64px !important;
        height: 64px !important;
        padding: 0 !important;
        box-shadow: 0 10px 25px -5px rgba(79, 70, 229, 0.5) !important;
        font-size: 32px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        background: linear-gradient(135deg, #4F46E5 0%, #6366F1 100%) !important;
        border: 2px solid white !important;
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
    except Exception:
        return pd.DataFrame(columns=[
            "DATE", "TRN. ID", "TRN. TYPE", "CATEGORY", 
            "DESCRIPTION", "AMOUNT", "TRN. MODE", 
            "BILL/VOUCHER", "BALANCE", "REMARKS"
        ])

def recalculate_and_save(conn, df):
    with st.spinner("Syncing..."):
        if 'TRN. ID' in df.columns:
            df['TRN. ID'] = pd.to_numeric(df['TRN. ID'], errors='coerce').fillna(0)
        if 'AMOUNT' in df.columns:
            df['AMOUNT'] = df['AMOUNT'].apply(clean_currency)
            
        df = df.sort_values(by=['DATE', 'TRN. ID'], ascending=[True, True]).reset_index(drop=True)
        
        running_balance = 0.0
        new_balances = []
        for index, row in df.iterrows():
            amt = row['AMOUNT']
            t_type = row['TRN. TYPE']
            if t_type in ["CREDIT", "ADV-IN"]: running_balance += amt
            elif t_type in ["EXPENSE", "ADV-OUT"]: running_balance -= amt
            new_balances.append(running_balance)
            
        df['BALANCE'] = new_balances
        conn.update(data=df)
        return df

# --- 4. APP INITIALIZATION ---
conn = st.connection("gsheets", type=GSheetsConnection)
if "df" not in st.session_state:
    st.session_state.df = load_data(conn)
df = st.session_state.df

# --- DIALOGS (MODALS) ---

@st.dialog("New Transaction")
def add_transaction_dialog():
    with st.form("new_entry_form", clear_on_submit=True):
        amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0, format="%.2f")
        c1, c2 = st.columns([1, 1.2])
        with c1: txn_date = st.date_input("Date", value=date.today())
        with c2: txn_type = st.selectbox("Type", TRN_TYPES)
        cat_idx = CATEGORIES.index(txn_type) if txn_type in CATEGORIES else 0
        category = st.selectbox("Category", CATEGORIES, index=cat_idx)
        desc = st.text_input("Description", placeholder="e.g. Fuel purchase")
        c5, c6 = st.columns(2)
        with c5: mode = st.selectbox("Mode", MODES)
        with c6: doc = st.selectbox("Proof", DOC_TYPES)
        rem = st.text_input("Remarks", placeholder="Optional notes")
        
        if st.form_submit_button("Save Transaction", type="primary"):
            new_id = 1
            if not df.empty and 'TRN. ID' in df:
                try: new_id = int(df['TRN. ID'].max()) + 1
                except: new_id = len(df) + 1
            new_row = {
                "DATE": pd.to_datetime(txn_date),
                "TRN. ID": new_id, "TRN. TYPE": txn_type, "CATEGORY": category,
                "DESCRIPTION": desc, "AMOUNT": amount, "TRN. MODE": mode,
                "BILL/VOUCHER": doc, "BALANCE": 0, "REMARKS": rem
            }
            updated_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            st.session_state.df = recalculate_and_save(conn, updated_df)
            st.rerun()

@st.dialog("Edit Transaction")
def edit_transaction_dialog(row_to_edit, selected_id):
    with st.form("edit_form"):
        e_date = st.date_input("Date", value=row_to_edit['DATE'])
        ec1, ec2 = st.columns(2)
        with ec1: e_amt = st.number_input("Amount", value=clean_currency(row_to_edit['AMOUNT']))
        with ec2: e_type = st.selectbox("Type", TRN_TYPES, index=TRN_TYPES.index(row_to_edit['TRN. TYPE']) if row_to_edit['TRN. TYPE'] in TRN_TYPES else 0)
        e_cat = st.selectbox("Category", CATEGORIES, index=CATEGORIES.index(row_to_edit['CATEGORY']) if row_to_edit['CATEGORY'] in CATEGORIES else 0)
        e_desc = st.text_input("Description", value=str(row_to_edit['DESCRIPTION']))
        ec3, ec4 = st.columns(2)
        with ec3: e_mode = st.selectbox("Mode", MODES, index=MODES.index(row_to_edit['TRN. MODE']) if row_to_edit['TRN. MODE'] in MODES else 0)
        with ec4: e_doc = st.selectbox("Proof", DOC_TYPES, index=DOC_TYPES.index(row_to_edit['BILL/VOUCHER']) if row_to_edit['BILL/VOUCHER'] in DOC_TYPES else 0)
        e_rem = st.text_input("Remarks", value=str(row_to_edit['REMARKS']) if pd.notnull(row_to_edit['REMARKS']) else "")

        bc1, bc2 = st.columns(2)
        if bc1.form_submit_button("💾 Save Changes", type="primary"):
            idx = df[df['TRN. ID'] == selected_id].index[0]
            df.at[idx, 'DATE'] = pd.to_datetime(e_date)
            df.at[idx, 'TRN. TYPE'] = e_type
            df.at[idx, 'CATEGORY'] = e_cat
            df.at[idx, 'AMOUNT'] = e_amt
            df.at[idx, 'DESCRIPTION'] = e_desc
            df.at[idx, 'TRN. MODE'] = e_mode
            df.at[idx, 'BILL/VOUCHER'] = e_doc
            df.at[idx, 'REMARKS'] = e_rem
            st.session_state.df = recalculate_and_save(conn, df)
            st.rerun()
            
        if bc2.form_submit_button("🗑️ Delete", type="secondary"):
            new_df = df[df['TRN. ID'] != selected_id]
            st.session_state.df = recalculate_and_save(conn, new_df)
            st.rerun()

# --- 5. SMART HEADER WIDGET ---
current_bal = 0.0

if not df.empty:
    try: 
        current_bal = df.iloc[-1]['BALANCE'] if 'BALANCE' in df.columns else 0.0
    except: pass

# 5a. Top Card (Balance ONLY)
st.markdown(f"""
    <div class="card-top">
        <div class="header-title">Current Balance</div>
        <div class="header-balance">₹ {current_bal:,.0f}</div>
    </div>
""", unsafe_allow_html=True)

# 5b. Middle Bar (Month Picker)
if not df.empty:
    dates_df = df[['DATE']].copy()
    dates_df['MonthLabel'] = dates_df['DATE'].dt.strftime('%B %Y')
    dates_df['YearMonth'] = dates_df['DATE'].dt.to_period('M')
    unique_months = dates_df.drop_duplicates('YearMonth').sort_values('YearMonth', ascending=False)['MonthLabel'].tolist()
else:
    unique_months = []

selected_month = None
if unique_months:
    with st.container():
        st.markdown('<div class="card-mid">', unsafe_allow_html=True)
        selected_month = st.selectbox("Select Period", unique_months, label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)

# 5c. Bottom Card (Grid Stats)
credit_sum, expense_sum, advin_sum, advout_sum = 0.0, 0.0, 0.0, 0.0

if selected_month and not df.empty:
    try:
        mask_month = df['DATE'].dt.strftime('%B %Y') == selected_month
        month_df = df.loc[mask_month]
        grp = month_df.groupby('TRN. TYPE')['AMOUNT'].sum()
        credit_sum = grp.get('CREDIT', 0.0)
        expense_sum = grp.get('EXPENSE', 0.0)
        advin_sum = grp.get('ADV-IN', 0.0)
        advout_sum = grp.get('ADV-OUT', 0.0)
    except: pass

st.markdown(f"""
    <div class="card-bot">
        <div class="stats-grid">
            <div class="stat-box">
                <div class="stat-label">Credit</div>
                <div class="stat-val val-green">₹ {credit_sum:,.0f}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Expense</div>
                <div class="stat-val val-red">₹ {expense_sum:,.0f}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Adv In</div>
                <div class="stat-val val-green">₹ {advin_sum:,.0f}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Adv Out</div>
                <div class="stat-val val-red">₹ {advout_sum:,.0f}</div>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

st.write("") 

# --- 6. NAVIGATION ---
tab1, tab2 = st.tabs(["Transactions", "Analytics"])

# === TAB 1: TRANSACTIONS ===
with tab1:
    # 1. Sync & Export Tools
    c_t1, c_t2 = st.columns([1, 4])
    with c_t1:
        if st.button("🔄", help="Force Sync"):
            st.cache_data.clear()
            fresh_df = conn.read(ttl=0)
            fresh_df.columns = fresh_df.columns.str.strip()
            fresh_df['DATE'] = pd.to_datetime(fresh_df['DATE'], dayfirst=True, errors='coerce')
            if 'AMOUNT' in fresh_df.columns: fresh_df['AMOUNT'] = fresh_df['AMOUNT'].apply(clean_currency)
            st.session_state.df = recalculate_and_save(conn, fresh_df)
            st.rerun()
            
    with c_t2:
        if not df.empty:
            csv_data = df.sort_values(by=['DATE', 'TRN. ID'], ascending=[True, True]).to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export CSV", csv_data, f"solar_backup.csv", "text/csv")

    # 2. Interactive Data Table
    if not df.empty:
        st.caption("👇 Tap row to Edit")
        display_df = df.sort_values(by=['DATE', 'TRN. ID'], ascending=False).copy()
        
        selection = st.dataframe(
            display_df,
            column_config={
                "DATE": st.column_config.DateColumn("Date", format="DD MMM"),
                "AMOUNT": st.column_config.NumberColumn("Amt", format="₹ %.0f"),
                "TRN. TYPE": st.column_config.TextColumn("Type", width="small"),
                "DESCRIPTION": st.column_config.TextColumn("Desc", width="medium"),
                "BALANCE": st.column_config.NumberColumn("Bal", format="₹ %.0f"),
                "TRN. ID": st.column_config.NumberColumn("ID", format="%d"),
            },
            width="stretch",
            hide_index=True,
            height=450,
            on_select="rerun",
            selection_mode="single-row"
        )

        if selection.selection.rows:
            selected_row_index = selection.selection.rows[0]
            selected_id = display_df.iloc[selected_row_index]['TRN. ID']
            row_to_edit = df[df['TRN. ID'] == selected_id].iloc[0]
            edit_transaction_dialog(row_to_edit, selected_id)
            
    else:
        st.info("No transactions found.")

# === TAB 2: ANALYTICS ===
with tab2:
    if not df.empty:
        col_f1, col_f2 = st.columns(2)
        with col_f1: date_range = st.date_input("Filter Date", value=(df['DATE'].min().date(), df['DATE'].max().date()))
        with col_f2: 
            avail = list(df['TRN. TYPE'].unique())
            sel_types = st.multiselect("Filter Type", avail, default=[t for t in ["EXPENSE", "ADV-OUT"] if t in avail])

        if len(date_range) == 2:
            mask = (df['DATE'].dt.date >= date_range[0]) & (df['DATE'].dt.date <= date_range[1]) & (df['TRN. TYPE'].isin(sel_types))
            df_filt = df.loc[mask]
            
            if not df_filt.empty:
                pivot = df_filt.groupby('CATEGORY')['AMOUNT'].sum().reset_index().sort_values('AMOUNT', ascending=False)
                st.metric("Total Selected", f"₹ {pivot['AMOUNT'].sum():,.0f}")
                st.dataframe(pivot, column_config={"AMOUNT": st.column_config.NumberColumn("Total", format="₹ %.0f")}, width="stretch", hide_index=True)
            else:
                st.info("No data in range.")
    else:
        st.info("No data.")

# --- FLOATING ACTION BUTTON (ADD) ---
# Fixed Position Button using valid Streamlit key targeting
if st.button("➕", key="fab_add", help="Add Transaction"):
    add_transaction_dialog()