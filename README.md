# Run with 3 concurrent downloads (default)
`python m3u_downloader_script.py input_file.txt`

# Run with 5 concurrent downloads
`python m3u_downloader_script.py input_file.txt -w 5`


# input_file.txt format

```
filename1, URL.m3u
filename2, URL.m3u
filename3, URL.m3u
```

# New script for processing .m3u files
python m3u_parser_downloader.py your_playlist.m3u -w 5

# New script for filtering .m3u files
python filter_m3u.py input_file.m3u "category1, category2, category3" output_file.m3u

# New script for extracting categories from .m3u files
python extract_categories.py input_file.m3u

# New script for splitting .m3u files by category
python split_m3u_by_category.py input_file.m3u

