import requests
import time
import os
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional, Tuple, Union

# Load environment variables
load_dotenv()

API_BASE_URL = os.getenv("JJCIMS_API_URL", "http://localhost:8000")


class MySQLConnector:
    """Replacement for AccessConnector that connects to MySQL through FastAPI.
    
    This connector implements the same interface as the original AccessConnector
    but uses HTTP requests to a FastAPI backend instead of direct database access.
    """
    
    def __init__(self, api_url=None):
        """Initialize the connector with the API URL."""
        self.api_url = api_url or API_BASE_URL
        # No actual connection is maintained, all operations are stateless HTTP requests
    
    def connect(self):
        """Simulate connection method for compatibility.
        
        Instead of returning a connection object, this returns self for method chaining.
        """
        return self
    
    def execute_query(self, query, params=None, retries=3, delay=2):
        """Execute a query by forwarding to the appropriate API endpoint.
        
        This method translates common SQL operations to API calls. It's not a general SQL
        executor but rather maps known query patterns to specific API endpoints.
        """
        last_exc = None
        for attempt in range(retries):
            try:
                # Extract operation and table from query
                query_lower = query.lower()
                
                # Handle UPDATE operations
                if query_lower.startswith("update itemsdb set [out] = [out] +"):
                    # Extract item name and quantity
                    name = params[1]
                    qty = params[0]
                    response = requests.put(f"{self.api_url}/items/{name}/out/{qty}")
                    response.raise_for_status()
                    return
                
                # Handle INSERT operations for logs
                elif query_lower.startswith("insert into [emp_logs]"):
                    # Extract log data
                    date_str, time_str, name, details = params
                    payload = {
                        "DATE": date_str,
                        "TIME": time_str,
                        "NAME": name,
                        "DETAILS": details
                    }
                    response = requests.post(f"{self.api_url}/employee-logs/", json=payload)
                    response.raise_for_status()
                    return
                
                # Handle INSERT operations for admin logs
                elif query_lower.startswith("insert into [adm_logs]"):
                    # Extract log data
                    date_str, time_str, user, details = params
                    payload = {
                        "DATE": date_str,
                        "TIME": time_str,
                        "USER": user,
                        "DETAILS": details
                    }
                    response = requests.post(f"{self.api_url}/admin-logs/", json=payload)
                    response.raise_for_status()
                    return
                
                # Handle DELETE operations for logs
                elif query_lower == "delete from [emp_logs]":
                    response = requests.delete(f"{self.api_url}/employee-logs/")
                    response.raise_for_status()
                    return
                
                # Handle DELETE operations for admin logs
                elif query_lower == "delete from [adm_logs]":
                    response = requests.delete(f"{self.api_url}/admin-logs/")
                    response.raise_for_status()
                    return
                
                # Handle DELETE operations for items
                elif query_lower.startswith("delete from itemsdb where name ="):
                    name = params[0]
                    # Find item ID first
                    response = requests.get(f"{self.api_url}/items/?name={name}")
                    response.raise_for_status()
                    items = response.json()
                    if items:
                        item_id = items[0]["ID"]
                        response = requests.delete(f"{self.api_url}/items/{item_id}")
                        response.raise_for_status()
                    return
                
                # For other queries, we would need to map them to specific API endpoints
                # This is a simplified implementation and would need to be expanded
                raise NotImplementedError(f"Query not supported: {query}")
                
            except requests.RequestException as e:
                last_exc = e
                if attempt < retries - 1:
                    time.sleep(delay)
                    continue
                else:
                    raise
        
        if last_exc:
            raise last_exc
    
    def get_2fa_secret(self, username):
        """Fetch the 2FA Secret for the given username."""
        try:
            response = requests.get(f"{self.api_url}/employees/{username.lower()}/2fa-and-access")
            response.raise_for_status()
            data = response.json()
            return data.get("2fa_secret")
        except requests.RequestException as e:
            print(f"API request failed: {e}")
            return None
    
    def fetchall(self, query, params=None, retries=3, delay=2):
        """Execute a SELECT query and return all rows.
        
        Maps common SELECT queries to API endpoints.
        """
        last_exc = None
        for attempt in range(retries):
            try:
                query_lower = query.lower()
                
                # Get items for employee dashboard
                if "select id, [items], [supplier], [po no] from [itemsdb]" in query_lower:
                    response = requests.get(f"{self.api_url}/items/employee-dashboard")
                    response.raise_for_status()
                    return response.json()
                
                # Get items by type
                elif "select id, name, brand, type, location, unit_of_measure, status, balance from itemsdb where type =" in query_lower:
                    category = params[0]
                    response = requests.get(f"{self.api_url}/items/by-type/{category}")
                    response.raise_for_status()
                    return response.json()
                
                # Get employee logs
                elif "select [date], [time], [name], [details] from [emp_logs]" in query_lower:
                    response = requests.get(f"{self.api_url}/employee-logs/")
                    response.raise_for_status()
                    return response.json()
                
                # Get admin logs
                elif "select [date], [time], [user], [details] from [adm_logs]" in query_lower:
                    response = requests.get(f"{self.api_url}/admin-logs/")
                    response.raise_for_status()
                    return response.json()
                
                # Get all items
                elif "select * from [itemsdb]" in query_lower:
                    response = requests.get(f"{self.api_url}/items/")
                    response.raise_for_status()
                    return response.json()
                
                # Get employee usernames
                elif "select username from [emp_list]" in query_lower:
                    response = requests.get(f"{self.api_url}/employees/")
                    response.raise_for_status()
                    employees = response.json()
                    return [(e["Username"],) for e in employees]
                
                # For other queries, we would need to map them to specific API endpoints
                raise NotImplementedError(f"Query not supported: {query}")
                
            except requests.RequestException as e:
                last_exc = e
                if attempt < retries - 1:
                    time.sleep(delay)
                    continue
                else:
                    raise
        
        if last_exc:
            raise last_exc
    
    def fetchone(self, query, params=None, retries=3, delay=2):
        """Execute a SELECT query and return a single row (or None)."""
        last_exc = None
        for attempt in range(retries):
            try:
                query_lower = query.lower()
                
                # Get unit of measure for an item
                if "select [unit of measure] from itemsdb where [name] =" in query_lower:
                    name = params[0]
                    response = requests.get(f"{self.api_url}/items/{name}/unit-of-measure")
                    response.raise_for_status()
                    data = response.json()
                    return (data.get("unit_of_measure"),)
                
                # Get employee 2FA secret and access level
                elif "select [2fa secret], [access level] from [emp_list] where lcase([username])=" in query_lower:
                    username_lower = params[0]
                    response = requests.get(f"{self.api_url}/employees/{username_lower}/2fa-and-access")
                    response.raise_for_status()
                    data = response.json()
                    return (data.get("2fa_secret"), data.get("access_level"))
                
                # Get user by username (case-sensitive)
                elif "select * from [emp_list] where [username]=" in query_lower:
                    username = params[0]
                    response = requests.get(f"{self.api_url}/employees/{username}")
                    response.raise_for_status()
                    data = response.json()
                    # Convert to a row-like format similar to pyodbc
                    return (data.get("id"), data.get("Username"), data.get("Password"), 
                           data.get("Access_Level"), data.get("TFA_Secret"))
                
                # Get user by lowercase username
                elif "select * from [emp_list] where lcase([username])=" in query_lower:
                    username_lower = params[0]
                    response = requests.get(f"{self.api_url}/employees/{username_lower}")
                    response.raise_for_status()
                    data = response.json()
                    # Convert to a row-like format similar to pyodbc
                    return (data.get("id"), data.get("Username"), data.get("Password"), 
                           data.get("Access_Level"), data.get("TFA_Secret"))
                
                # Check if table exists
                elif "select name from msysobjects where type=1 and flags=0 and name=?" in query_lower:
                    # For API, assume all standard tables exist
                    table_name = params[0]
                    standard_tables = ["ITEMSDB", "emp_logs", "adm_logs", "emp_list"]
                    if table_name.lower() in [t.lower() for t in standard_tables]:
                        return (table_name,)
                    return None
                
                # For other queries, we would need to map them to specific API endpoints
                raise NotImplementedError(f"Query not supported: {query}")
                
            except requests.HTTPError as e:
                if e.response.status_code == 404:
                    return None
                last_exc = e
                if attempt < retries - 1:
                    time.sleep(delay)
                    continue
                else:
                    raise
            except requests.RequestException as e:
                last_exc = e
                if attempt < retries - 1:
                    time.sleep(delay)
                    continue
                else:
                    raise
        
        if last_exc:
            raise last_exc
    
    def close(self):
        """Close any existing database connection.
        
        This is a no-op for the HTTP-based connector.
        """
        pass
