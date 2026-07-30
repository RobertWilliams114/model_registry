from pathlib import Path
from models import Version

def safe_file(model_id, version_tag, content, filename, db):
    path = Path("artifacts") / model_id / version_tag   
    path.mkdir(parents=True, exist_ok=True)
    
    new_file = open(path / filename, "wb")
    new_file.write(content)

    new_file.close()

    file_path = str(path / filename)

    db.query(Version).filter(Version.model_id == model_id, Version.version_tag == version_tag).update({"artifact_uri": file_path})

    db.commit()

    return file_path
    
def load_file(model_id, version_tag, db):
    return str(db.query(Version.artifact_uri).filter(Version.model_id == model_id, Version.version_tag == version_tag).scalar())
