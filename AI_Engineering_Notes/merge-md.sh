#!/bin/bash

output="Interview-All-In-One.md"
temp="temp.md"

rm -f "$output"

filelist=$(find . -maxdepth 1 -name '*.md' ! -name "$output" ! -name "$temp" \
  | awk -F'[/.]' '{ printf "%05d%05d %s\n", $2, ($3==""?0:$3), $0 }' \
  | sort -k1,1n \
  | cut -d' ' -f2-)

echo "$filelist" | while IFS= read -r file; do
    filename=$(basename "$file" .md)

    if [[ $filename =~ ^[0-9]+(\.[0-9]+)?\ .*$ ]]; then
        if [[ $filename =~ ^[0-9]+\ .*$ ]]; then
            echo -e "\n# $filename\n" >> "$output"
        elif [[ $filename =~ ^[0-9]+\.[0-9]+\ .*$ ]]; then
            echo -e "\n## $filename\n" >> "$output"
        fi
    else
        echo -e "\n# $filename\n" >> "$output"
    fi

    while IFS= read -r line; do
        if [[ $line =~ ^# ]]; then
            echo "${line/#/#}" >> "$output"
        else
            echo "$line" >> "$output"
        fi
    done < "$file"
done

if ! git diff --quiet; then
    git add "$output"
    git commit -m "Automatically merged Markdown files into $output"
fi
