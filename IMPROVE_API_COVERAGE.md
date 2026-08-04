# API-Abdeckung: Bestandsaufnahme & Empfehlungen

Abgleich der CLIP v2 Resource-Liste (`/resource/*`) gegen das, was `hueify`
heute abbildet. Ziel ist nicht Vollständigkeit gegenüber der Bridge-API,
sondern Value für eine **Python-Bibliothek zur programmatischen Steuerung**
von Licht – vergleichbar mit dem, was `hue.lights` / `hue.rooms` / `hue.zones`
/ `hue.scenes` heute leisten.

Referenz für den aktuellen Stand: `hueify/models.py` (`ResourceType`-Enum,
bereits fast vollständig als String-Enum gepflegt), `hueify/resources/*.py`
(die tatsächlich exponierten Namespaces), `hueify/sse/stream.py`
(`_EVENT_MODELS`, welche Events typisiert ankommen).

## 1. Bereits abgedeckt

| Resource | Wie |
| --- | --- |
| `light` | `LightNamespace` – voller Befehlssatz (`turn_on`, `set_color`, `set_brightness`, `set_color_temperature`, `identify`, `set_state`, CRUD via `update`) |
| `scene` | `SceneNamespace` – CRUD + `recall` / `activate` (inkl. `dynamic`, `brightness`, `transition`) |
| `room` | `RoomNamespace` (`GroupNamespace[Room]`) – CRUD, `lights()`, `scenes()`, Lichtbefehle über `grouped_light` |
| `zone` | `ZoneNamespace` (`GroupNamespace[Zone]`) – analog zu `room` |
| `grouped_light` | Kein eigener Namespace, aber vollständig genutzt: `GroupNamespace.grouped_light()` / `.apply()` / `.is_on()` lösen den Service für Room/Zone auf |
| Events (`light`, `room`, `zone`, `scene`) | Typisiert über `LightEvent` / `RoomEvent` / `ZoneEvent` / `SceneEvent` in `_EVENT_MODELS`; alles andere fällt auf generisches `HueEvent` zurück (funktioniert, aber untypisiert) |

Das deckt exakt den Kernfall ab, für den die Bibliothek wirbt: Lampen,
Räume und Zonen über ein gemeinsames Kommando-Interface schalten, dimmen,
einfärben, Szenen abrufen. Sauber geschnitten, keine Lücken in diesem Kern.

## 2. Empfehlenswert als Nächstes

Sortiert nach Verhältnis Value/Aufwand.

### 2.1 Sensoren: `motion`, `temperature`, `light_level`, `contact`, `button`

**Das ist die naheliegendste Lücke.** Die Bibliothek hat bereits einen
funktionierenden SSE-Eventbus (`hue.on(ResourceType.X, handler)`) – das
Fundament für reaktive Automatisierung steht. Ohne Sensor-Modelle bleibt
dieser Mechanismus aber auf "Lampenzustand beobachten" beschränkt. Der
naheliegende Anwendungsfall einer Steuerungs-Bibliothek – *"wenn Bewegung,
dann Licht an"* – lässt sich damit heute nicht typisiert schreiben.

Konkret fehlt:
- Pydantic-Modelle: `MotionState`, `TemperatureState`, `LightLevelState`,
  `ContactState`, `ButtonState` (analog zu `OnState`/`DimmingState`)
- `Motion`, `Temperature`, `LightLevel`, `Contact`, `Button` als
  `NamedResource`-Subtypen (die meisten Sensoren tragen keinen eigenen
  Namen, sondern hängen am Gerätenamen über `owner.rid` – das Muster kennt
  `groups.py` bereits über `owner.rid`-Auflösung)
- Ein schlanker Lese-Namespace (kein `LightCommands`-Mixin nötig, die meisten
  Sensoren sind read-only bzw. nur eingeschränkt konfigurierbar – z. B.
  `motion.enabled` per `PUT`)
- Passende Event-Modelle in `_EVENT_MODELS`, damit `hue.on(ResourceType.MOTION, ...)`
  typisiert statt generisch ankommt

Aufwand: moderat, folgt exakt bestehenden Mustern (`ResourceNamespace`,
`HueModel` mit `extra="allow"`). Kein neues Architekturkonzept nötig.

### 2.2 `device` (+ `device_power`)

Wird faktisch schon gebraucht, nur nicht exponiert: Sensoren und Schalter
hängen an einem `device`, nicht an einem Room/Zone. Ohne `DeviceNamespace`
lässt sich ein Bewegungsmelder oder Taster nicht mit seinem Klarnamen aus
der Hue-App verknüpfen – man hat nur die rohe `owner.rid`. `device_power`
liefert den Batteriestand, was für jede Sensor-Automatisierung relevant
ist ("warne mich, wenn der Batteriesensor unter 20 % fällt").

Sinnvoll im selben Schritt wie 2.1, da Sensor-Value ohne Gerätezuordnung
nur halb nutzbar ist.

### 2.3 `smart_scene`

Natürliche Erweiterung von `SceneNamespace` – zeitgesteuerte/automatische
Szenen (z. B. Sonnenaufgangs-Dimmer). Gleiche CRUD-Form wie `scene`, gleiches
Muster (`recall`-artige Aktivierung). Geringer Zusatzaufwand, passt exakt
in die bestehende Architektur.

### 2.4 `bridge`

Ein einzelner GET-Endpunkt (Bridge-ID, Softwareversion, Zeitzone). Trivial
zu ergänzen, nützlich für Diagnose/Logging ("welche Bridge-Firmware läuft
gerade"), aber kein Steuerungs-Value. Niedrige Priorität, aber quasi
kostenlos mitzunehmen, falls ohnehin an `resources/` gearbeitet wird.

## 3. Geringer Value für diese Bibliothek – bewusst zurückstellen

| Resource(n) | Warum (eher) nicht |
| --- | --- |
| `entertainment`, `entertainment_configuration` | Der eigentliche Value (Musik-/Game-Sync) läuft über einen separaten DTLS/UDP-Streaming-Kanal, nicht über CLIP-REST. Nur die Konfiguration abzubilden bringt ohne den Streaming-Teil kaum etwas – das wäre ein eigenes, deutlich größeres Feature, kein "API-Coverage"-Item |
| `homekit`, `matter`, `matter_fabric` | Ökosystem-Bridging/Provisioning für Drittanbieter-Plattformen, keine Lichtsteuerung. Passt eher zu einem Bridge-Admin-Tool als zu einer Steuerungs-Bibliothek |
| `geofence_client`, `geolocation` | Präsenzbasierte Automatisierung ist ein valider Use-Case, aber datenschutzsensibel und in der Praxis meist über die Hue-App selbst konfiguriert, nicht programmatisch. Nur bei konkretem Bedarf |
| `zigbee_connectivity`, `zgp_connectivity`, `wifi_connectivity`, `zigbee_device_discovery` | Netzwerk-/Pairing-Diagnostik, kein Licht-Value. Eher Baustein für ein Health-Check-Tool als für diese Bibliothek |
| `device_software_update` | Firmware-Update-Steuerung ist ein Admin-Feature mit Risiko (Bridge-Zustand verändern), passt nicht zum "Licht steuern"-Scope |
| `behavior_script`, `behavior_instance` | Mächtig (steuert eingebaute Hue-Automatisierungen), aber komplexes, generisches Config-Schema pro Skript-Typ – hoher Modellierungsaufwand für wenig zusätzlichen Nutzen gegenüber "die Automatisierung einfach selbst in Python schreiben", was diese Bibliothek ja gerade ermöglichen soll |
| `speaker` | Neue Hardware-Kategorie (Hue Smart Speaker), nicht Licht, vermutlich kaum Nutzerbasis in diesem Kontext |
| `camera_motion`, `motion_area_configuration`, `motion_area_candidate`, `convenience_area_motion`, `security_area_motion` | Hue-Secure-Kamera-Funktionen. Nur relevant mit entsprechender Hardware; eigenes Feature-Set, kein genereller Coverage-Gewinn |
| `service_group`, `grouped_motion`, `grouped_light_level` | Aggregation für Sensor-Gruppen – sinnvoller Folgeschritt *nachdem* `motion`/`light_level` selbst existieren (Muster: wie `grouped_light` heute für Rooms/Zones), aber ohne die Basis-Sensoren nutzlos |
| `bridge_home` | Grenzfall: aggregiert Räume/Geräte außerhalb eines Rooms. Selten gebraucht, solange `room`/`zone` reichen |
| `relative_rotary`, `bell_button`, `switch_input_configuration`, `tamper` | Ergänzen `button`/`contact` sinnvoll, aber Nischenhardware (Rotary-Dial, Türklingel-Taster) – erst nachziehen, wenn Feedback von Nutzern mit dieser Hardware kommt |
| `clip` | Reiner Meta-/Reflection-Endpunkt, kein praktischer Nutzen für Konsumenten der API |

## 4. Vorschlag für die Reihenfolge

1. **Sensoren + Device** (2.1 + 2.2) – größter Hebel: macht aus der
   Bibliothek eine vollständige "beobachten + reagieren"-Lösung statt nur
   "schalten". Baut auf vorhandenem SSE-Eventbus auf, keine neue Architektur.
2. **`smart_scene`** (2.3) – kleiner, isolierter Aufwand, rundet den
   Szenen-Bereich ab.
3. **`bridge`** (2.4) – nebenbei, wenn ohnehin an `resources/` gearbeitet wird.
4. Alles aus Abschnitt 3 nur auf konkrete Nachfrage, nicht proaktiv.
