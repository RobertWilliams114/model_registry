from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

engine = create_engine("postgresql://registry:registry@postgres:5432/registry", echo=True)

Base = declarative_base()

Session = sessionmaker(bind=engine)

## Use the Session class so you get a unique session for every time the api calls are called.
def get_db():
    try:
        db = Session()
        yield db
    finally:
        db.close()
