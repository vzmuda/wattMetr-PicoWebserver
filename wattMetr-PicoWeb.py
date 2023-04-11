# This code based on original code from Raspberry Pi
# Connecting to the internet with pico w doc
# Modified for usage with Mutusoft's wattMetr http://mutusoft.com/kitpages/
# Code provided without any warranty and is free to use


import network
import socket
import time
import json
import urequests
from machine import WDT
from machine import Pin, UART
import uasyncio as asyncio



# Change these parameters before running the scipt
ssid = "<WiFi_name>"
password = "<WiFi_password>"
ip = '<internal_net_fix_IP>'
mask = '<IP mask>'
gw = '<Default Gateway>'
dns = '<DNS server>'
# Change these parameters before running the scipt


onboard = Pin("LED", Pin.OUT, value=0)

html1 = """<!DOCTYPE html>
<html>
    <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>wattMetr web by Mutusoft.com</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC" crossorigin="anonymous">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body>
    <div class="container text-center">
        <div class="row">
            <div class="col-sm-3"></div>
            <div class="col-sm-6">
                <img src="http://mutusoft.com/Grafika/mutusoft_picture.png" width="150" />
                <h2>wattMetr web</h2>
            </div>
            <div class="col-sm-3"></div>
        </div>
        
        <div class="row">
            <div class="col-sm-3"></div>
            <div class="col-sm-6">
                    <table class="table">"""
                    
html2 = """
                        <tbody>
                          <tr>
                            <td style="text-align: left">Datum a Čas</td>
                            <td style="text-align: right"><strong>{TimeStamp}</strong></td>
                          </tr>
                          <tr>
                            <td style="text-align: left">Aktuální Napětí [V]</td>
                            <td style="text-align: right"><strong>{Voltage:10.0f}</strong></td>
                          </tr>
                          <tr>
                            <td style="text-align: left">Aktuální Proud [A]</td>
                            <td style="text-align: right"><strong>{Current:10.1f}</strong></td>
                          </tr>
                          <tr>
                            <td style="text-align: left">Aktuální Výkon [W]</td>
                            <td style="text-align: right"><strong>{Power:10.0f}</strong></td>
                          </tr>
                          <tr>
                            <td style="text-align: left">Energie za den [kWh]</td>
                            <td style="text-align: right"><strong>{EnergyDay:10.3f}</strong></td>
                          </tr>
                          <tr>
                            <td style="text-align: left">Energie celkem [kWh]</td>
                            <td style="text-align: right"><strong>{Energy:10.0f}</strong></td>
                          </tr>
                          <tr>
                            <td style="text-align: left">Teplota [Celsius]</td>
                            <td style="text-align: right"><strong>{Teplota:10.1f}</strong></td>
                          </tr>
                          <tr>
                            <td style="text-align: left">Uptime</td>
                            <td style="text-align: right"><strong>{Uptime}</strong></td>
                          </tr>              
                          </tbody> """
html3 = """
                </table>
            </div>
            <div class="col-sm-3"></div>
        </div>
        
        <div class="row">
            <div class="col-sm-3"></div>
            <div class="col-sm-6">
                <canvas id="tempChart" style="width:100%;max-width:700px"></canvas>
            </div>
            <div class="col-sm-3"></div>
        </div>
        <div class="row">
            <div class="col-sm-3"></div>
            <div class="col-sm-6">
                <canvas id="pwrChart" style="width:100%;max-width:700px"></canvas>
            </div>
            <div class="col-sm-3"></div>
        </div>
        <div class="row">
            <div class="col-sm-3"></div>
            <div class="col-sm-6">
                <canvas id="enDeChart" style="width:100%;max-width:700px"></canvas>
            </div>
            <div class="col-sm-3"></div>
        </div>
        <div class="row">
            <div class="col-sm-3"></div>
            <div class="col-sm-6">
                <canvas id="enMeChart" style="width:100%;max-width:700px"></canvas>
            </div>
            <div class="col-sm-3"></div>
        </div>
        <div class="row">
            <div class="col-sm-3"></div>
            <div class="col-sm-6">
                <canvas id="enRoChart" style="width:100%;max-width:700px"></canvas>
            </div>
            <div class="col-sm-3"></div>
        </div>
        <div class="row">
            <div class="col-sm-3"></div>
            <div class="col-sm-6">
                <canvas id="en10RChart" style="width:100%;max-width:700px"></canvas>
            </div>
            <div class="col-sm-3"></div>
        </div>
    </div>
"""

html4 = """
<script>
const xTempValues = [{xTempValues}];
const yTempValues = [{yTempValues}];
const xPwrValues = [{xPwrValues}];
const yPwrValues = [{yPwrValues}];
const xEnDenValues = [{xEnDenValues}];
const yEnDenValues = [{yEnDenValues}];
const xEnMesValues = [{xEnMesValues}];
const yEnMesValues = [{yEnMesValues}];
const xEnRokValues = [{xEnRokValues}];
const yEnRokValues = [{yEnRokValues}];
const xEn10RValues = [{xEn10RValues}];
const yEn10RValues = [{yEn10RValues}];
"""

html5 = """ 
    new Chart("tempChart", {
      type: "line",
      data: {
        labels: xTempValues,
        datasets: [{
          label: 'Teplota za 12h',
          fill: false,
          lineTension: 0,
          pointRadius: 2,
          borderWidth: 2,          
          backgroundColor: "Orange",
          borderColor: "DarkOrange",
          data: yTempValues
        }]
      },
      options: {
                 scales: {
                    x: {
                        ticks: {
                          callback: function(val, index) {
                            if (this.getLabelForValue(val) == 0) return 'Nyní';
                            if (this.getLabelForValue(val) == 32) return 'před 3h';
                            if (this.getLabelForValue(val) == 64) return 'před 6h';
                            if (this.getLabelForValue(val) == 96) return 'před 9h';
                            if (this.getLabelForValue(val) == 127) return 'před 12h';
                          }
                        }
          }
        }
      }
    });

    new Chart("pwrChart", {
      type: "line",
      data: {
        labels: xPwrValues,
        datasets: [{
          label: 'Výkon za 12h',
          fill: true,
          lineTension: 0.0,
          pointRadius: 2,
          borderWidth: 2,
          backgroundColor: "LightSalmon",
          borderColor: "OrangeRed",
          data: yPwrValues
        }]
      },
      options: {
        legend: {display: false},
        scales: {
                    x: {
                        ticks: {
                          callback: function(val, index) {
                            if (this.getLabelForValue(val) == 0) return 'Nyní';
                            if (this.getLabelForValue(val) == 32) return 'před 3h';
                            if (this.getLabelForValue(val) == 64) return 'před 6h';
                            if (this.getLabelForValue(val) == 96) return 'před 9h';
                            if (this.getLabelForValue(val) == 127) return 'před 12h';
                          }
                        },
          }
        }
      }
    });

    new Chart("enDeChart", {
      type: "bar",
      data: {
        labels: xEnDenValues,
        datasets: [{
          label: 'Výroba za 1 den [kWh]',
          backgroundColor: "LimeGreen",
           data: yEnDenValues
        }]
      },
      options: {
        legend: {display: false}
      }
    });

    new Chart("enMeChart", {
      type: "bar",
      data: {
        labels: xEnMesValues,
        datasets: [{
          label: 'Výroba za 1 Měsíc [kWh]',
          backgroundColor: "LimeGreen",
          data: yEnMesValues
        }]
      },
      options: {
        legend: {display: false},
      }
    });

    new Chart("enRoChart", {
      type: "bar",
      data: {
        labels: xEnRokValues,
        datasets: [{
          label: 'Výroba za 1 Rok [MWh]',
          backgroundColor: "LimeGreen",
          data: yEnRokValues
        }]
      },
      options: {
        legend: {display: false},
      }
    });

    new Chart("en10RChart", {
      type: "bar",
      data: {
        labels: xEn10RValues,
        datasets: [{
          label: 'Výroba za 10 let [MWh]',
          backgroundColor: "LimeGreen",
          data: yEn10RValues
        }]
      },
      options: {
        legend: {display: false},
      }
    });

    setTimeout(function () {
        window.location.reload();
    }, 60000);
    
</script>

</body>

</html>


<script>
</script>
<script>
</script>
<script>
</script>
<script>
</script>
<script>
</script>

<script>
</script>

<script>
</script>

"""

wdt = WDT(timeout=8000)
wlan = network.WLAN(network.STA_IF)
uart0 = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1), rxbuf=4096, timeout_char = 100)
rxData = bytes()
rxDataStr = "<undefined>"
json_decoded = json.loads('{}')
err_in_json = 0



def connect_to_network():
    global ssid, password, wlan
    wlan.active(True)
    wlan.config(pm = 0xa11140) # Disable power-save mode
    wlan.connect(ssid, password)
    max_wait = 20
    while max_wait > 0:
        if wlan.status() >= 3:
            break
        max_wait -= 1
        print('Připojuji se k Wifi ...')
        time.sleep(1)
        wdt.feed()
        onboard.on()
        time.sleep_ms(200)
        onboard.off()
        
    print('wlan status = ', wlan.status())
    if (wlan.status() < 0):
        print('Wifi je nedostupná.')
    else:
        print('Wifi připojena.')
        wlan.ifconfig((ip, mask, gw, dns))
        status = wlan.ifconfig()
        print('ip = ' + status[0])

def create_web():
    global rxDataStr, json_decoded
    global html1,html2,html3,html4,html5
    #json_decoded = json.loads(rxDataStr)
    #print(rxDataStr)
    if (len(json_decoded) == 0):
        return [ '', '', '', '', '' ]
    i = 0
    ytemp_data = ''
    xtemp_data = ''
    for temp in json_decoded['Temp12h[C]']:
        #temp_data = temp_data + '{x:' + str(i) + ',y:' + str(temp) + '},\n'
        ytemp_data = ytemp_data + str(temp) + ','
        xtemp_data = xtemp_data + str(i) + ','
        i += 1

    #vykon
    i = 0
    xpwr_data = ''
    ypwr_data = ''
    for pwr in json_decoded['Power12h[kW]']:
        ypwr_data = ypwr_data + str(pwr) + ','
        xpwr_data = xpwr_data + str(i) + ','
        i += 1
   
    #energie den
    i = 0
    xenden_data = ''
    yenden_data = ''
    for en in json_decoded['EnergyDay[kWh]']:
        yenden_data = yenden_data + str(en) + ','
        xenden_data = xenden_data + str(i) + ','
        i += 1
   
    #energie mesic
    i = 0
    xenmes_data = ''
    yenmes_data = ''
    for en in json_decoded['EnergyMonth[kWh]']:
        yenmes_data = yenmes_data + str(en) + ','
        i += 1
        xenmes_data = xenmes_data + str(i) + ','

        
    #energie rok
    i = 0
    xenrok_data = ''
    yenrok_data = ''
    for en in json_decoded['EnergyYear[MWh]']:
        yenrok_data = yenrok_data + str(en) + ','
        i += 1
        xenrok_data = xenrok_data + str(i) + ','

        
    #energie 10 let
    i = 0
    xen10r_data = ''
    yen10r_data = ''
    for en in json_decoded['Energy10Y[MWh]']:
        yen10r_data = yen10r_data + str(en) + ','
        i += 1
        xen10r_data = xen10r_data + str(i) + ','
         
    # uptime
    time = json_decoded['Uptime[s]']

    day = time // (24 * 3600)
    time = time % (24 * 3600)
    hour = time // 3600
    time %= 3600
    minutes = time // 60
    time %= 60
    seconds = time
    uptime = ( "%dd, %dh, %dmin, %ds" % (day, hour, minutes, seconds))
    #html0 = 'HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n'
    #html1
    aux1 = html2.format(TimeStamp = json_decoded['TimeStamp'], Voltage = json_decoded['Voltage[V]'], Current = json_decoded['Current[A]'], Power = json_decoded['Power[W]'], EnergyDay = json_decoded['EnergyDayAcc[kWh]'], Energy = json_decoded['EnergyAllAcc[kWh]'], Teplota = json_decoded['Temperature[C]'], Uptime = uptime)
    #html3
    aux2 = html4.format(xTempValues = xtemp_data, yTempValues = ytemp_data, xPwrValues = xpwr_data, yPwrValues = ypwr_data, xEnDenValues = xenden_data, yEnDenValues = yenden_data, xEnMesValues = xenmes_data, yEnMesValues = yenmes_data, xEnRokValues = xenrok_data, yEnRokValues = yenrok_data, xEn10RValues = xen10r_data, yEn10RValues = yen10r_data )
    #html5
    
    #return [ html0, html1, html2, html3, html4, html5 ]
    return [ html1, aux1, html3, aux2, html5 ]

async def serve_client(reader, writer):
    print("Client connected")
    request_line = await reader.readline()
    print("Request:", request_line)
    while await reader.readline() != b"\r\n":
        pass
    request = str(request_line)
    writer.write('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
    for html in create_web():
        writer.write(html)
    await writer.drain()
    await writer.wait_closed()
    print("Client disconnected")


def uart0_rxh():
    global rxDataStr, json_decoded, err_in_json
    
    while uart0.any() > 0:
        print('Rx chars = ',uart0.any())
        rxData = uart0.read()
    
    err_in_json = 0
    try:
        rxDataStr = rxData.decode('utf-8')
        #json_decoded = json.loads(rxDataStr)
        decoded_tmp = json.loads(rxDataStr)
        print('JSON OK')
    except:
        print('JSON not parsed')
        err_in_json = 1
        
    if (err_in_json == 0):
        json_decoded = decoded_tmp
    else:
        json_decoded = json.loads('{}')
    
async def main():
    global wdt
    onboard.on()
    print('Startuju main()')
    time.sleep(1)
    onboard.off()
    connect_to_network()
    onboard.off()
    time.sleep(1)
    print('Startuju webserver...')
    asyncio.create_task(asyncio.start_server(serve_client, "0.0.0.0", 80))
    push_timer = 0
    while True:
        if (uart0.any()):
            uart0_rxh()

        status = wlan.ifconfig()
        if (wlan.isconnected()):
            if (status[0] != ''):
                print('Připojeno IP -- ', status[0])
                onboard.on()
            else:
                print('Připojeno bez IP')
                onboard.off()
        else:
            onboard.off()
            connect_to_network()
        wdt.feed()        
        await asyncio.sleep(1)


try:
    asyncio.run(main())
finally:
    print ("Program ukončen ...")
    #machine.reset()