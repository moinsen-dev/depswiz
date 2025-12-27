#!/bin/bash

# Default dependency section
DEPENDENCY_SECTION="dependencies"

# Help function
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo "Check for package updates in pyproject.toml"
    echo
    echo "Options:"
    echo "  -s, --section NAME    Specify the dependency section to check (default: dependencies)"
    echo "  -h, --help           Show this help message"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -s|--section)
            DEPENDENCY_SECTION="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Check if pyproject.toml exists
if [ ! -f "pyproject.toml" ]; then
  echo "Error: pyproject.toml file not found!"
  exit 1
fi

# Initialize arrays to store package information
declare -a package_names=()
declare -a current_versions=()
declare -a latest_versions=()
declare -a has_updates=()
declare -a package_extras=()

# Initialize update flag
updates_available=false

# Extract package names and versions from pyproject.toml
packages=$(awk -v section="$DEPENDENCY_SECTION" '
    $0 ~ section" = \\[" {
        in_section = 1
        next
    }
    in_section && /^]/ {
        in_section = 0
        next
    }
    in_section && $0 ~ /^    ".*>=.*"/ {
        gsub(/[",]/, "")
        gsub(/^    /, "")
        print $0
    }
' pyproject.toml)

# Check if any packages were found
if [ -z "$packages" ]; then
  echo "No packages found in section '$DEPENDENCY_SECTION' in pyproject.toml."
  exit 0
fi

# Function to get the latest version from PyPI
get_latest_version() {
  package_name=$1
  response=$(curl -s "https://pypi.org/pypi/${package_name}/json")
  if [ $? -ne 0 ]; then
    return 1
  fi
  latest_version=$(echo "$response" | grep -o '"version":"[^"]*"' | head -1 | cut -d'"' -f4)
  echo "$latest_version"
}

# Check each package for updates
echo "Checking for package updates in section '$DEPENDENCY_SECTION'..."
echo

index=0
while IFS= read -r package; do
  # Extract package name and specified version using parameter expansion
  full_package_name=${package%>=*}
  current_version=${package#*>=}

  # Handle packages with extras
  base_package=${full_package_name%\[*}
  extras=""
  if [ "$base_package" != "$full_package_name" ]; then
    extras=${full_package_name#*\[}
    extras=${extras%\]}
    package_name=$base_package
  else
    package_name=$full_package_name
  fi

  # Get the latest version from PyPI
  latest_version=$(get_latest_version "$package_name")

  if [ -z "$latest_version" ]; then
    echo "Could not retrieve information for package: $package_name"
    continue
  fi

  # Store package information
  package_names[$index]=$package_name
  current_versions[$index]=$current_version
  latest_versions[$index]=$latest_version
  package_extras[$index]=$extras

  # Compare versions and store update status
  if [ "$current_version" != "$latest_version" ]; then
    has_updates[$index]=1
    updates_available=true
    echo "Update available for $package_name: Specified: $current_version, Latest: $latest_version"
  else
    has_updates[$index]=0
    echo "$package_name is up to date (Version: $current_version)."
  fi

  ((index++))
done <<< "$packages"

echo
echo "Done checking for package updates."

# Only ask for updates if there are actually updates available
if [ "$updates_available" = true ]; then
  echo
  read -p "Would you like to update pyproject.toml with the latest versions? (y/N) " -n 1 -r
  echo

  if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Updating pyproject.toml..."

    # Create a temporary file
    temp_file=$(mktemp)

    # Create a package data file for awk to read
    pkg_data_file=$(mktemp)
    for i in "${!package_names[@]}"; do
      if [ -n "${package_extras[$i]}" ]; then
        echo "${package_names[$i]}[${package_extras[$i]}] ${latest_versions[$i]}" >> "$pkg_data_file"
      else
        echo "${package_names[$i]} ${latest_versions[$i]}" >> "$pkg_data_file"
      fi
    done

    # Process the file and update versions
    awk -v pkg_data="$pkg_data_file" -v section="$DEPENDENCY_SECTION" '
    BEGIN {
      # Read package data into an associative array
      while ((getline line < pkg_data) > 0) {
        split(line, parts, " ")
        package_data[parts[1]] = parts[2]
      }
      close(pkg_data)
      in_section = 0
    }
    $0 ~ section" = \\[" { in_section = 1; print; next }
    /^]/ && in_section { in_section = 0; print; next }
    {
      if (in_section && $0 ~ /^    ".*>=.*"/) {
        # Extract the full package specification
        match($0, /"([^"]+)>=/)
        pkg = substr($0, RSTART+1, RLENGTH-3)
        if (pkg in package_data) {
          # Preserve the trailing comma if it exists
          has_comma = ($0 ~ /,\s*$/)
          printf "    \"%s>=%s\"%s\n", pkg, package_data[pkg], (has_comma ? "," : "")
        } else {
          print
        }
      } else {
        print
      }
    }' pyproject.toml > "$temp_file"

    # Replace original with updated content
    mv "$temp_file" pyproject.toml

    # Clean up temporary package data file
    rm -f "$pkg_data_file"

    echo "pyproject.toml has been updated"

    # Ask user if they want to run uv lock --upgrade
    echo
    read -p "Would you like to run 'uv lock --upgrade' to update the lockfile? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      echo "Running uv lock --upgrade..."
      uv lock --upgrade
      uv sync
      uv pip compile pyproject.toml -o requirements.txt
      if [ $? -eq 0 ]; then
        echo "Successfully updated lockfile"
      else
        echo "Error updating lockfile"
        exit 1
      fi
    else
      echo "Skipping lockfile update"
    fi
  else
    echo "No changes were made to pyproject.toml"
  fi
else
  echo "All packages are up to date!"
fi
