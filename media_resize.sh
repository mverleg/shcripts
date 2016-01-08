#!/usr/bin/env bash

# without changing the actual image, make the size smaller
alias minipng='echo "use -c NR to remove color or alpha"; pngcrush -brute -e ".crush.png" -l 9'

# resizes largest dimension to 1024 and places in ./resized/
alias jpgresize='mkdir -p resized; mogrify -path "$(pwd)/resized" -resize 1024x1024 *.jpg; jhead -purejpg -norot resized/*.jpg'

#	usage in video dir: mp4trim *
function mp4trim () {
	for fn in "$@"; do
		if [[ $file =~ \.mp4$ ]]; then
			echo "$fn: not a video?";
			continue;
		fi
		avflags="";
		res="$(avprobe "$fn" 2>&1 | grep -o ' [0-9]\+x[0-9]\+' | cut -d x -f 1 | grep -v '^\s*0\s*')"
		if [[ "$res" -gt "640" ]]; then 
			echo "$fn: reducing resolution";
			avflags="$avflags -vf scale='400:trunc(ow/a/2)*2'";
		fi;
		dr="$(avprobe "$fn" 2>&1 | grep -o 'Duration: [0-9]\+:[0-9]\+:[0-9]\+')";
		ds="$(bc -l <<< "$(cut -d ':' -f 2 <<< $dr)*3600 + $(cut -d ':' -f 3 <<< $dr)*60 + $(cut -d ':' -f 4 <<< $dr)")"
		if [[ "$ds" -gt "900" ]]; then 
			echo "$fn: cutting duration";
			avflags="$avflags -ss 00:00:00 -t 00:12:00";
		fi;
		if [[ $avflags = *[![:space:]]* ]];
		then
			mkdir -p resized;
			avconv -i "$fn" -strict experimental $avflags -y "resized/${fn%.*}.mp4";
		fi;
	done;
}
