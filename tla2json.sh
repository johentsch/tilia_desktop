#!/usr/bin/env bash
# tla2json.sh - Recursively convert all .tla files to .json
# Usage: ./tla2json.sh IN_DIR [OUT_DIR]
#
# Without OUT_DIR: .json files are created next to each .tla file.
# With OUT_DIR:    .json files are created under OUT_DIR, mirroring
#                  the subfolder hierarchy relative to IN_DIR.
#                  e.g. IN_DIR/sub/file.tla -> OUT_DIR/sub/file.json

set -euo pipefail

in_dir="$(realpath "${1:-.}")"
out_dir="${2:-}"

if [ -n "$out_dir" ]; then
    out_dir="$(realpath -m "$out_dir")"
fi

# Build a tilia CLI script using absolute paths
# (tilia changes cwd on boot, so relative paths won't resolve correctly)
script=""
count=0
while IFS= read -r tla; do
    if [ -n "$out_dir" ]; then
        # Mirror the relative path under out_dir
        rel="${tla#"$in_dir"/}"
        json="${out_dir}/${rel%.tla}.json"
        mkdir -p "$(dirname "$json")"
    else
        json="${tla%.tla}.json"
    fi
    script+="clear --force
open \"${tla}\"
export \"${json}\" --overwrite
"
    count=$((count + 1))
done < <(find "$in_dir" -name '*.tla' -type f)

if [ "$count" -eq 0 ]; then
    echo "No .tla files found in '$in_dir'"
    exit 1
fi

script+="quit"

echo "Found $count .tla file(s). Converting..."

# Feed it into tilia's CLI
echo "$script" | python -m tilia.main -i cli

echo "Done. Converted $count file(s)."
