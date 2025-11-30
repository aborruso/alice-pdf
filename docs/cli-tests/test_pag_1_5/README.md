# Test pagine 1-5

File di test deriva dall'estrazione di pagina 1 e 5 di `sample/edilizia-residenziale_comune_2024_PATRIMONIO.pdf`

*I path sono relativi alla root del repository*

## Installazione

Se vuoi installare `alice-pdf` come cli, prima [installa uv](https://docs.astral.sh/uv/getting-started/installation/) (gestore di pacchetti Python veloce):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Poi clona il repository e installa le dipendenze:

```bash
git clone <repository-url>
cd alice-pdf
uv sync
```

Oppure installa globalmente:

```bash
uv tool install .
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
alice-pdf sample/edilizia-residenziale_comune_2024_PATRIMONIO_pages1-5.pdf output/pdfplumber-basic/ --engine pdfplumber
```

Output: [`output/pdfplumber-basic/`](../../../output/pdfplumber-basic/)

**Note:**

- Aggiunti spazi, come in "V e n e z i a" invece di "Venezia"
- Per la seconda pagina non estrae diversi Id Cespite (molti NULL)

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
```

Output: [`output/mistral-schema/`](../../../output/mistral-schema/) (completato con schema)

**Note:**

- Omette "Castello" dalla descrizione (es. "Edificio residenziale - Calle Salomon" invece di "Edificio residenziale - Castello Calle Salomon")
- Errore grave pagina 2: 19 righe invece di 33, tutte con Id_Cespite = 1 (non ha letto affatto la pagina 2, ha copiato dati pagina 1)
