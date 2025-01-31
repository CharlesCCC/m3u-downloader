import re
import argparse
from pathlib import Path

def extract_categories(m3u_file):
    category_pattern = re.compile(r'\[(.*?)\]')
    categories = set()

    with open(m3u_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('#EXTINF'):
                match = category_pattern.search(line)
                if match:
                    categories.add(match.group(1))
    
    print("Unique categories found:")
    for category in sorted(categories):
        print(f"- {category}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract unique categories from M3U file')
    parser.add_argument('input_file', type=Path, help='Path to M3U file')
    args = parser.parse_args()
    
    extract_categories(args.input_file) 