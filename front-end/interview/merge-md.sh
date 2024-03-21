#!/bin/bash

# set filename for the big md file
output="All-In-One.md"

# rm old file
rm -f $output

# merge all md files
for file in *.md; do
    # skip the output file
    if [[ $file != $output ]]; then
        echo -e "\n# $file\n" >> $output
        cat $file >> $output
    fi
done

# add to git
git add $output
