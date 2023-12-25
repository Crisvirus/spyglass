#!/bin/bash
#rpicam-vid -n -t 0 --inline -o - --width 1920 --height 1080 --framerate 50 | cvlc stream:///dev/stdin --sout '#rtp{sdp=rtsp://:8554/stream1}' :demux=h264 --h264-fps=50

is_day()
{
    day=$(cat /home/pi/day.txt)
    if [[ "$day" = "day" ]]; then
        return 0
    else
        return 1
    fi
}


if is_day; then
    filter=imx708_wide_noir.json
else
    filter=imx708_wide_noir_night.json
    EXTRA_PARAMS="-n"
fi
echo $filter
/home/pi/spyglass/run.py -r 2304x1296 -f 50 -af manual -l 0 -tf /usr/share/libcamera/ipa/rpi/vc4/$filter $EXTRA_PARAMS