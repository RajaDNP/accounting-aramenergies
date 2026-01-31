import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURATION & RESPONSIVE DESIGN SYSTEM ---
st.set_page_config(page_title="Account Book", page_icon="", layout="wide", initial_sidebar_state="collapsed")

# Apple-Style Responsive CSS (Desktop & Mobile)
st.markdown("""
    <style>
    /* 1. Global Typography & Reset */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    .stApp {
        background-color: #F5F5F7; /* Apple System Gray 6 */
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        color: #1D1D1F;
    }
    
    /* 2. Responsive Container Logic - PADDING UPDATED */
    .main .block-container {
        padding-top: 0rem;  /* REMOVED TOP SPACE */
        padding-bottom: 1rem; /* REDUCED BOTTOM SPACE */
        margin: 0 auto;
        transition: max-width 0.3s ease;
    }

    /* DESKTOP VIEW */
    @media (min-width: 768px) {
        .main .block-container {
            max-width: 950px;
            padding-left: 1rem; /* REDUCED LEFT SPACE */
            padding-right: 1rem; /* REDUCED RIGHT SPACE */
        }
    }
    
    /* MOBILE VIEW */
    @media (max-width: 767px) {
        .main .block-container {
            max-width: 100%;
            padding-left: 0.5rem; /* REDUCED LEFT SPACE */
            padding-right: 0.5rem; /* REDUCED RIGHT SPACE */
        }
    }

    /* 3. Gap Reduction */
    div[data-testid="stVerticalBlock"] {
        gap: 0.6rem !important;
    }
    
    /* Hide Header/Footer */
    #MainMenu, footer, header {visibility: hidden;}
    
    /* 4. Apple Wallet Card */
    .wallet-card {
        background: linear-gradient(135deg, #007AFF 0%, #0055D4 100%);
        border-radius: 22px;
        padding: 24px 24px;
        color: white;
        margin-bottom: 12px;
        box-shadow: 0 10px 25px -5px rgba(0, 122, 255, 0.35);
        position: relative;
        overflow: hidden;
    }
    
    .wallet-card::before {
        content: "";
        position: absolute;
        top: -50%; left: -50%; width: 200%; height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 60%);
        transform: rotate(30deg);
        pointer-events: none;
    }

    .bal-label { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; opacity: 0.85; margin-bottom: 4px; }
    .bal-val { font-size: 38px; font-weight: 700; letter-spacing: -1px; margin-bottom: 24px; }
    
    /* Mini Stats Grid */
    .stats-row {
        display: flex;
        justify-content: space-between;
        background: rgba(0, 0, 0, 0.18);
        border-radius: 14px;
        padding: 14px 0;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
    }
    .stat-item { text-align: center; width: 25%; border-right: 1px solid rgba(255,255,255,0.15); }
    .stat-item:last-child { border-right: none; }
    .stat-lbl { font-size: 9px; opacity: 0.85; font-weight: 600; margin-bottom: 2px; letter-spacing: 0.5px; }
    .stat-num { font-size: 13px; font-weight: 600; }

    /* 5. Inputs & Buttons */
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #FFFFFF !important;
        border: 1px solid #D1D1D6 !important;
        border-radius: 10px !important;
        height: 42px !important;
        color: #1D1D1F !important;
    }
    
    /* Button Styling */
    .stButton button {
        border-radius: 12px;
        font-weight: 600;
        height: 44px;
        margin-top: 0px !important;
        border: none;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        transition: all 0.2s ease;
    }
    
    /* Primary Button (Add) */
    div[data-testid="stVerticalBlock"] button[kind="primary"] {
        background-color: #007AFF; 
        color: white;
    }
    div[data-testid="stVerticalBlock"] button[kind="primary"]:hover {
        background-color: #0062CC;
        box-shadow: 0 4px 12px rgba(0, 122, 255, 0.3);
    }

    /* Secondary Buttons (Sync, Export) */
    div[data-testid="stVerticalBlock"] button[kind="secondary"] {
        background-color: #FFFFFF;
        color: #1D1D1F;
        border: 1px solid #E5E5EA;
    }
    div[data-testid="stVerticalBlock"] button[kind="secondary"]:hover {
        background-color: #F2F2F7;
        border-color: #D1D1D6;
    }

    /* 6. Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #E5E5EA;
        padding: 4px;
        border-radius: 12px;
        margin-bottom: 16px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 32px;
        border-radius: 8px;
        border: none;
        color: #8E8E93;
        font-weight: 500;
        font-size: 13px;
        flex: 1;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF;
        color: #000000;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        font-weight: 600;
    }
    
    /* 7. Dataframe */
    div[data-testid="stDataFrame"] {
        background: white;
        border-radius: 16px;
        padding: 0px; 
        border: 1px solid #E5E5EA;
        overflow: hidden;
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
        return pd.DataFrame(columns=["DATE", "TRN. ID", "TRN. TYPE", "CATEGORY", "DESCRIPTION", "AMOUNT", "TRN. MODE", "BILL/VOUCHER", "BALANCE", "REMARKS"])

def recalculate_and_save(conn, df):
    with st.spinner("Processing..."):
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

# --- 4. DATA LOADING ---
conn = st.connection("gsheets", type=GSheetsConnection)
if "df" not in st.session_state:
    st.session_state.df = load_data(conn)
df = st.session_state.df

# --- DIALOGS (MODALS) ---
@st.dialog("New Entry")
def add_transaction_dialog():
    st.write("")
    with st.form("new_entry_form", clear_on_submit=True):
        amount = st.number_input("Amount", min_value=0.0, step=100.0, format="%.2f")
        c1, c2 = st.columns([1, 1.3])
        with c1: txn_date = st.date_input("Date", value=date.today())
        with c2: txn_type = st.selectbox("Type", TRN_TYPES)
        
        cat_idx = CATEGORIES.index(txn_type) if txn_type in CATEGORIES else 0
        category = st.selectbox("Category", CATEGORIES, index=cat_idx)
        desc = st.text_input("Description", placeholder="Description")
        c5, c6 = st.columns(2)
        with c5: mode = st.selectbox("Mode", MODES)
        with c6: doc = st.selectbox("Proof", DOC_TYPES)
        rem = st.text_input("Remarks", placeholder="Notes")
        
        st.write("")
        if st.form_submit_button("Done", type="primary"):
            new_id = 1
            if not df.empty and 'TRN. ID' in df:
                try: new_id = int(df['TRN. ID'].max()) + 1
                except: new_id = len(df) + 1
            new_row = {
                "DATE": pd.to_datetime(txn_date), "TRN. ID": new_id, "TRN. TYPE": txn_type, "CATEGORY": category,
                "DESCRIPTION": desc, "AMOUNT": amount, "TRN. MODE": mode, "BILL/VOUCHER": doc, "BALANCE": 0, "REMARKS": rem
            }
            updated_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            st.session_state.df = recalculate_and_save(conn, updated_df)
            st.rerun()

@st.dialog("Edit Detail")
def edit_transaction_dialog(row_to_edit, selected_id):
    st.write("")
    with st.form("edit_form"):
        ec1, ec2 = st.columns(2)
        with ec1: e_amt = st.number_input("Amount", value=clean_currency(row_to_edit['AMOUNT']))
        with ec2: e_date = st.date_input("Date", value=row_to_edit['DATE'])
        e_type = st.selectbox("Type", TRN_TYPES, index=TRN_TYPES.index(row_to_edit['TRN. TYPE']) if row_to_edit['TRN. TYPE'] in TRN_TYPES else 0)
        e_cat = st.selectbox("Category", CATEGORIES, index=CATEGORIES.index(row_to_edit['CATEGORY']) if row_to_edit['CATEGORY'] in CATEGORIES else 0)
        e_desc = st.text_input("Description", value=str(row_to_edit['DESCRIPTION']))
        ec3, ec4 = st.columns(2)
        with ec3: e_mode = st.selectbox("Mode", MODES, index=MODES.index(row_to_edit['TRN. MODE']) if row_to_edit['TRN. MODE'] in MODES else 0)
        with ec4: e_doc = st.selectbox("Proof", DOC_TYPES, index=DOC_TYPES.index(row_to_edit['BILL/VOUCHER']) if row_to_edit['BILL/VOUCHER'] in DOC_TYPES else 0)
        e_rem = st.text_input("Remarks", value=str(row_to_edit['REMARKS']) if pd.notnull(row_to_edit['REMARKS']) else "")
        st.write("---")
        bc1, bc2 = st.columns(2)
        if bc1.form_submit_button("Save", type="primary", use_container_width=True):
            idx = df[df['TRN. ID'] == selected_id].index[0]
            df.at[idx, 'DATE'] = pd.to_datetime(e_date); df.at[idx, 'TRN. TYPE'] = e_type; df.at[idx, 'CATEGORY'] = e_cat
            df.at[idx, 'AMOUNT'] = e_amt; df.at[idx, 'DESCRIPTION'] = e_desc; df.at[idx, 'TRN. MODE'] = e_mode
            df.at[idx, 'BILL/VOUCHER'] = e_doc; df.at[idx, 'REMARKS'] = e_rem
            st.session_state.df = recalculate_and_save(conn, df)
            st.rerun()
        if bc2.form_submit_button("Delete", type="secondary", use_container_width=True):
            new_df = df[df['TRN. ID'] != selected_id]
            st.session_state.df = recalculate_and_save(conn, new_df)
            st.rerun()

# --- 5. TOP HEADER & FILTER ---

# Date & Month Logic
if not df.empty:
    dates_df = df[['DATE']].copy()
    dates_df['MonthLabel'] = dates_df['DATE'].dt.strftime('%B %Y')
    dates_df['YearMonth'] = dates_df['DATE'].dt.to_period('M')
    unique_months = dates_df.drop_duplicates('YearMonth').sort_values('YearMonth', ascending=False)['MonthLabel'].tolist()
else:
    unique_months = []

# --- Header Layout ---
col_h1, col_h2 = st.columns([3, 1], vertical_alignment="center")

with col_h1:
    # Custom Apple-Style Title
    st.markdown("""
    <div style="font-size: 28px; font-weight: 800; color: #1D1D1F; letter-spacing: -0.5px;">
        Account Book
    </div>
    """, unsafe_allow_html=True)

with col_h2:
    selected_month = unique_months[0] if unique_months else None
    if unique_months:
        selected_month = st.selectbox("Period", unique_months, label_visibility="collapsed")

# --- 6. WALLET CARD ---
current_bal = 0.0
credit_sum, expense_sum, advin_sum, advout_sum = 0.0, 0.0, 0.0, 0.0

if not df.empty:
    try: current_bal = df.iloc[-1]['BALANCE']
    except: pass

if selected_month and not df.empty:
    mask_month = df['DATE'].dt.strftime('%B %Y') == selected_month
    month_df = df.loc[mask_month]
    grp = month_df.groupby('TRN. TYPE')['AMOUNT'].sum()
    credit_sum = grp.get('CREDIT', 0.0)
    expense_sum = grp.get('EXPENSE', 0.0)
    advin_sum = grp.get('ADV-IN', 0.0)
    advout_sum = grp.get('ADV-OUT', 0.0)

st.markdown(f"""
    <div class="wallet-card">
        <div class="bal-label">Total Balance</div>
        <div class="bal-val">₹ {current_bal:,.0f}</div>
        <div class="stats-row">
            <div class="stat-item"><div class="stat-lbl">CREDIT</div><div class="stat-num">₹{credit_sum/1000:.1f}k</div></div>
            <div class="stat-item"><div class="stat-lbl">EXPENSE</div><div class="stat-num">₹{expense_sum/1000:.1f}k</div></div>
            <div class="stat-item"><div class="stat-lbl">ADV +</div><div class="stat-num">₹{advin_sum/1000:.1f}k</div></div>
            <div class="stat-item"><div class="stat-lbl">ADV -</div><div class="stat-num">₹{advout_sum/1000:.1f}k</div></div>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- 7. TABS & ACTIONS ---
tab1, tab2 = st.tabs(["Transactions", "Analytics"])

with tab1:
    # --- ACTION BUTTONS (EQUAL SIZE) ---
    c_sync, c_add, c_exp = st.columns(3)
    
    with c_sync:
        if st.button("↻ Sync", help="Reload Data", use_container_width=True):
            st.cache_data.clear()
            fresh_df = conn.read(ttl=0)
            fresh_df.columns = fresh_df.columns.str.strip()
            fresh_df['DATE'] = pd.to_datetime(fresh_df['DATE'], dayfirst=True, errors='coerce')
            if 'AMOUNT' in fresh_df.columns: fresh_df['AMOUNT'] = fresh_df['AMOUNT'].apply(clean_currency)
            st.session_state.df = recalculate_and_save(conn, fresh_df)
            st.rerun()
            
    with c_add:
        # Primary Action - Blue Button
        if st.button("＋ Add", type="primary", help="Add Transaction", use_container_width=True):
            add_transaction_dialog()

    with c_exp:
        if not df.empty:
            csv_data = df.sort_values(by=['DATE', 'TRN. ID']).to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export", csv_data, "solar_backup.csv", "text/csv", use_container_width=True)
        else:
             st.button("📥 Export", disabled=True, use_container_width=True)

    # --- TABLE ---
    if not df.empty:
        display_df = df.sort_values(by=['DATE', 'TRN. ID'], ascending=False).copy()
        
        # UPDATED: Replaced use_container_width=True with width='stretch'
        selection = st.dataframe(
            display_df,
            column_config={
                "DATE": st.column_config.DateColumn("Date", format="DD MMM"),
                "AMOUNT": st.column_config.NumberColumn("Amt", format="₹%.0f"),
                "TRN. TYPE": st.column_config.TextColumn("Type", width="small"),
                "DESCRIPTION": st.column_config.TextColumn("Desc", width="medium"),
                "BALANCE": st.column_config.NumberColumn("Bal", format="₹%.0f"),
                "TRN. ID": st.column_config.NumberColumn("ID", format="%d"),
            },
            width="stretch", 
            hide_index=True,
            height=500,
            on_select="rerun",
            selection_mode="single-row"
        )

        if selection.selection.rows:
            selected_row_index = selection.selection.rows[0]
            selected_id = display_df.iloc[selected_row_index]['TRN. ID']
            row_to_edit = df[df['TRN. ID'] == selected_id].iloc[0]
            edit_transaction_dialog(row_to_edit, selected_id)
    else:
        st.info("No recent transactions.")

with tab2:
    st.write("")
    if not df.empty:
        col_f1, col_f2 = st.columns(2)
        with col_f1: date_range = st.date_input("Range", value=(df['DATE'].min().date(), df['DATE'].max().date()))
        with col_f2: 
            avail = list(df['TRN. TYPE'].unique())
            sel_types = st.multiselect("Type", avail, default=[t for t in ["EXPENSE", "ADV-OUT"] if t in avail])

        if len(date_range) == 2:
            mask = (df['DATE'].dt.date >= date_range[0]) & (df['DATE'].dt.date <= date_range[1]) & (df['TRN. TYPE'].isin(sel_types))
            df_filt = df.loc[mask]
            
            if not df_filt.empty:
                pivot = df_filt.groupby('CATEGORY')['AMOUNT'].sum().reset_index().sort_values('AMOUNT', ascending=False)
                st.metric("Total Selected", f"₹ {pivot['AMOUNT'].sum():,.0f}")
                # UPDATED: Replaced use_container_width=True with width='stretch'
                st.dataframe(pivot, column_config={"AMOUNT": st.column_config.NumberColumn("Total", format="₹ %.0f")}, width="stretch", hide_index=True)
            else:
                st.info("No data available.")
    else:
        st.info("Database is empty.")
