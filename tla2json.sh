#!/usr/bin/env bash
# tla2json.sh - Recursively convert all .tla files to .json
# Usage: ./tla2json.sh /path/to/search

set -euo pipefail

dir="$(realpath "${1:-.}")"

# Build a tilia CLI script using absolute paths
# (tilia changes cwd on boot, so relative paths won't resolve correctly)
script=""
count=0
while IFS= read -r tla; do
    json="${tla%.tla}.json"
    script+="clear --force
open \"${tla}\"
export \"${json}\" --overwrite
"
    count=$((count + 1))
done < <(find "$dir" -name '*.tla' -type f)

if [ "$count" -eq 0 ]; then
    echo "No .tla files found in '$dir'"
    exit 1
fi

script+="quit"

echo "Found $count .tla file(s). Converting..."

# Feed it into tilia's CLI
echo "$script" | python -m tilia.main -i cli

echo "Done. Converted $count file(s)."
