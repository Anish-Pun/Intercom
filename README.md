# 📡 Intercom Systeem

Dit project is een netwerkgebaseerd intercomsysteem waarbij een Raspberry Pi als zender en een Google AIY Voice Kit als ontvanger fungeert. Het systeem streamt live audio in real-time via een lokaal netwerk met Python, UDP-sockets en multithreading. De receiver speelt de audio af via een speaker en beschikt over een fysieke mute/unmute-knop en LED-indicatoren die de status tonen.

![Google AIY Voice Kit](Resources/GoogleAIYVoiceKits.png)


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
