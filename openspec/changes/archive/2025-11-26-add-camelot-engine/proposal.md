# Change: Add Camelot engine for simple PDF tables

## Why

Camelot è specializzato nell'estrazione di tabelle da PDF "nativi" (non scansioni) con layout ben strutturati. È più veloce ed economico di Mistral/Textract per PDF semplici come `edilizia-residenziale_comune_2019.pdf`. Aggiungere Camelot come terzo motore offre:

- Estrazione locale (no API calls, no costi)
- Velocità superiore su PDF nativi con bordi tabella
- Modalità `lattice` (bordi) e `stream` (spaziatura)

## What Changes

- Estensione opzione `--engine` da `{mistral,textract}` a `{mistral,textract,camelot}`
- Nuovo modulo `camelot_extractor.py` con funzioni:
  - `extract_tables_with_camelot()` - orchestrazione
  - `extract_page_with_camelot()` - estrazione singola pagina
- Opzione `--camelot-flavor {lattice,stream}` per scegliere algoritmo (default: `lattice`)
- Dipendenza opzionale: `camelot-py[cv]` (include opencv per lattice mode)
- Nessuna validazione incompatibilità (Camelot non ha opzioni specifiche oltre flavor)

## Impact

- Affected specs: `cli-interface` (modifica), `extraction-workflow` (modifica)
- Affected code: `alice_pdf/cli.py`, nuovo `alice_pdf/camelot_extractor.py`
- Dependencies: camelot-py[cv] opzionale
- Backward compatibility: preservata (default `mistral`)
- No breaking changes
