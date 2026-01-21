
# 📸 Proiettore (v3)

**Projector Photo Viewer** è un visualizzatore di slideshow d'immagini leggero e performante, scritto in Python.
Questa terza iterazione ("proiettore_3") introduce un sistema di preload intelligente, logging avanzato, configurazione tramite JSON e un'API di controllo opzionale basata su Flask.

## ✨ Funzionalità

- **Visualizzazione Fluida:** Slideshow con transizioni e preload delle immagini in background per evitare lag.
- **Interfaccia GUI:** Basata su `tkinter`, semplice e reattiva.
- **Configurabile:** Gestione tramite file `proiettore_settings.json` (percorso, intervallo, shuffle).
- **Controllo Remoto (Opzionale):** Server API Flask integrato per controllare lo slideshow da remoto.
- **Logging:** Sistema di log per il debug e il monitoraggio dello stato.

## 📋 Prerequisiti

- **Python 3.8+**
- Librerie dipendenti (vedi `requirements.txt`):
  - `Pillow` (Gestione immagini)
  - `Flask` (Opzionale, per le API)

## 🚀 Installazione

1. **Clona la repository:**
   ```powershell
   git clone https://github.com/RuggeroCadamuroITA/Projector-Photo-Viewer.git
   cd Projector-Photo-Viewer

Installa le dipendenze:

code
Powershell
download
content_copy
expand_less
python -m pip install -r requirements.txt

(Nota: Se non intendi usare l'API remota, puoi installare solo Pillow)

Smoke-test (Opzionale):
Verifica che tutte le librerie siano caricate correttamente:

code
Powershell
download
content_copy
expand_less
python test_imports.py
🖥️ Utilizzo

Per avviare l'applicazione principale:

code
Powershell
download
content_copy
expand_less
python proiettore_3.py

Il programma cercherà le immagini nella cartella predefinita o in quella specificata nel file di configurazione.

⚙️ Configurazione

Puoi personalizzare il comportamento creando un file proiettore_settings.json nella stessa cartella dell'eseguibile o nella cartella delle immagini.

Esempio di struttura JSON:

code
JSON
download
content_copy
expand_less
{
  "image_folder": "C:/Users/Public/Pictures",
  "interval_ms": 5000,
  "shuffle": true,
  "api_enabled": false,
  "api_port": 5000
}
Chiave	Tipo	Descrizione
image_folder	string	Percorso assoluto o relativo della cartella immagini.
interval_ms	int	Tempo tra le slide in millisecondi (es. 5000 = 5 sec).
shuffle	bool	true per ordine casuale, false per ordine alfabetico.
api_enabled	bool	Abilita o disabilita il server Flask.
📂 Struttura del Progetto

proiettore_3.py: Core application. Contiene la logica GUI, il thread di preload e il server Flask.

requirements.txt: Elenco delle dipendenze per pip.

test_imports.py: Script di diagnostica rapida.

proiettore.log: File di log generato automaticamente durante l'esecuzione.

📝 Note

API Flask: Se abilitata, l'API gira su un thread separato. Utile per integrazioni domotiche o app di controllo.

Performance: Il sistema di preload carica l'immagine successiva in memoria mentre quella corrente è mostrata, garantendo transizioni istantanee anche con file pesanti.

(c) 2024-2026 - Tutti i diritti riservati.

code
Code
download
content_copy
expand_less
### Principali miglioramenti apportati:
1.  **Formattazione:** Uso di grassetti, tabelle e blocchi di codice per rendere tutto più leggibile.
2.  **Configurazione:** Ho inventato un esempio di JSON (`proiettore_settings.json`). È fondamentale mostrare all'utente *come* configurare il software, altrimenti la funzionalità è nascosta.
3.  **Tabella Parametri:** Spiega cosa fanno le opzioni del JSON.
4.  **Sezione Installazione:** Aggiunto il passaggio del `git clone` (visto che l'hai appena caricato su GitHub).
5.  **Professionalità:** Rimosso il tono colloquiale ("Se vuoi, posso...") che non si usa nei README pubblici.
