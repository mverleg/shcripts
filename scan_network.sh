
##
## This attempts to find devices on the local network by pinging them.
## It uses ifconfig to find 192.168.* subnetworks, and pings all addresses in those and 192.168.0.* and 192.168.1.*
## It also checks for a few open ports (ssh, http, https) and reports the ping time.
##
## This script has no arguments or return values.
##

ip_locals="$(ifconfig | grep -Eo '192\.168\.[0-9]+\.[0-9]+' | grep -Ev '192\.168\.[0-9]+\.255' | sort | uniq)"
ip_f3s="`echo \"$ip_locals\" | cut -d '.' -f 3`"

function check_ping_ip ()
{
	# arg1: ip address
	if echo " $(echo $ip_locals) " | grep -E " $ip " 1> /dev/null
	then
		pingtime="local"
	elif ping -w2 "$1" 1> /dev/null
	then
		pingtime=$(ping -w2 "$1" | grep -Eo '[0-9]+\.[0-9]+ ms' | head -n1 | sed -r 's/([0-9]+)\.[0-9]+/\1/')
	else
		return
	fi
	services=""
	if nc -z "$ip" 80 1> /dev/null
	then
		services="$services http"
	fi
	if nc -z "$ip" 443 1> /dev/null
	then
		services="$services https"
	fi
	if nc -z "$ip" 22 1> /dev/null
	then
		services="$services ssh"
	fi
	if nc -z "$ip" 6532 1> /dev/null
	then
		services="$services ssh*"
	fi
	printf "%-16s %7s %s\n" "$1" "$pingtime" "$services"
}

printf "scanning ranges "
for ip_f3 in $ip_f3s
do
	printf "192.168.${ip_f3}.*; "
done
printf "\n"

for ip_f3 in $ip_f3s
do
	for ip_f4 in $(seq 0 255)
	do
		ip="192.168.${ip_f3}.${ip_f4}"
		check_ping_ip "$ip" 2>&1 | grep -v 'Do you want to ping broadcast? Then -b' &
	done
done

wait
echo "done"


