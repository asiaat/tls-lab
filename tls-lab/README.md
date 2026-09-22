# tls-lab

Docker Compose'i põhine küberturvalisuse praktikum, mis demonstreerib:
- mida brauseri tabalukk (TLS/SSL) tegelikult tõendab ja mida mitte;
- mis vahe on HTTP ja HTTPS liikluse pealtkuulamisel;
- kuidas toimib ARP spoofing ja man-in-the-middle (MITM) rünne kohtvõrgus;
- mida teeb HSTS ja miks see kaitseb SSL stripping'u vastu.

Täielik õppematerjal (ülesanded, küsimused, kontseptsioonide selgitused kahes
keeles) on failis [`EXERCISES.md`](EXERCISES.md). See README kirjeldab ainult
tehnilist ülesehitust ja käivitamist.

## ⚠️ Ainult isoleeritud laborikeskkonnale

Kogu labor jookseb ühes eraldi Docker'i võrgus (`lab_net`) ja ei puutu kokku
päris internetiga peale image'ite build'imise. Kirjeldatud tehnikaid
(ARP spoofing, MITM, liikluse pealtkuulamine) **ei tohi kasutada** väljaspool
seda isoleeritud keskkonda ega ilma selgesõnalise loata.

## Struktuur

```
tls-lab/
├── docker-compose.yml     # 3 "masinat" ühes bridge-võrgus: web, victim, attacker
├── web/
│   ├── Dockerfile         # Python + self-signed TLS-sertifikaat
│   └── server.py          # HTTP (:80) ja HTTPS (:443) login-vorm
├── attacker/
│   └── Dockerfile         # dsniff, tcpdump, tshark, mitmproxy, iptables
├── EXERCISES.md           # täielik praktikumijuhend (ülesanded 1-3 + lisaülesanne)
└── .gitignore
```

| Konteiner  | IP           | Roll                                              |
|------------|--------------|----------------------------------------------------|
| `web`      | 172.28.0.10  | "Pank" — HTTP ja HTTPS login-server                |
| `victim`   | 172.28.0.20  | Ohvri masin, saadab päringuid `web`-ile             |
| `attacker` | 172.28.0.30  | Pealtkuulaja/MITM masin (NET_ADMIN, NET_RAW õigused)|

## Kiirstart

Eeldused: Docker + Docker Compose plugin (`docker.io`, `docker-compose-plugin`).

```bash
git clone <see repo> tls-lab
cd tls-lab
docker compose up -d --build
docker compose ps
```

Kontrolli host-brauserist:
- `http://localhost:8080` — ilma tabalukuta
- `https://localhost:8443` — brauser hoiatab (self-signed sertifikaat)

Ava kaks lisaterminali harjutusteks:
```bash
docker compose exec victim   sh
docker compose exec attacker sh
```

Serveri poolt "saadud" sisselogimisandmeid näed:
```bash
docker compose logs -f web
```

Kõik konkreetsed käsud, küsimused ja hindamiskriteeriumid on failis
[`EXERCISES.md`](EXERCISES.md).

## Koristus

```bash
docker compose down -v
```

## HSTS harjutuse jaoks

`web/server.py` sisaldab lülitit `HSTS_ENABLED = False` faili alguses.
Lisaülesande jaoks muuda see `True`-ks ja tee `docker compose up -d --build web`,
et näha `Strict-Transport-Security` päise mõju.

## Litsents / kasutus

Materjal on mõeldud õppeotstarbeliseks kasutamiseks küberturvalisuse ainetes.
