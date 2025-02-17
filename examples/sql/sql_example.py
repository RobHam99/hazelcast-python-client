from __future__ import print_function

import hazelcast
from hazelcast.serialization.api import Portable
from hazelcast.sql import SqlStatement


class Customer(Portable):
    def __init__(self, name=None, age=None, is_active=None):
        self.name = name
        self.age = age
        self.is_active = is_active

    def write_portable(self, writer):
        writer.write_string("name", self.name)
        writer.write_int("age", self.age)
        writer.write_boolean("is_active", self.is_active)

    def read_portable(self, reader):
        self.name = reader.read_string("name")
        self.age = reader.read_int("age")
        self.is_active = reader.read_boolean("is_active")

    def get_factory_id(self):
        return 1

    def get_class_id(self):
        return 1

    def __repr__(self):
        return "Customer(name=%s, age=%s, is_active=%s)" % (self.name, self.age, self.is_active)


client = hazelcast.HazelcastClient(portable_factories={1: {1: Customer}})

customers = client.get_map("customers").blocking()

# Fill the customers map with some values
customers.set(1, Customer("Peter", 42, True))
customers.set(2, Customer("John", 23, False))
customers.set(3, Customer("Joe", 33, True))

# Project a single column that fits the criterion
result = client.sql.execute("SELECT name FROM customers WHERE age < 35 AND is_active")

for row in result:
    # Get the object with the given column name in the row
    name = row.get_object("name")
    print(name)

# One can select all fields with *.
# Also, with statement can be used to close the resources on the
# server-side if something goes bad while iterating over rows.

with client.sql.execute("SELECT * FROM customers") as result:
    for row in result:
        # Get the objects with column names
        name = row.get_object("name")
        age = row.get_object("age")

        # Get the metadata associated with the row
        row_metadata = row.metadata

        # Get the index of the is_active column
        is_active_index = row_metadata.find_column("is_active")

        # Get the object with the column index
        is_active = row.get_object_with_index(is_active_index)

        print(name, age, is_active)

# Construct a statement object to control the properties of the query
# Special keywords __key and this can be used to refer to key and value.
# Also, a placeholder parameters can be specified
statement = SqlStatement("SELECT __key, age FROM customers WHERE name LIKE ?")

# Parameters will replace the placeholders on the server side
statement.add_parameter("Jo%")
statement.timeout = 5

with client.sql.execute_statement(statement) as result:
    # Row metadata can also be retrieved from the result
    row_metadata = result.get_row_metadata().result()

    for row in result:
        key = row.get_object("__key")
        age = row.get_object("age")

        print(key, age)

# Parameters can be passed directly in the basic execution syntax
result = client.sql.execute("SELECT this FROM customers WHERE age > ? AND age < ?", 30, 40)

for row in result:
    customer = row.get_object("this")
    print(customer)

# Query can be closed explicitly
result.close().result()
