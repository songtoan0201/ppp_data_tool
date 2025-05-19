# PPP Data Analysis Tool

## 🚀 Project Overview

This tool automates the scraping, validation, processing, and querying of Paycheck Protection Program (PPP) loan data from the U.S. Small Business Administration (SBA)'s public dataset.

It showcases an end-to-end data engineering workflow involving:

- Web scraping
- Data validation and transformation
- PostgreSQL data storage
- REST API querying
- Dockerized deployment

---

## 🛠️ Tech Stack

- **Python 3.12**
- **FastAPI** – RESTful API framework
- **Playwright** – Headless browser automation for scraping
- **Pandas** – Data parsing and transformation
- **SQLAlchemy** – ORM for database interactions
- **PostgreSQL** – Relational data storage
- **Docker + Docker Compose** – Containerization and orchestration
- **uv** – Fast Python dependency manager

---

### 🕸 Web Scraping

- The `/load` API endpoint triggers data scraping. Although this could be handled by a standalone script, exposing it via an endpoint for better usability
- **Playwright** is used to navigate [https://data.sba.gov/organization] and locate the latest CSV and Excel files.
- The actual download of the CSV file is performed using `aiohttp` after the URL is retrieved via Playwright.
- Both files are saved to `tmp/downloads/` for staging and debugging, though they can be streamed into memory if needed. For massive data , we can stage them to a blog storage like S3 and another process will pick the files and load to the database

### 📊 Data Validation & Cleaning

- The downloaded CSV is parsed using **pandas**.
- Schema validation is performed by comparing against the columns defined in the Excel data dictionary, missing collumns will raise an error
- Data is cleaned to remove any rows with invalid or missing values.
- The `LoanNumber` column is used as the primary key for the database table.
- Fields are coerced to correct data types: numeric and datetime values are parsed gracefully.
- Records with missing primary keys (`LoanNumber`) are dropped.
- Data is limited to the first 10,000 rows to improve loading speed during local development.

### 🗄️ PostgreSQL Integration

- Database schema is auto-generated using `SQLAlchemy`'s `Base.metadata.create_all()` on Fastapi's startup
- Records are bulk-inserted into the database using the ORM layer.
- The PostgreSQL database is containerized and provisioned via `docker-compose`.

### 🌐 API Development

- `/load`: Triggers scraping, validation, cleaning, and insertion into the database.
- `/search?name=...`: Searches businesses by name with optional filters for city and state.
- `/business/{tin}`: Returns business details for a given TIN (Tax Identification Number, aka `LoanNumber`).
- Performance is improved via SQL indexes on searchable fields: `borrowername`, `borrowercity`, and `borrowerstate`.

## 🧑‍💻 Frontend Functionality

The frontend provides an easy-to-use interface for interacting with the API:

- **Load PPP Data** – Triggers the backend scraping and loads new records into PostgreSQL.
- **Search Businesses** – Allows searching by business name, city, or state.
- **View Details** – Clicking a result shows detailed business info fetched from the backend.

---

## 🔧 Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ppp_data_tool
```

### 2. Configure Environment Variables

Edit the `.env` file in the root directory if you need to change database credentials or connection info.  
Default values are provided:

```
DATABASE_URL=postgresql://postgres:postgres@db:5432/postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=postgres
```

### 3. Build and Start All Services

```bash
docker-compose up --build
```

This command will:

- Build the backend (FastAPI) and frontend (React/Vite) Docker images
- Start the PostgreSQL database, backend API, and frontend UI

### 4. Access the Application

- **Frontend UI:** [http://localhost:3000](http://localhost:3000)
- **Backend API:** [http://localhost:8000](http://localhost:8000)
- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
