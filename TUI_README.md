# EZNet TUI - k9s-style Terminal Interface

## Overview

Das EZNet TUI (Terminal User Interface) bietet eine interaktive, k9s-ähnliche Benutzeroberfläche für Netzwerktests. Es wurde inspiriert von der beliebten k9s-Anwendung für Kubernetes und bietet ähnliche Navigation und Funktionalität.

## Features

### 🎯 k9s-inspirierte Funktionen

- **Keyboard-Navigation**: vim-ähnliche Tastenkürzel (j/k für auf/ab, g/G für top/bottom)
- **Tabellen-Interface**: Ähnlich zu k9s Resource-Listen
- **Breadcrumb-Navigation**: Zeigt den aktuellen Kontext an
- **Status-Bar**: Aktuelle Aktionen und Nachrichten
- **Modal-Dialoge**: Für Host-Management
- **Multi-Tab-Results**: Detaillierte Ergebnisse in Tabs organisiert

### 🚀 Netzwerk-Testing Features

- **Host-Management**: Hinzufügen, löschen und verwalten von Test-Hosts
- **Multi-Port-Scanning**: Gleichzeitiges Testen mehrerer Ports
- **Real-time Updates**: Live-Updates während der Scans
- **Detaillierte Ergebnisse**: DNS, TCP, HTTP, ICMP und SSL-Resultate
- **Concurrent Scanning**: Asynchrone Tests für bessere Performance

## Verwendung

### Starten der TUI

```bash
# Interaktive TUI starten
eznet --tui

# Oder direkt mit dem Demo-Skript
python demo_tui.py
```

### Keyboard-Shortcuts

#### Navigation (k9s-style)
- `↑`/`↓` oder `j`/`k` - Cursor bewegen
- `g` - Zum Anfang springen
- `G` - Zum Ende springen
- `Enter` / `Space` - Detaillierte Ergebnisse anzeigen

#### Host-Management
- `a` - Neuen Host hinzufügen
- `d` / `Ctrl+d` - Ausgewählten Host löschen
- `r` / `Ctrl+r` - Ansicht aktualisieren

#### Scanning
- `s` - Alle Hosts scannen

#### Anwendung
- `?` / `h` - Hilfe anzeigen
- `q` - Beenden
- `Esc` - Zurück/Abbrechen
- `Ctrl+c` - Beenden

## Interface-Komponenten

### 1. Header
- **Title Bar**: EZNet Branding mit Gradient
- **Breadcrumbs**: Aktuelle Navigation (eznet > hosts > ...)

### 2. Main Area
- **Host Table**: Liste aller konfigurierten Hosts
  - Host-Name/IP
  - Ports (gekürzt bei vielen Ports)
  - Status mit Emoji-Indikatoren
  - Letzte Scan-Zeit
  - Kurze Ergebnis-Zusammenfassung
- **Info Panel**: Detaillierte Informationen zum ausgewählten Host
  - Host-Details
  - Port-Konfiguration  
  - Scan-Ergebnisse-Übersicht
  - DNS-Auflösung
  - Offene/geschlossene Ports
  - HTTP-Services
  - ICMP-Status

### 3. Footer
- **Menu Bar**: Verfügbare Aktionen und Shortcuts
- **Status Bar**: Aktuelle Nachrichten und Aktions-Feedback

## Detaillierte Ergebnisse

Beim Drücken von `Enter` auf einem Host mit Scan-Ergebnissen öffnet sich ein Modal mit Tabs:

### DNS Tab
- IPv4/IPv6 Auflösung
- Aufgelöste IP-Adressen
- Fehler-Details

### Ports Tab  
- Port-Status (Offen/Geschlossen)
- Response-Zeiten
- Service-Identifikation
- Fehler-Details

### HTTP Tab
- HTTP-Status-Codes
- Server-Informationen
- Response-Zeiten
- Redirect-Informationen

### ICMP Tab
- Ping-Erreichbarkeit
- Response-Zeiten
- Fehler-Informationen

### SSL Tab (bei HTTPS-Ports)
- Zertifikat-Details
- Security-Bewertung
- Gültigkeitsdauer
- Issuer-Informationen

## Host-Management

### Host hinzufügen (`a`)
1. Modal-Dialog öffnet sich
2. Hostname oder IP eingeben
3. Optional: Ports spezifizieren (z.B. `80,443` oder `80-90`)
4. Bestätigen mit Enter oder "Add"-Button

### Host löschen (`d`)
- Sofortiges Löschen des ausgewählten Hosts
- Bestätigung in der Status-Bar

## Scanning-Process

### Single-Host Scan
- Automatische Erkennung: Einzelner Port oder Standard-Ports
- DNS, TCP, HTTP, ICMP Tests
- Optional: SSL-Zertifikat-Analyse

### Multi-Host Scan (`s`)
- Concurrent-Scanning aller Hosts
- Semaphore-basierte Begrenzung (max. 10 gleichzeitig)
- Real-time Status-Updates
- Progress-Anzeige in Breadcrumbs

## Error-Handling

- **Graceful Degradation**: Bei Fehlern bleiben andere Funktionen verfügbar
- **User Feedback**: Klare Fehlermeldungen in Status-Bar
- **Timeout-Management**: Konfigurierbare Timeouts für Tests
- **Exception-Handling**: Robuste Fehlerbehandlung für alle Netzwerk-Operationen

## Technische Details

### Architektur
- **Textual Framework**: Moderne Python TUI-Bibliothek
- **Async/Await**: Nicht-blockierende Netzwerk-Tests
- **Screen-Stack**: k9s-ähnliche Screen-Navigation
- **Event-System**: Reactive Updates

### Styling
- **k9s-Theme**: Authentische Farbpalette und Styling
- **Responsive Design**: Anpassung an Terminal-Größe
- **Gradient Effects**: Moderne visuelle Effekte
- **Status-Indikatoren**: Emojis und Farb-Coding

### Performance
- **Concurrent Scanning**: Bis zu 50 gleichzeitige Verbindungen
- **Efficient Updates**: Nur notwendige UI-Updates
- **Memory Management**: Cleanup von abgeschlossenen Tasks
- **Resource Limits**: Semaphore-basierte Concurrency-Kontrolle

## Vergleich zu k9s

| Feature | k9s | EZNet TUI |
|---------|-------|-----------|
| Navigation | ✅ vim-style | ✅ vim-style |
| Resource Tables | ✅ Kubernetes | ✅ Network Hosts |
| Real-time Updates | ✅ Live | ✅ Live |
| Detail Views | ✅ YAML/Logs | ✅ Network Results |
| Keyboard Shortcuts | ✅ Comprehensive | ✅ k9s-inspired |
| Breadcrumb Navigation | ✅ Context | ✅ Context |
| Status/Menu Bars | ✅ Yes | ✅ Yes |
| Modal Dialogs | ✅ Actions | ✅ Host Management |
| Theme Support | ✅ Customizable | ✅ k9s-inspired |

## Zukünftige Erweiterungen

- **Configuration Files**: YAML-basierte Host-Konfiguration
- **History View**: Scan-Historie und Trends
- **Export Functions**: CSV/JSON Export von Ergebnissen
- **Custom Themes**: Weitere Theme-Optionen
- **Plugin System**: Erweiterbare Test-Module
- **Watch Mode**: Kontinuierliche Überwachung
- **Alerting**: Benachrichtigungen bei Status-Änderungen

## Beispiel-Session

```
1. eznet --tui starten
2. 'a' drücken → Host hinzufügen (z.B. google.com)
3. Ports eingeben (z.B. 80,443)
4. 's' drücken → Scan starten
5. Mit ↑/↓ durch Hosts navigieren
6. Enter drücken → Detaillierte Ergebnisse ansehen
7. Tabs durchgehen (DNS, Ports, HTTP, etc.)
8. Esc → Zurück zur Host-Liste
9. 'q' → Beenden
```

Das EZNet TUI bringt die bewährte k9s-Benutzererfahrung in die Welt des Netzwerk-Testings!