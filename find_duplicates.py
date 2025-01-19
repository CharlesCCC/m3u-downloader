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
                        'url': url.strip()
                    })
                except ValueError:
                    print(f"Warning: Invalid format at line {line_num}: {line}")
                    continue
        
        # Write duplicates to output file in name,url format
        with open(output_file, 'w', encoding='utf-8') as f:
            for name, occurrences in filename_occurrences.items():
                if len(occurrences) > 1:  # Only write duplicates
                    for occurrence in occurrences:
                        f.write(f"{name},{occurrence['url']}\n")
        
        # Print summary
        duplicate_count = sum(1 for occurrences in filename_occurrences.values() if len(occurrences) > 1)
        if duplicate_count > 0:
            print(f"Found {duplicate_count} duplicated filenames. Results saved to: {output_file}")
        else:
            print("No duplicates found.")
            # Remove output file if it's empty
            try:
                import os
                os.remove(output_file)
            except:
                pass
            
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