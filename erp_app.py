import streamlit as st
import pandas as pd
import datetime
import json
import smtplib
from email.mime.text import MIMEText

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- Configuration ---
st.set_page_config(layout="wide", page_title="Inter-College Festive Event ERP")

# --- Glassmorphism CSS (Injected at the start) ---
GLASSMORPHISM_CSS = """
<style>
/* Basic body styling */
body {
    background: linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%);
    color: #333; /* Darker text for readability */
}

/* Main content container */
.main .block-container {
    background: rgba(255, 255, 255, 0.25); /* Transparent white */
    backdrop-filter: blur(10px); /* Frosted glass effect */
    -webkit-backdrop-filter: blur(10px); /* Safari support */
    border: 1px solid rgba(255, 255, 255, 0.18); /* Light border */
    border-radius: 12px;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.15); /* Subtle shadow */
    padding: 2rem;
    margin-top: 1.5rem; /* Add some space from header */
}

/* Sidebar styling */
.st-emotion-cache-vk33gh { /* Target the main sidebar wrapper */
    background: rgba(255, 255, 255, 0.15); /* More transparent for sidebar */
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    border-right: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 2px 0 10px rgba(0, 0, 0, 0.05);
    border-radius: 0 12px 12px 0; /* Rounded on the right side */
    padding: 1.5rem;
}

/* Headers and Titles */
h1, h2, h3, h4, h5, h6 {
    color: #1a1a1a;
    text-shadow: 0px 1px 2px rgba(0,0,0,0.05);
}

/* Buttons */
.stButton > button {
    background: rgba(255, 255, 255, 0.3);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    color: #1a1a1a;
    font-weight: bold;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
    transition: all 0.2s ease-in-out;
}
.stButton > button:hover {
    background: rgba(255, 255, 255, 0.45);
    transform: translateY(-2px);
    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
}

/* Text Inputs and Selectboxes */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > button {
    background: rgba(255, 255, 255, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    color: #1a1a1a;
    padding: 0.75rem 1rem;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus,
.stSelectbox > div > div > button:focus {
    border-color: rgba(255, 255, 255, 0.3);
    box-shadow: 0 0 0 0.2rem rgba(255, 255, 255, 0.25);
}

/* Data Editor / Dataframes */
.st-emotion-cache-j9f0j6 /* data editor parent */,
.st-emotion-cache-pej8to /* dataframe parent */ {
    background: rgba(255, 255, 255, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
    padding: 10px;
}
.st-emotion-cache-163v2p /* dataframe header */ {
    background: rgba(255, 255, 255, 0.3);
}

/* Expander */
.streamlit-expanderHeader {
    background: rgba(255, 255, 255, 0.25);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    margin-bottom: 0.5rem;
    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
}
.streamlit-expanderContent {
    background: rgba(255, 255, 255, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 0 0 8px 8px;
    padding: 1rem;
    margin-top: -0.5rem; /* Overlap with header */
}

/* Info, Success, Warning, Error boxes */
.st-emotion-cache-1fcp7ec /* message boxes wrapper */ {
    background: rgba(255, 255, 255, 0.25);
    backdrop-filter: blur(5px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}
.st-emotion-cache-1fcp7ec.stAlert-info { border-left: 5px solid #2196F3; }
.st-emotion-cache-1fcp7ec.stAlert-success { border-left: 5px solid #4CAF50; }
.st-emotion-cache-1fcp7ec.stAlert-warning { border-left: 5px solid #ff9800; }
.st-emotion-cache-1fcp7ec.stAlert-error { border-left: 5px solid #f44336; }

/* Customizing the Streamlit header, remove default */
header {
    background: none !important;
    box-shadow: none !important;
}

/* Ensure images have rounded corners too */
img {
    border-radius: 8px;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
}

</style>
"""
st.markdown(GLASSMORPHISM_CSS, unsafe_allow_html=True)


# --- Google Sheets Database Global Configuration ---
# These are module-level global variables for GSheet connectivity status and client objects.
# The cached function and GoogleSheetDB class will refer to these.
_gspread_enabled = False
_client = None
_spreadsheet = None
_spreadsheet_name_global = "Mock Sheet" # Default name, updated if GSheets enabled

# Global mock data to be used when gspread is disabled or fails
_global_mock_data = {}

# Helper to populate global mock data
def _populate_global_mock_data_init():
    global _global_mock_data
    _global_mock_data = {
        "users": pd.DataFrame([
            {"Username": "admin", "Password": "admin", "Role": "Admin", "Name": "Alice Admin", "Availability": "N/A"},
            {"Username": "coord1", "Password": "coord", "Role": "Coordinator", "Name": "Bob Coordinator", "Availability": "N/A"},
            {"Username": "part1", "Password": "part", "Role": "Participant", "Name": "Charlie Participant", "Availability": "N/A"},
            {"Username": "volun1", "Password": "volun", "Role": "Volunteer", "Name": "Diana Volunteer", "Availability": "Available"},
        ]),
        "events": pd.DataFrame({
            "Event ID": ["E001", "E002", "E003"],
            "Name": ["Tech Fest", "Cultural Gala", "Sports Day"],
            "Date": [datetime.date(2025, 10, 15), datetime.date(2025, 11, 20), datetime.date(2025, 12, 5)],
            "Time": ["10:00 AM", "06:00 PM", "09:00 AM"],
            "Location": ["Auditorium A", "Amphitheater", "Main Sports Ground"],
            "Coordinator": ["Bob Coordinator", "Bob Coordinator", "Alice Admin"],
            "Budget": [50000, 75000, 30000],
            "Status": ["Upcoming", "Upcoming", "Upcoming"],
            "Description": [
                "A showcase of the latest technologies and innovations.",
                "An evening celebrating diverse cultural performances.",
                "Inter-college sports competition across various disciplines."
            ]
        }),
        "registrations": pd.DataFrame([
            {"Reg ID": "R001", "Participant Username": "part1", "Event ID": "E001", "Registration Date": datetime.date.today()}
        ]),
        "volunteers": pd.DataFrame([
            {"Volunteer Username": "volun1", "Full Name": "Diana Volunteer", "Availability": "Available"}
        ]),
        "tasks": pd.DataFrame([
            {"Task ID": "T001", "Event ID": "E001", "Description": "Set up registration desk", "Assigned To Volunteer Username": "volun1", "Due Date": datetime.date(2025, 10, 14), "Status": "Assigned", "Created By": "coord1"},
            {"Task ID": "T002", "Event ID": "E001", "Description": "Guide guests to main hall", "Assigned To Volunteer Username": "volun1", "Due Date": datetime.date(2025, 10, 15), "Status": "Assigned", "Created By": "coord1"},
        ]),
        "announcements": pd.DataFrame([
            {"Announcement ID": "A001", "Title": "Welcome to the ERP!", "Content": "This is the new Inter-College Festive Event ERP. Explore its features!", "Author Username": "admin", "Date Posted": datetime.date.today(), "Target Role": "All"},
            {"Announcement ID": "A002", "Title": "Volunteer Briefing for Tech Fest", "Content": "Mandatory briefing for all Tech Fest volunteers on Oct 10th.", "Author Username": "coord1", "Date Posted": datetime.date.today(), "Target Role": "Volunteer"},
        ]),
        "sponsors": pd.DataFrame([
            {"Sponsor ID": "S001", "Name": "Mega Corp", "Contact Person": "John Doe", "Contact Email": "john.doe@megacorp.com", "Contribution Amount": 100000, "Tier": "Platinum", "Date Added": datetime.date.today()}
        ])
    }

# Attempt to initialize Google Sheets client
try:
    if "google_sheets" in st.secrets and "service_account_key" in st.secrets.google_sheets:
        _creds_json = json.loads(st.secrets.google_sheets.service_account_key)
        _scope = ['https://sheets.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'] # Adjusted scope for gspread
        
        _creds = ServiceAccountCredentials.from_json_keyfile_dict(_creds_json, _scope)
        _client = gspread.authorize(_creds)
        _spreadsheet_name_global = st.secrets.google_sheets.spreadsheet_name
        _spreadsheet = _client.open(_spreadsheet_name_global)
        _gspread_enabled = True
        st.success("Google Sheets integration enabled. ✅")
    else:
        st.warning("Google Sheets secrets not found. Running with in-memory data. Please configure `secrets.toml`.")
        _populate_global_mock_data_init() # Initialize mock data if GSheets is disabled
except Exception as e:
    st.error(f"Error initializing Google Sheets: {e}. Running with in-memory data.")
    _gspread_enabled = False
    _populate_global_mock_data_init() # Initialize mock data if GSheets fails

# --- Global Cached Function for Reading Sheets ---
@st.cache_data(ttl=300) # Cache sheet data for 5 minutes
def _read_sheet_data_cached(gspread_is_enabled: bool, spreadsheet_name: str, sheet_name: str) -> pd.DataFrame:
    """
    Helper function to read a sheet with caching. It explicitly takes hashable arguments.
    It uses the global _spreadsheet object and _global_mock_data.
    """
    st.info(f"Loading data for '{sheet_name}' from {'Google Sheets' if gspread_is_enabled else 'in-memory mock'}...")
    
    global _spreadsheet, _gspread_enabled # Declare globals used within this function

    if gspread_is_enabled:
        try:
            if _spreadsheet is None: # Defensive check, should ideally not happen if gspread_is_enabled is True
                raise ValueError("Google Sheets client not initialized for reading, despite being enabled.")
            
            worksheet = _spreadsheet.worksheet(sheet_name)
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
            # Convert specific columns to datetime.date objects where appropriate
            for col in ["Date", "Registration Date", "Due Date", "Date Posted", "Date Added"]:
                if col in df.columns:
                    # Use errors='coerce' to turn unparseable dates into NaT (Not a Time)
                    df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
            return df
        except Exception as e:
            st.error(f"Failed to read sheet '{sheet_name}' from Google Sheets: {e}")
            st.warning("Falling back to in-memory mock data for this operation. Disabling Google Sheets for subsequent operations within this session.")
            _gspread_enabled = False # Propagate failure globally
            st.rerun() # Rerun to re-evaluate based on new _gspread_enabled state
            return _global_mock_data.get(sheet_name, pd.DataFrame(columns=_get_mock_columns(sheet_name))) # Fallback to mock
    else:
        return _global_mock_data.get(sheet_name, pd.DataFrame(columns=_get_mock_columns(sheet_name))) # Return empty DF with correct columns if not found

def _get_mock_columns(sheet_name):
    # Helper to get expected columns for an empty DataFrame in mock mode
    if sheet_name == "users": return ["Username", "Password", "Role", "Name", "Availability"]
    if sheet_name == "events": return ["Event ID", "Name", "Date", "Time", "Location", "Coordinator", "Budget", "Status", "Description"]
    if sheet_name == "registrations": return ["Reg ID", "Participant Username", "Event ID", "Registration Date"]
    if sheet_name == "volunteers": return ["Volunteer Username", "Full Name", "Availability"]
    if sheet_name == "tasks": return ["Task ID", "Event ID", "Description", "Assigned To Volunteer Username", "Due Date", "Status", "Created By"]
    if sheet_name == "announcements": return ["Announcement ID", "Title", "Content", "Author Username", "Date Posted", "Target Role"]
    if sheet_name == "sponsors": return ["Sponsor ID", "Name", "Contact Person", "Contact Email", "Contribution Amount", "Tier", "Date Added"]
    return []

# --- GoogleSheetDB Class (Orchestrator) ---
class GoogleSheetDB:
    """
    A class to manage interactions with Google Sheets as a database.
    This version delegates reading to a globally cached function and
    writes directly to global state/gspread client.
    """
    def __init__(self, spreadsheet_name):
        self._spreadsheet_name = spreadsheet_name

    def read_sheet(self, sheet_name):
        """Reads data from a specified worksheet, using the global cached function."""
        # Pass current global _gspread_enabled and _spreadsheet_name_global to the cached function
        return _read_sheet_data_cached(_gspread_enabled, _spreadsheet_name_global, sheet_name)

    def save_dataframe(self, sheet_name, df):
        """Saves a DataFrame to a worksheet and updates global mock data."""
        global _spreadsheet, _global_mock_data, _gspread_enabled # Declare globals to be used

        if _gspread_enabled:
            try:
                if _spreadsheet is None: # Defensive check
                    raise ValueError("Google Sheets client not initialized for writing.")
                worksheet = _spreadsheet.worksheet(sheet_name)
                worksheet.clear() # Clear existing content
                # Convert datetime.date objects to string for gspread
                df_to_write = df.copy()
                for col in ["Date", "Registration Date", "Due Date", "Date Posted", "Date Added"]:
                    if col in df_to_write.columns:
                        df_to_write[col] = df_to_write[col].astype(str)
                worksheet.update([df_to_write.columns.values.tolist()] + df_to_write.values.tolist())
                st.success(f"Data for '{sheet_name}' written to Google Sheets. 💾")
            except Exception as e:
                st.error(f"Failed to write sheet '{sheet_name}' to Google Sheets: {e}")
                st.warning("Data saved to in-memory mock only. Disabling Google Sheets for this session.")
                _gspread_enabled = False # Propagate failure globally
                st.rerun() # Rerun to re-evaluate based on new _gspread_enabled state
        
        _global_mock_data[sheet_name] = df # Update mock data regardless of gspread status
        st.cache_data.clear() # Clear cache for all sheets after a write (important!)
        # st.rerun() # Re-run app to reflect changes immediately (careful with too many reruns)

# Initialize Google Sheet DB client
google_db = GoogleSheetDB(
    spreadsheet_name=_spreadsheet_name_global
)


# --- Session State Initialization ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.user_full_name = None
    st.session_state.current_page = "Home"

# Load initial data from Google Sheets (or mock data) into session state
if "users_df" not in st.session_state:
    st.session_state.users_df = google_db.read_sheet("users")
    global USERS 
    if "Username" in st.session_state.users_df.columns:
        USERS = st.session_state.users_df.set_index("Username").to_dict(orient="index")
    else:
        USERS = {}

if "events_df" not in st.session_state:
    st.session_state.events_df = google_db.read_sheet("events")

if "registrations_df" not in st.session_state:
    st.session_state.registrations_df = google_db.read_sheet("registrations")

if "volunteers_df" not in st.session_state:
    st.session_state.volunteers_df = google_db.read_sheet("volunteers")

if "tasks_df" not in st.session_state:
    st.session_state.tasks_df = google_db.read_sheet("tasks")

if "announcements_df" not in st.session_state:
    st.session_state.announcements_df = google_db.read_sheet("announcements")

if "sponsors_df" not in st.session_state:
    st.session_state.sponsors_df = google_db.read_sheet("sponsors")


# --- Role-based Page Mapping ---
ROLE_PAGES = {
    "Admin": ["Home", "Announcements", "Dashboard", "User Management", "Event Management", "Sponsor Management", "Budget Overview", "Reports"],
    "Coordinator": ["Home", "Announcements", "My Events", "Event Task Management", "Volunteer Assignment", "Event Budget Tracking", "Communication Hub"],
    "Participant": ["Home", "Announcements", "View Event Details", "Register for Events", "My Registrations"],
    "Volunteer": ["Home", "Announcements", "My Tasks", "Update Availability"],
    "Public": ["Home", "View Event Details", "Announcements"]
}


# --- Email Helper Function ---
def send_email(recipient_email, subject, body):
    """
    Sends an email notification.
    Requires SMTP configuration in .streamlit/secrets.toml.
    """
    if "smtp" not in st.secrets:
        st.warning(f"Email configuration not found in secrets. Email to '{recipient_email}' not sent.")
        print(f"--- MOCK EMAIL TO: {recipient_email} ---\nSubject: {subject}\n\n{body}\n--- END MOCK EMAIL ---")
        return
    
    sender_email = st.secrets.smtp.email_sender
    sender_password = st.secrets.smtp.email_password
    smtp_server = st.secrets.smtp.smtp_server
    smtp_port = st.secrets.smtp.smtp_port
    enable_tls = st.secrets.smtp.enable_tls

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = recipient_email

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if enable_tls:
                server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        st.success(f'Email notification "{subject}" sent to {recipient_email}. 📧') 
        print(f"--- EMAIL SENT TO: {recipient_email} ---\nSubject: {subject}\n\n{body}\n--- END EMAIL ---") 
    except Exception as e:
        st.error(f"Failed to send email to {recipient_email}: {e}")
        st.warning(f"Email notification '{subject}' failed for {recipient_email}. 📧 (See console for details)")
        print(f"--- FAILED EMAIL TO: {recipient_email} ---\nSubject: {subject}\nError: {e}\n\n{body}\n--- END FAILED EMAIL ---")


# --- Helper Functions ---
def logout():
    """Logs the user out by resetting session state variables."""
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.user_full_name = None
    st.session_state.current_page = "Home"
    st.success("You have been logged out. 👋")
    st.rerun()

def login(username, password):
    """Authenticates the user and sets session state."""
    if username in USERS and USERS[username]["Password"] == password:
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.role = USERS[username]["Role"]
        st.session_state.user_full_name = USERS[username]["Name"]
        
        accessible_pages_for_role = ROLE_PAGES.get(st.session_state.role, ["Home"])
        st.session_state.current_page = accessible_pages_for_role[0] if accessible_pages_for_role else "Home"
        
        st.success(f"Welcome, {st.session_state.user_full_name} ({st.session_state.role})! 🎉")
        st.rerun()
    else:
        st.error("Invalid username or password 🚫")

# --- Page Content Functions ---

def home_page():
    """Displays the general home page."""
    st.title("🏛️ Inter-College Festive Event ERP")
    st.markdown("---")
    st.write("This system helps manage all aspects of our annual inter-college festive events, from planning and budgeting to registration and volunteer coordination.")
    st.image("https://images.pexels.com/photos/357335/pexels-photo-357335.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1", caption="Festive Event", use_column_width=True)
    st.markdown("---")
    if not st.session_state.logged_in:
        st.info("Please log in using the sidebar to access specific functionalities based on your role.")
        st.markdown("Try logging in with: `admin`/`admin`, `coord1`/`coord`, `part1`/`part`, `volun1`/`volun`")
    else:
        st.info(f"You are logged in as **{st.session_state.user_full_name}** ({st.session_state.role}). Use the sidebar for navigation.")

def show_announcements():
    """Displays announcements visible to the current user's role."""
    st.title("📢 Announcements")
    st.markdown("---")
    st.write("Stay updated with the latest news and important messages.")

    current_role = st.session_state.role if st.session_state.logged_in else "Public"

    relevant_announcements = st.session_state.announcements_df[
        (st.session_state.announcements_df["Target Role"] == "All") |
        (st.session_state.announcements_df["Target Role"] == current_role)
    ].sort_values("Date Posted", ascending=False)

    if relevant_announcements.empty:
        st.info("No announcements available at the moment.")
    else:
        for idx, row in relevant_announcements.iterrows():
            with st.expander(f"**{row['Title']}** - _Posted by {row['Author Username']} on {row['Date Posted']}_"):
                st.write(row["Content"])
                st.markdown(f"**Target Audience:** {row['Target Role']}")
            st.markdown("---")

    if st.session_state.role in ["Admin", "Coordinator"]:
        st.subheader("Create New Announcement 📝")
        with st.expander("Expand to Create New Announcement"):
            with st.form("new_announcement_form"):
                announcement_title = st.text_input("Title")
                announcement_content = st.text_area("Content")
                target_role_options = ["All", "Admin", "Coordinator", "Participant", "Volunteer"]
                if st.session_state.role == "Coordinator":
                    target_role_options = ["All", "Coordinator", "Participant", "Volunteer"]
                announcement_target = st.selectbox("Target Audience", options=target_role_options)
                
                submit_announcement = st.form_submit_button("Publish Announcement")

                if submit_announcement:
                    if announcement_title and announcement_content:
                        new_announcement_id = f"A{len(st.session_state.announcements_df) + 1:03d}"
                        new_entry = {
                            "Announcement ID": new_announcement_id,
                            "Title": announcement_title,
                            "Content": announcement_content,
                            "Author Username": st.session_state.username,
                            "Date Posted": datetime.date.today(),
                            "Target Role": announcement_target
                        }
                        st.session_state.announcements_df = pd.concat([st.session_state.announcements_df, pd.DataFrame([new_entry])], ignore_index=True)
                        google_db.save_dataframe("announcements", st.session_state.announcements_df)
                        st.success("Announcement published successfully! 🚀")
                        st.rerun()
                    else:
                        st.error("Please fill in both title and content for the announcement.")

def show_admin_dashboard():
    """Admin Dashboard: Overview of events, participants, and budget."""
    st.title("📊 Admin Dashboard")
    st.markdown("---")
    st.write(f"Welcome, {st.session_state.user_full_name}! Here's a quick overview of the system.")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Events", st.session_state.events_df.shape[0])
    with col2:
        st.metric("Total Participants", st.session_state.registrations_df["Participant Username"].nunique())
    with col3:
        st.metric("Total Volunteers", st.session_state.volunteers_df.shape[0])
    with col4:
        st.metric("Total Budget Allocated", f"₹{st.session_state.events_df['Budget'].sum():,.2f}")

    st.subheader("Upcoming Events 🗓️")
    upcoming = st.session_state.events_df[st.session_state.events_df["Status"] == "Upcoming"].sort_values("Date")
    if upcoming.empty:
        st.info("No upcoming events.")
    else:
        st.dataframe(upcoming.head(5), use_container_width=True)

    st.subheader("Recent Registrations 🧑‍🤝‍🧑")
    recent_regs = st.session_state.registrations_df.sort_values("Registration Date", ascending=False).head(5)
    if recent_regs.empty:
        st.info("No recent registrations.")
    else:
        st.dataframe(recent_regs, use_container_width=True)

    st.subheader("Recent Announcements 📣")
    recent_announcements = st.session_state.announcements_df.sort_values("Date Posted", ascending=False).head(3)
    if recent_announcements.empty:
        st.info("No recent announcements.")
    else:
        for idx, row in recent_announcements.iterrows():
            with st.expander(f"**{row['Title']}** - _Posted by {row['Author Username']} on {row['Date Posted']}_"):
                st.write(row["Content"])

def show_user_management():
    """Admin User Management: Add/view/edit users."""
    global USERS 
    st.title("👤 User Management")
    st.markdown("---")
    st.write("Manage system users, their roles, and basic profiles.")

    st.subheader("Existing System Users")
    
    if st.session_state.users_df.empty:
        st.info("No users in the system.")
    else:
        editable_users_df = st.data_editor(
            st.session_state.users_df.drop(columns=["Password"]),
            key="users_editor", 
            use_container_width=True,
            column_config={
                "Role": st.column_config.SelectboxColumn(options=["Admin", "Coordinator", "Participant", "Volunteer"]),
                "Availability": st.column_config.SelectboxColumn(options=["Available", "Busy", "On Leave", "N/A"])
            }
        )
        if not editable_users_df.equals(st.session_state.users_df.drop(columns=["Password"])):
            temp_users_df = st.session_state.users_df.copy()
            for col in editable_users_df.columns:
                if col in temp_users_df.columns:
                    temp_users_df[col] = editable_users_df[col]
            st.session_state.users_df = temp_users_df
            google_db.save_dataframe("users", st.session_state.users_df)
            USERS = st.session_state.users_df.set_index("Username").to_dict(orient="index")
            st.success("User details updated successfully! ✅")
            st.rerun()

    st.subheader("Add New User ➕")
    with st.expander("Expand to Add New User"):
        with st.form("add_user_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_username = st.text_input("New Username (unique)")
                new_password = st.text_input("Password", type="password")
            with col2:
                new_name = st.text_input("Full Name")
                new_role = st.selectbox("Role", options=["Admin", "Coordinator", "Participant", "Volunteer"])
            
            submit_button = st.form_submit_button("Add User")

            if submit_button:
                if new_username in st.session_state.users_df["Username"].values:
                    st.error("Username already exists! Please choose a different one.")
                elif not new_username or not new_password or not new_name:
                    st.error("Please fill in all required fields.")
                else:
                    new_user_entry = {
                        "Username": new_username, 
                        "Password": new_password,
                        "Role": new_role, 
                        "Name": new_name,
                        "Availability": "Available" if new_role == "Volunteer" else "N/A"
                    }
                    st.session_state.users_df = pd.concat([st.session_state.users_df, pd.DataFrame([new_user_entry])], ignore_index=True)
                    google_db.save_dataframe("users", st.session_state.users_df)

                    if new_role == "Volunteer":
                        new_volunteer_profile = {
                            "Volunteer Username": new_username,
                            "Full Name": new_name,
                            "Availability": "Available"
                        }
                        st.session_state.volunteers_df = pd.concat([st.session_state.volunteers_df, pd.DataFrame([new_volunteer_profile])], ignore_index=True)
                        google_db.save_dataframe("volunteers", st.session_state.volunteers_df)

                    USERS = st.session_state.users_df.set_index("Username").to_dict(orient="index")
                    st.success(f"User '{new_username}' added with role '{new_role}'. ✅")
                    st.rerun() 

def show_event_management():
    """Admin Event Management: Create, view, and edit events."""
    st.title("📅 Event Management")
    st.markdown("---")
    st.write("Create, view, and manage all festive events.")

    tab1, tab2 = st.tabs(["View All Events", "Create New Event"])

    with tab1:
        st.subheader("All Events 📋")
        if st.session_state.events_df.empty:
            st.info("No events created yet.")
        else:
            editable_events_df = st.data_editor(
                st.session_state.events_df, 
                key="events_editor", 
                use_container_width=True,
                column_config={
                    "Description": st.column_config.Column(width="medium"),
                    "Budget": st.column_config.NumberColumn(format="₹%,.2f"),
                    "Date": st.column_config.DateColumn(format="YYYY/MM/DD"),
                    "Status": st.column_config.SelectboxColumn(options=["Upcoming", "Ongoing", "Completed", "Cancelled"])
                }
            )
            if not editable_events_df.equals(st.session_state.events_df):
                st.session_state.events_df = editable_events_df
                google_db.save_dataframe("events", st.session_state.events_df)
                st.success("Events updated successfully! ✅")
                st.rerun()

    with tab2:
        st.subheader("Create New Event ✨")
        with st.form("new_event_form"):
            col1, col2 = st.columns(2)
            with col1:
                event_id = st.text_input("Event ID (e.g., E004)", help="Must be unique")
                name = st.text_input("Event Name")
                date = st.date_input("Date", datetime.date.today())
                time = st.text_input("Time (e.g., 10:00 AM)")
            with col2:
                location = st.text_input("Location")
                coordinator_names = st.session_state.users_df[st.session_state.users_df["Role"] == "Coordinator"]["Name"].tolist()
                coordinator_options = [""] + coordinator_names
                coordinator = st.selectbox("Coordinator", options=coordinator_options)
                budget = st.number_input("Budget", min_value=0, value=10000, step=1000)
                status = st.selectbox("Status", options=["Upcoming", "Ongoing", "Completed", "Cancelled"])
            
            description = st.text_area("Event Description", height=100)
            
            submit_event = st.form_submit_button("Add Event")

            if submit_event:
                if event_id in st.session_state.events_df["Event ID"].values:
                    st.error("Event ID already exists! Please choose a unique ID.")
                elif not event_id or not name or not location or not coordinator:
                    st.error("Please fill in all required fields (Event ID, Name, Location, Coordinator).")
                else:
                    new_event = {
                        "Event ID": event_id,
                        "Name": name,
                        "Date": date,
                        "Time": time,
                        "Location": location,
                        "Coordinator": coordinator,
                        "Budget": budget,
                        "Status": status,
                        "Description": description
                    }
                    st.session_state.events_df = pd.concat([st.session_state.events_df, pd.DataFrame([new_event])], ignore_index=True)
                    google_db.save_dataframe("events", st.session_state.events_df)
                    st.success(f"Event '{name}' added successfully! 🎉")
                    st.rerun()

def show_sponsor_management():
    """Admin Sponsor Management: Add, view, and edit sponsors."""
    st.title("🤝 Sponsor Management")
    st.markdown("---")
    st.write("Manage event sponsors, their contact information, and contributions.")

    tab1, tab2 = st.tabs(["View All Sponsors", "Add New Sponsor"])

    with tab1:
        st.subheader("All Sponsors 💰")
        if st.session_state.sponsors_df.empty:
            st.info("No sponsors added yet.")
        else:
            editable_sponsors_df = st.data_editor(
                st.session_state.sponsors_df, 
                key="sponsors_editor", 
                use_container_width=True,
                column_config={
                    "Contribution Amount": st.column_config.NumberColumn(format="₹%,.2f"),
                    "Date Added": st.column_config.DateColumn(format="YYYY/MM/DD"),
                    "Tier": st.column_config.SelectboxColumn(options=["Bronze", "Silver", "Gold", "Platinum"])
                }
            )
            if not editable_sponsors_df.equals(st.session_state.sponsors_df):
                st.session_state.sponsors_df = editable_sponsors_df
                google_db.save_dataframe("sponsors", st.session_state.sponsors_df)
                st.success("Sponsor details updated successfully! ✅")
                st.rerun()

    with tab2:
        st.subheader("Add New Sponsor 🌟")
        with st.form("new_sponsor_form"):
            col1, col2 = st.columns(2)
            with col1:
                sponsor_id = st.text_input("Sponsor ID (e.g., S002)", help="Must be unique")
                name = st.text_input("Sponsor Name")
                contact_person = st.text_input("Contact Person")
            with col2:
                contact_email = st.text_input("Contact Email")
                contribution_amount = st.number_input("Contribution Amount", min_value=0, value=0, step=1000)
                tier = st.selectbox("Sponsor Tier", options=["Bronze", "Silver", "Gold", "Platinum"])
            
            submit_sponsor = st.form_submit_button("Add Sponsor")

            if submit_sponsor:
                if sponsor_id in st.session_state.sponsors_df["Sponsor ID"].values:
                    st.error("Sponsor ID already exists! Please choose a unique ID.")
                elif not sponsor_id or not name or not contact_person or not contact_email:
                    st.error("Please fill in all required fields.")
                else:
                    new_sponsor = {
                        "Sponsor ID": sponsor_id,
                        "Name": name,
                        "Contact Person": contact_person,
                        "Contact Email": contact_email,
                        "Contribution Amount": contribution_amount,
                        "Tier": tier,
                        "Date Added": datetime.date.today()
                    }
                    st.session_state.sponsors_df = pd.concat([st.session_state.sponsors_df, pd.DataFrame([new_sponsor])], ignore_index=True)
                    google_db.save_dataframe("sponsors", st.session_state.sponsors_df)
                    st.success(f"Sponsor '{name}' added successfully! 🎉")
                    st.rerun()

def show_budget_overview():
    """Admin Budget Overview: Monitor overall budget and expenses."""
    st.title("💰 Budget Overview")
    st.markdown("---")
    st.write("Monitor budget allocations and expenses across all events.")

    total_allocated_budget = st.session_state.events_df["Budget"].sum()
    total_sponsor_contributions = st.session_state.sponsors_df["Contribution Amount"].sum() if not st.session_state.sponsors_df.empty else 0

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Allocated Event Budget", f"₹{total_allocated_budget:,.2f}")
    with col2:
        st.metric("Total Sponsor Contributions", f"₹{total_sponsor_contributions:,.2f}")

    st.subheader("Event-wise Budget Allocation 📊")
    if st.session_state.events_df.empty:
        st.info("No events with budget data.")
    else:
        st.dataframe(st.session_state.events_df[["Event ID", "Name", "Budget", "Status"]], use_container_width=True)
        st.bar_chart(st.session_state.events_df.set_index("Name")["Budget"])

    st.subheader("Overall Expenses (Dummy Data) 📉")
    st.warning("This section uses dummy expense data. In a real ERP, integrate with actual financial tracking.")
    expenses_data = {
        "Category": ["Marketing", "Venue Rental", "Artist Fees", "Equipment", "Food"],
        "Amount": [15000, 20000, 30000, 10000, 12000],
        "Event ID": ["E001", "E002", "E001", "E003", "E002"]
    }
    expenses = pd.DataFrame(expenses_data)
    st.dataframe(expenses, use_container_width=True)
    
    total_expenses_dummy = expenses["Amount"].sum()
    st.metric("Total Expenses Recorded (Dummy)", f"₹{total_expenses_dummy:,.2f}")
    st.metric("Estimated Overall Balance", f"₹{total_allocated_budget + total_sponsor_contributions - total_expenses_dummy:,.2f}")


def show_reports():
    """Admin Reports: Generate various analytical reports."""
    st.title("📈 Reports")
    st.markdown("---")
    st.write("Generate various analytical reports for better event insights.")

    report_type = st.selectbox("Select Report Type", ["Event Participation", "Budget vs Actual", "Volunteer Engagement", "Sponsor Contribution"])

    if report_type == "Event Participation":
        st.subheader("Event Participation Report 🧑‍🤝‍🧑")
        if st.session_state.registrations_df.empty:
            st.info("No registrations to report on.")
        else:
            participation_counts = st.session_state.registrations_df.groupby("Event ID").size().reset_index(name="Participants")
            participation_merged = pd.merge(participation_counts, st.session_state.events_df[["Event ID", "Name"]], on="Event ID", how="left")
            st.dataframe(participation_merged.sort_values("Participants", ascending=False), use_container_width=True)
            st.bar_chart(participation_merged.set_index("Name")["Participants"])

    elif report_type == "Budget vs Actual":
        st.subheader("Budget vs Actual Expenses Report 💸")
        st.warning("This report currently uses dummy expense data. Integrate with actual expense tracking for real data.")
        expenses_data = {
            "Category": ["Marketing", "Venue Rental", "Artist Fees", "Equipment", "Food"],
            "Amount": [15000, 20000, 30000, 10000, 12000],
            "Event ID": ["E001", "E002", "E001", "E003", "E002"]
        }
        expenses = pd.DataFrame(expenses_data)
        event_expenses = expenses.groupby("Event ID")["Amount"].sum().reset_index(name="Actual Expenses")
        budget_vs_actual = pd.merge(st.session_state.events_df[["Event ID", "Name", "Budget"]], event_expenses, on="Event ID", how="left").fillna(0)
        budget_vs_actual["Variance"] = budget_vs_actual["Budget"] - budget_vs_actual["Actual Expenses"]
        st.dataframe(budget_vs_actual, use_container_width=True)
        st.bar_chart(budget_vs_actual.set_index("Name")[["Budget", "Actual Expenses"]])

    elif report_type == "Volunteer Engagement":
        st.subheader("Volunteer Engagement Report 💪")
        if st.session_state.tasks_df.empty:
            st.info("No volunteer tasks assigned to report on.")
        else:
            volunteer_tasks_counts = st.session_state.tasks_df.groupby("Assigned To Volunteer Username").size().reset_index(name="Assigned Tasks")
            volunteer_tasks_merged = pd.merge(volunteer_tasks_counts, st.session_state.volunteers_df[["Volunteer Username", "Full Name"]], on="Volunteer Username", how="left")
            st.dataframe(volunteer_tasks_merged, use_container_width=True)
            st.bar_chart(volunteer_tasks_merged.set_index("Full Name")["Assigned Tasks"])
    
    elif report_type == "Sponsor Contribution":
        st.subheader("Sponsor Contribution Report 🌟")
        if st.session_state.sponsors_df.empty:
            st.info("No sponsors to report on.")
        else:
            st.dataframe(st.session_state.sponsors_df[["Name", "Tier", "Contribution Amount", "Contact Person"]], use_container_width=True)
            st.bar_chart(st.session_state.sponsors_df.set_index("Name")["Contribution Amount"])


def show_my_events():
    """Coordinator: View and manage events assigned to them."""
    st.title("My Events 🗓️")
    st.markdown("---")
    st.write(f"Events you are coordinating, {st.session_state.user_full_name}.")
    
    my_events = st.session_state.events_df[st.session_state.events_df["Coordinator"] == st.session_state.user_full_name]
    if my_events.empty:
        st.info("You are not currently assigned to coordinate any events.")
    else:
        st.dataframe(my_events[["Event ID", "Name", "Date", "Location", "Status"]], use_container_width=True)

        st.subheader("Update Event Status 🔄")
        with st.expander("Update Status for an Event"):
            event_to_update_id = st.selectbox("Select Event to Update", 
                                              options=my_events["Event ID"].tolist(), 
                                              format_func=lambda x: my_events[my_events["Event ID"] == x]["Name"].iloc[0] if not my_events.empty else x,
                                              key="update_my_event_status_select")
            
            if event_to_update_id:
                current_status = st.session_state.events_df[st.session_state.events_df["Event ID"] == event_to_update_id]["Status"].iloc[0]
                new_status = st.selectbox("New Status", 
                                          options=["Upcoming", "Ongoing", "Completed", "Cancelled"], 
                                          index=["Upcoming", "Ongoing", "Completed", "Cancelled"].index(current_status), 
                                          key=f"status_select_{event_to_update_id}")
                
                if st.button(f"Update Status for {event_to_update_id}", key=f"update_status_btn_{event_to_update_id}"):
                    idx = st.session_state.events_df[st.session_state.events_df["Event ID"] == event_to_update_id].index
                    st.session_state.events_df.loc[idx, "Status"] = new_status
                    google_db.save_dataframe("events", st.session_state.events_df)
                    st.success(f"Status for {event_to_update_id} updated to {new_status}. ✅")
                    st.rerun()

def show_event_task_management():
    """Coordinator: Define and manage tasks for their events."""
    st.title("✅ Event Task Management")
    st.markdown("---")
    st.write(f"Manage tasks for events you coordinate, {st.session_state.user_full_name}.")

    my_events_df = st.session_state.events_df[st.session_state.events_df["Coordinator"] == st.session_state.user_full_name]

    if my_events_df.empty:
        st.info("You are not coordinating any events to manage tasks for.")
        return

    selected_event_id = st.selectbox("Select Event", 
                                      options=my_events_df["Event ID"].tolist(),
                                      format_func=lambda x: my_events_df[my_events_df["Event ID"] == x]["Name"].iloc[0] if not my_events_df.empty else x,
                                      key="select_event_for_task_management")

    if selected_event_id:
        event_name = my_events_df[my_events_df["Event ID"] == selected_event_id]["Name"].iloc[0]
        st.subheader(f"Tasks for: {event_name} ({selected_event_id}) 📝")

        current_event_tasks = st.session_state.tasks_df[st.session_state.tasks_df["Event ID"] == selected_event_id]
        
        if current_event_tasks.empty:
            st.info("No tasks defined for this event yet.")
        else:
            editable_tasks_df = st.data_editor(
                current_event_tasks, 
                key=f"tasks_editor_{selected_event_id}", 
                use_container_width=True,
                column_config={
                    "Due Date": st.column_config.DateColumn(format="YYYY/MM/DD"),
                    "Status": st.column_config.SelectboxColumn(options=["Assigned", "Pending", "In Progress", "Completed"])
                }
            )
            if not editable_tasks_df.equals(current_event_tasks):
                st.session_state.tasks_df = editable_tasks_df
                google_db.save_dataframe("tasks", st.session_state.tasks_df)
                st.success("Tasks updated successfully! ✅")
                st.rerun()

        st.subheader("Add New Task ➕")
        with st.expander(f"Add a new task for {event_name}"):
            with st.form(f"add_task_form_{selected_event_id}"):
                task_description = st.text_input("Task Description")
                volunteer_usernames = st.session_state.users_df[st.session_state.users_df["Role"] == "Volunteer"]["Username"].tolist()
                volunteer_options = [""] + volunteer_usernames
                assigned_to_volunteer = st.selectbox("Assign to Volunteer (Optional)", options=volunteer_options)
                due_date = st.date_input("Due Date", datetime.date.today())
                task_status = st.selectbox("Initial Status", options=["Assigned", "Pending", "In Progress"])

                add_task_button = st.form_submit_button("Add Task")

                if add_task_button:
                    if task_description:
                        new_task_id = f"T{len(st.session_state.tasks_df) + 1:03d}"
                        new_task = {
                            "Task ID": new_task_id,
                            "Event ID": selected_event_id,
                            "Description": task_description,
                            "Assigned To Volunteer Username": assigned_to_volunteer if assigned_to_volunteer else None,
                            "Due Date": due_date,
                            "Status": task_status,
                            "Created By": st.session_state.username
                        }
                        st.session_state.tasks_df = pd.concat([st.session_state.tasks_df, pd.DataFrame([new_task])], ignore_index=True)
                        google_db.save_dataframe("tasks", st.session_state.tasks_df)
                        st.success(f"Task '{task_description}' added to '{event_name}'! ✅")

                        if assigned_to_volunteer:
                            volunteer_email_row = st.session_state.users_df[st.session_state.users_df["Username"] == assigned_to_volunteer]
                            if not volunteer_email_row.empty:
                                dummy_volunteer_email = f"{assigned_to_volunteer}@example.com" 
                                email_subject = f"New Task Assignment for {event_name}"
                                email_body = f"Hello {USERS[assigned_to_volunteer]['Name']},\n\nYou have been assigned a new task for '{event_name}':\n\nTask: {task_description}\nDue Date: {due_date}\n\nPlease check the ERP system for more details.\n\nRegards,\n{st.session_state.user_full_name} (Coordinator)"
                                send_email(dummy_volunteer_email, email_subject, email_body)
                        st.rerun()
                    else:
                        st.error("Task description cannot be empty.")

def show_volunteer_assignment():
    """Coordinator: Assign volunteers to tasks within their events."""
    st.title("👥 Volunteer Assignment")
    st.markdown("---")
    st.write(f"Assign volunteers to tasks for events you coordinate, {st.session_state.user_full_name}.")

    my_events_df = st.session_state.events_df[st.session_state.events_df["Coordinator"] == st.session_state.user_full_name]

    if my_events_df.empty:
        st.info("You are not coordinating any events to assign volunteers to.")
        return

    selected_event_id = st.selectbox("Select Event", options=my_events_df["Event ID"].tolist(),
                                      format_func=lambda x: my_events_df[my_events_df["Event ID"] == x]["Name"].iloc[0] if not my_events_df.empty else x,
                                      key="select_event_for_volunteer_assignment")

    if selected_event_id:
        st.subheader(f"Volunteers and Tasks for {my_events_df[my_events_df['Event ID'] == selected_event_id]['Name'].iloc[0]}")
        
        current_event_tasks = st.session_state.tasks_df[st.session_state.tasks_df["Event ID"] == selected_event_id]
        
        if current_event_tasks.empty:
            st.info("No tasks defined for this event yet. Please create tasks in 'Event Task Management' first.")
        else:
            display_tasks = pd.merge(current_event_tasks, st.session_state.volunteers_df[["Volunteer Username", "Full Name", "Availability"]],
                                     left_on="Assigned To Volunteer Username", right_on="Volunteer Username", how="left").fillna({"Full Name": "Unassigned", "Availability": "N/A"})
            st.dataframe(display_tasks[["Description", "Full Name", "Availability", "Status", "Due Date"]], use_container_width=True)

            st.subheader("Assign/Reassign Task to Volunteer ✏️")
            with st.expander("Assign/Reassign Task"):
                with st.form(f"assign_task_form_{selected_event_id}"):
                    task_options = [""] + current_event_tasks["Description"].tolist()
                    selected_task_description = st.selectbox("Select Task", options=task_options)
                    
                    available_volunteers_df = st.session_state.volunteers_df[st.session_state.volunteers_df["Availability"] == "Available"]
                    volunteer_options = [""] + available_volunteers_df["Volunteer Username"].tolist()
                    
                    assigned_volunteer = st.selectbox("Assign To (Available Volunteers)", options=volunteer_options, help="Only 'Available' volunteers are shown.")
                    
                    assign_button = st.form_submit_button("Assign/Update Assignment")

                    if assign_button:
                        if selected_task_description:
                            task_idx = st.session_state.tasks_df[
                                (st.session_state.tasks_df["Event ID"] == selected_event_id) &
                                (st.session_state.tasks_df["Description"] == selected_task_description)
                            ].index
                            
                            if not task_idx.empty:
                                old_assigned_volunteer = st.session_state.tasks_df.loc[task_idx, "Assigned To Volunteer Username"].iloc[0]
                                
                                if assigned_volunteer:
                                    st.session_state.tasks_df.loc[task_idx, "Assigned To Volunteer Username"] = assigned_volunteer
                                    st.session_state.tasks_df.loc[task_idx, "Status"] = "Assigned"
                                    google_db.save_dataframe("tasks", st.session_state.tasks_df)
                                    st.success(f"Task '{selected_task_description}' assigned to '{assigned_volunteer}'. ✅")
                                    
                                    volunteer_user_row = st.session_state.users_df[st.session_state.users_df["Username"] == assigned_volunteer]
                                    if not volunteer_user_row.empty:
                                        dummy_volunteer_email = f"{assigned_volunteer}@example.com"
                                        email_subject = f"Your Task Assignment for {my_events_df[my_events_df['Event ID'] == selected_event_id]['Name'].iloc[0]}"
                                        email_body = f"Hello {USERS[assigned_volunteer]['Name']},\n\nYou have been assigned a task for '{my_events_df[my_events_df['Event ID'] == selected_event_id]['Name'].iloc[0]}':\n\nTask: {selected_task_description}\nDue Date: {st.session_state.tasks_df.loc[task_idx, 'Due Date'].iloc[0]}\n\nPlease check the ERP system for more details.\n\nRegards,\n{st.session_state.user_full_name} (Coordinator)"
                                        send_email(dummy_volunteer_email, email_subject, email_body)
                                else:
                                    st.session_state.tasks_df.loc[task_idx, "Assigned To Volunteer Username"] = None
                                    st.session_state.tasks_df.loc[task_idx, "Status"] = "Pending"
                                    google_db.save_dataframe("tasks", st.session_state.tasks_df)
                                    st.info(f"Task '{selected_task_description}' unassigned. It is now 'Pending'.")

                                st.rerun()
                            else:
                                st.error("Selected task not found.")
                        else:
                            st.error("Please select a task.")

def show_event_budget_tracking():
    """Coordinator: Track budget and expenses for their assigned events."""
    st.title("💸 Event Budget Tracking")
    st.markdown("---")
    st.write(f"Track the budget for events you coordinate, {st.session_state.user_full_name}.")

    my_events_df = st.session_state.events_df[st.session_state.events_df["Coordinator"] == st.session_state.user_full_name]
    
    if my_events_df.empty:
        st.info("You are not coordinating any events to track budget for.")
        return

    selected_event_id = st.selectbox("Select Event", options=my_events_df["Event ID"].tolist(),
                                      format_func=lambda x: my_events_df[my_events_df["Event ID"] == x]["Name"].iloc[0],
                                      key="budget_tracking_event_select")

    if selected_event_id:
        event_info = my_events_df[my_events_df["Event ID"] == selected_event_id].iloc[0]
        st.subheader(f"Budget for {event_info['Name']} ({selected_event_id})")
        st.metric("Allocated Budget", f"₹{event_info['Budget']:,.2f}")

        st.subheader("Recorded Expenses (Dummy Data) 📉")
        st.warning("This is dummy expense data. In a real system, you would integrate actual expense recording.")
        
        expenses_data_all = {
            "Expense ID": ["EXP001", "EXP002", "EXP003", "EXP004", "EXP005"],
            "Category": ["Decorations", "Venue Rental", "Artist Fees", "Equipment", "Food"],
            "Amount": [10000, 20000, 30000, 10000, 12000],
            "Date": [datetime.date(2025, 10, 10), datetime.date(2025, 11, 15), datetime.date(2025, 10, 12), datetime.date(2025, 12, 1), datetime.date(2025, 11, 18)],
            "Event ID": ["E001", "E002", "E001", "E003", "E002"]
        }
        all_expenses_df = pd.DataFrame(expenses_data_all)
        event_expenses_for_display = all_expenses_df[all_expenses_df["Event ID"] == selected_event_id]

        if event_expenses_for_display.empty:
            st.info("No expenses recorded for this event yet (dummy data).")
        else:
            st.dataframe(event_expenses_for_display[["Expense ID", "Category", "Amount", "Date"]], use_container_width=True)

        total_expenses = event_expenses_for_display["Amount"].sum() if not event_expenses_for_display.empty else 0
        st.metric("Total Expenses Recorded (Dummy)", f"₹{total_expenses:,.2f}")
        st.metric("Remaining Budget", f"₹{event_info['Budget'] - total_expenses:,.2f}")

        st.subheader("Add New Expense (Dummy Entry) ➕")
        with st.expander("Add a new dummy expense"):
            with st.form(f"add_expense_form_{selected_event_id}"):
                expense_category = st.text_input("Expense Category")
                expense_amount = st.number_input("Amount", min_value=0.0, value=0.0, step=100.0)
                expense_date = st.date_input("Date", datetime.date.today())
                add_expense_button = st.form_submit_button("Add Expense (Dummy)")
                if add_expense_button:
                    if expense_category and expense_amount > 0:
                        st.info(f"Dummy Expense Added: Event '{event_info['Name']}' - {expense_category} - ₹{expense_amount} on {expense_date}. (This entry is not saved persistently.)")
                    else:
                        st.error("Please provide a category and a positive amount for the dummy expense.")

def show_communication_hub():
    """Coordinator: View general announcements and potentially send event-specific communications."""
    st.title("🗣️ Communication Hub")
    st.markdown("---")
    st.write(f"Manage communications for your events, {st.session_state.user_full_name}.")

    st.subheader("Relevant Announcements")
    coordinator_relevant_announcements = st.session_state.announcements_df[
        (st.session_state.announcements_df["Target Role"] == "All") |
        (st.session_state.announcements_df["Target Role"] == "Coordinator")
    ].sort_values("Date Posted", ascending=False)
    
    if coordinator_relevant_announcements.empty:
        st.info("No relevant announcements for you.")
    else:
        for idx, row in coordinator_relevant_announcements.iterrows():
            with st.expander(f"**{row['Title']}** - _Posted by {row['Author Username']} on {row['Date Posted']}_"):
                st.write(row["Content"])
                st.markdown(f"**Target Audience:** {row['Target Role']}")
            st.markdown("---")

    st.subheader("Send Event-Specific Message (Simplified) ✉️")
    st.info("This is a simplified message sending feature. In a real system, this would integrate with email/notification services.")
    with st.expander("Send a Message"):
        with st.form("send_message_form"):
            my_events_df = st.session_state.events_df[st.session_state.events_df["Coordinator"] == st.session_state.user_full_name]
            event_options = [""] + my_events_df["Event ID"].tolist()
            target_event_id = st.selectbox("Select Event (Optional, for event-specific message)", options=event_options,
                                           format_func=lambda x: my_events_df[my_events_df["Event ID"] == x]["Name"].iloc[0] if x else "General")
            
            message_subject = st.text_input("Subject")
            message_content = st.text_area("Message Content")
            
            send_button = st.form_submit_button("Send Message (Dummy)")

            if send_button:
                if message_subject and message_content:
                    target_display = f"for Event '{my_events_df[my_events_df['Event ID'] == target_event_id]['Name'].iloc[0]}'" if target_event_id else "General Audience"
                    st.success(f"Dummy Message Sent: Subject '{message_subject}' to {target_display}. (Not persistently saved or sent.)")
                else:
                    st.error("Please provide a subject and content for the message.")

def show_view_event_details():
    """Participant: View detailed information about events."""
    st.title("ℹ️ View Event Details")
    st.markdown("---")
    st.write(f"{'Welcome, ' + st.session_state.user_full_name + '!' if st.session_state.logged_in else 'Welcome!'} Browse details of our upcoming events.")

    st.subheader("All Events")
    
    search_query = st.text_input("Search events by Name or Location", key="event_details_search")
    
    filtered_events = st.session_state.events_df
    if search_query:
        filtered_events = filtered_events[
            filtered_events["Name"].str.contains(search_query, case=False) |
            filtered_events["Location"].str.contains(search_query, case=False)
        ]

    if filtered_events.empty:
        st.info("No events found matching your search criteria.")
    else:
        selected_event_id = st.selectbox("Select an Event to view details", 
                                        options=filtered_events["Event ID"].tolist(),
                                        format_func=lambda x: filtered_events[filtered_events["Event ID"] == x]["Name"].iloc[0] if not filtered_events.empty else x,
                                        key="view_event_details_select")
        
        if selected_event_id:
            event_details = filtered_events[filtered_events["Event ID"] == selected_event_id].iloc[0]
            st.markdown("---")
            st.subheader(f"{event_details['Name']} Details")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Event ID:** `{event_details['Event ID']}`")
                st.write(f"**Date:** `{event_details['Date']}`")
                st.write(f"**Time:** `{event_details['Time']}`")
                st.write(f"**Location:** `{event_details['Location']}`")
            with col2:
                st.write(f"**Coordinator:** `{event_details['Coordinator']}`")
                st.write(f"**Status:** `{event_details['Status']}`")
                if event_details['Budget'] > 0:
                    st.write(f"**Budget:** `₹{event_details['Budget']:,.2f}` (Internal)")
                
            st.markdown("---")
            st.write("**Description:**")
            st.markdown(event_details['Description'])
            
            if st.session_state.logged_in and st.session_state.role == "Participant":
                is_registered = not st.session_state.registrations_df[
                    (st.session_state.registrations_df["Participant Username"] == st.session_state.username) &
                    (st.session_state.registrations_df["Event ID"] == selected_event_id)
                ].empty
                
                if is_registered:
                    st.success("You are already registered for this event! 🎉")
                else:
                    if event_details["Status"] == "Upcoming":
                        st.info(f"You can register for '{event_details['Name']}' on the 'Register for Events' page.")
                    else:
                        st.warning(f"Registration for '{event_details['Name']}' is not currently open (Status: {event_details['Status']}).")
            elif not st.session_state.logged_in:
                st.info("Log in as a Participant to register for events.")


def show_register_for_events():
    """Participant: View available events and register."""
    st.title("📝 Register for Events")
    st.markdown("---")
    st.write(f"Welcome, {st.session_state.user_full_name}! Register for exciting upcoming events.")

    st.subheader("Available Upcoming Events")
    search_query = st.text_input("Search events by Name or Location", key="register_event_search")
    
    upcoming_events = st.session_state.events_df[st.session_state.events_df["Status"] == "Upcoming"]
    
    if search_query:
        upcoming_events = upcoming_events[
            upcoming_events["Name"].str.contains(search_query, case=False) |
            upcoming_events["Location"].str.contains(search_query, case=False)
        ]

    if upcoming_events.empty:
        st.info("No upcoming events available for registration at the moment, or no events match your search.")
        return

    events_for_display = upcoming_events[["Event ID", "Name", "Date", "Time", "Location", "Coordinator"]]
    st.dataframe(events_for_display, use_container_width=True)

    st.subheader("Register for an Event ✨")
    with st.expander("Register for Selected Event"):
        with st.form("event_registration_form"):
            event_to_register_id = st.selectbox("Select Event to Register For", 
                                                options=upcoming_events["Event ID"].tolist(), 
                                                format_func=lambda x: upcoming_events[upcoming_events["Event ID"] == x]["Name"].iloc[0] if not upcoming_events.empty else x,
                                                key="register_event_select")
            
            register_button = st.form_submit_button("Register Now")

            if register_button:
                if event_to_register_id:
                    if not st.session_state.registrations_df[
                        (st.session_state.registrations_df["Participant Username"] == st.session_state.username) &
                        (st.session_state.registrations_df["Event ID"] == event_to_register_id)
                    ].empty:
                        st.warning("You are already registered for this event. No need to register again! 🔔")
                    else:
                        new_reg_id = f"R{len(st.session_state.registrations_df) + 1:03d}"
                        new_registration = {
                            "Reg ID": new_reg_id,
                            "Participant Username": st.session_state.username,
                            "Event ID": event_to_register_id,
                            "Registration Date": datetime.date.today()
                        }
                        st.session_state.registrations_df = pd.concat([st.session_state.registrations_df, pd.DataFrame([new_registration])], ignore_index=True)
                        google_db.save_dataframe("registrations", st.session_state.registrations_df)
                        event_name = upcoming_events[upcoming_events['Event ID'] == event_to_register_id]['Name'].iloc[0]
                        st.success(f"Successfully registered for event '{event_name}'! 🎉")

                        participant_email_row = st.session_state.users_df[st.session_state.users_df["Username"] == st.session_state.username]
                        if not participant_email_row.empty:
                            dummy_participant_email = f"{st.session_state.username}@example.com"
                            email_subject = f"Registration Confirmation for {event_name}"
                            email_body = f"Hello {st.session_state.user_full_name},\n\nThis is to confirm your registration for '{event_name}'.\n\nEvent Date: {upcoming_events[upcoming_events['Event ID'] == event_to_register_id]['Date'].iloc[0]}\nEvent Location: {upcoming_events[upcoming_events['Event ID'] == event_to_register_id]['Location'].iloc[0]}\n\nWe look forward to seeing you there!\n\nRegards,\nFestive Event Team"
                            send_email(dummy_participant_email, email_subject, email_body)
                        st.rerun()
                else:
                    st.error("Please select an event to register.")

def show_my_registrations():
    """Participant: View events they have registered for and allow cancellation."""
    st.title("My Registrations 📋")
    st.markdown("---")
    st.write(f"Events you have registered for, {st.session_state.user_full_name}.")

    my_regs = st.session_state.registrations_df[st.session_state.registrations_df["Participant Username"] == st.session_state.username]
    
    if my_regs.empty:
        st.info("You haven't registered for any events yet.")
        return

    display_regs = pd.merge(my_regs, st.session_state.events_df[["Event ID", "Name", "Date", "Location", "Status"]], on="Event ID", how="left")
    st.subheader("Your Registered Events")
    st.dataframe(display_regs[["Name", "Date", "Location", "Status", "Registration Date"]], use_container_width=True)

    st.subheader("Cancel Registration ❌")
    with st.expander("Cancel an Event Registration"):
        events_for_cancellation = display_regs[display_regs["Status"] == "Upcoming"]
        if events_for_cancellation.empty:
            st.info("No upcoming events to cancel registration for.")
        else:
            event_to_cancel_id = st.selectbox("Select Event to Cancel Registration For", 
                                            options=events_for_cancellation["Event ID"].tolist(), 
                                            format_func=lambda x: events_for_cancellation[events_for_cancellation["Event ID"] == x]["Name"].iloc[0],
                                            key="cancel_registration_select")
            
            if event_to_cancel_id:
                st.warning(f"Are you sure you want to cancel your registration for '{events_for_cancellation[events_for_cancellation['Event ID'] == event_to_cancel_id]['Name'].iloc[0]}'?")
                col_y, col_n = st.columns(2)
                with col_y:
                    confirm_cancel = st.button("Yes, Cancel Registration", key="confirm_cancel_btn")
                with col_n:
                    st.button("No, Keep Registration", key="deny_cancel_btn")

                if confirm_cancel:
                    st.session_state.registrations_df = st.session_state.registrations_df[
                        ~((st.session_state.registrations_df["Participant Username"] == st.session_state.username) &
                          (st.session_state.registrations_df["Event ID"] == event_to_cancel_id))
                    ]
                    google_db.save_dataframe("registrations", st.session_state.registrations_df)
                    st.success(f"Registration for '{events_for_cancellation[events_for_cancellation['Event ID'] == event_to_cancel_id]['Name'].iloc[0]}' cancelled successfully. 👋")
                    st.rerun()
            else:
                st.info("Please select an event to cancel registration.")


def show_my_tasks():
    """Volunteer: View assigned tasks and update their status."""
    st.title("My Tasks ✅")
    st.markdown("---")
    st.write(f"Tasks assigned to you as a volunteer, {st.session_state.user_full_name}.")

    my_tasks = st.session_state.tasks_df[st.session_state.tasks_df["Assigned To Volunteer Username"] == st.session_state.username]

    if my_tasks.empty:
        st.info("You currently have no tasks assigned.")
        return

    display_tasks = pd.merge(my_tasks, st.session_state.events_df[["Event ID", "Name", "Date", "Location"]], on="Event ID", how="left")
    st.subheader("Your Assigned Tasks")
    st.dataframe(display_tasks[["Name", "Date", "Location", "Description", "Due Date", "Status"]], use_container_width=True)

    st.subheader("Update Task Status 🔄")
    with st.expander("Update a Task's Status"):
        if not display_tasks.empty:
            task_options_display = [f"{row['Name']} - {row['Description']} (Due: {row['Due Date']})" for _, row in display_tasks.iterrows()]
            selected_task_display = st.selectbox("Select Task to Update", options=task_options_display, key="select_task_to_update_volunteer")
            
            if selected_task_display:
                selected_task_row = display_tasks[display_tasks.apply(lambda row: f"{row['Name']} - {row['Description']} (Due: {row['Due Date']})" == selected_task_display, axis=1)].iloc[0]

                current_status = selected_task_row["Status"]
                new_status = st.selectbox(
                    "New Status", 
                    options=["Assigned", "In Progress", "Completed", "Pending"], 
                    index=["Assigned", "In Progress", "Completed", "Pending"].index(current_status),
                    key=f"task_status_update_{selected_task_row['Task ID']}"
                )
                
                if st.button(f"Update Status for '{selected_task_row['Description']}' in '{selected_task_row['Name']}'", 
                             key=f"update_task_btn_{selected_task_row['Task ID']}"):
                    idx_in_main_df = st.session_state.tasks_df[
                        (st.session_state.tasks_df["Task ID"] == selected_task_row["Task ID"])
                    ].index
                    
                    if not idx_in_main_df.empty:
                        st.session_state.tasks_df.loc[idx_in_main_df, "Status"] = new_status
                        google_db.save_dataframe("tasks", st.session_state.tasks_df)
                        st.success(f"Status for '{selected_task_row['Description']}' updated to '{new_status}'. ✅")
                        st.rerun()
                    else:
                        st.error("Could not find the task to update.")

def show_update_availability():
    """Volunteer: Manage their availability status."""
    global USERS
    st.title("📅 Update Availability")
    st.markdown("---")
    st.write(f"Manage your availability for volunteer assignments, {st.session_state.user_full_name}.")

    current_availability = USERS[st.session_state.username].get("Availability", "Available")
    
    st.subheader("Current Availability Status")
    st.info(f"Your current availability is: **{current_availability}**")

    new_availability = st.selectbox("Update your Availability", options=["Available", "Busy", "On Leave"], key="volunteer_availability_select")
    
    if st.button("Save Availability", key="save_availability_btn"):
        user_idx = st.session_state.users_df[st.session_state.users_df["Username"] == st.session_state.username].index
        if not user_idx.empty:
            st.session_state.users_df.loc[user_idx, "Availability"] = new_availability
            google_db.save_dataframe("users", st.session_state.users_df)
            USERS = st.session_state.users_df.set_index("Username").to_dict(orient="index")

        volunteer_idx = st.session_state.volunteers_df[st.session_state.volunteers_df["Volunteer Username"] == st.session_state.username].index
        if not volunteer_idx.empty:
            st.session_state.volunteers_df.loc[volunteer_idx, "Availability"] = new_availability
            google_db.save_dataframe("volunteers", st.session_state.volunteers_df)
        else:
            new_volunteer_entry = {
                "Volunteer Username": st.session_state.username,
                "Full Name": st.session_state.user_full_name,
                "Availability": new_availability
            }
            st.session_state.volunteers_df = pd.concat([st.session_state.volunteers_df, pd.DataFrame([new_volunteer_entry])], ignore_index=True)
            google_db.save_dataframe("volunteers", st.session_state.volunteers_df)

        st.success(f"Your availability has been updated to: **{new_availability}** ✅")
        st.rerun()


# --- Main Application Logic ---

st.sidebar.title("ERP Navigation 🌐")
st.sidebar.markdown("---")

if not st.session_state.logged_in:
    st.sidebar.subheader("Login 🔑")
    with st.sidebar.form("login_form"):
        username = st.text_input("Username", key="login_username_input")
        password = st.text_input("Password", type="password", key="login_password_input")
        login_button = st.form_submit_button("Login")
        if login_button:
            login(username, password)
    
    current_accessible_pages = ROLE_PAGES.get("Public", ["Home"])
    st.session_state.current_page = st.sidebar.radio(
        "Go to",
        current_accessible_pages,
        index=current_accessible_pages.index(st.session_state.current_page) if st.session_state.current_page in current_accessible_pages else 0,
        key="public_sidebar_navigation_radio"
    )
    if st.session_state.current_page == "Home":
        home_page()
    elif st.session_state.current_page == "View Event Details":
        show_view_event_details()
    elif st.session_state.current_page == "Announcements":
        show_announcements()
    else:
        st.error("Page not found or not accessible for public role.")
        home_page()

else:
    st.sidebar.write(f"Hello, **{st.session_state.user_full_name}**!")
    st.sidebar.write(f"Role: **{st.session_state.role}**")
    st.sidebar.button("Logout", on_click=logout, help="Click to securely log out of the system.")
    st.sidebar.markdown("---")

    accessible_pages = ROLE_PAGES.get(st.session_state.role, ["Home"])
    
    if st.session_state.current_page not in accessible_pages:
        st.session_state.current_page = accessible_pages[0] if accessible_pages else "Home"

    selected_page_from_radio = st.sidebar.radio(
        "Go to",
        accessible_pages,
        index=accessible_pages.index(st.session_state.current_page),
        key="sidebar_navigation_radio"
    )
    st.session_state.current_page = selected_page_from_radio

    if st.session_state.current_page == "Home":
        home_page()
    elif st.session_state.current_page == "Announcements":
        show_announcements()
    elif st.session_state.current_page == "Dashboard":
        show_admin_dashboard()
    elif st.session_state.current_page == "User Management":
        show_user_management()
    elif st.session_state.current_page == "Event Management":
        show_event_management()
    elif st.session_state.current_page == "Sponsor Management":
        show_sponsor_management()
    elif st.session_state.current_page == "Budget Overview":
        show_budget_overview()
    elif st.session_state.current_page == "Reports":
        show_reports()
    elif st.session_state.current_page == "My Events":
        show_my_events()
    elif st.session_state.current_page == "Event Task Management":
        show_event_task_management()
    elif st.session_state.current_page == "Volunteer Assignment":
        show_volunteer_assignment()
    elif st.session_state.current_page == "Event Budget Tracking":
        show_event_budget_tracking()
    elif st.session_state.current_page == "Communication Hub":
        show_communication_hub()
    elif st.session_state.current_page == "View Event Details":
        show_view_event_details()
    elif st.session_state.current_page == "Register for Events":
        show_register_for_events()
    elif st.session_state.current_page == "My Registrations":
        show_my_registrations()
    elif st.session_state.current_page == "My Tasks":
        show_my_tasks()
    elif st.session_state.current_page == "Update Availability":
        show_update_availability()
    else:
        st.error(f"Page '{st.session_state.current_page}' not found or not accessible for your role. Please use the navigation.")
        home_page()
