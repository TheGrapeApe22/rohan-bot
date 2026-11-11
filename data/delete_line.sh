#!/usr/bin/env bash

data_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
sqlite3 "$data_dir/david_lines.sqlite3" "DELETE FROM david_lines WHERE line = '$1';"
