# Tasks

## 1. Implementation

- [ ] Creare `alice_pdf/camelot_extractor.py` con funzioni base
- [x] Implementare `extract_tables_with_camelot()` - loop pagine, chiamata Camelot API
- [x] Aggiungere gestione parametri comuni (pages, dpi, merge_output, resume)
- [x] Estendere `--engine` a `{mistral,textract,camelot}` in CLI
- [x] Aggiungere opzione `--camelot-flavor {lattice,stream}` con default `lattice`
- [x] Implementare routing a `camelot_extractor` in `cli.py`
- [x] Gestire ImportError se camelot-py non installato

## 2. Testing

- [x] Test CLI con `--engine camelot` su edilizia-residenziale_comune_2019.pdf
- [x] Test flavor lattice vs stream
- [x] Test merge output
- [x] Test pages selection
- [x] Verifica errore chiaro se camelot-py mancante

## 3. Documentation

- [x] Aggiornare README con sezione Camelot
- [x] Aggiornare help CLI
- [x] Aggiungere esempio uso Camelot
- [x] Aggiornare "Choosing an engine" con quando usare Camelot

## 4. Validation

- [x] Eseguire `openspec validate add-camelot-engine --strict`
- [x] Test comparativo: Camelot vs Mistral vs Textract su stesso PDF
- [x] Verifica performance/velocità Camelot
