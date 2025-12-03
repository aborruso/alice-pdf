# Changelog

## 2025-12-03

- Fix dependency resolution: requires-python >=3.9 (era >=3.8)
  - Risolve conflitto pdfplumber/camelot-py con pdfminer-six
  - Rimosso Python 3.8 da classifiers pyproject.toml
- Fix test suite: 41/41 test passano
  - Mock MISTRAL_API_KEY env var in test camelot/pdfplumber per evitare auto-switch engine
  - Risolve fallimenti test_cli_camelot_stream_routes, test_cli_camelot_lattice_default, test_cli_pdfplumber_strip_text_toggle
- Textract: rimosso `FORMS` da `FeatureTypes` (ora solo `TABLES`) per ridurre il costo a ~0,015 USD/pagina; aggiornato README con nota sui costi

## 2025-11-30

- Release 0.1.1
  - Pubblicata su PyPI
  - Aggiunto alias CLI `--mistral-api-key` per passare la chiave Mistral
  - Documentazione: installazione diretta da PyPI (pip/uv), quick upgrade commands
  - Aggiunta checklist di rilascio in `AGENTS.md`; `.venv` ignorata nel `.gitignore`

## 2025-11-27

- Fix errore "columns passed, passed data had X columns"
  - Aggiunto padding automatico per righe con meno colonne (riempite con stringhe vuote)
  - Aggiunto trimming per righe con più colonne (colonne extra scartate)
  - Warning quando righe vengono modificate per match con header
  - Risolve crash quando API Mistral restituisce JSON con righe incomplete
- Creato schema `sample/canoni_schema.yaml` per tabelle canoni locazione
  - Schema corregge problema € symbol in colonna sbagliata
  - Note critiche guidano API per corretta interpretazione IMPORTO
  - Estrazione 100% accurata con schema vs errori senza
- Creato `docs/best-practices.md` con guida completa (in inglese)
  - Quando usare ciascun motore (Mistral/Textract/Camelot)
  - Come scrivere schema YAML efficaci
  - Troubleshooting problemi comuni
  - Workflow raccomandato per progetti reali
  - Esempi pratici e ottimizzazioni performance/costi

## 2025-11-26

- Aggiunta funzione `merge_wrapped_rows()` per unire righe spezzate in output Camelot
  - Rileva righe con pochi valori non-vuoti (wrapped text)
  - Le unisce alla riga seguente concatenando valori
  - Risolve problema indirizzi multi-riga estratti come righe separate
- Aggiunta opzione `--engine {mistral,textract,camelot}` per scegliere motore di estrazione
- Implementato supporto Camelot per PDF nativi (non scansioni)
- Aggiunta opzione `--camelot-flavor {lattice,stream}` per modalità estrazione
- Fix gestione colonne duplicate in Camelot merge
- Aggiunta opzione `--engine {mistral,textract}` per scegliere motore di estrazione
- Implementato supporto AWS Textract come motore alternativo
- Aggiunta validazione opzioni engine-specific (incompatibilità tra opzioni Mistral e Textract)
- Standardizzato env var: `api_key` → `MISTRAL_API_KEY` in `.env`
- Aggiunto template credenziali AWS in `.env`
- Fix bug chiusura documento PDF in `textract_extractor.py`
- Aggiornato README con esempi dual-engine
- Pulizia script di test temporanei
