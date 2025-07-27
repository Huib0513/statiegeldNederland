# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os.path
from typing import List, Optional, Dict, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


class SheetsManager:
    """
    A class to manage Google Sheets operations including reading and writing data.
    """
    
    def __init__(self, service_account_file: str = 'servicecredentials.json'):
        """
        Initialize the SheetsManager with service account credentials.
        
        Args:
            service_account_file (str): Path to the service account JSON file
        """
        self.service_account_file = service_account_file
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate and build the Google Sheets service."""
        try:
            creds = service_account.Credentials.from_service_account_file(
                self.service_account_file, scopes=SCOPES
            )
            self.service = build("sheets", "v4", credentials=creds)
        except Exception as e:
            raise Exception(f"Failed to authenticate: {e}")
    
    def read_sheet(self, spreadsheet_id: str, range_name: str) -> List[List[str]]:
        """
        Read data from a Google Sheet.
        
        Args:
            spreadsheet_id (str): The ID of the spreadsheet
            range_name (str): The range to read (e.g., 'Sheet1' or 'A1:C10')
        
        Returns:
            List[List[str]]: The values from the sheet
        
        Raises:
            HttpError: If there's an error accessing the sheet
        """
        try:
            sheet = self.service.spreadsheets()
            result = (
                sheet.values()
                .get(spreadsheetId=spreadsheet_id, range=range_name)
                .execute()
            )
            values = result.get("values", [])
            return values
        except HttpError as err:
            raise HttpError(f"Error reading sheet: {err}")
    
    def find_row_by_value(self, spreadsheet_id: str, range_name: str, 
                         search_value: str, column_index: int = 0) -> Optional[int]:
        """
        Find the row number (1-based) where a specific value appears in a given column.
        
        Args:
            spreadsheet_id (str): The ID of the spreadsheet
            range_name (str): The range to search in
            search_value (str): The value to search for
            column_index (int): The column index to search in (0-based)
        
        Returns:
            Optional[int]: The row number (1-based) if found, None otherwise
        """
        values = self.read_sheet(spreadsheet_id, range_name)
        
        for row_idx, row in enumerate(values):
            if len(row) > column_index and row[column_index] == search_value:
                return row_idx + 1  # Return 1-based row number
        
        return None
    
    def write_to_sheet(self, spreadsheet_id: str, range_name: str, 
                      values: List[List[Any]], value_input_option: str = 'USER_ENTERED') -> Dict:
        """
        Write data to a Google Sheet.
        
        Args:
            spreadsheet_id (str): The ID of the spreadsheet
            range_name (str): The range to write to (e.g., 'A1:C1')
            values (List[List[Any]]): The values to write
            value_input_option (str): How to interpret the input ('USER_ENTERED' or 'RAW')
        
        Returns:
            Dict: The result from the API call
        
        Raises:
            HttpError: If there's an error writing to the sheet
        """
        try:
            body = {"values": values}
            result = (
                self.service.spreadsheets()
                .values()
                .update(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption=value_input_option,
                    body=body,
                )
                .execute()
            )
            return result
        except HttpError as error:
            raise HttpError(f"Error writing to sheet: {error}")
    
    def insert_row(self, spreadsheet_id: str, sheet_id: int, row_number: int, 
                   values: Optional[List[List[Any]]] = None) -> Dict:
        """
        Insert a new row at a specific position in the sheet.
        
        Args:
            spreadsheet_id (str): The ID of the spreadsheet
            sheet_id (int): The sheet ID (not the sheet name, but the numeric ID)
            row_number (int): The row number where to insert (1-based)
            values (Optional[List[List[Any]]]): Optional values to populate the new row
        
        Returns:
            Dict: The result from the API call
        
        Raises:
            HttpError: If there's an error inserting the row
        """
        try:
            # First, insert an empty row
            requests = [{
                "insertDimension": {
                    "range": {
                        "sheetId": sheet_id,
                        "dimension": "ROWS",
                        "startIndex": row_number - 1,  # Convert to 0-based
                        "endIndex": row_number  # Insert 1 row
                    },
                    "inheritFromBefore": False
                }
            }]
            
            body = {"requests": requests}
            result = (
                self.service.spreadsheets()
                .batchUpdate(spreadsheetId=spreadsheet_id, body=body)
                .execute()
            )
            
            # If values are provided, write them to the new row
            if values:
                # Determine the range for the new row (assuming we want to start from column A)
                num_columns = len(values[0]) if values and len(values) > 0 else 1
                end_column = chr(ord('A') + num_columns - 1)  # Convert to column letter
                range_name = f"A{row_number}:{end_column}{row_number}"
                
                self.write_to_sheet(spreadsheet_id, range_name, values)
            
            return result
        except HttpError as error:
            raise HttpError(f"Error inserting row: {error}")
    
    def get_sheet_id(self, spreadsheet_id: str, sheet_name: str) -> int:
        """
        Get the sheet ID (numeric) from the sheet name.
        
        Args:
            spreadsheet_id (str): The ID of the spreadsheet
            sheet_name (str): The name of the sheet
        
        Returns:
            int: The numeric sheet ID
        
        Raises:
            ValueError: If the sheet name is not found
            HttpError: If there's an error accessing the spreadsheet
        """
        try:
            spreadsheet = self.service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            sheets = spreadsheet.get('sheets', [])
            
            for sheet in sheets:
                if sheet['properties']['title'] == sheet_name:
                    return sheet['properties']['sheetId']
            
            raise ValueError(f"Sheet '{sheet_name}' not found in spreadsheet")
        except HttpError as error:
            raise HttpError(f"Error getting sheet ID: {error}")
    
    def get_column_names(self, spreadsheet_id: str, sheet_name: str, header_row: int = 1) -> Dict[str, str]:
        """
        Get column names from the header row and return a mapping of column names to column letters.
        
        Args:
            spreadsheet_id (str): The ID of the spreadsheet
            sheet_name (str): The name of the sheet
            header_row (int): The row number containing headers (1-based, default is 1)
        
        Returns:
            Dict[str, str]: Dictionary mapping column names to column letters
                           e.g., {'Name': 'A', 'Date': 'B', 'Amount': 'C'}
        
        Raises:
            HttpError: If there's an error reading the sheet
            ValueError: If the header row is empty or doesn't exist
        """
        try:
            # Read the header row
            range_name = f"{sheet_name}!{header_row}:{header_row}"
            values = self.read_sheet(spreadsheet_id, range_name)
            
            if not values or not values[0]:
                raise ValueError(f"Header row {header_row} is empty or doesn't exist")
            
            header_values = values[0]
            column_mapping = {}
            
            # Create mapping from column name to column letter
            for col_index, header_value in enumerate(header_values):
                if header_value:  # Skip empty headers
                    column_letter = self._index_to_column_letter(col_index)
                    column_mapping[str(header_value).strip()] = column_letter
            
            return column_mapping
            
        except HttpError as error:
            raise HttpError(f"Error getting column names: {error}")
    
    def _index_to_column_letter(self, index: int) -> str:
        """
        Convert a 0-based column index to a column letter (A, B, C, ..., Z, AA, AB, etc.).
        
        Args:
            index (int): 0-based column index
        
        Returns:
            str: Column letter(s)
        """
        result = ""
        while index >= 0:
            result = chr(index % 26 + ord('A')) + result
            index = index // 26 - 1
        return result


def insert_row_by_name(spreadsheet_id: str, sheet_name: str, row_number: int, 
                      values: Optional[List[List[Any]]] = None, 
                      service_account_file: str = 'servicecredentials.json') -> Dict:
    """
    Insert a new row at a specific position using the sheet name.
    
    Args:
        spreadsheet_id (str): The ID of the spreadsheet
        sheet_name (str): The name of the sheet (e.g., 'Blad1')
        row_number (int): The row number where to insert (1-based)
        values (Optional[List[List[Any]]]): Optional values to populate the new row
        service_account_file (str): Path to service account credentials
    
    Returns:
        Dict: The result from the insert operation
    
    Raises:
        ValueError: If the sheet name is not found
        HttpError: If there's an error with the Google Sheets API
    """
    sheets_manager = SheetsManager(service_account_file)
    
    # Get the sheet ID from the sheet name
    sheet_id = sheets_manager.get_sheet_id(spreadsheet_id, sheet_name)
    
    # Insert the row
    result = sheets_manager.insert_row(spreadsheet_id, sheet_id, row_number, values)
    
    #print(f"Inserted new row at position {row_number} in sheet '{sheet_name}'")
    #if values:
    #    print(f"Populated with values: {values}")
    
    return result


def update_sheet_by_search(spreadsheet_id: str, sheet_name: str, search_value: str, 
                          write_values: List[List[Any]], write_columns: str = 'E:G',
                          search_column: int = 0, service_account_file: str = 'servicecredentials.json') -> Dict:
    """
    Find a row by searching for a value and update specific columns in that row.
    This replicates the functionality of your original script.
    
    Args:
        spreadsheet_id (str): The ID of the spreadsheet
        sheet_name (str): The name of the sheet (e.g., 'Blad1')
        search_value (str): The value to search for
        write_values (List[List[Any]]): The values to write
        write_columns (str): The column range to write to (e.g., 'E:G')
        search_column (int): The column index to search in (0-based)
        service_account_file (str): Path to service account credentials
    
    Returns:
        Dict: The result from the write operation
    
    Raises:
        ValueError: If the search value is not found
        HttpError: If there's an error with the Google Sheets API
    """
    sheets_manager = SheetsManager(service_account_file)
    
    # Find the row containing the search value
    found_row = sheets_manager.find_row_by_value(
        spreadsheet_id, sheet_name, search_value, search_column
    )
    
    if found_row is None:
        raise ValueError(f"Value '{search_value}' not found in column {search_column}")
    
    # Create the write range (e.g., 'E5:G5' if found_row is 5)
    write_range = f"{write_columns.split(':')[0]}{found_row}:{write_columns.split(':')[1]}{found_row}"
    
    # Write the values
    result = sheets_manager.write_to_sheet(spreadsheet_id, write_range, write_values)
    
    #print(f"Found '{search_value}' in row {found_row}")
    #print(f"Updated range: {write_range}")
    #print(f"{result.get('updatedCells')} cells updated.")
    
    return result


# Example usage function that replicates your original script's behavior
def replicate_original_functionality():
    """
    Example function that replicates the exact behavior of your original script.
    """
    SPREADSHEET_ID = '1DJmUp6qd7gZxrlHdUcjwTA1pnDFES7iYq_GfAoyNkHE'
    SHEET_NAME = 'Blad1'
    SEARCH_VALUE = '59322291'
    WRITE_VALUES = [['X', '29-2-2024', -10]]
    
    try:
        result = update_sheet_by_search(
            spreadsheet_id=SPREADSHEET_ID,
            sheet_name=SHEET_NAME,
            search_value=SEARCH_VALUE,
            write_values=WRITE_VALUES,
            write_columns='E:G',
            search_column=0
        )
        return result
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


if __name__ == "__main__":
    # Run the original functionality when script is executed directly
    replicate_original_functionality()

