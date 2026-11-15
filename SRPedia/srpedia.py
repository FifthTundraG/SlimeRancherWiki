# SPDX-License-Identifier: MIT
#
# SlimeRancherWiki
# Copyright (c) 2026 FifthTundraG


# Generates a Lua module for the SR1 Slimepedia when provided
# with a pedia.txt extraction.
import argparse
import re

DEFAULT_OUTPUT_FILE = "output.lua"


def parse_pedia(filename):
    with open(filename, "r", encoding="utf-8") as f:
        content = f.read()

    # handle lines ending with \
    lines = content.splitlines()
    combined_lines = []
    current_line = ""

    for line in lines:
        if line.endswith("\\"):
            current_line += line[:-1] + "\n"
        else:
            current_line += line
            combined_lines.append(current_line)
            current_line = ""
    if current_line:
        combined_lines.append(current_line)

    entries = {}

    # parse titles (t.<key> = <title>)
    for line in combined_lines:
        line = line.strip()
        if line.startswith("t."):
            match = re.match(r"^t\.([^\s=]+)\s*=\s*(.*)$", line)
            if match:
                key, title = match.groups()
                if key not in entries:
                    entries[key] = {}
                entries[key]["title"] = title

    # parse metadata/fields (m.<field>.<key> = <value>)
    for line in combined_lines:
        line = line.strip()
        if line.startswith("m."):
            match = re.match(r"^m\.([^\s=]+)\s*=\s*(.*)$", line)
            if match:
                path_str, val = match.groups()
                parts = path_str.split(".")

                # Identify which part is the entry key
                entry_key = None
                key_idx = -1
                for i, part in enumerate(parts):
                    if part in entries:
                        entry_key = part
                        key_idx = i
                        break

                if entry_key:
                    field_parts = parts[:key_idx] + parts[key_idx+1:]

                    if not field_parts:
                        entries[entry_key]["value"] = val
                    else:
                        # Build nested dictionary structure safely
                        curr = entries[entry_key]
                        for fp in field_parts[:-1]:
                            if fp not in curr:
                                curr[fp] = {}
                            elif isinstance(curr[fp], str):
                                # Convert string node to a dict if it needs children
                                old_val = curr[fp]
                                curr[fp] = {"value": old_val}
                            curr = curr[fp]

                        last_fp = field_parts[-1]
                        if isinstance(curr.get(last_fp), dict):
                            curr[last_fp]["value"] = val
                        else:
                            curr[last_fp] = val

    return entries

def dict_to_lua(d, indent=2):
    """Recursively converts a Python dictionary to a Lua table string format."""
    lines = ["{"]
    ind = " " * indent
    for k, v in d.items():
        key_str = f"  {ind}[\"{k}\"] = "
        if isinstance(v, dict):
            sub_str = dict_to_lua(v, indent + 2)
            lines.append(f"{key_str}{sub_str},")
        else:
            val_str = str(v).replace('"', '\\"')
            lines.append(f'{key_str}\"{val_str}\",')
    lines.append(" " * (indent - 2) + "}")
    return "\n".join(lines)

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "file",
        nargs="?",
        default="pedia.txt",
        help="Input file (default: pedia.txt)"
    )

    parser.add_argument(
        "-o", "--output",
        default=DEFAULT_OUTPUT_FILE,
        help=f"Output file (default: {DEFAULT_OUTPUT_FILE})"
    )

    args = parser.parse_args()

    
    parsed_data = parse_pedia(args.file)

    lua_output = "return " + dict_to_lua(parsed_data)
    
    with open(DEFAULT_OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(lua_output)
        
    print(f"Parsing complete! Output saved to {DEFAULT_OUTPUT_FILE}")

if __name__ == "__main__":
    main()
