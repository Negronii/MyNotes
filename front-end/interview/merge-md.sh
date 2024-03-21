#!/bin/bash

# define the output file
output="All-In-One.md"

# delete the output file if it exists
rm -f $output

# merge all markdown files into the output file
for file in *.md; do
    # skip the output file
    if [[ $file != $output ]]; then
        echo -e "\n# $file\n" >> $output
        cat $file >> $output
    fi
done

# see if the output file has changed
if ! git diff --quiet -- $output; then
    # add the output file to the staging area
    git add $output

    # commit the output file
    git commit -m "Automatically merged Markdown files into $output"
fi
