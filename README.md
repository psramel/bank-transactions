
# Bank Transactions (Setup, Execution and Test)

## Python Environment
1. Create a new environment:
   ```bash
   conda create -n bank_transactions python pip
   ```
2. Activate the environment:
   ```bash
   conda activate bank_transactions
   ```
3. Install dependencies:
   ```bash
   pip install "Django>=5.0" psycopg2-binary python-dotenv black mypy pytest pytest-django
   ```
4. Verify installed packages (optional):
   - If you used conda to install everything:
     ```bash
     conda list
     conda list --export > package-list.txt
     ```
     Note: package-list.txt contains also pypi package so this command should be enough.
   - If you installed via pip:
     ```bash
     pip list
     ```

## Database (Docker Postgres)
Start PostgreSQL with the project's defaults:
```bash
docker run --name bank-postgres \
  -e POSTGRES_DB=bank \
  -e POSTGRES_USER=bank \
  -e POSTGRES_PASSWORD=bankpass \
  -p 5432:5432 -d postgres:16
```
Check the container is running:
```bash
docker ps -a
```
If the container already exists, just start it:
```bash
docker start bank-postgres
```

## Environment file (.env)
Keep local secrets/config in `.env` in the project root. Example:
```env
DB_NAME=bank
DB_USER=bank
DB_PASSWORD=bankpass
DB_HOST=127.0.0.1
DB_PORT=5432
```
IMPORTANT: These values are illustrative only. Use your own credentials locally and never commit real secrets or passwords to Source Control Systems.

## Create Dajngo project and app
1. Start project
   ```bash
   django-admin startproject config .
   ```
   what should create structure similar to this
   ```env
   bank-transactions/
     config/
       __init__.py
       settings.py
       urls.py
       asgi.py
       wsgi.py
     manage.py
     .env
   ```
2. Create app transactions
   ```bash
   python manage.py startapp transactions
   ```
   In file `config/settings.py` add new app similar to
   ```env
   INSTALLED_APPS = [
    ...
    "transactions",
   ]
   ```
3. Load `.env` file in `settings.py` by adding
   ```python
   import os
   from pathlib import Path
   from dotenv import load_dotenv

   BASE_DIR = Path(__file__).resolve().parent.parent

   load_dotenv(BASE_DIR / ".env")
   ```
   and check for issues by running 
   ```bash
   python manage.py migrate
   ```
   In case no error everything should work correctly.

## Suggestion for model Transaction
1. Based on CSV what looks similar to
   ```csv
   reference,timestamp,amount,currency,description
   10000001,2023-01-11T03:00:01Z,20000,CZK,
   10000002,2023-01-11T09:00:00Z,-100,CZK,Lekárna Hradčanská
   10000003,2023-01-11T10:10:10Z,-1337,CZK,Lidl
   10000004,2023-01-11T12:00:00Z,-220,CZK,Šenkýrna
   10000005,2023-01-11T13:00:01Z,-100,CZK,Kofii
   10000006,2023-01-11T17:00:00Z,-12000,CZK,Servis Škoda Praha
   10000007,2023-01-11T13:00:01Z,100,CZK,Pepa
   ```
2. Create model in `transactions/model.py`
   ```python
   from django.db import models

   class Transaction(models.Model):
       reference = models.CharField(max_length=32, unique=True)
       timestamp = models.DateTimeField()
       amount = models.DecimalField(max_digits=12, decimal_places=2)
       currency = models.CharField(max_length=3)
       description = models.TextField(blank=True)

       created_at = models.DateTimeField(auto_now_add=True)

       class Meta:
           ordering = ["-timestamp"]

       def __str__(self) -> str:
           return f"{self.reference} {self.amount} {self.currency}"
   ```
   Note: Update based on your given data
3. Run following commands
   ```bash
   # creates just plan for migration. Check differences with previous model (looking for changes)
   python manage.py makemigrations
   # apply changes from previous command
   python manage.py migrate
   ```
   Note: run always when you create/change model

## URL structure
1. Open `urls.py` and add pages in `urlpatterns` similar to:
   ```python
      path("admin/", admin.site.urls),
      path("transactions", views.transactions_view, name="transactions"),
      path("", views.render_transactions_page),
   ```

## Functions for POST and GET transactions
- `transactions/views.py`:
  - `transactions_view` routes `POST` (CSV upload) and `GET` (HTML list).
  - `csv_upload` validates content type, parses CSV (header + rows), invokes `import_transactions`, and returns a summary response.
  - `render_transactions_page` loads transactions (newest first) and passes the biggest income to the template for highlighting.
- `transactions/services.py`:
  - `validate_row` checks required fields, parses timestamp/amount, and returns a cleaned dict or error.
  - `import_transactions` iterates rows, stores new transactions (`reference` unique), counts duplicates/errors, and returns an `ImportResult`.
- URLs (`config/urls.py`):
  - `path("transactions", views.transactions_view, name="transactions")`


## Create superuser for Django
1. Django doesn't have admin by default so for the first time it needs to be created by
   ```bash
   python manage.py createsuperuser
   ```

## Run the app
```bash
python manage.py migrate
python manage.py runserver 0.0.0.0:5000  # app listens on http://127.0.0.1:5000
```
Transactions page: http://127.0.0.1:5000/transactions
Note: it can happen that port is already occupied by other project. In this case kill the PID of the project or choose different port.

## Import transactions via CSV
Send a CSV file to the /transactions endpoint:
```bash
curl -X POST -H "Content-Type: text/csv" --data-binary @transactions-2023-03-01.csv http://127.0.0.1:5000/transactions
```
Note: without using --data-binary it didn't work on my machine, might be caused by MacOS.

## Tests
Use pytest (configured via `pytest.ini`):
```bash
pytest transactions
```
Examples:
- View tests: `pytest transactions/tests/test_view.py`
- Services tests: `pytest transactions/tests/test_services.py`
- Template highlight test: `pytest transactions/tests/test_template.py`

## Future improvements
1. Stream CSV uploads in chunks to reduce memory usage.
2. Replace `@csrf_exempt` with a standard CSRF-safe approach.
3. Add full typing annotations across the project.
4. Add basic documentation with Sphinx.
5. Logging in file
