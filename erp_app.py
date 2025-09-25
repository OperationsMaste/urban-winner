import streamlit as st
import pandas as pd
import datetime

# --- Configuration ---
st.set_page_config(layout="wide", page_title="Inter-College Festive Event ERP")

# --- Session State Initialization ---
# This ensures that these variables exist even on first run and persist across reruns for the same user session
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.current_page = "Home" # Default page for logged-in users

# --- User Data (For demonstration purposes - in a real app, this would be a secure database) ---
# Passwords are plaintext for demo simplicity. NEVER do this in production.
USERS = {
    "admin": {"password": "admin", "role": "Admin", "name": "Alice Admin"},
    "coord1": {"password": "coord", "role": "Coordinator", "name": "Bob Coordinator"},
    "part1": {"password": "part", "role": "Participant", "name": "Charlie Participant"},
    "volun1": {"password": "volun", "role": "Volunteer", "name": "Diana Volunteer"},
}

# --- Role-based Page Mapping ---
# This dictionary defines which "tabs" or modules each role can access.
# This is key for role-based access control.
ROLE_PAGES = {
    "Admin": ["Dashboard", "User Management", "Event Management", "Budget Overview", "Reports"],
    "Coordinator": ["My Events", "Volunteer Assignment", "Event Budget Tracking"],
    "Participant": ["Register for Events", "My Registrations"],
    "Volunteer": ["My Tasks", "Update Availability"],
    "Public": ["Home"] # Pages visible when not logged in
}

# --- Data Stores (Simulated databases using Pandas DataFrames in session_state) ---
# This data will reset if the Streamlit app is restarted, but persists across user interactions.
# For a real ERP, connect to a persistent database (SQL, NoSQL).

if "events_df" not in st.session_state:
    st.session_state.events_df = pd.DataFrame(columns=[
        "Event ID", "Name", "Date", "Time", "Location", "Coordinator", "Budget", "Status"
    ])
    # Add some dummy data
    st.session_state.events_df = pd.DataFrame({
        "Event ID": ["E001", "E002", "E003"],
        "Name": ["Tech Fest", "Cultural Gala", "Sports Day"],
        "Date": [datetime.date(2025, 10, 15), datetime.date(2025, 11, 20), datetime.date(2025, 12, 5)],
        "Time": ["10:00 AM", "06:00 PM", "09:00 AM"],
        "Location": ["Auditorium", "Amphitheater", "Sports Ground"],
        "Coordinator": ["Bob Coordinator", "Bob Coordinator", "Alice Admin"], # Link to user names
        "Budget": [50000, 75000, 30000],
        "Status": ["Upcoming", "Upcoming", "Upcoming"]
    })

if "registrations_df" not in st.session_state:
    st.session_state.registrations_df = pd.DataFrame(columns=["Reg ID", "Participant Username", "Event ID", "Registration Date"])
    # Add some dummy data
    st.session_state.registrations_df = pd.DataFrame({
        "Reg ID": ["R001"],
        "Participant Username": ["part1"],
        "Event ID": ["E001"],
        "Registration Date": [datetime.date.today()]
    })

if "volunteers_df" not in st.session_state:
    st.session_state.volunteers_df = pd.DataFrame(columns=["Volunteer Username", "Event ID", "Assigned Task", "Status", "Availability"])
    st.session_state.volunteers_df = pd.DataFrame({
        "Volunteer Username": ["volun1"],
        "Event ID": ["E001"],
        "Assigned Task": ["Registration Desk"],
        "Status": ["Assigned"],
        "Availability": ["Available"]
    })

# --- Helper Functions ---
def logout():
    """Logs the user out by resetting session state variables."""
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.current_page = "Home" # Redirect to home page after logout
    st.success("You have been logged out.")
    st.rerun() # Rerun to refresh the UI and show login form

def login(username, password):
    """Authenticates the user and sets session state."""
    if username in USERS and USERS[username]["password"] == password:
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.role = USERS[username]["role"]
        # Set the default page to the first accessible page for the role
        st.session_state.current_page = ROLE_PAGES[st.session_state.role][0] if st.session_state.role in ROLE_PAGES and ROLE_PAGES[st.session_state.role] else "Home"
        st.success(f"Welcome, {USERS[username]['name']} ({st.session_state.role})!")
        st.rerun() # Rerun to refresh the UI and show role-specific navigation
    else:
        st.error("Invalid username or password")

# --- Page Content Functions (These represent the "tabs" or modules) ---

def home_page():
    """Displays the general home page."""
    st.title("🏛️ Welcome to the Inter-College Festive Event ERP")
    st.write("This system helps manage all aspects of our annual inter-college festive events.")
    st.image("https://images.pexels.com/photos/357335/pexels-photo-357335.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1", caption="Festive Event", use_column_width=True)
    st.markdown("---")
    st.info("Please log in using the sidebar to access specific functionalities based on your role.")
    st.markdown("Try logging in with: `admin`/`admin`, `coord1`/`coord`, `part1`/`part`, `volun1`/`volun`")


def show_admin_dashboard():
    """Admin Dashboard: Overview of events, participants, and budget."""
    st.title("📊 Admin Dashboard")
    st.write(f"Welcome, {USERS[st.session_state.username]['name']}!")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Events", st.session_state.events_df.shape[0])
    with col2:
        st.metric("Total Participants", st.session_state.registrations_df["Participant Username"].nunique())
    with col3:
        st.metric("Total Budget Allocated", f"₹{st.session_state.events_df['Budget'].sum():,.2f}")

    st.subheader("Upcoming Events")
    upcoming = st.session_state.events_df[st.session_state.events_df["Status"] == "Upcoming"]
    if upcoming.empty:
        st.info("No upcoming events.")
    else:
        st.dataframe(upcoming.head(5))

    st.subheader("Recent Registrations")
    recent_regs = st.session_state.registrations_df.sort_values("Registration Date", ascending=False).head(5)
    if recent_regs.empty:
        st.info("No recent registrations.")
    else:
        st.dataframe(recent_regs)

def show_user_management():
    """Admin User Management: Add/view users (simplified)."""
    st.title("👤 User Management")
    st.write("Manage system users and their roles.")

    st.subheader("Existing Users")
    user_data = []
    for username, data in USERS.items():
        user_data.append({"Username": username, "Role": data["role"], "Full Name": data.get("name", "")})
    st.dataframe(pd.DataFrame(user_data), use_container_width=True)

    st.subheader("Add New User")
    with st.form("add_user_form"):
        new_username = st.text_input("New Username")
        new_password = st.text_input("Password", type="password")
        new_name = st.text_input("Full Name")
        new_role = st.selectbox("Role", options=["Admin", "Coordinator", "Participant", "Volunteer"])
        submit_button = st.form_submit_button("Add User")

        if submit_button:
            if new_username in USERS:
                st.error("Username already exists!")
            elif not new_username or not new_password or not new_name:
                st.error("Please fill in all fields.")
            else:
                USERS[new_username] = {"password": new_password, "role": new_role, "name": new_name}
                st.success(f"User '{new_username}' added with role '{new_role}'.")
                st.rerun() # To refresh the user list in the dataframe

def show_event_management():
    """Admin Event Management: Create, view, and edit events."""
    st.title("📅 Event Management")
    st.write("Create, view, and manage events for the festive season.")

    # Using st.tabs to organize content WITHIN this specific page
    tab1, tab2 = st.tabs(["View All Events", "Create New Event"])

    with tab1:
        st.subheader("All Events")
        if st.session_state.events_df.empty:
            st.info("No events created yet.")
        else:
            # st.data_editor allows direct editing of the DataFrame
            editable_events_df = st.data_editor(st.session_state.events_df, key="events_editor", use_container_width=True)
            if not editable_events_df.equals(st.session_state.events_df):
                st.session_state.events_df = editable_events_df
                st.success("Events updated successfully!")
                st.rerun() # Rerun to ensure state consistency

    with tab2:
        st.subheader("Create New Event")
        with st.form("new_event_form"):
            event_id = st.text_input("Event ID (e.g., E004)")
            name = st.text_input("Event Name")
            date = st.date_input("Date", datetime.date.today())
            time = st.text_input("Time (e.g., 10:00 AM)")
            location = st.text_input("Location")
            # Filter for actual coordinators, add an empty option
            coordinator_options = [u["name"] for u in USERS.values() if u["role"] == "Coordinator"]
            coordinator_options.insert(0, "") # Add an empty option at the beginning
            coordinator = st.selectbox("Coordinator", options=coordinator_options, index=0)
            budget = st.number_input("Budget", min_value=0, value=10000, step=1000)
            status = st.selectbox("Status", options=["Upcoming", "Ongoing", "Completed", "Cancelled"])
            
            submit_event = st.form_submit_button("Add Event")

            if submit_event:
                if event_id in st.session_state.events_df["Event ID"].values:
                    st.error("Event ID already exists!")
                elif not event_id or not name or not location or not coordinator:
                    st.error("Please fill in all required fields.")
                else:
                    new_event = {
                        "Event ID": event_id,
                        "Name": name,
                        "Date": date,
                        "Time": time,
                        "Location": location,
                        "Coordinator": coordinator,
                        "Budget": budget,
                        "Status": status
                    }
                    st.session_state.events_df = pd.concat([st.session_state.events_df, pd.DataFrame([new_event])], ignore_index=True)
                    st.success(f"Event '{name}' added successfully!")
                    st.rerun() # To refresh the event list in the other tab

def show_budget_overview():
    """Admin Budget Overview: Monitor overall budget and expenses."""
    st.title("💰 Budget Overview")
    st.write("Monitor budget allocations and expenses across all events.")

    st.subheader("Event-wise Budget Allocation")
    if st.session_state.events_df.empty:
        st.info("No events with budget data.")
    else:
        st.dataframe(st.session_state.events_df[["Event ID", "Name", "Budget"]], use_container_width=True)

    total_budget = st.session_state.events_df["Budget"].sum()
    st.metric("Total Allocated Budget", f"₹{total_budget:,.2f}")

    # Dummy expense tracking for demo (in a real app, this would be actual expense data)
    st.subheader("Overall Expenses (Dummy Data)")
    expenses = pd.DataFrame({
        "Category": ["Marketing", "Venue Rental", "Artist Fees", "Equipment", "Food"],
        "Amount": [15000, 20000, 30000, 10000, 12000],
        "Event ID": ["E001", "E002", "E001", "E003", "E002"]
    })
    st.dataframe(expenses, use_container_width=True)
    st.metric("Total Expenses (Dummy)", f"₹{expenses['Amount'].sum():,.2f}")
    st.metric("Remaining Budget (Estimate)", f"₹{total_budget - expenses['Amount'].sum():,.2f}")

def show_reports():
    """Admin Reports: Generate various analytical reports."""
    st.title("📈 Reports")
    st.write("Generate various reports for event analysis.")

    report_type = st.selectbox("Select Report Type", ["Event Participation", "Budget vs Actual", "Volunteer Engagement"])

    if report_type == "Event Participation":
        st.subheader("Event Participation Report")
        if st.session_state.registrations_df.empty:
            st.info("No registrations to report on.")
        else:
            participation_counts = st.session_state.registrations_df.groupby("Event ID").size().reset_index(name="Participants")
            participation_merged = pd.merge(participation_counts, st.session_state.events_df[["Event ID", "Name"]], on="Event ID", how="left")
            st.dataframe(participation_merged.sort_values("Participants", ascending=False), use_container_width=True)
            st.bar_chart(participation_merged.set_index("Name")["Participants"])

    elif report_type == "Budget vs Actual":
        st.subheader("Budget vs Actual Expenses Report")
        st.warning("This report currently uses dummy expense data. Integrate with actual expense tracking for real data.")
        expenses = pd.DataFrame({ # Re-using dummy expense data from budget overview
            "Category": ["Marketing", "Venue Rental", "Artist Fees", "Equipment", "Food"],
            "Amount": [15000, 20000, 30000, 10000, 12000],
            "Event ID": ["E001", "E002", "E001", "E003", "E002"]
        })
        event_expenses = expenses.groupby("Event ID")["Amount"].sum().reset_index(name="Actual Expenses")
        budget_vs_actual = pd.merge(st.session_state.events_df[["Event ID", "Name", "Budget"]], event_expenses, on="Event ID", how="left").fillna(0)
        budget_vs_actual["Variance"] = budget_vs_actual["Budget"] - budget_vs_actual["Actual Expenses"]
        st.dataframe(budget_vs_actual, use_container_width=True)
        st.bar_chart(budget_vs_actual.set_index("Name")[["Budget", "Actual Expenses"]])

    elif report_type == "Volunteer Engagement":
        st.subheader("Volunteer Engagement Report")
        if st.session_state.volunteers_df.empty:
            st.info("No volunteer assignments to report on.")
        else:
            volunteer_counts = st.session_state.volunteers_df.groupby("Volunteer Username").size().reset_index(name="Assigned Tasks")
            st.dataframe(volunteer_counts, use_container_width=True)
            st.bar_chart(volunteer_counts.set_index("Volunteer Username")["Assigned Tasks"])


def show_my_events():
    """Coordinator: View and manage events assigned to them."""
    st.title("My Events")
    coordinator_name = USERS[st.session_state.username]["name"]
    st.write(f"Events coordinated by you, {coordinator_name}.")
    
    my_events = st.session_state.events_df[st.session_state.events_df["Coordinator"] == coordinator_name]
    if my_events.empty:
        st.info("You are not currently assigned to coordinate any events.")
    else:
        st.dataframe(my_events, use_container_width=True)

        st.subheader("Update Event Status")
        event_to_update = st.selectbox("Select Event to Update", options=my_events["Event ID"].tolist(), 
                                      format_func=lambda x: my_events[my_events["Event ID"] == x]["Name"].iloc[0] if not my_events.empty else x)
        
        if event_to_update:
            current_status = st.session_state.events_df[st.session_state.events_df["Event ID"] == event_to_update]["Status"].iloc[0]
            new_status = st.selectbox("New Status", options=["Upcoming", "Ongoing", "Completed", "Cancelled"], 
                                      index=["Upcoming", "Ongoing", "Completed", "Cancelled"].index(current_status), key=f"status_{event_to_update}")
            
            if st.button(f"Update Status for {event_to_update}", key=f"update_status_btn_{event_to_update}"):
                idx = st.session_state.events_df[st.session_state.events_df["Event ID"] == event_to_update].index
                st.session_state.events_df.loc[idx, "Status"] = new_status
                st.success(f"Status for {event_to_update} updated to {new_status}.")
                st.rerun()


def show_volunteer_assignment():
    """Coordinator: Assign volunteers to their events."""
    st.title("👥 Volunteer Assignment")
    coordinator_name = USERS[st.session_state.username]["name"]
    st.write(f"Assign volunteers to events you coordinate, {coordinator_name}.")

    my_events_ids = st.session_state.events_df[st.session_state.events_df["Coordinator"] == coordinator_name]["Event ID"].tolist()

    if not my_events_ids:
        st.info("You are not coordinating any events to assign volunteers to.")
        return

    st.subheader("Current Volunteer Assignments for My Events")
    current_assignments = st.session_state.volunteers_df[st.session_state.volunteers_df["Event ID"].isin(my_events_ids)]
    if current_assignments.empty:
        st.info("No volunteers assigned to your events yet.")
    else:
        # Allow editing existing assignments
        editable_volunteers_df = st.data_editor(current_assignments, key="volunteer_assignments_editor", use_container_width=True)
        if not editable_volunteers_df.equals(current_assignments):
            # This is a bit of a workaround for data_editor on subsets: update the main df
            st.session_state.volunteers_df = st.session_state.volunteers_df[~st.session_state.volunteers_df["Event ID"].isin(my_events_ids)]
            st.session_state.volunteers_df = pd.concat([st.session_state.volunteers_df, editable_volunteers_df], ignore_index=True)
            st.success("Volunteer assignments updated!")

    st.subheader("Assign New Volunteer")
    with st.form("assign_volunteer_form"):
        volunteer_options = [u for u, data in USERS.items() if data["role"] == "Volunteer"]
        selected_volunteer = st.selectbox("Select Volunteer", options=volunteer_options, index=0 if volunteer_options else None)
        selected_event = st.selectbox("Select Event", options=my_events_ids, 
                                      format_func=lambda x: st.session_state.events_df[st.session_state.events_df["Event ID"] == x]["Name"].iloc[0])
        task = st.text_input("Assigned Task (e.g., Registration Desk, Usher)")
        
        assign_button = st.form_submit_button("Assign Volunteer")

        if assign_button:
            if selected_volunteer and selected_event and task:
                # Check if already assigned this exact task for this event
                if not st.session_state.volunteers_df[
                    (st.session_state.volunteers_df["Volunteer Username"] == selected_volunteer) &
                    (st.session_state.volunteers_df["Event ID"] == selected_event) &
                    (st.session_state.volunteers_df["Assigned Task"] == task)
                ].empty:
                    st.warning("This volunteer is already assigned this exact task for this event.")
                else:
                    new_assignment = {
                        "Volunteer Username": selected_volunteer,
                        "Event ID": selected_event,
                        "Assigned Task": task,
                        "Status": "Assigned",
                        "Availability": USERS[selected_volunteer].get("availability", "Available") # Placeholder for volunteer's availability
                    }
                    st.session_state.volunteers_df = pd.concat([st.session_state.volunteers_df, pd.DataFrame([new_assignment])], ignore_index=True)
                    st.success(f"Volunteer '{selected_volunteer}' assigned to '{selected_event}' for task '{task}'.")
                    st.rerun()
            else:
                st.error("Please fill all fields.")

def show_event_budget_tracking():
    """Coordinator: Track budget and expenses for their assigned events."""
    st.title("💸 Event Budget Tracking")
    coordinator_name = USERS[st.session_state.username]["name"]
    st.write(f"Track the budget for events you coordinate, {coordinator_name}.")

    my_events = st.session_state.events_df[st.session_state.events_df["Coordinator"] == coordinator_name]
    
    if my_events.empty:
        st.info("You are not coordinating any events to track budget for.")
        return

    selected_event_id = st.selectbox("Select Event", options=my_events["Event ID"].tolist(),
                                      format_func=lambda x: my_events[my_events["Event ID"] == x]["Name"].iloc[0])

    if selected_event_id:
        event_info = my_events[my_events["Event ID"] == selected_event_id].iloc[0]
        st.subheader(f"Budget for {event_info['Name']} ({selected_event_id})")
        st.metric("Allocated Budget", f"₹{event_info['Budget']:,.2f}")

        # Dummy expense tracking specific to this event (would be actual data in real ERP)
        st.subheader("Recorded Expenses (Dummy Data)")
        # In a real app, expenses would be filtered by `Event ID` from a global expense table
        if selected_event_id == "E001":
            event_expenses_for_display = pd.DataFrame({
                "Expense ID": ["EXP001", "EXP003"],
                "Category": ["Decorations", "Artist Fees"],
                "Amount": [10000, 30000],
                "Date": [datetime.date(2025, 10, 10), datetime.date(2025, 10, 12)]
            })
        elif selected_event_id == "E002":
            event_expenses_for_display = pd.DataFrame({
                "Expense ID": ["EXP002", "EXP005"],
                "Category": ["Venue Rental", "Food"],
                "Amount": [20000, 12000],
                "Date": [datetime.date(2025, 11, 15), datetime.date(2025, 11, 18)]
            })
        elif selected_event_id == "E003":
            event_expenses_for_display = pd.DataFrame({
                "Expense ID": ["EXP004"],
                "Category": ["Equipment"],
                "Amount": [10000],
                "Date": [datetime.date(2025, 12, 1)]
            })
        else: # For newly created events, no dummy expenses
            event_expenses_for_display = pd.DataFrame(columns=["Expense ID", "Category", "Amount", "Date"])

        if event_expenses_for_display.empty:
            st.info("No expenses recorded for this event yet (dummy data).")
        else:
            st.dataframe(event_expenses_for_display, use_container_width=True)

        total_expenses = event_expenses_for_display["Amount"].sum() if not event_expenses_for_display.empty else 0
        st.metric("Total Expenses Recorded (Dummy)", f"₹{total_expenses:,.2f}")
        st.metric("Remaining Budget", f"₹{event_info['Budget'] - total_expenses:,.2f}")

        st.subheader("Add New Expense (Dummy Entry)")
        st.warning("This is a dummy expense entry and will not be saved. In a real system, it would be persisted to a database.")
        with st.form(f"add_expense_form_{selected_event_id}"):
            expense_category = st.text_input("Expense Category")
            expense_amount = st.number_input("Amount", min_value=0.0, value=0.0, step=100.0)
            expense_date = st.date_input("Date", datetime.date.today())
            add_expense_button = st.form_submit_button("Add Expense (Dummy)")
            if add_expense_button:
                if expense_category and expense_amount > 0:
                    st.info(f"Dummy Expense Added: Event '{event_info['Name']}' - {expense_category} - ₹{expense_amount} on {expense_date}. (Not saved)")
                else:
                    st.error("Please provide a category and a positive amount for the dummy expense.")


def show_register_for_events():
    """Participant: View available events and register."""
    st.title("📝 Register for Events")
    st.write(f"Welcome, {USERS[st.session_state.username]['name']}! Register for exciting events.")

    st.subheader("Available Upcoming Events")
    # Only show upcoming events for registration
    upcoming_events = st.session_state.events_df[st.session_state.events_df["Status"] == "Upcoming"]
    
    if upcoming_events.empty:
        st.info("No upcoming events available for registration at the moment.")
        return

    events_for_display = upcoming_events[["Event ID", "Name", "Date", "Time", "Location", "Coordinator"]]
    st.dataframe(events_for_display, use_container_width=True)

    st.subheader("Register for an Event")
    with st.form("event_registration_form"):
        # Use format_func to show event names in the selectbox
        event_to_register_id = st.selectbox("Select Event", options=upcoming_events["Event ID"].tolist(), 
                                            format_func=lambda x: upcoming_events[upcoming_events["Event ID"] == x]["Name"].iloc[0] if not upcoming_events.empty else x)
        
        register_button = st.form_submit_button("Register")

        if register_button:
            if event_to_register_id:
                # Check if already registered for this event
                if not st.session_state.registrations_df[
                    (st.session_state.registrations_df["Participant Username"] == st.session_state.username) &
                    (st.session_state.registrations_df["Event ID"] == event_to_register_id)
                ].empty:
                    st.warning("You are already registered for this event.")
                else:
                    new_reg_id = f"R{len(st.session_state.registrations_df) + 1:03d}"
                    new_registration = {
                        "Reg ID": new_reg_id,
                        "Participant Username": st.session_state.username,
                        "Event ID": event_to_register_id,
                        "Registration Date": datetime.date.today()
                    }
                    st.session_state.registrations_df = pd.concat([st.session_state.registrations_df, pd.DataFrame([new_registration])], ignore_index=True)
                    event_name = upcoming_events[upcoming_events['Event ID'] == event_to_register_id]['Name'].iloc[0]
                    st.success(f"Successfully registered for event '{event_name}'.")
                    st.rerun()
            else:
                st.error("Please select an event to register.")

def show_my_registrations():
    """Participant: View events they have registered for."""
    st.title("My Registrations")
    st.write(f"Events you have registered for, {USERS[st.session_state.username]['name']}.")

    my_regs = st.session_state.registrations_df[st.session_state.registrations_df["Participant Username"] == st.session_state.username]
    
    if my_regs.empty:
        st.info("You haven't registered for any events yet.")
    else:
        # Merge with event details for better display
        display_regs = pd.merge(my_regs, st.session_state.events_df[["Event ID", "Name", "Date", "Location"]], on="Event ID", how="left")
        st.subheader("Your Registered Events")
        st.dataframe(display_regs[["Name", "Date", "Location", "Registration Date"]], use_container_width=True)

def show_my_tasks():
    """Volunteer: View assigned tasks and update their status."""
    st.title("My Tasks")
    st.write(f"Tasks assigned to you as a volunteer, {USERS[st.session_state.username]['name']}.")

    my_tasks = st.session_state.volunteers_df[st.session_state.volunteers_df["Volunteer Username"] == st.session_state.username]

    if my_tasks.empty:
        st.info("You currently have no tasks assigned.")
    else:
        # Merge with event details for better display
        display_tasks = pd.merge(my_tasks, st.session_state.events_df[["Event ID", "Name", "Date", "Location"]], on="Event ID", how="left")
        st.subheader("Assigned Tasks")
        st.dataframe(display_tasks[["Name", "Date", "Location", "Assigned Task", "Status"]], use_container_width=True)

        st.subheader("Update Task Status")
        if not display_tasks.empty:
            # Create a unique identifier for each task for the selectbox
            task_options_display = [f"{row['Name']} - {row['Assigned Task']} (Event ID: {row['Event ID']})" for index, row in display_tasks.iterrows()]
            selected_task_display = st.selectbox("Select Task to Update", options=task_options_display)
            
            if selected_task_display:
                # Find the original row in `my_tasks` dataframe using the unique identifier
                # This is crucial for correctly updating the state.
                selected_task_row_idx = display_tasks.index[display_tasks.apply(lambda row: f"{row['Name']} - {row['Assigned Task']} (Event ID: {row['Event ID']})" == selected_task_display, axis=1)].tolist()[0]
                selected_task_row = display_tasks.loc[selected_task_row_idx]

                current_status = selected_task_row["Status"]
                new_status = st.selectbox(
                    "New Status", 
                    options=["Assigned", "In Progress", "Completed", "Pending"], 
                    index=["Assigned", "In Progress", "Completed", "Pending"].index(current_status),
                    key=f"task_status_update_{selected_task_row['Event ID']}_{selected_task_row['Assigned Task']}"
                )
                
                if st.button(f"Update Status for '{selected_task_row['Assigned Task']}' in '{selected_task_row['Name']}'", 
                             key=f"update_task_btn_{selected_task_row['Event ID']}_{selected_task_row['Assigned Task']}"):
                    # Find the exact row in the main volunteers_df to update
                    idx_in_main_df = st.session_state.volunteers_df[
                        (st.session_state.volunteers_df["Volunteer Username"] == st.session_state.username) &
                        (st.session_state.volunteers_df["Event ID"] == selected_task_row["Event ID"]) &
                        (st.session_state.volunteers_df["Assigned Task"] == selected_task_row["Assigned Task"])
                    ].index
                    
                    if not idx_in_main_df.empty:
                        st.session_state.volunteers_df.loc[idx_in_main_df, "Status"] = new_status
                        st.success(f"Status for '{selected_task_row['Assigned Task']}' updated to '{new_status}'.")
                        st.rerun()
                    else:
                        st.error("Could not find the task to update.")

def show_update_availability():
    """Volunteer: Manage their availability status."""
    st.title("📅 Update Availability")
    st.write(f"Manage your availability for volunteer assignments, {USERS[st.session_state.username]['name']}.")

    # Get current availability from USERS dict (simulate profile setting)
    current_availability = USERS[st.session_state.username].get("availability", "Available")
    
    st.subheader("Current Availability Status")
    st.info(f"Your current availability is: **{current_availability}**")

    new_availability = st.selectbox("Update your Availability", options=["Available", "Busy", "On Leave"])
    
    if st.button("Save Availability"):
        # Update in the USERS dictionary (profile)
        USERS[st.session_state.username]["availability"] = new_availability
        
        # Also update in `volunteers_df` for any current assignments
        # This ensures coordinators see the latest availability for assigned volunteers
        st.session_state.volunteers_df.loc[
            st.session_state.volunteers_df["Volunteer Username"] == st.session_state.username, 
            "Availability"
        ] = new_availability
        
        st.success(f"Your availability has been updated to: **{new_availability}**")
        st.rerun()


# --- Main Application Logic ---

st.sidebar.title("ERP Navigation")

# Authentication section in the sidebar
if not st.session_state.logged_in:
    st.sidebar.subheader("Login")
    with st.sidebar.form("login_form"):
        username = st.text_input("Username", key="login_username_input")
        password = st.text_input("Password", type="password", key="login_password_input")
        login_button = st.form_submit_button("Login")
        if login_button:
            login(username, password)
    home_page() # Show home page when not logged in
else:
    # Display user info and logout button when logged in
    st.sidebar.write(f"Hello, **{USERS[st.session_state.username]['name']}**!")
    st.sidebar.write(f"Role: **{st.session_state.role}**")
    st.sidebar.button("Logout", on_click=logout)
    st.sidebar.markdown("---")

    # Dynamic page selection based on role
    # Get pages accessible to the current role, or default to "Home" if role not found
    accessible_pages = ROLE_PAGES.get(st.session_state.role, ["Home"])
    
    # Use st.sidebar.radio for main navigation.
    # The 'index' parameter ensures the last selected page remains active after a rerun.
    selected_page = st.sidebar.radio(
        "Go to",
        accessible_pages,
        index=accessible_pages.index(st.session_state.current_page) if st.session_state.current_page in accessible_pages else 0,
        key="sidebar_navigation_radio" # Unique key for the widget
    )
    st.session_state.current_page = selected_page # Update current_page in session state

    # --- Display content based on selected page ---
    if st.session_state.current_page == "Home":
        home_page()
    elif st.session_state.current_page == "Dashboard":
        show_admin_dashboard()
    elif st.session_state.current_page == "User Management":
        show_user_management()
    elif st.session_state.current_page == "Event Management":
        show_event_management()
    elif st.session_state.current_page == "Budget Overview":
        show_budget_overview()
    elif st.session_state.current_page == "Reports":
        show_reports()
    elif st.session_state.current_page == "My Events":
        show_my_events()
    elif st.session_state.current_page == "Volunteer Assignment":
        show_volunteer_assignment()
    elif st.session_state.current_page == "Event Budget Tracking":
        show_event_budget_tracking()
    elif st.session_state.current_page == "Register for Events":
        show_register_for_events()
    elif st.session_state.current_page == "My Registrations":
        show_my_registrations()
    elif st.session_state.current_page == "My Tasks":
        show_my_tasks()
    elif st.session_state.current_page == "Update Availability":
        show_update_availability()
    else:
        # Fallback for any unhandled page selections (shouldn't happen with dynamic radio)
        st.error("Page not found or not accessible for your role.")
        home_page()
