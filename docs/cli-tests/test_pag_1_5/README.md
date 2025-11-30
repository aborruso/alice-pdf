# Test pagine 1-5

Il file PDF di test è [`edilizia-residenziale_comune_2024_PATRIMONIO_pages1-5.pdf`](../../../sample/edilizia-residenziale_comune_2024_PATRIMONIO_pages1-5.pdf), che deriva dall'estrazione di pagina 1 e 5 di [`sample/edilizia-residenziale_comune_2024_PATRIMONIO.pdf`](../../../sample/edilizia-residenziale_comune_2024_PATRIMONIO.pdf).

*I path sono relativi alla root del repository*

## Installazione

Prerequisiti: Python 3.8+.

Installa `alice-pdf` direttamente da PyPI (scegli una modalità):

- `pip install alice-pdf`
- `uv tool install alice-pdf` (serve prima [uv](https://docs.astral.sh/uv/getting-started/installation/))

Aggiornamento all'ultima versione:

```bash
pip install -U alice-pdf
# oppure
uv tool upgrade alice-pdf
```

**Nota**: Per usare Mistral e AWS Textract sono necessarie le rispettive API key.

## Comandi CLI

### Camelot basic

```bash
alice-pdf sample/edilizia-residenziale_comune_2024_PATRIMONIO_pages1-5.pdf output/camelot-basic/ --engine camelot
```

Output: [`output/camelot-basic/`](../../../output/camelot-basic/)

**Note:**

- Molti campi vuoti
- vari problemi nell'interpretare la struttura tabellare

### Camelot stream

```bash
alice-pdf sample/edilizia-residenziale_comune_2024_PATRIMONIO_pages1-5.pdf output/camelot-stream/ --engine camelot --camelot-flavor stream
```

Output: [`output/camelot-stream/`](../../../output/camelot-stream/)

**Note:**

- Diversi problemi, tra cui numero di colonne errato (15 invece di 17)

### pdfplumber basic

```bash
alice-pdf sample/edilizia-residenziale_comune_2024_PATRIMONIO_pages1-5.pdf output/pdfplumber-basic/ --engine pdfplumber --pdfplumber-strip-text
```

Output: [`output/pdfplumber-basic/`](../../../output/pdfplumber-basic/)

**Note:**

- Aggiunti spazi, come in "V e n e z i a" invece di "Venezia"
- Per la seconda pagina non estrae diversi Id Cespite (molti NULL)

### pdfplumber senza strip di spazi

```bash
alice-pdf sample/edilizia-residenziale_comune_2024_PATRIMONIO_pages1-5.pdf output/pdfplumber-no-strip/ --engine pdfplumber --no-pdfplumber-strip-text
```

Output: [`output/pdfplumber-no-strip/`](../../../output/pdfplumber-no-strip/)

**Note:**

- Disattiva lo `strip_text` di pdfplumber (può aiutare se serve mantenere spazi iniziali/finali nelle celle)
- Restano eventuali spazi interni inseriti dall'OCR

### AWS Textract

```bash
alice-pdf sample/edilizia-residenziale_comune_2024_PATRIMONIO_pages1-5.pdf output/textract-basic/ --engine textract --aws-region eu-west-1 --aws-access-key-id xxx --aws-secret-access-key xxx
```

Output: [`output/textract-basic/`](../../../output/textract-basic/)

**Note:**

- Rimuove i trattini (es. "01 Venezia" invece di "01 - Venezia")
- Errori di lettura (es. "SALAMON" invece di "SALOMON")

### Mistral con schema

```bash
alice-pdf sample/edilizia-residenziale_comune_2024_PATRIMONIO_pages1-5.pdf output/mistral-schema/ --engine mistral --api-key xxx --schema sample/test.yaml
# alias: --mistral-api-key
```

Output: [`output/mistral-schema/`](../../../output/mistral-schema/) (completato con schema)

**Note:**

- Omette "Castello" dalla descrizione (es. "Edificio residenziale - Calle Salomon" invece di "Edificio residenziale - Castello Calle Salomon")
- Errore grave pagina 2: 19 righe invece di 33, tutte con Id_Cespite = 1 (non ha letto affatto la pagina 2, ha copiato dati pagina 1)
