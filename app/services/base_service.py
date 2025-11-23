from app.database import neo4j_connection
from typing import List, Dict


class BaseService:
    def __init__(self):
        self.driver = neo4j_connection.get_driver()

    def execute_query(self, query: str, parameters: dict = None) -> List[Dict]:
        if parameters is None:
            parameters = {}

        with self.driver.session() as session:
            result = session.run(query, parameters)
            return [record.data() for record in result]

    def execute_procedure(self, procedure: str, parameters: dict = None) -> List[Dict]:
        if parameters is None:
            parameters = {}

        query = f"CALL {procedure}($params)"
        with self.driver.session() as session:
            result = session.run(query, params=parameters)
            return [record.data() for record in result]

    def drop_graph(self, graph_name: str) -> None:
        """
        Delete a projected graph GDS (without deprecation warning)
        """
        try:
            self.execute_query(
                "CALL gds.graph.drop($graph_name) YIELD graphName",
                {"graph_name": graph_name}
            )
        except Exception as e:
            # Ignore if graph doesn't exist
            print(f"Error: {e}")
            pass