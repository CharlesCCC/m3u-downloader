import re
import argparse

def filter_m3u(input_file, categories, output_file):
    """Filter M3U entries by specified categories while preserving original format"""
    category_list = [c.strip() for c in categories.split(',')]
    pattern = re.compile(r'\[(.*?)\]')
    
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    headers = []
    filtered_entries = []
    in_header = True
    current_entry = []
    category_match = False

    for line in lines:
        # Preserve header section
        if in_header:
            if line.startswith('#EXTINF'):
                in_header = False
            else:
                headers.append(line)
                continue
        
        # Process entries
        if line.startswith('#EXTINF'):
            # Check previous entry completion
            if current_entry:
                if category_match:
                    filtered_entries.extend(current_entry)
                current_entry = []
                category_match = False
            
            # Check category match
            match = pattern.search(line)
            current_entry.append(line)
            if match and match.group(1) in category_list:
                category_match = True
        else:
            current_entry.append(line)

    # Add the last entry if matched
    if category_match and current_entry:
        filtered_entries.extend(current_entry)

    # Write output with original formatting
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(headers)
        f.writelines(filtered_entries)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Filter M3U file by categories')
    parser.add_argument('input_file', help='Input M3U file path')
    parser.add_argument('categories', help='Comma-separated list of categories to filter')
    parser.add_argument('output_file', help='Output M3U file path')
    args = parser.parse_args()
    
    filter_m3u(args.input_file, args.categories, args.output_file) 