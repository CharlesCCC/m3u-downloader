import re
import argparse
from collections import defaultdict

def split_m3u_by_category(input_file):
    """Split M3U file into category-specific files with original formatting"""
    pattern = re.compile(r'\[(.*?)\]')
    headers = []
    entries = defaultdict(list)
    current_category = None
    current_entry = []
    in_header = True

    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            # Preserve header section
            if in_header:
                if line.startswith('#EXTINF'):
                    in_header = False
                else:
                    headers.append(line)
                    continue
            
            # Process entries
            if line.startswith('#EXTINF'):
                # Save previous entry
                if current_entry and current_category:
                    entries[current_category].extend(current_entry)
                
                # Start new entry
                current_entry = [line]
                match = pattern.search(line)
                current_category = match.group(1) if match else None
            else:
                if current_category:  # Only collect entries with valid categories
                    current_entry.append(line)

    # Write output files
    for category, lines in entries.items():
        # Sanitize filename and preserve Chinese characters
        safe_name = re.sub(r'[\\/*?:"<>|]', '_', category)
        filename = f"{safe_name}.m3u"
        
        with open(filename, 'w', encoding='utf-8', newline='') as f:
            f.writelines(headers)
            f.writelines(lines)
            if lines[-1][-1] != '\n':  # Ensure proper line ending
                f.write('\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Split M3U file into category-specific files')
    parser.add_argument('input_file', help='Input M3U file path')
    args = parser.parse_args()
    
    split_m3u_by_category(args.input_file) 