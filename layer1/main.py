from fastapi import FastAPI, status
import schemas
from uuid import UUID
import store

app = FastAPI()

@app.post("/models",
          response_model=schemas.ModelResponse,
          status_code=status.HTTP_201_CREATED,
          summary="Created a new model (no version)")
def create_model(payload: schemas.ModelCreate):
    model = store.model_creation(payload)
    store.models.append(model)
    return model

@app.get("/models",
         response_model=list[schemas.ModelResponse],
         status_code=status.HTTP_200_OK,
         summary="Get a list of models")
def list_models():
    return (store.models)

@app.get("/models/{model_id}",
         response_model=schemas.ModelResponse,
         status_code=status.HTTP_200_OK,
         summary="Get a singular model")
def retrieve_model(model_id: UUID):
    for model in store.models:
        if model["id"] == model_id:
            return model

@app.delete("/models/{model_id}",
            status_code=status.HTTP_204_NO_CONTENT,
            summary="Delete a model")
def delete_model(model_id: UUID):
    for model in store.models:
        if model["id"] == model_id:
            store.models.remove(model)
    return

@app.post("/models/{model_id}/versions",
          response_model=schemas.VersionResponse,
          status_code=status.HTTP_201_CREATED,
          summary="Create a new model version")
def create_model_version(payload: schemas.VersionCreate):
    model_version = store.version_creation(payload)
    store.model_versions.append(model_version)
    return model_version

@app.get("/models/{model_id}/versions",
         response_model=list[schemas.VersionResponse],
         status_code=status.HTTP_200_OK,
         summary="Get a list of versions from one model")
def retrieve_model_versions(model_id: UUID):
    versions = []
    for version in store.model_versions:
        if version["model_id"] == model_id:
            versions.append(version)
    return versions
