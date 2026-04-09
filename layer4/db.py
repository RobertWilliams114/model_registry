from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

engine = create_engine("sqlite:///registry.db", echo=True)

Base = declarative_base()

Session = sessionmaker(bind=engine)

## Use the Session class so you get a unique session for every time the api calls are called.
def get_db():
    try:
        db = Session()
        yield db
    finally:
        db.close()
