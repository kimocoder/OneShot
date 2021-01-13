$1 == "BSSID:" {
	MAC = $2
	wifi[MAC]["BSSID"] = MAC
}
$1 == "Datetime:" {
	wifi[MAC]["DATE"] = $2" "$3
}
$1 == "ESSID:" {
	wifi[MAC]["SSID"] = $2
}
$1 == "WPS" {
	wifi[MAC]["WPS_PIN"] = $3
}
$1 == "WPA" {
	wifi[MAC]["WPA_PASS"] = $3
	printf "%s\t%s\t%s\t%s\t%s\n",wifi[MAC]["BSSID"],wifi[MAC]["SSID"],wifi[MAC]["WPS_PIN"],wifi[MAC]["WPA_PASS"],wifi[MAC]["DATE"]
}
