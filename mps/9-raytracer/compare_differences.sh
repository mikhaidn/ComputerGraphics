#!/bin/bash

# Initialize an empty array to store temporary difference files
temp_files=()

# Loop through all PNG files in the current directory
for file in *.png; do
    # Check if the file exists in the reference directory
    if [ -f "reference/ray-$file" ]; then
        # Create a temporary file for the difference
        temp_diff=$(mktemp)
        temp_files+=("$temp_diff")
        
        # Compare the current file with its reference counterpart
        compare -fuzz 3% -metric AE "$file" "reference/ray-$file" "$temp_diff" 2>/dev/null
        
        echo "Processed $file"
    else
        echo "Warning: No reference file found for $file"
    fi
done

# Combine all temporary difference files into one
montage "${temp_files[@]}" -geometry +0+0 -tile 1x differences.png

# Clean up temporary files
rm "${temp_files[@]}"

echo "All differences combined in differences.png"