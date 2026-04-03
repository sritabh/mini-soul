#!/bin/bash

DEVICE="/dev/cu.usbmodem101"

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --device|-d) DEVICE="$2"; shift ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

IGNORE=(sim tdoc README.md flash.sh)

echo "Flashing to device: $DEVICE"

for item in *; do
    skip=false
    for ignored in "${IGNORE[@]}"; do
        if [[ "$item" == "$ignored" ]]; then
            skip=true
            break
        fi
    done

    if $skip; then
        echo "Skipping: $item"
        continue
    fi

    echo "Copying: $item"
    mpremote connect "$DEVICE" cp -r "./$item" :
done

echo "Done."
