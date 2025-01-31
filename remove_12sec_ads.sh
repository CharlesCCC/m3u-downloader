#!/bin/bash

# Create the output directory if it doesn't exist
mkdir -p processed

# Loop through all MP4 files in the source directory
for file in "18+yutu-500-8th-ads"/*.mp4; do
    # Get just the filename without the path
    filename=$(basename "$file")
    
    # Process the file with ffmpeg
    ffmpeg -i "$file" -ss 12 -c copy "processed/$filename"
done

echo "Processing complete! Check the 'processed' folder."