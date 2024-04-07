#!/bin/bash

# Define the output file and temporary file
output="Interview-All-In-One.md"
temp="temp.md"

# Delete the output file if it exists
rm -f "$output"

# Use find to safely handle filenames with spaces
# Concatenate the content of each markdown file into the output file
find . -maxdepth 1 -name '*.md' ! -name "$output" ! -name "$temp" -print0 | while IFS= read -r -d '' file; do
    echo -e "\n# $(basename "$file")\n" >> "$output"
    cat "$file" >> "$output"
done

# Check if there have been any changes
if ! git diff --quiet; then
    # Add the output file to the staging area
    git add "$output"

    # Commit the changes
    git commit -m "Automatically merged Markdown files into $output"
fi
