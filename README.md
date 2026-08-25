# U.S. Airline Operations Analytics

An end-to-end airline operations analytics platform built with **Python, SQL, Pandas, Streamlit, Plotly, and scikit-learn** using official U.S. Department of Transportation flight data.

The project processes **75,000 real U.S. domestic flights** to analyze airline performance, airport and route bottlenecks, delay patterns, cancellations, and pre-departure delay risk.

**Pipeline:** `DOT/BTS Flight Data → Python ETL → SQL Analytics → Operational Dashboard → Delay Risk Model`

## Overview

This project builds an end-to-end analytics workflow around official U.S. DOT/Bureau of Transportation Statistics flight-level data. It downloads official airline operations data, cleans and transforms flight records with Python and Pandas, creates a reproducible 75,000-flight analytical dataset, loads flight data into a fact-and-dimension SQL model, analyzes airline/airport/route/time-based performance, visualizes operational KPIs, and estimates pre-departure delay risk using logistic regression.

## Business Questions

- Which airlines have the strongest on-time performance?
- Which carriers experience the highest average delays and cancellation rates?
- Which airports create the largest operational bottlenecks?
- Which routes experience the greatest delays?
- How does scheduled departure time affect delay performance?
- Which operational causes contribute the most delay minutes?
- Can information available before departure identify flights at higher risk of arriving late?

## Data

**Source:** U.S. Department of Transportation — Bureau of Transportation Statistics (BTS), Reporting Carrier On-Time Performance dataset.

Each record represents a reported U.S. domestic nonstop flight and includes airline, origin/destination airports, scheduled and actual flight times, arrival/departure delays, cancellations/diversions, distance, taxi times, and delay causes.

For a portfolio-scale implementation, the ETL pipeline creates a **fixed-seed sample of up to 75,000 flights** from the selected BTS source period.

## Data Pipeline

```text
Official DOT/BTS Flight Data
             ↓
       Python + Pandas
             ↓
   Cleaning & Transformation
             ↓
      Feature Engineering
             ↓
       75K Flight Sample
             ↓
      SQL Analytical Store
             ↓
 ┌───────────┴────────────┐
 ↓                        ↓
SQL Analytics        Delay Risk Model
 ↓                        ↓
 └───────────┬────────────┘
             ↓
    Streamlit Dashboard
```

## Data Engineering

The ETL pipeline handles cleaning numeric/date fields, missing values, route identifiers, scheduled departure hour, weekend indicators, on-time performance indicators, 15+ minute arrival-delay targets, primary delay-cause categorization, and reproducible sampling.

## SQL Analytics

Processed flight data is loaded into an analytical SQL structure centered around `fact_flights`, with supporting dimensions for `dim_airline`, `dim_airport`, `dim_date`, and `dim_route`.

The SQL analysis demonstrates `GROUP BY` aggregations, KPI calculations, `HAVING`, Common Table Expressions (CTEs), window functions, ranking, and route/airport/airline/time-based analysis.

Example ranking logic:

```sql
RANK() OVER (
    PARTITION BY month
    ORDER BY on_time_pct DESC
)
```

## Operational Analytics

The project compares airline performance by flight volume, on-time percentage, average arrival delay, and cancellation rate; identifies airport bottlenecks; analyzes route performance; measures delay patterns by scheduled departure hour; and aggregates delay minutes associated with carrier, weather, NAS, security, and late-aircraft delays.

## Interactive Dashboard

The **Streamlit + Plotly dashboard** displays total flights, on-time percentage, average arrival delay, and cancellation percentage. Users can filter by airline and explore on-time performance, delay by scheduled departure hour, high-delay origin airports, and route-level performance.

## Delay Risk Model

The project includes an interpretable **logistic regression model** that estimates whether a flight will arrive **15 or more minutes late** using information available before departure: airline, origin, destination, month, day of week, scheduled departure hour, distance, weekend indicator, and scheduled elapsed time.

Post-departure information such as actual departure delay and reported delay causes is excluded from the feature set to avoid leakage.

Categorical variables are imputed and one-hot encoded; numerical variables are median-imputed and standardized before logistic regression. The data is sorted chronologically, with the first 80% used for training and the final 20% for testing.

## Model Evaluation

The classifier is evaluated with:

- Accuracy
- Precision
- Recall
- F1 score
- ROC-AUC

These metrics provide different views of model performance rather than relying on accuracy alone.

## Technology Stack

| Area | Technologies |
|---|---|
| Data Processing | Python, Pandas |
| Database & Analytics | SQL, SQLAlchemy |
| Modeling | scikit-learn, Logistic Regression |
| Visualization | Streamlit, Plotly |
| Data Source | U.S. DOT / BTS |
| Testing | pytest |

## Repository Structure

```text
Airline-Operations-Analytics/
├── data/
│   ├── raw/
│   └── processed/
├── sql/
│   ├── schema.sql
│   └── analysis.sql
├── src/
│   ├── config.py
│   ├── dashboard.py
│   ├── download_data.py
│   ├── etl.py
│   ├── make_sample_data.py
│   └── train_model.py
├── tests/
│   └── test_etl.py
├── .env.example
├── .gitignore
├── pytest.ini
├── requirements.txt
└── README.md
```

Raw and processed flight datasets are excluded from Git because they can be reproduced through the project pipeline.

## Running the Project

### 1. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows: `.venv\Scripts\activate`

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure the environment

```bash
cp .env.example .env
```

The default configuration uses a local SQLite analytical database. Sample size and random seed can be configured through `.env`.

### 4. Download BTS flight data

```bash
python -m src.download_data --year 2026 --months 6
```

### 5. Run the ETL pipeline

```bash
python -m src.etl
```

### 6. Train the delay model

```bash
python -m src.train_model
```

### 7. Launch the dashboard

```bash
streamlit run src/dashboard.py
```

## Design Decisions

- **Official transportation data:** DOT/BTS provides reproducible, real airline operations data.
- **Multi-airline analysis:** Enables benchmarking across reporting carriers.
- **Reproducible 75K sample:** A fixed random seed keeps local analysis manageable and reproducible.
- **Fact-and-dimension modeling:** Demonstrates analytical data modeling for reporting and BI.
- **Pre-departure modeling:** Excludes post-departure information so risk estimates use only information reasonably known beforehand.
- **Interpretable baseline:** Logistic regression provides a straightforward, explainable baseline.

## Future Improvements

- Integrate airport weather data available before scheduled departure
- Add additional operational features
- Compare multiple classification approaches
- Add model explainability
- Evaluate performance separately across airlines
- Expand dashboard filtering and route analysis
- Automate recurring BTS data ingestion
- Add model monitoring and data-quality checks

## Disclaimer

This project was created for educational and portfolio purposes using publicly available U.S. transportation data. The delay-risk model is an analytical demonstration and is not intended for operational airline decision-making.
