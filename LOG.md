# Changelog

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
