
from db.database import engine, init_db
from services.scraper import download_ppp_csv, download_ppp_dictionary
from services.processor import load_ppp_csv, validate_schema, clean_ppp_data
from services.loader import insert_ppp_records
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from db.models import PPPRecordDB, Base
from datetime import datetime
from api.schemas import PPPRecordOut, PPPDetailedRecordOut
from pydantic import BaseModel, Field
from typing import Optional
from services.logger import get_logger

router = APIRouter()

init_db()
logger = get_logger()


def get_db():
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()


@router.get("/search", response_model=list[PPPRecordOut])
def search_businesses(
    name: str = Query(..., description="Full or partial business name"),
    state: str = Query(None),
    city: str = Query(None),
    db: Session = Depends(get_db)
):
    logger.info(f"Searching for businesses with name: {name}, state: {state}, city: {city}")
    query = db.query(PPPRecordDB).filter(PPPRecordDB.borrowername.ilike(f"%{name}%"))
    if state:
        query = query.filter(PPPRecordDB.borrowerstate == state)
    if city:
        query = query.filter(PPPRecordDB.borrowercity == city)

    results = query.limit(50).all()
    return results

@router.get("/business/{tin}", response_model=PPPDetailedRecordOut)
def get_business_by_tin(tin: str, db: Session = Depends(get_db)):
    logger.info(f"Fetching business details for TIN: {tin}")
    record = db.query(PPPRecordDB).filter(PPPRecordDB.loannumber == tin).first()
    print(record)
    if not record:
        raise HTTPException(status_code=404, detail="Business not found")
    return record



@router.get("/load")
async def load_ppp_data():
    try:
        # Step 1: Download files
        logger.info("Step 1: Downloading files...")
        csv_path, dict_path = await asyncio.gather(
            download_ppp_csv(),
            download_ppp_dictionary()
        )
        logger.info("Step 2 Load and validate...")
        # Step 2: Load and validate
        df = load_ppp_csv(csv_path)
        schema_valid = validate_schema(df, dict_path)
        if not schema_valid:
            raise HTTPException(status_code=400, detail="Schema validation failed.")

        # Step 3: Clean and insert
        logger.info("Step 3 : Cleaning and inserting data...")
        df_cleaned = clean_ppp_data(df)

        insert_ppp_records(df_cleaned)

        return {"message": "✅ Data loaded into PostgreSQL", "rows": len(df_cleaned)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"❌ Failed to load data: {repr(e)}")