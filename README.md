# Proiettore (proiettore_3)

Versione migliorata del progetto "proiettore" — slideshow d'immagini con preload, configurazione, logging e API opzionale.

Prerequisiti
- Python 3.8+
- dipendenze: vedi `requirements.txt`

Installazione

```powershell
python -m pip install -r requirements.txt
```

Smoke-test rapido

```powershell
python test_imports.py
```

Esecuzione GUI

```powershell
python proiettore_3.py
```

File principali
- `proiettore_3.py`: nuova versione con GUI Tkinter, preload immagini, logging e API Flask opzionale.
- `requirements.txt`: Pillow e Flask.
- `test_imports.py`: script di prova per controllare le importazioni.

Note
- Se non vuoi avviare l'API Flask, puoi ignorare l'installazione di Flask; il programma funziona comunque per la GUI.
- Configurazione per cartella/interval/shuffle si può aggiungere con `proiettore_settings.json` nella cartella delle immagini.

Se vuoi, posso:
- aggiungere autenticazione per l'API
- creare pacchetto (`pyproject.toml` + build)
- integrare test unitari più estesi
