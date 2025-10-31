"""
Business logic for Google Sheets operations.
Handles all sheet-related operations for bag management.
"""
from typing import List, Dict, Optional
from sheetsmanager import SheetsManager, insert_row_by_name


class SheetService:
    """Service class for Google Sheets operations."""
    
    def __init__(self, credentials_file: str = 'servicecredentials.json'):
        """
        Initialize the sheet service.
        
        Args:
            credentials_file: Path to Google service account credentials
        """
        self.credentials_file = credentials_file
        self.sheets_manager = SheetsManager(credentials_file)
    
    def update_bags_in_sheet(self, spreadsheet_id: str, sheet_name: str, 
                            processing_date: str, bags: List[Dict]) -> Dict[str, any]:
        """
        Update or insert multiple bags in the Google Sheet.
        
        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            sheet_name: Name of the sheet to update
            processing_date: Date to mark as processing date
            bags: List of bag dictionaries with 'id' and 'amount'
            
        Returns:
            Dictionary with success status and message
        """
        try:
            columns = self.sheets_manager.get_column_names(spreadsheet_id, sheet_name)
            
            # Validate required columns
            required_columns = ['Zaknummer', 'Verwerkt', 'Verwerkingsdatum', 'Bedrag']
            missing_columns = [col for col in required_columns if col not in columns]
            
            if missing_columns:
                return {
                    'success': False,
                    'message': f"Missing required columns: {', '.join(missing_columns)}"
                }
            
            zaknummer_col_index = ord(columns['Zaknummer']) - ord('A')
            
            updated_count = 0
            inserted_count = 0
            errors = []
            
            for bag in bags:
                try:
                    result = self._update_or_insert_bag(
                        spreadsheet_id, sheet_name, bag, 
                        processing_date, zaknummer_col_index
                    )
                    
                    if result['action'] == 'updated':
                        updated_count += 1
                    elif result['action'] == 'inserted':
                        inserted_count += 1
                        
                except Exception as e:
                    errors.append(f"Bag {bag['id']}: {str(e)}")
            
            if errors:
                return {
                    'success': False,
                    'message': f"Errors occurred: {'; '.join(errors)}",
                    'updated': updated_count,
                    'inserted': inserted_count
                }
            
            return {
                'success': True,
                'message': f"Successfully processed {len(bags)} bags ({updated_count} updated, {inserted_count} inserted)",
                'updated': updated_count,
                'inserted': inserted_count
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"Error accessing sheet: {str(e)}"
            }
    
    def _update_or_insert_bag(self, spreadsheet_id: str, sheet_name: str, 
                             bag: Dict, processing_date: str, 
                             zaknummer_col_index: int) -> Dict:
        """
        Update existing bag or insert new one.
        
        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            sheet_name: Name of the sheet
            bag: Bag dictionary with 'id' and 'amount'
            processing_date: Processing date
            zaknummer_col_index: Column index for bag number
            
        Returns:
            Dictionary with action taken ('updated' or 'inserted')
        """
        row_num = self.sheets_manager.find_row_by_value(
            spreadsheet_id, sheet_name, bag['id'], zaknummer_col_index
        )
        
        if row_num is not None:
            # Update existing row
            self.sheets_manager.write_to_sheet(
                spreadsheet_id,
                f'E{row_num}:G{row_num}',
                [['X', processing_date, bag['amount']]]
            )
            return {'action': 'updated', 'row': row_num}
        else:
            # Insert new row
            position = self._find_insert_position(
                spreadsheet_id, sheet_name, bag['id'], zaknummer_col_index
            )
            
            insert_row_by_name(
                spreadsheet_id,
                sheet_name,
                row_number=position,
                values=[[bag['id'], '', '', '', 'X', processing_date, bag['amount']]],
                service_account_file=self.credentials_file
            )
            return {'action': 'inserted', 'row': position}
    
    def _find_insert_position(self, spreadsheet_id: str, sheet_name: str, 
                             target_id: str, col_index: int) -> int:
        """
        Find the correct position to insert a new bag based on numeric sorting.
        
        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            sheet_name: Name of the sheet
            target_id: Bag ID to insert
            col_index: Column index to search
            
        Returns:
            Row number where to insert (1-based)
        """
        try:
            all_data = self.sheets_manager.read_sheet(spreadsheet_id, sheet_name)
            
            # Skip header row and find insertion position
            for row_idx, row in enumerate(all_data[1:], start=2):
                if len(row) > col_index and row[col_index]:
                    try:
                        current_id = int(row[col_index])
                        target_id_int = int(target_id)
                        
                        if current_id > target_id_int:
                            return row_idx
                            
                    except (ValueError, TypeError):
                        # Fallback to string comparison
                        if row[col_index] > target_id:
                            return row_idx
            
            # Insert at the end if no higher value found
            return len(all_data) + 1
            
        except Exception as e:
            print(f"Warning: Error finding insert position: {str(e)}")
            try:
                all_data = self.sheets_manager.read_sheet(spreadsheet_id, sheet_name)
                return len(all_data) + 1
            except:
                return 2  # Default to row 2
    
    def register_bag(self, spreadsheet_id: str, sheet_name: str, 
                    bag_id: str, source: str, bag_type: str, date: str) -> Dict:
        """
        Register a new bag in the sheet.
        
        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            sheet_name: Name of the sheet
            bag_id: Bag identification number
            source: Source of the bag
            bag_type: Type of bag
            date: Registration date
            
        Returns:
            Dictionary with success status and message
        """
        try:
            columns = self.sheets_manager.get_column_names(spreadsheet_id, sheet_name)
            zaknummer_col_index = ord(columns['Zaknummer']) - ord('A')
            afgiftedatum_col_index = ord(columns['Afgiftedatum']) - ord('A')
            
            # Check if bag already exists
            # TODO: fix search, it does not work
            existing_row = self.sheets_manager.find_row_by_value(
                spreadsheet_id, sheet_name, bag_id, zaknummer_col_index
            )
            
            if existing_row:
                return {
                    'success': False,
                    'message': f"Bag {bag_id} already exists in row {existing_row}"
                }
            
            # Find insert position
            #position = self._find_insert_position(
            #    spreadsheet_id, sheet_name, bag_id, zaknummer_col_index
            #)
            position = self._find_insert_position(
                spreadsheet_id, sheet_name, date, afgiftedatum_col_index
            )
            
            # Insert new row with registration data
            insert_row_by_name(
                spreadsheet_id,
                sheet_name,
                row_number=position,
                values=[[bag_id, source, bag_type, date, '', '', '']],
                service_account_file=self.credentials_file
            )
            
            return {
                'success': True,
                'message': f"Bag {bag_id} registered successfully at row {position}"
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"Error registering bag: {str(e)}"
            }
