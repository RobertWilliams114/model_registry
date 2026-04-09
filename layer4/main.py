from fastapi import FastAPI, status, Depends
import schemas
from uuid import UUID
from db import engine, Base, get_db
from sqlalchemy.orm import Session
import models
import crud

Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.post("/models",
          response_model=schemas.ModelResponse,
          status_code=status.HTTP_201_CREATED,
          summary="Created a new model (no version)")
def create_model(payload: schemas.ModelCreate, db: Session = Depends(get_db)):
    return crud.create_model(db, payload)

@app.get("/models",
         response_model=list[schemas.ModelResponse],
         status_code=status.HTTP_200_OK,
         summary="Get a list of models")
def list_models(db: Session = Depends(get_db)):
    return (crud.get_models(db))

@app.get("/models/{model_id}",
         response_model=schemas.ModelResponse,
         status_code=status.HTTP_200_OK,
         summary="Get a singular model")
def retrieve_model(model_id: str, db: Session = Depends(get_db)):
   return (crud.get_model(db, model_id))

@app.delete("/models/{model_id}",
            status_code=status.HTTP_204_NO_CONTENT,
            summary="Delete a model")
def delete_model(model_id: str, db: Session = Depends(get_db)):
    crud.delete_model(db, model_id)
    return 

@app.post("/models/{model_id}/versions",
          response_model=schemas.VersionResponse,
          status_code=status.HTTP_201_CREATED,
          summary="Create a new model version")
def create_model_version(payload: schemas.VersionCreate, db: Session = Depends(get_db)):
    return crud.create_version(db, payload)

@app.get("/models/{model_id}/versions",
         response_model=list[schemas.VersionResponse],
         status_code=status.HTTP_200_OK,
         summary="Get a list of versions from one model")
def retrieve_model_versions(model_id: str, db: Session = Depends(get_db)):
    return crud.get_versions(db, model_id)
