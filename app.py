import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="Wallet", page_icon="💳", layout="centered", initial_sidebar_state="collapsed")

# 💎 PROFESSIONAL FINTECH CSS (Reference: Clean White UI)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* Global Reset */
    .stApp {
        background-color: #F2F4F7; /* Light grey background */
        font-family: 'Inter', sans-serif;
    }
    
    /* Mobile Container Constraint */
    .main .block-container {
        max-width: 480px;
        padding: 0;
        background-color: #F2F4F7;
        min-height: 100vh;
        margin: 0 auto;
    }

    /* Hide Streamlit Elements */
    #MainMenu, footer, header {visibility: hidden;}
    div[data-testid="stToolbar"] { display: none; }

    /* --- COMPONENT 1: TOP HEADER --- */
    .top-header {
        padding: 40px 24px 20px 24px;
        background-color: transparent;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .welcome-text { font-size: 14px; color: #667085; font-weight: 500; }
    .icon-btn { font-size: 18px; color: #1D2939; cursor: pointer; }

    /* --- COMPONENT 2: BALANCE CARD --- */
    .balance-card {
        background-color: white;
        margin: 0 20px;
        padding: 32px 24px;
        border-radius: 24px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    }
    .balance-label {
        font-size: 13px;
        color: #667085;
        font-weight: 500;
        margin-bottom: 8px;
    }
    .balance-value {
        font-size: 36px;
        font-weight: 800;
        color: #101828;
        letter-spacing: -1px;
    }
    .balance-id {
        font-size: 12px;
        color: #98A2B3;
        margin-top: 8px;
        font-family: monospace;
    }

    /* --- COMPONENT 3: ACTION BUTTONS (The Circles) --- */
    .action-row {
        display: flex;
        justify-content: space-between;
        padding: 24px 32px;
    }
    .action-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 8px;
    }
    /* Invisible button overlay for Streamlit interaction */
    .stButton button {
        border-radius: 20px !important;
        height: 60px !important;
        width: 60px !important;
        background-color: white !important;
        border: 1px solid #EAECF0 !important;
        color: #1D2939 !important;
        font-size: 24px !important;
        box-shadow: 0 1px 2px rgba(16, 24, 40, 0.05) !important;
        transition: all 0.2s !important;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0 !important;
    }
    .stButton button:hover {
        background-color: #F9FAFB !important;
        border-color: #D0D5DD !important;
        transform: translateY(-2px);
    }
    /* Specific styling for the middle ADD button to make it black like the image? 
       Or keep white for consistency. Let's keep white for clean look, user can change. */
    
    .action-label {
        font-size: 12px;
        color: #475467;
        font-weight: 500;
    }

    /* --- COMPONENT 4: TRANSACTION LIST --- */
    .section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0 24px 16px 24px;
    }
    .section-title { font-size: 16px; font-weight: 600; color: #101828; }
    .section-link { font-size: 13px; color: #667085; text-decoration: none; cursor: pointer; }

    .txn-list {
        padding: 0 20px;
        display: flex;
        flex-direction: column;
        gap: 12px;
        padding-bottom: 80px; /* Space for scrolling */
    }
    .txn-item {
        background-color: white;
        padding: 16px;
        border-radius: 16px;
        display: flex;
        align-items: center;
        gap: 16px;
        box-shadow: 0 1px 2px rgba(16, 24, 40, 0.03);
    }
    .txn-icon {
        width: 40px;
        height: 40px;
        border-radius: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
    }
    .icon-in { background-color: #ECFDF3; color: #027A48; } /* Green background */
    .icon-out { background-color: #FEF3F2; color: #B42318; } /* Red background */
    
    .txn-details { flex: 1; }
    .txn-title { font-size: 14px; font-weight: 600; color: #101828; margin-bottom: 2px;}
    .txn-sub { font-size: 12px; color: #667085; }
    
    .txn-amount { font-size: 14px; font-weight: 700; color: #101828; text-align: right; }
    .txn-bal { font-size: 11px; color: #98A2B3; text-align: right; margin-top: 2px; }

    /* Custom Input Styling for Modal */
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
        
        running_balance = 0.0
        new_balances = []
        for _, row in df.iterrows():
            amt = row['AMOUNT']
            t = row['TRN. TYPE']
            if t in ["CREDIT", "ADV-IN"]: running_balance += amt
            elif t in ["EXPENSE", "ADV-OUT"]: running_balance -= amt
            new_balances.append(running_balance)
        df['BALANCE'] = new_balances
        conn.update(data=df)
        return df

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
        if st.form_submit_button("Save Entry", type="primary"):
            nid = 1
            if not df.empty:
                try: nid = int(df['TRN. ID'].max()) + 1
                except: nid = len(df) + 1
            new_row = {"DATE": pd.to_datetime(dte), "TRN. ID": nid, "TRN. TYPE": typ, "CATEGORY": cat, "DESCRIPTION": desc, "AMOUNT": amt, "TRN. MODE": "CASH", "BILL/VOUCHER": "NA", "BALANCE": 0, "REMARKS": ""}
            st.session_state.df = recalculate_and_save(conn, pd.concat([df, pd.DataFrame([new_row])], ignore_index=True))
            st.rerun()

@st.dialog("Manage Transaction")
def edit_dialog(row, rid):
    with st.form("edit_form"):
        st.caption(f"Editing ID #{rid}")
        c1, c2 = st.columns(2)
        with c1: dte = st.date_input("Date", value=row['DATE'])
        with c2: amt = st.number_input("Amount", value=clean_currency(row['AMOUNT']))
        typ = st.selectbox("Type", TRN_TYPES, index=TRN_TYPES.index(row['TRN. TYPE']) if row['TRN. TYPE'] in TRN_TYPES else 0)
        cat = st.selectbox("Category", CATEGORIES, index=CATEGORIES.index(row['CATEGORY']) if row['CATEGORY'] in CATEGORIES else 0)
        desc = st.text_input("Description", value=str(row['DESCRIPTION']))
        
        b1, b2 = st.columns(2)
        if b1.form_submit_button("Update"):
            idx = df[df['TRN. ID'] == rid].index[0]
            df.at[idx, 'DATE'] = pd.to_datetime(dte)
            df.at[idx, 'TRN. TYPE'] = typ
            df.at[idx, 'CATEGORY'] = cat
            df.at[idx, 'AMOUNT'] = amt
            df.at[idx, 'DESCRIPTION'] = desc
            st.session_state.df = recalculate_and_save(conn, df)
            st.rerun()
        if b2.form_submit_button("Delete", type="primary"):
            st.session_state.df = recalculate_and_save(conn, df[df['TRN. ID'] != rid])
            st.rerun()

# --- 5. UI LAYOUT (Mimicking the Image) ---

# A. Header
st.markdown("""
    <div class="top-header">
        <div class="welcome-text">Solar Finance</div>
        <div class="icon-btn">🔔</div>
    </div>
""", unsafe_allow_html=True)

# B. Balance Card
curr_bal = df.iloc[-1]['BALANCE'] if not df.empty and 'BALANCE' in df.columns else 0.0
st.markdown(f"""
    <div class="balance-card">
        <div class="balance-label">Account balance</div>
        <div class="balance-value">₹ {curr_bal:,.2f}</div>
        <div class="balance-id">**** **** {str(int(curr_bal))[-4:] if curr_bal > 1000 else "0000"}</div>
    </div>
""", unsafe_allow_html=True)

# C. Action Buttons (Using Columns for layout)
# We use st.columns but style the buttons with CSS to look like circles/squares
st.write("") # Spacer
c1, c2, c3, c4 = st.columns([1,1,1,1])

with c2:
    if st.button("＋", key="btn_add"):
        add_dialog()
    st.markdown('<div style="text-align:center; font-size:12px; color:#475467; margin-top:4px;">Add</div>', unsafe_allow_html=True)

with c3:
    if st.button("📊", key="btn_stats"):
        # Simple Analytics Dialog
        pass 
    st.markdown('<div style="text-align:center; font-size:12px; color:#475467; margin-top:4px;">Stats</div>', unsafe_allow_html=True)

with c1:
    if st.button("↻", key="btn_sync"):
        st.cache_data.clear()
        st.session_state.df = recalculate_and_save(conn, conn.read(ttl=0))
        st.rerun()
    st.markdown('<div style="text-align:center; font-size:12px; color:#475467; margin-top:4px;">Sync</div>', unsafe_allow_html=True)

# D. Transactions List
st.write("")
st.write("")
col_title, col_see_all = st.columns([3, 1])
with col_title:
    st.markdown('<div class="section-title">Transactions</div>', unsafe_allow_html=True)
with col_see_all:
    # Toggle State to show Table view
    if "view_mode" not in st.session_state: st.session_state.view_mode = "list"
    
    if st.button("See all", key="see_all_btn"):
        st.session_state.view_mode = "table" if st.session_state.view_mode == "list" else "list"
        st.rerun()

# Logic to switch between "Pretty List" and "Editable Table"
if st.session_state.view_mode == "list":
    # 1. PRETTY LIST VIEW (Read Only)
    if not df.empty:
        # Get recent 10
        recent = df.sort_values(by=['DATE', 'TRN. ID'], ascending=False).head(10)
        
        list_html = '<div class="txn-list">'
        for _, row in recent.iterrows():
            is_expense = row['TRN. TYPE'] in ["EXPENSE", "ADV-OUT"]
            icon = "↓" if is_expense else "↑"
            icon_class = "icon-out" if is_expense else "icon-in"
            amount_fmt = f"-₹{row['AMOUNT']:,.0f}" if is_expense else f"+₹{row['AMOUNT']:,.0f}"
            
            # Shorten Category
            cat_name = row['CATEGORY'].split('/')[0].title()
            date_str = row['DATE'].strftime("%b %d")
            desc = row['DESCRIPTION'] if row['DESCRIPTION'] else "No description"
            
            list_html += f"""
            <div class="txn-item">
                <div class="txn-icon {icon_class}">{icon}</div>
                <div class="txn-details">
                    <div class="txn-title">{cat_name}</div>
                    <div class="txn-sub">{desc} • {date_str}</div>
                </div>
                <div>
                    <div class="txn-amount">{amount_fmt}</div>
                </div>
            </div>
            """
        list_html += "</div>"
        st.markdown(list_html, unsafe_allow_html=True)
    else:
        st.info("No transactions yet.")

else:
    # 2. EDITABLE TABLE VIEW
    if st.button("← Back to Home"):
        st.session_state.view_mode = "list"
        st.rerun()
        
    st.caption("Tap a row to Edit/Delete")
    display_df = df.sort_values(by=['DATE', 'TRN. ID'], ascending=False)
    
    sel = st.dataframe(
        display_df,
        column_config={
            "DATE": st.column_config.DateColumn("Date", format="DD MMM"),
            "AMOUNT": st.column_config.NumberColumn("Amt", format="₹ %.0f"),
            "CATEGORY": st.column_config.TextColumn("Category"),
            "DESCRIPTION": st.column_config.TextColumn("Desc"),
            "TRN. ID": st.column_config.NumberColumn("ID", format="%d"),
        },
        use_container_width=True,
        hide_index=True,
        height=500,
        on_select="rerun",
        selection_mode="single-row"
    )
    
    if sel.selection.rows:
        rid = display_df.iloc[sel.selection.rows[0]]['TRN. ID']
        row = df[df['TRN. ID'] == rid].iloc[0]
        edit_dialog(row, rid)
