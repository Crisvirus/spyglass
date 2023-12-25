#!/bin/bash
is_day()
{
    full_sunrise=$(sunrise --long 5.12 --lat 52.09 | tail -n2 | head -n 1)
    sunrise=$(echo $full_sunrise | cut -d ' ' -f2)
    sunset=$(echo $full_sunrise | cut -d ' ' -f4)
    currenttime=$(date +%H:%M:%S)
    if [[ "$currenttime" > "$sunset" ]] || [[ "$currenttime" < "$sunrise" ]]; then
        echo "night">/home/pi/day.txt
    else
        echo "day">/home/pi/day.txt
    fi
}

is_day