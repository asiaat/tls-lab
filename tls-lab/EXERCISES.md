# Praktikum: SSL/TLS ja veebisaitide usaldusväärsus (Docker-põhine)

**Sihtgrupp:** tehnoloogiakolledži küberturvalisuse/võrgunduse õpilased
**Keskkond:** Ubuntu + Docker / Docker Compose (üks masin piisab — "masinaid" simuleerivad konteinerid)
**Kestus:** ~2 akadeemilist tundi (+ lisaülesanne)

---

## Terminite sõnastik (EE → EN)

Küberturbes on valdav osa dokumentatsioonist, tööriistadest ja CVE-kirjeldustest ingliskeelsed — seetõttu on hea õppida termineid kohe kahes keeles.

| Eestikeelne mõiste | Ingliskeelne termin | Lühiselgitus |
|---|---|---|
| Tabalukk (brauseris) | **padlock icon** | Näitab, et ühendus kasutab TLS-i (on krüpteeritud) |
| Turvasertifikaat | **(TLS/SSL) certificate** | Digitaalne dokument, mis seob avaliku võtme domeeninimega |
| Sertifitseerimiskeskus | **Certificate Authority (CA)** | Usaldusväärne organisatsioon, kes sertifikaate väljastab/allkirjastab |
| Usaldusahel | **chain of trust** | Rida allkirju sertifikaadist juursertifikaadini (root CA) välja |
| Iseallkirjastatud sertifikaat | **self-signed certificate** | Sertifikaat, mille väljastaja = omanik ise; brauser seda ei usalda |
| Turvakäepigistus | **TLS/SSL handshake** | Protsess, mille käigus klient ja server lepivad kokku krüptovõtmetes |
| Vahemehe rünne | **Man-in-the-Middle (MITM) attack** | Ründaja paigutab end kahe osapoole vahele liiklust lugema/muutma |
| ARP-tabeli võltsimine | **ARP spoofing / ARP cache poisoning** | Ründaja veenab kohtvõrku (LAN), et tema MAC = ohvri/serveri IP |
| Pealtkuulamine (passiivne) | **sniffing / eavesdropping** | Võrguliikluse jälgimine ilma seda muutmata |
| Läbipaistev puhverserver | **transparent proxy** | Puhver, mille kaudu liiklus suunatakse ilma kliendi seadistuseta |
| Range transpordi turve | **HTTP Strict Transport Security (HSTS)** | Server käsib brauseril kasutada ainult HTTPS-i, kunagi mitte HTTP-d |
| Turbe allalaskmise rünne | **SSL stripping / downgrade attack** | Ründaja üritab sundida ohvrit kasutama HTTPS-i asemel HTTP-d |
| Võrgusild | **(network) bridge** | Tarkvaraline "kommutaator/switch", mis ühendab konteinerid ühte L2-segmenti |
| Kommuteeritud võrk | **switched network** | Võrk, kus kaadrid saadetakse ainult õigele sihtkoha MAC-ile (mitte kõigile) |
| Sertifikaadi kinnistamine | **certificate pinning** | Rakendus usaldab ainult kindlat sertifikaati/CA-d, mitte iga usaldusahelat |
| Sertifikaadi läbipaistvuse logi | **Certificate Transparency (CT) log** | Avalik logi kõigist väljastatud sertifikaatidest, et avastada võltsitud/varastatud sertifikaate |

## 0. Miks Docker VM-ide asemel?

Docker Compose loob mitu "masinat" (konteinerit) ühte virtuaalsesse võrku (Docker bridge-võrk), ilma et oleks vaja häälestada port-forwardimist VM-ide vahel või hostist. Kõik konteinerid näevad üksteist otse oma sisevõrgu IP-de kaudu ning tervik jookseb ühe õpilase enda arvutis, mistõttu on lahendus koolilaborisse palju lihtsam üles seada kui mitme VM-i skeem.

Boonusena on Docker'i **bridge**-võrk (network bridge) kohalikus võrgus (**LAN**, Local Area Network) toimuva **switchi** (kommutaatori) hea analoog: konteinerite vaheline liiklus **ei ole vaikimisi** teistele konteineritele nähtav (nn **switched network**), mis teeb **ARP spoofing'u** demonstratsiooni realistlikuks õppetunniks — täpselt sama põhimõte kehtib ka päris kontori-WiFi-s.

## ⚠️ Eetika ja ohutus

Kogu praktikum toimub isolatsioonis olevas Docker'i võrgus (`lab_net`), mis ei puutu kokku kooli WiFi ega päris internetiga peale image'ite allalaadimise. Kirjeldatud tehnikaid (ARP-võltsimine, MITM, liikluse pealtkuulamine) **ei tohi kunagi** kasutada kooli päris võrgus, avalikus WiFi-s ega kellegi teise seadme/serveri vastu ilma selgesõnalise loata — see on Eestis karistusseadustiku § 217 (arvutikuriteod) alla kuuluv tegu.

## Eeltingimused

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin
sudo usermod -aG docker $USER   # logi seejärel uuesti sisse
```

Kontrolli: `docker run hello-world`

---

## 1. Labori käivitamine

Kõik vajalikud failid (`docker-compose.yml`, `web/Dockerfile`, `web/server.py`,
`attacker/Dockerfile`) on juba selles repos — vt projekti juurkausta struktuuri
failis [`README.md`](README.md).

```bash
docker compose up -d --build
docker compose ps
```

Kolm konteinerit peaksid olema `running`:

| Konteiner  | IP           | Roll                                              |
|------------|--------------|----------------------------------------------------|
| `web`      | 172.28.0.10  | "Pank" — HTTP (port 80) ja HTTPS (port 443) login-server |
| `victim`   | 172.28.0.20  | Ohvri masin                                        |
| `attacker` | 172.28.0.30  | Pealtkuulaja/MITM masin                            |

---

## Ülesanne 1: Mida tabalukk tegelikult tõendab?

### 1a. Vaatlus host-i brauseris
Ava host-arvuti brauseris:
- `http://localhost:8080` — ei ole tabalukku, andmed liiguvad avatult.
- `https://localhost:8443` — brauser hoiatab ("Your connection is not private"), kuigi TLS on olemas!

**Küsimus:** miks brauser hoiatab, kui liiklus on ju tehniliselt krüpteeritud?

### 1b. Sertifikaadi kontroll konteineri seest (nagu ründaja/analüütik seda näeks)
```bash
docker compose exec attacker \
  openssl s_client -connect 172.28.0.10:443 -servername lab-pank.local </dev/null 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates
```

**Küsimused:**
1. Mis on Subject ja mis on Issuer väli — kas need on samad? Mida see tähendab usaldusväärsuse mõttes?
2. Milline erinevus oleks väljundis, kui `web`-konteineris kasutaksime päris CA (nt Let's Encrypt) väljastatud sertifikaati?
3. Selgita oma sõnadega vahet **konfidentsiaalsuse** (kas liiklus on krüpteeritud) ja **autentsuse** (kas server on tõesti see, kes ta väidab) vahel.

### Taustaks: kuidas usaldusahel (chain of trust) töötab

Meie labori sertifikaat on **self-signed** — server "kinnitab" ise, et ta on ise. Päris internetis toimib see nii:

1. **Root CA** (juursertifitseerimiskeskus, nt DigiCert, ISRG/Let's Encrypt) on eelinstallitud brauseri/OS-i usaldatavate juursertifikaatide nimekirja (*trust store*).
2. Root CA allkirjastab **intermediate CA** sertifikaadi (turvakaalutlustel ei kasutata root-võtit iga päev).
3. Intermediate CA allkirjastab konkreetse veebilehe sertifikaadi (**leaf certificate**), kontrollides enne, et taotleja tõesti omab seda domeeni.
4. Brauser kontrollib **kogu ahelat** (chain of trust) lehe sertifikaadist juurCA-ni — kui kõik allkirjad klapivad ja miski pole aegunud/tühistatud, kuvatakse tabalukk.

Meie labori sertifikaadil puudub 1.-3. samm täielikult, seetõttu brauser hoiatab — mitte sellepärast, et andmed poleks krüpteeritud, vaid sellepärast, et **keegi kolmas usaldusväärne osapool pole kinnitanud, kes server tegelikult on**.

Lisaks kontrollivad kaasaegsed brauserid sertifikaate ka avalike **Certificate Transparency (CT) logide** vastu — kui keegi väljastaks (nt varastatud CA-võtmega) võltssertifikaadi mõnele päris domeenile, oleks see logides nähtav ja tuvastatav.

---

## Ülesanne 2: Docker'i võrk ja "võrguteekond"

```bash
docker compose exec victim ip route
docker compose exec victim traceroute 172.28.0.10
```

**Küsimused:**
1. Mitu "hüpet" traceroute näitab? Miks nii vähe, võrreldes päris internetiliiklusega mõne avaliku saidini?
2. Docker'i bridge-võrk on sisuliselt üks suur kohtvõrk (LAN segment) — mis tähendab see ründaja jaoks võrreldes olukorraga, kus ohver ja ründaja on eri võrkudes (nt eri riikides)?
3. Kas traceroute annaks sulle infot selle kohta, kas keegi *samast* võrgusegmendist (nagu meie `attacker`-konteiner) suudab liiklust pealt kuulata? Miks/miks mitte?

*(Lisamõte edasijõudnutele: kaks eraldi `networks:` plokki + kolmas "router"-konteiner, mis on ühendatud mõlemasse, annaks mitme hüppega topoloogia — hea täiendav harjutus, kui aega jääb üle.)*

---

## Ülesanne 3: HTTP vs HTTPS pealtkuulamine — ja miks "lihtne" pealtkuulamine ei tööta

### Kontseptsioon: mis on MITM ja mis on ARP spoofing?

**Man-in-the-Middle (MITM) attack** — vahemehe rünne — tähendab, et ründaja paigutab end loogiliselt kahe suhtleva osapoole (nt sinu arvuti ja panga server) vahele, nii et kogu liiklus läbib teda. Ründaja saab siis liiklust lugeda (**passive MITM / eavesdropping**) või koguni muuta (**active MITM**, nt asendada allalaaditava faili pahavaraga).

Kohtvõrgus (LAN) on üks levinumaid viise MITM-positsiooni saavutamiseks **ARP spoofing** (ka *ARP cache poisoning*):

- **ARP (Address Resolution Protocol)** on protokoll, mis vastab küsimusele "Kellel on see IP-aadress? Anna oma MAC-aadress." Seadmed usaldavad ARP-vastuseid **ilma igasuguse autentimiseta** — protokoll loodi 1980ndatel, kui turvalisusest keegi ei mõelnud.
- Ründaja saadab võrku valeARP-vastuseid ("172.28.0.10 (server) MAC-aadress on tegelikult minu oma") nii ohvrile kui ka serverile.
- Mõlemad uuendavad oma **ARP-tabelit (ARP cache)** valeandmetega ja hakkavad saatma pakette hoopis ründaja masinasse.
- Ründaja lülitab sisse **IP forwarding** (`ip_forward`), et pakette edasi saata — muidu katkeks ohvri internetiühendus täielikult ja rünnak paljastuks kohe.

See on täpselt see, mida `arpspoof` meie laboris teeb, ja täpselt sama tehnika töötab ka päris WiFi-võrgus, kui ründaja on samas võrgusegmendis.

### 3a. Proovi pealt kuulata ilma millegita — see EI tööks
Ühes terminalis:
```bash
docker compose exec attacker tcpdump -i eth0 -A 'tcp port 80'
```
Teises terminalis:
```bash
docker compose exec victim curl -d "user=admin&pass=SuperSecret123" http://172.28.0.10/login
```

**Oodatav tulemus:** `attacker` **ei näe** seda päringut (või näeb väga harva/juhuslikult), kuna Docker'i bridge käitub nagu switch — see saadab kaadrid ainult õigele sihtkoha MAC-aadressile, mitte kõigile.

**Küsimus:** miks see on hea uudis tavakasutajale switchitud LAN-is (nt kontori- või koolivõrgus)?

### 3b. Muuda ründaja "vahemeheks" — ARP-võltsimine
```bash
docker compose exec attacker sh -c "echo 1 > /proc/sys/net/ipv4/ip_forward"

# Kaks tööd taustal: peta ohver uskuma, et ründaja on server, ja vastupidi
docker compose exec attacker arpspoof -i eth0 -t 172.28.0.20 172.28.0.10 &
docker compose exec attacker arpspoof -i eth0 -t 172.28.0.10 172.28.0.20 &
```

Korda nüüd tcpdump + curl katset (3a) — nüüd peaks `attacker` nägema **kasutajanime ja parooli selges tekstis**, sest kogu liiklus suunatakse tema kaudu (klassikaline man-in-the-middle).

### 3c. Sama katse, aga HTTPS-iga
```bash
docker compose exec victim curl -k -d "user=admin&pass=SuperSecret123" https://172.28.0.10/login
```
Vaata uuesti `tcpdump -i eth0 'tcp port 443'` väljundit.

**Küsimused:**
1. Mida erinevat sa nüüd tcpdump'is näed võrreldes HTTP-versiooniga?
2. Kas ARP-võltsimine ise "murrab" TLS-i? Mida ründaja täpselt saavutas ja mida mitte?
3. Miks pead sa `curl`-is kasutama lippu `-k` (ehk "ignoreeri sertifikaadi viga")? Mis juhtuks päris brauseris, kui kasutaja seda "ignoreeri" nuppu vajutaks?

**Lõpetamine:** peata arpspoof protsessid (`Ctrl+C` või `docker compose restart attacker`), muidu jääb konteinerite vaheline liiklus häirituks.

---

## Lisaülesanne (keerukam): täielik läbipaistev MITM-proxy + HSTS

**Eesmärk:** näha, kuidas ründaja saab ARP-positsiooni pealt mitte ainult *lugeda*, vaid ka liiklust *reaalajas suunata* läbi oma tööriista (mitmproxy), ning mõista, mis kaitseb selle vastu.

### Kontseptsioon: transparent proxy ja miks seda vaja on

Ülesanne 3b-s nägid liiklust ainult toorete pakettidena (`tcpdump`). Päris ründaja tahab sageli midagi mugavamat: näha täisväärtuslikke HTTP-päringuid/vastuseid, neid filtreerida, muuta või salvestada. Selleks kasutatakse **transparent proxy** (läbipaistev puhverserver) tehnikat:

- Tavaline puhverserver eeldab, et klient on **teadlikult** seadistatud selle kaudu suhtlema (nt brauseri proxy-seadetes).
- **Transparent proxy** puhul klient (ohver) ei tea ega pea midagi seadistama — ründaja "sunnib" liikluse läbi enda tarkvara operatsioonisüsteemi tasemel, kasutades **iptables**-i `REDIRECT`/`NAT` reegleid, mis suunavad kõik konkreetsele pordile (nt 80 või 443) minevad paketid kohalikule proxy-protsessile (**mitmproxy**) ümber.
- Kombinatsioon **ARP spoofing** (saad liikluse enda masinasse) + **transparent proxy** (mugav tööriist sisu lugemiseks/muutmiseks) on klassikaline päris-maailma MITM-tööriistakomplekt (samad põhimõtted, mida kasutavad nt Wi-Fi Pineapple või Bettercap).

### Samm 1 — suuna HTTP-liiklus läbi mitmproxy
Pärast ülesanne 3b ARP-võltsimise käivitamist, lisa `attacker`-konteineris iptables-reegel, mis suunab läbimineva pordi-80 liikluse kohalikule mitmproxy'le:
```bash
docker compose exec attacker sh -c "iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8081"
docker compose exec attacker mitmdump --mode transparent -p 8081
```
Korda `victim`-konteinerist HTTP-päringut (3a stiilis) — mitmproxy logi peaks näitama päringu sisu reaalajas, mitte ainult tcpdump'i toorete pakettidena.

### Samm 2 — sama HTTPS-i vastu
Proovi sama trikki port 443 jaoks. Ilma täiendava sammuta (ohvri veenmine usaldama ründaja enda CA-sertifikaati) mitmproxy ei suuda sisu dekrüpteerida — ta näeb ainult TLS handshake't.

**Arutlusküsimus:** mida peaks ründaja tegema, et ka HTTPS-liiklust dešifreerida (vihje: rogue root CA installimine ohvri seadmesse — nt läbi pahavara või ettevõtte "turbetarkvara" väärkasutuse)? Miks see on palju raskem kui pelgalt ARP-võltsimine?

### Samm 3 — HSTS ja SSL stripping

**Kontseptsioon — miks on vaja HSTS-i?**

Enamik kasutajaid trükib brauseri aadressiribale `pank.ee`, mitte `https://pank.ee` — brauser üritab vaikimisi esmalt **HTTP**-d (`http://pank.ee`) ja alles server suunab (redirect) HTTPS-ile üle. See esimene, veel krüpteerimata hetk on rünnatav:

- **SSL stripping / downgrade attack**: ründaja (juba MITM-positsioonis, nt sammudest 3b + Samm 1) püüab kinni ohvri esialgse HTTP-päringu ja **ei lase** serveri HTTPS-suunamisel ohvrini jõuda — ta ise räägib serveriga HTTPS-i kaudu (nii server "näeb" kõik korras), aga ohvrile saadab tagasi tavalise HTTP-lehe. Ohver ei märkagi, et tabalukku pole, sest ta polnudki seda algusest peale otsimas.
- Selle tehnika populariseeris tööriist nimega **sslstrip** (Moxie Marlinspike, 2009) ja see töötab siiani lehtedel, kus HSTS puudub.

**HTTP Strict Transport Security (HSTS)** lahendab selle nii:
`web/server.py` failis on lüliti `HSTS_ENABLED`. Kui see on `True`, lisab server HTTPS-vastusele päise:
```python
self.send_header('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
```
Kui brauser on selle päise korra domeenilt saanud, **jätab ta meelde** (määratud ajaks, `max-age` sekundites), et see domeen tuleb **alati** avada ainult `https://`-ga — isegi kui kasutaja trükib või klõpsab `http://` linki, ei tee brauser üldse võrgupäringut HTTP-le, vaid asendab selle lokaalselt HTTPS-iga **enne** paketi väljasaatmist. Nii pole ründajal enam midagi kinni püüda.

Lülita see sisse ja ehita konteiner uuesti:
```bash
sed -i 's/HSTS_ENABLED = False/HSTS_ENABLED = True/' web/server.py
docker compose up -d --build web
```

Seejärel selgita:
1. Mida see päis brauserile täpselt ütleb ja mille poolest erineb see tavalisest serveripoolsest 301/302 HTTP→HTTPS suunamisest?
2. Miks see takistab ülalkirjeldatud SSL stripping'ut?
3. **Trust On First Use (TOFU) probleem:** mis juhtub, kui kasutaja külastab lehte **kõige esimest korda**, kui brauser HSTS-reeglit veel ei tunne? Kas see esimene külastus on ikka rünnatav?
4. Kuidas lahendab punkti 3 probleemi brauseritesse sisseehitatud **HSTS preload list** (nimekiri domeenidest, mis on brauseri tarnesse juba sisse kirjutatud, ilma et esimest külastust oleks üldse vaja)?

**Hindamiskriteerium:** õpilane peab suutma joonistada/kirjeldada ründeahela — kus ründaja Docker-võrgus asub (ARP-tabelite tase), mida ta näeb HTTP puhul, mida HTTPS puhul, ja miks HSTS + kehtiv sertifikaat + kasutaja tähelepanelikkus on kolm eraldi kaitsekihti, mitte üks.

---

## Kokkuvõtlikud arutlusküsimused

1. Miks käitub Docker'i võrk pealtkuulamise mõttes sarnaselt päris switchitud kontorivõrguga, ja mille poolest see erineb vanast hub-põhisest võrgust?
2. Miks polnud traceroute (ülesanne 2) piisav, et ennustada, kas keegi suudab su liiklust pealt kuulata?
3. Millist konkreetset kaitsemehhanismi (kehtiv sertifikaat, HSTS, kasutaja tähelepanu) me täna nägime toimimas ja millise puudumine tegi ründe võimalikuks?
4. Kuidas te sõnastaksite oma sõbrale ühe lausega, miks tasub avalikus WiFi-s alati kontrollida, et sait kasutab HTTPS-i ja tabalukk on ilma hoiatusteta?

---

## Koristus

```bash
docker compose down -v
```

*Materjal on koostatud õppeotstarbel isoleeritud Docker-laborikeskkonnas kasutamiseks. Kirjeldatud tehnikaid (ARP-võltsimine, MITM, liikluse pealtkuulamine) ei tohi kasutada väljaspool seda isoleeritud keskkonda ega ilma selgesõnalise loata.*
