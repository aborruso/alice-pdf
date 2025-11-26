# Tasks

## 1. Implementation

- [x] Aggiungere argomento `--engine {mistral,textract}` a CLI con default `mistral`
- [x] Aggiungere argomenti AWS per Textract: `--aws-region`, `--aws-access-key-id`, `--aws-secret-access-key`
- [x] Implementare validazione: incompatibilità tra `--engine textract` e opzioni Mistral-specific (`--schema`, `--prompt`, `--model`)
- [x] Implementare routing in `cli.py`: chiamare `extract_tables()` o `extract_tables_with_textract()` in base a `--engine`
- [x] Verificare gestione credenziali AWS: env vars (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`) vs CLI args

## 2. Testing

- [x] Test CLI con `--engine mistral` (comportamento default invariato)
- [x] Test CLI con `--engine textract --aws-region eu-west-1`
- [x] Test validazione: errore se `--engine textract --schema schema.yaml`
- [x] Test credenziali AWS: env vars + CLI args

## 3. Documentation

- [x] Aggiornare README.md con esempi Textract
- [x] Aggiornare CLAUDE.md con info architettura dual-engine
- [x] Aggiornare help CLI con nuove opzioni

## 4. Validation

- [x] Eseguire `openspec validate add-engine-option --strict`
- [x] Test manuale: estrazione sample PDF con entrambi i motori
- [x] Verifica dipendenze opzionali: errore chiaro se boto3 mancante
