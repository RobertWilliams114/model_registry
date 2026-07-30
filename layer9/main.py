from fastapi import FastAPI, status, Depends, File, UploadFile, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
import schemas
from uuid import UUID
from db import engine, Base, get_db
from sqlalchemy.orm import Session
import models
import crud
import storage_local
import storage_s3
from models import Version
from pathlib import Path

app = FastAPI()

ALLOWED_EXTENSIONS = {
    "pytorch": [".pth", ".pt", ".bin", ".safetensors"],
    "tensorflow": [".h5", ".pb", ".ckpt", ".keras"],
    "lightgbm": [".txt", ".model"],
}

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

@app.post("/models/{model_id}/versions/{version_tag}/upload",
          summary="Upload artifact uri")
def upload_artifact(model_id: str, version_tag: str, filename: str, db: Session = Depends(get_db)):

    object_key = f"{model_id}/{version_tag}/{filename}"

    db.query(Version).filter(Version.model_id == model_id, Version.version_tag == version_tag).update({"artifact_uri": object_key})
    db.commit()

    return storage_s3.presign_put_url(object_key)


@app.get("/models/{model_id}/versions/{version_tag}/upload-form",
         summary="HTML upload form for an artifact")
def upload_form(model_id: str, version_tag: str, filename: str, db: Session = Depends(get_db)):

    version = db.query(Version).filter(Version.model_id == model_id, Version.version_tag == version_tag).one()

    ext = Path(filename).suffix.lower()
    
    if ext not in ALLOWED_EXTENSIONS.get(version.framework.lower(), []):
        raise HTTPException(status_code = 400,
                            detail = f"Framework '{version.framework}' does not allow '{ext}' files")

    object_key =  f"{model_id}/{version_tag}/{filename}"

    db.query(Version).filter(Version.model_id == model_id, Version.version_tag == version_tag).update({"artifact_uri": object_key})
    db.commit()

    response = storage_s3.presign_put_url(object_key)

    html = f"""
    <html>
        <body>
            <form action="{response['url']}" method="POST" enctype="multipart/form-data">
                {''.join(f'<input type="hidden" name="{k}" value="{v}" />' for k, v in response['fields'].items())}
                <input type="file" name="file" />
                <input type="submit" value="Upload" />
            </form>
        </body>
    </html>
    """

    return HTMLResponse(content=html)

@app.get("/models/{model_id}/versions/{version_tag}/download",
         summary="Download artifact uri")
async def download_artifact(model_id: str, version_tag: str, db: Session = Depends(get_db)):
    file_path = str(db.query(Version.artifact_uri).filter(Version.model_id == model_id, Version.version_tag == version_tag).scalar())

    return storage_s3.presign_get_url(file_path)

@app.post("/deployments",
          summary="Changes the status and endpoint_url of a model and version")
def deployment_status(model_id: str, version_id: str, db: Session = Depends(get_db)):
    version = db.query(Version).filter(Version.id == version_id, Version.model_id == model_id).one()
    return

@app.get("/deployments/{id}",
         summary="Queries the deployment")
def get_deployment():
    return
