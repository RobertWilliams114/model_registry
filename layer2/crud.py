import uuid
from models import Model, Version

def create_model(db, data):
    model_dict = data.dict()
    model_identification = str(uuid.uuid4())
    new_model = Model(id=model_identification, name=model_dict['name'], description=model_dict['description'], current_version_id=None)
    db.add(new_model)
    db.commit()
    return new_model

def get_models(db):
    return db.query(Model).all()

def get_model(db, model_id):
    return db.query(Model).filter(Model.id == model_id).first()

def delete_model(db, model_id):
    db.query(Model).filter(Model.id == model_id).delete()
    db.commit()
    return

def create_version(db, data):
    version_dict = data.dict()
    version_identification = str(uuid.uuid4())
    new_version = Version(id=version_identification, model_id=str(version_dict['model_id']), version_tag=version_dict['version_tag'], framework=version_dict['framework'], current_version=version_dict['promote_to_current'])
    db.add(new_version)
    if (new_version.current_version == True):
        db.query(Version).filter(Version.current_version == True).update({"current_version": False})
    db.query(Model).filter(Version)
    db.commit()
    return new_version

def get_versions(db, model_id):
    return db.query(Version).filter(Version.model_id == model_id).all()
