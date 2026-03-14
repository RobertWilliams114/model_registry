from uuid import UUID
import uuid

def model_creation(passed_model):
    model_dict = passed_model.dict()
    model_identification = uuid.uuid4()
    model_dict["id"] = model_identification
    return model_dict

def version_creation(passed_model_version):
    model_version_dict = passed_model_version.dict()
    version_identification = uuid.uuid4()
    model_version_dict["id"] = version_identification
    return model_version_dict

models = []

model_versions = []
