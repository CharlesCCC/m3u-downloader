#!/usr/bin/env python3
import sys
from collections import defaultdict
import argparse
from datetime import datetime

def find_duplicates(input_file, output_file=None):
    # If no output file specified, create one with timestamp
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"duplicates_{timestamp}.txt"
    
    # Dictionary to store filename occurrences with line numbers and URLs
    filename_occurrences = defaultdict(list)
    
    try:
        # Read input file
        with open(input_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    name, url = line.split(',', 1)
                    filename_occurrences[name].append({
                        'line_number': line_num,
                        'url': url
                    })
                except ValueError:
                    print(f"Warning: Invalid format at line {line_num}: {line}")
                    continue
        
        # Write results to output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Duplicate Check Results for: {input_file}\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("-" * 80 + "\n\n")
            
            found_duplicates = False
            for name, occurrences in filename_occurrences.items():
                if len(occurrences) > 1:
                    found_duplicates = True
                    f.write(f"Duplicate found: '{name}'\n")
                    f.write("Occurrences:\n")
                    for occurrence in occurrences:
                        f.write(f"  Line {occurrence['line_number']}: {occurrence['url']}\n")
                    f.write("\n")
            
            if not found_duplicates:
                f.write("No duplicates found in the file.\n")
        
        print(f"Results have been saved to: {output_file}")
            
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Find duplicate filenames in a text file')
    parser.add_argument('input_file', help='Input file containing names and URLs (format: name,url)')
    parser.add_argument('-o', '--output', help='Output file path (optional, default: duplicates_TIMESTAMP.txt)')
    
    args = parser.parse_args()
    find_duplicates(args.input_file, args.output) 