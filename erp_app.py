import streamlit as st
import pandas as pd
from google_sheet_db import GoogleSheetDB # Import our class

# Initialize the GoogleSheetDB instance
# In a real app, you'd pass your actual sheet ID and credentials path
google_db = GoogleSheetDB(
    sheet_id="my_app_data_sheet", 
    credentials_path="gcp_credentials.json"
)

st.set_page_config(layout="centered", initial_sidebar_state="auto", page_title="ERP App")
st.title("Simplified ERP Dashboard")

# Initialize session state variables if they don't exist
if "users_df" not in st.session_state:
    st.session_state.users_df = pd.DataFrame() # Initialize as empty
if "products_df" not in st.session_state:
    st.session_state.products_df = pd.DataFrame()


# --- Functions to load data ---
@st.cache_data(ttl=600) # Cache the function that calls our DB class for a short time
def load_users_data(db_instance):
    """Loads user data from the GoogleSheetDB instance."""
    return db_instance.read_sheet("users")

@st.cache_data(ttl=600)
def load_products_data(db_instance):
    """Loads product data from the GoogleSheetDB instance."""
    return db_instance.read_sheet("products")


# --- Sidebar Navigation ---
st.sidebar.title("Navigation")
menu_selection = st.sidebar.radio("Go to", ["Users Management", "Products Catalog", "Raw Data Viewer"])

# --- Main Content Area ---

if menu_selection == "Users Management":
    st.header("User Management")
    
    # Load user data (this will call our cached _read_sheet_cached)
    users_df_loaded = load_users_data(google_db)
    st.session_state.users_df = users_df_loaded # Update session state

    st.subheader("Current Users")
    st.dataframe(st.session_state.users_df)

    with st.expander("Add New User"):
        with st.form("new_user_form"):
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Add User")
            
            if submitted and new_username and new_password:
                # Assign a new ID (simplistic for demo)
                new_id = st.session_state.users_df["id"].max() + 1 if not st.session_state.users_df.empty else 1
                new_user_data = pd.DataFrame([{"id": new_id, "username": new_username, "password": new_password}])
                
                updated_df = pd.concat([st.session_state.users_df, new_user_data], ignore_index=True)
                
                # Write back to the "database" and invalidate cache
                google_db.write_sheet("users", updated_df)
                
                # After writing and clearing cache, reload data to reflect changes
                # This will trigger _read_sheet_cached again, but it won't be cached until after this run.
                # However, since load_users_data is also cached, we need to clear its cache too.
                load_users_data.clear() # Clear cache for the Streamlit wrapper function
                st.session_state.users_df = load_users_data(google_db) # Reload
                st.success(f"User '{new_username}' added successfully!")
                st.experimental_rerun() # Rerun to update the display

elif menu_selection == "Products Catalog":
    st.header("Products Catalog")

    # Load product data (this will call our cached _read_sheet_cached)
    products_df_loaded = load_products_data(google_db)
    st.session_state.products_df = products_df_loaded # Update session state

    st.subheader("Available Products")
    st.dataframe(st.session_state.products_df)

    with st.expander("Add New Product"):
        with st.form("new_product_form"):
            product_name = st.text_input("Product Name")
            product_price = st.number_input("Price", min_value=0.0, format="%.2f")
            submitted = st.form_submit_button("Add Product")

            if submitted and product_name and product_price is not None:
                new_id = f"P{st.session_state.products_df['product_id'].str.replace('P','').astype(int).max() + 1:03d}" if not st.session_state.products_df.empty else "P001"
                new_product_data = pd.DataFrame([{"product_id": new_id, "name": product_name, "price": product_price}])
                
                updated_df = pd.concat([st.session_state.products_df, new_product_data], ignore_index=True)
                
                google_db.write_sheet("products", updated_df)
                
                load_products_data.clear() # Clear cache for the Streamlit wrapper function
                st.session_state.products_df = load_products_data(google_db) # Reload
                st.success(f"Product '{product_name}' added successfully!")
                st.experimental_rerun()

elif menu_selection == "Raw Data Viewer":
    st.header("Raw Data Viewer")
    st.write("This section directly accesses the cached dataframes.")
    
    st.subheader("Users DataFrame")
    if not st.session_state.users_df.empty:
        st.dataframe(st.session_state.users_df)
    else:
        st.info("No user data loaded yet. Navigate to 'Users Management' to load it.")

    st.subheader("Products DataFrame")
    if not st.session_state.products_df.empty:
        st.dataframe(st.session_state.products_df)
    else:
        st.info("No product data loaded yet. Navigate to 'Products Catalog' to load it.")

