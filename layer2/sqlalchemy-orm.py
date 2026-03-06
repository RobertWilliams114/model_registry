from sqlalchemy import create_engine, Integer, String, Float, Column, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

engine = create_engine('sqlite:///database.db', echo=True)

## This is the base that we enherit from in our classes
Base = declarative_base()

class Person(Base):
    __tablename__ = 'people'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    age = Column(Integer)

    things = relationship('Thing', back_populates='person')

class Thing(Base):
    __tablename__ = 'things'
    id = Column(Integer, primary_key=True)
    description = Column(String, nullable=False)
    value = Column(Float)
    owner = Column(Integer, ForeignKey('people.id'))

    person = relationship('Person', back_populates='things')

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

#new_person = Person(name='Charlie', age=70)
#session.add(new_person)

## This temperarily adds the new person to the database without completely commiting it.
#session.flush()

#new_thing = Thing(description='Camera', value=500, owner=new_person.id)
#session.add(new_thing)

#session.commit()

#print([t.description for t in new_person.things])
#print(new_thing.person.name)

## Selecting people that are older than 30
result = session.query(Person).filter(Person.age > 30).all()

## Update the people whose names are Charlie to Charles
result = session.query(Person).filter(Person.name == "Charlie").update({"name": "Charles"})

## Deleting things that have a value less than 40
result = session.query(Thing).filter(Thing.value < 40).delete()

## Join the two tables, displaying all of the people and what they own
result = session.query(Person.name, Thing.description).join(Thing).all()

print([p.name for p in result])

## This commits and closes the connection to the database
session.close()
