from neo4j import GraphDatabase
from app.config import settings

class Neo4jConnection:
    def __init__(self):
        # self._driver: AsyncDriver | None = None
        self._driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password)
        )

    def connect(self):
        return self._driver

    def verify_connectivity(self):
        try:
            self._driver.verify_connectivity()
            print("Neo4j connection is established")
        except Exception as e:
            print(f"Connection error: {e}")

    def close(self):
        if self._driver:
            self._driver.close()
            print("Neo4j driver is unconnected successfully")

    def get_driver(self):
        return self._driver

neo4j_connection = Neo4jConnection()