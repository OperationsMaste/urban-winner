import streamlit as st
import pandas as pd
import time # For simulating network latency

class GoogleSheetDB:
    def __init__(self, sheet_id="11IEx5m5zLjn3OfXN5Man7gZ04YicktFj5kgh15EjKtQ", credentials_path="path/to/your/credentials.json"):
        """
        Initializes the GoogleSheetDB.
        In a real application, this would set up gspread client, authenticate, etc.
        For this example, we'll just store placeholder connection details.
        """
        self.sheet_id = sheet_id
        self.credentials_path = credentials_path
        # Simulate a client connection (e.g., from gspread)
        # self.client = gspread.service_account(filename=credentials_path)
        print(f"GoogleSheetDB initialized with sheet ID: {self.sheet_id}")

    @st.cache_data(ttl=3600) # Cache for 1 hour, or until arguments change
    def _read_sheet_cached(_self, sheet_name):
        """
        Helper method to read data from a specified worksheet, using Streamlit's cache.
        The '_self' argument is ignored for caching purposes because of the leading underscore.
        This is where the actual, potentially expensive, I/O operation happens.
        """
        print(f"--- ACTUALLY READING SHEET: '{sheet_name}' from Google Sheets ---")
        
        # Simulate network latency and data fetching
        time.sleep(2) 
        
        # Placeholder for actual data fetching logic
        # In a real scenario:
        # worksheet = _self.client.open_by_key(_self.sheet_id).worksheet(sheet_name)
        # data = worksheet.get_all_records()
        # return pd.DataFrame(data)

        # For demonstration, we'll return a simple DataFrame based on the sheet_name
        if sheet_name == "users":
            data = [
                {"id": 1, "username": "alice", "password": "password123"},
                {"id": 2, "username": "bob", "password": "password456"}
            ]
        elif sheet_name == "products":
            data = [
                {"product_id": "P001", "name": "Laptop", "price": 1200},
                {"product_id": "P002", "name": "Mouse", "price": 25}
            ]
        else:
            data = [{"info": f"No specific data for {sheet_name}", "timestamp": time.time()}]

        return pd.DataFrame(data)

    def read_sheet(self, sheet_name):
        """
        Public method to read data from a specified worksheet.
        It delegates to the cached _read_sheet_cached method.
        """
        return self._read_sheet_cached(sheet_name)

    def _write_sheet(self, sheet_name, df):
        """
        Helper to write data to a sheet (no caching on write operations).
        This would typically involve updating cells in Google Sheets.
        """
        print(f"--- WRITING DATA TO SHEET: '{sheet_name}' ---")
        # In a real app, you'd use gspread here to update the sheet.
        # For example:
        # worksheet = self.client.open_by_key(self.sheet_id).worksheet(sheet_name)
        # worksheet.clear() # Clear existing data
        # gspread_dataframe.set_with_dataframe(worksheet, df) # Write new data
        st.success(f"Successfully wrote data to '{sheet_name}' (simulated).")

    def write_sheet(self, sheet_name, df):
        """
        Public method to write data to a specified worksheet.
        After writing, invalidate the cache for this sheet so that
        the next read gets the fresh data.
        """
        self._write_sheet(sheet_name, df)
        # Invalidate the cache for this specific sheet to ensure fresh data on next read
        self._read_sheet_cached.clear() # Clear the entire cache for the function
        # Or, if you wanted to clear only for a specific sheet_name:
        # This is more complex with st.cache_data, clearing the whole function's cache is simpler
        # For lru_cache, you'd call instance_of_cached_method.cache_clear()
        # For st.cache_data, clearing the function is the common approach.
        print(f"Cache cleared for _read_sheet_cached after writing to '{sheet_name}'.")

