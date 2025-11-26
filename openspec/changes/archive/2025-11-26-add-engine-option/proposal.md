# Change: Add engine selection (Mistral or AWS Textract)

## Why

Attualmente Alice PDF supporta solo Mistral come motore di estrazione. AWS Textract è già stato implementato e testato (`test_textract.py`, `alice_pdf/textract_extractor.py`) ma non è accessibile via CLI. Aggiungere l'opzione `--engine` permette di scegliere il motore più adatto al caso d'uso: Mistral per maggiore controllo tramite prompt/schema, Textract per velocità e affidabilità su tabelle standard.

## What Changes

- Aggiunta opzione CLI `--engine {mistral,textract}` con default `mistral`
- Opzioni specifiche per Textract: `--aws-region`, `--aws-access-key-id`, `--aws-secret-access-key`
- Routing logico in `cli.py` verso `extractor.py` o `textract_extractor.py`
- Validazione: opzioni Mistral (`--schema`, `--prompt`, `--model`) incompatibili con `--engine textract`
- Documentazione aggiornata (README, help)

## Impact

- Affected specs: `cli-interface` (nuovo), `extraction-workflow` (nuovo)
- Affected code: `alice_pdf/cli.py`, README.md, CLAUDE.md
- Dependencies: boto3 opzionale (installato solo se si usa Textract)
- Backward compatibility: preservata (default `--engine mistral`)
