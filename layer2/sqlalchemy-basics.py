## CORE allows us to use functions and metadata to create everything
## ORM (Object Relational Mapper) maps python classes to SQL tables

## create_engine is used to create an engine that connects to the database
## text is used in order to create the SQL text scripts that are being executed.
#from sqlalchemy import create_engine, text

## This is the engine that connects to the database that is in the string. The echo prints what is happening to the terminal.
#engine = create_engine("sqlite:///database.db", echo=True)

## This conn variable is the connection to the database
#conn = engine.connect()

## This executes the SQL commands in the parenthesis to the engine that is connected.
#conn.execute(text("CREATE TABLE IF NOT EXISTS people (name str, age int)"))

## This commits the changes making them stick
#conn.commit()

## Session works the same way as a connection when working with an engine.
#from sqlalchemy.orm import Session

#session = Session(engine)

#session.execute(text('INSERT INTO people (name, age) VALUES ("Mike", 30);'))

#session.commit()

from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, ForeignKey, func

engine = create_engine("sqlite:///database.db", echo=True)

meta = MetaData()

people = Table(
        "people",
        meta,
        Column('id', Integer, primary_key=True),
        Column('name', String, nullable=False),
        Column('age', Integer)
        )

things = Table(
            "things",
            meta,
            Column('id', Integer, primary_key=True),
            Column('description', String, nullable=False),
            Column('value', Float),
            Column('owner', Integer, ForeignKey('people.id'))
        )

meta.create_all(engine)

conn = engine.connect()

## Insert statement to add data into the database
#insert_statement = people.insert().values(name='Jane', age=25)
#result = conn.execute(insert_statement)
#conn.commit()

## Select statement to select data from the database
#select_statement = people.select().where(people.c.age > 22)
#result = conn.execute(select_statement)

#for row in result.fetchall():
#    print(row)

## Update statement to update data in the database
#update_statement = people.update().where(people.c.name == "Jane").values(age=50)
#result = conn.execute(update_statement)

#conn.commit()

#delete_statement = people.delete().where(people.c.name == "Jane")
#result = conn.execute(delete_statement)

#conn.commit()

insert_people = people.insert().values([
        {'name': 'Mike', 'age': 30},
        {'name': 'Bob', 'age': 35},
        {'name': 'Anna', 'age': 38},
        {'name': 'John', 'age': 50},
        {'name': 'Clara', 'age': 42}
    ])

insert_things = things.insert().values([
        {'owner': 2, 'description': 'Laptop', 'value': 800.50},
        {'owner': 2, 'description': 'Mouse', 'value': 50.50},
        {'owner': 2, 'description': 'Keyboard', 'value': 100.50},
        {'owner': 3, 'description': 'Book', 'value': 30},
        {'owner': 4, 'description': 'Bottle', 'value': 10.50},
        {'owner': 5, 'description': 'Speakers', 'value': 80.50}
    ])

#conn.execute(insert_people)
#conn.commit()
#conn.execute(insert_things)
#conn.commit()

#join_statement = people.join(things, people.c.id == things.c.owner)
#select_statement = people.select().with_only_columns(people.c.name, things.c.description).select_from(join_statement)

#result = conn.execute(select_statement)

#for row in result.fetchall():
#    print(row)

group_by_statement = things.select().with_only_columns(things.c.owner, func.sum(things.c.value)).group_by(things.c.owner).having(func.sum(things.c.value) > 50)
result = conn.execute(group_by_statement)

for row in result.fetchall():
    print(row)
