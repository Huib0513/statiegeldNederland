"""
Business logic for bag processing operations.
Handles CHR file processing and bag management.
"""
from typing import List, Dict, Tuple
from collections import defaultdict


class BagService:
    """Service class for bag-related business logic."""
    
    @staticmethod
    def process_chr_content(content: str) -> Tuple[int, List[Dict], float, str]:
        """
        Process CHR file content and extract bag information.
        
        Args:
            content: Raw content from CHR file
            
        Returns:
            Tuple containing:
                - processed_lines: Number of lines processed
                - bags: List of bag dictionaries with 'id' and 'amount'
                - total_money: Total amount from all bags
                - processing_date: Date from the file
                
        Raises:
            ValueError: If file format is invalid
        """
        try:
            lines = content.split('\n')
            
            if not lines:
                raise ValueError("Empty file content")
            
            processing_date = lines[0].split(';')[7]
            
            processed_lines = 0
            bags_dict = defaultdict(float)
            total_money = 0.0
            
            for line in lines:
                if line.strip():  # Skip empty lines
                    processed_lines += 1
                    values = line.split(';')
                    
                    # Skip lines where column 8 has '50' after first character
                    if len(values) > 10 and values[8][1:] != '50':
                        bag_id = values[5]
                        amount = float(values[10].replace(',', '.'))
                        
                        bags_dict[bag_id] += amount
                        total_money += amount
            
            # Convert to list of dictionaries
            processed_bags = [
                {'id': bag_id, 'amount': amount}
                for bag_id, amount in bags_dict.items()
            ]
            
            return processed_lines, processed_bags, total_money, processing_date
            
        except (IndexError, ValueError) as e:
            raise ValueError(f"Invalid CHR file format: {str(e)}")
    
    @staticmethod
    def validate_bag_data(bag_id: str, source: str, bag_type: str, date: str) -> Dict[str, str]:
        """
        Validate bag registration data.
        
        Args:
            bag_id: Bag identification number
            source: Source of the bag
            bag_type: Type of bag (mini/small)
            date: Registration date
            
        Returns:
            Dictionary of validation errors (empty if valid)
        """
        errors = {}
        
        if not bag_id or not bag_id.strip():
            errors['bag_id'] = "Bag ID is required"
        
        if not source or not source.strip():
            errors['source'] = "Source is required"
        
        if bag_type not in ['Mini', 'Small']:
            errors['bag_type'] = "Invalid bag type"
        
        if not date:
            errors['date'] = "Date is required"
        
        return errors
