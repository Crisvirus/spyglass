#!/bin/bash
is_day()
{
    full_sunrise=$(sunrise --long 5.12 --lat 52.09 | tail -n2 | head -n 1)
    sunrise=$(echo $full_sunrise | cut -d ' ' -f2)
    sunset=$(echo $full_sunrise | cut -d ' ' -f4)
    currenttime=$(date +%H:%M:%S)
    if [[ "$currenttime" > "$sunset" ]] || [[ "$currenttime" < "$sunrise" ]]; then
        now="night"
    else
        now="day"
    fi
    last=$(cat /home/pi/day.txt)
    if [[ "$now" != "$last" ]]; then
        echo "$now">/home/pi/day.txt
        sudo systemctl restart camera.service
    fi
}

is_day