#!/bin/bash

# Define the output file and temporary file
output="Interview-All-In-One.md"
temp="temp.md"

# Delete the output file if it exists
rm -f "$output"

# Initialize a variable to track the current main topic
current_main_topic=""

# Use find to get the list of markdown files, excluding the ones we don't want,
# and then sort them. We use 'sort -V' for natural sorting, which handles the numerical sorting nicely.
find . -maxdepth 1 -name '*.md' ! -name "$output" ! -name "$temp" -print0 | sort -zV | while IFS= read -r -d '' file; do
    filename=$(basename "$file" .md)

    # Check if the filename is a main topic or a subtopic
    if [[ $filename =~ ^[0-9]+(\.[0-9]+)?\ .*$ ]]; then
        # Main topic
        if [[ $filename =~ ^[0-9]+\ .*$ ]]; then
            current_main_topic="$filename"
            echo -e "\n# $current_main_topic\n" >> "$output"
        # Subtopic
        elif [[ $filename =~ ^[0-9]+\.[0-9]+\ .*$ ]]; then
            echo -e "\n## $filename\n" >> "$output"
        fi
    else
        # If the filename doesn't match the pattern, treat it as a main topic
        current_main_topic="$filename"
        echo -e "\n# $current_main_topic\n" >> "$output"
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
