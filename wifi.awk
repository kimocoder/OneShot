$3 == iface {
	MAC = $2
	wifi[MAC]["BSSID"] = MAC
}
$1 == "SSID:" {
	wifi[MAC]["SSID"] = $2
}
$1 == "signal:" {
	wifi[MAC]["SIG"] = $2
}
$1 == "WPS:" {
	printf "%s\t%s\t%s\n",wifi[MAC]["BSSID"],wifi[MAC]["SSID"],wifi[MAC]["SIG"]
}
