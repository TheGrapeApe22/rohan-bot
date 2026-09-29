#!/usr/bin/env bash

sqlite3 david_lines.sqlite3 "DELETE FROM david_lines WHERE line = '$1';"