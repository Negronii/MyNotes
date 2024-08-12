#!/bin/bash

# Define the output file and temporary file
output="Interview-All-In-One.md"
temp="temp.md"

# Delete the output file if it exists
rm -f "$output"

# Use find to get the list of markdown files, excluding the ones we don't want,
# and then sort them. We use a custom sort with awk to handle filenames numerically.
filelist=$(find . -maxdepth 1 -name '*.md' ! -name "$output" ! -name "$temp" \
  | awk -F'[/.]' '{ printf "%05d%05d %s\n", $2, ($3==""?0:$3), $0 }' \
  | sort -k1,1n \
  | cut -d' ' -f2-)

# Process each file
echo "$filelist" | while IFS= read -r file; do
    filename=$(basename "$file" .md)

    # Check if the filename is a main topic or a subtopic
    if [[ $filename =~ ^[0-9]+(\.[0-9]+)?\ .*$ ]]; then
        # Main topic
        if [[ $filename =~ ^[0-9]+\ .*$ ]]; then
            echo -e "\n# $filename\n" >> "$output"
        # Subtopic
        elif [[ $filename =~ ^[0-9]+\.[0-9]+\ .*$ ]]; then
            echo -e "\n## $filename\n" >> "$output"
        fi
    else
        # If the filename doesn't match the pattern, treat it as a main topic
        echo -e "\n# $filename\n" >> "$output"
    fi

    # Read the file line by line
    while IFS= read -r line; do
        # Check if the line is a header
        if [[ $line =~ ^# ]]; then
            # Increment the header level by 1
            echo "${line/#/#}" >> "$output"
        else
            echo "$line" >> "$output"
        fi
    done < "$file"
done

# Check if there have been any changes
if ! git diff --quiet; then
    # Add the output file to the staging area
    git add "$output"

    # Commit the changes
    git commit -m "Automatically merged Markdown files into $output"
fi
