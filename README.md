# 📡 Intercom Systeem

Dit project is een netwerkgebaseerd intercomsysteem waarbij een Raspberry Pi als zender en een Google AIY Voice Kit als ontvanger fungeert. Het systeem streamt live audio in real-time via een lokaal netwerk met Python, UDP-sockets en multithreading. De receiver speelt de audio af via een speaker en beschikt over een fysieke mute/unmute-knop en LED-indicatoren die de status tonen.

![Google AIY Voice Kit](Resources/GoogleAIYVoiceKits.png)


## Connecteren met de Google AIY Voice Kit

Voor meer informatie over de Google AIY Voice Kit, zie: https://aiyprojects.withgoogle.com/voice/#connect

Er zijn twee manieren om te connecteren met de AIY Voice Kit:

### Via de App (aanbevolen)
1. Gebruik de AIY Projects app om verbinding te maken met het netwerk
2. Via de app kun je het IP-adres van de Voice Kit achterhalen

### Via Monitor
1. Sluit een monitor en muis aan op de AIY Voice Kit
2. Configureer de netwerkverbinding direct via de Raspberry Pi interface

## 💡 Functies

- Live audio streaming van zender naar receiver
- Mute / unmute via fysieke knop
- LED-indicatoren tonen systeemstatus
- Multithreading voor gelijktijdig verzenden, ontvangen en statusbeheer

## 📦 Technologieën

- Python
- UDP-sockets
- Multithreading
- Google AIY Voice Kit

## 📁 Projectstructuur

```
src/
	Sender/           # Code voor de zender (Raspberry Pi)
		hoofdmodule.py
	Receiver/         # Code voor de ontvanger (AIY Voice Kit)
		RecieverIntercom.py
tests/              # Unittests
Resources/          # Afbeeldingen en documentatie
```

## 📋 Vereisten

### Hardware
- Raspberry Pi (zender) met GPIO-pinnen
- Google AIY Voice Kit (ontvanger)
- Microfoon voor Raspberry Pi
- Speaker (geïntegreerd in AIY Voice Kit)
- 6 drukknoppen voor kamerselectie
- LED's (geïntegreerd in AIY Voice Kit)

### Software
- Python 3.x
- Raspberry Pi OS
- AIY Voice Kit OS

### Python Libraries
**Voor de Zender (Raspberry Pi):**
- `RPi.GPIO` - GPIO control
- `socket` - UDP communicatie
- `subprocess` - Audio opname via arecord

**Voor de Ontvanger (AIY Voice Kit):**
- `Flask` - Web dashboard
- `aiy.board` - AIY Board control
- `aiy.leds` - LED indicatoren
- `aiy.voice.tts` - Text-to-speech
- `numpy` - Audio processing
- `socket` - UDP communicatie

## ⚙️ Installatie

### Stap 1: Clone het project
```bash
git clone <repository-url>
cd Intercom
```

### Stap 2: Installeer dependencies op de Zender (Raspberry Pi)
```bash
sudo apt-get update
sudo apt-get install python3-rpi.gpio alsa-utils
pip3 install numpy
```

### Stap 3: Installeer dependencies op de Ontvanger (AIY Voice Kit)
```bash
pip3 install flask numpy
# AIY libraries zijn standaard geïnstalleerd op AIY OS
```

### Stap 4: Configureer IP-adressen
Pas in [src/Sender/hoofdmodule.py](src/Sender/hoofdmodule.py) de IP-adressen aan naar je eigen netwerk:
```python
ROOMS = {
    1: ("192.168.1.101", 50001),
    2: ("192.168.1.102", 50002),
    3: ("192.168.1.103", 50003),
    4: ("192.168.1.104", 50004),
}
```

## 🚀 Gebruik

### Start de Ontvanger (AIY Voice Kit)
```bash
cd src/Receiver
python3 RecieverIntercom.py
```
Het web dashboard is beschikbaar op `http://<AIY-IP>:5000`

### Start de Zender (Raspberry Pi)
```bash
cd src/Sender
python3 hoofdmodule.py
```

### Bediening
- Druk op een kamerknop (1-4) om naar een specifieke kamer te streamen
- Druk op de "Alle kamers" knop om naar alle kamers tegelijk te streamen
- Druk op de sirene knop voor een alarmsignaal
- Gebruik de mute-knop op de AIY Voice Kit om audio te dempen
- Beheer volume via het web dashboard

## 🎛️ Hardware Setup

### Zender GPIO Configuratie (Raspberry Pi)
```
GPIO 5  → Kamer 1 knop
GPIO 6  → Kamer 2 knop
GPIO 13 → Kamer 3 knop
GPIO 19 → Kamer 4 knop
GPIO 26 → Alle kamers knop
GPIO 21 → Sirene knop
```

### Ontvanger (AIY Voice Kit)
- Ingebouwde speaker
- Ingebouwde LED-ring voor statusweergave
- Hardware mute-knop

## 🔧 Configuratie

### Audio Instellingen
- **Sample Rate:** 16000 Hz
- **Kanalen:** Mono (1)
- **Format:** S16_LE (16-bit signed little-endian)
- **Chunk Size:** 
  - Zender: 4096 bytes
  - Ontvanger: 2048 bytes

### Netwerk Poorten
- UDP Port ontvanger: 50007 (standaard)
- Web Dashboard: 5000 (HTTP)

### LED Indicatoren
- **Groen:** Systeem actief, geen audio
- **Blauw:** Audio wordt ontvangen
- **Rood:** Mute actief

## 🐛 Troubleshooting

### Geen audio ontvangen
- Controleer of beide apparaten op hetzelfde netwerk zitten
- Verify IP-adressen in de configuratie
- Check firewall instellingen (UDP poort 50007 moet open zijn)

### Audio vertraging
- Verhoog de CHUNK size
- Controleer netwerklatency
- Zorg voor een stabiele WiFi verbinding

### GPIO fouten op Raspberry Pi
```bash
sudo pip3 install --upgrade RPi.GPIO
```

### AIY Voice Kit reageert niet
- Herstart de AIY Voice Kit
- Controleer of de AIY libraries correct geïnstalleerd zijn
- Bekijk logs via het web dashboard

## 📝 Toekomstige Features

- [ ] Encryptie voor audiostream
- [ ] Mobile app
- [ ] Betere manier om te configureren

