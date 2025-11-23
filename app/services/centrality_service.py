from app.services.base_service import BaseService

class CentralityService(BaseService):
    def calculate_betweenness(self, relationship_type: str, options: dict = None):
        """Calculate the betweenness centrality."""
        opts = options or {}
        # config = {
        #     "nodeProjection": "*",
        #     "relationshipProjection": {
        #         relationship_type: {
        #             "type": relationship_type,
        #             "orientation": opts.get("orientation", "UNDIRECTED")
        #         }
        #     },
        #     "samplingSize": opts.get("samplingSize", -1),
        #     "samplingSeed": opts.get("samplingSeed", None)
        # }
        #
        # config = {k: v for k, v in config.items() if v is not None}
        #
        # query = """
        #    CALL gds.betweenness.stream(config: $config)
        #    YIELD nodeId, score
        #    RETURN nodeId, score
        #    ORDER BY score DESC
        #    """

        graph_name = opts.get("graph_name", f"temp_betweenness_{id(self)}")

        try:
            create_query = """
                CALL gds.graph.project(
                    $graph_name,
                    '*',
                    $relationship_type
                )
                YIELD graphName, nodeCount, relationshipCount
                """
            self.execute_query(create_query, {
                "graph_name": graph_name,
                "relationship_type": relationship_type
            })

            config = {
                "samplingSize": opts.get("samplingSize", -1),
                "samplingSeed": opts.get("samplingSeed", 42)
            }
            config = {k: v for k, v in config.items() if v != -1}

            query = """
                CALL gds.betweenness.stream($graph_name, $config)
                YIELD nodeId, score
                WHERE score > 0
                RETURN nodeId as node_id, score
                ORDER BY score DESC
                """
            results = self.execute_query(query, {
                "graph_name": graph_name,
                "config": config
            })

            self.execute_query("CALL gds.graph.drop($graph_name)", {"graph_name": graph_name})
            self.drop_graph(graph_name=graph_name)
            return results
        except Exception as e:
            try:
                self.drop_graph(graph_name=graph_name)
            except Exception as err :
                print(f"Error: {err}")
                pass
            raise e
        # return self.execute_query(query, {"config": config})

    def calculate_closeness_v1(self, relationship_type: str, options: dict = None):
        """Calculate the closeness centrality"""
        opts = options or {}
        config = {
            "nodeProjection": "*",
            "relationshipProjection": {
                relationship_type: {
                    "type": relationship_type,
                    "orientation": opts.get("orientation", "UNDIRECTED")
                }
            },
            "useWassermanFaust": opts.get("useWassermanFaust", False)
        }

        query = """
                CALL gds.closeness.stream(config: $config)
                YIELD nodeId, score
                RETURN nodeId as node_id, score
                ORDER BY score DESC
                """
        return self.execute_query(query, {"config": config})

    def calculate_closeness(self, relationship_type: str, options: dict = None):
        opts = options or {}
        graph_name = opts.get("graph_name", f"temp_closeness_{id(self)}")

        try:
            self.execute_query("""
                CALL gds.graph.project($graph_name, '*', $relationship_type)
            """, {"graph_name": graph_name, "relationship_type": relationship_type})

            config = {"useWassermanFaust": opts.get("useWassermanFaust", False)}
            query = """
            CALL gds.closeness.stream($graph_name, $config)
            YIELD nodeId, score
            WHERE score > 0
            RETURN nodeId as node_id, score
            ORDER BY score DESC
            """
            results = self.execute_query(query, {"graph_name": graph_name, "config": config})

            self.drop_graph(graph_name=graph_name)
            return results
        except Exception as e:
            try:
                self.drop_graph(graph_name=graph_name)
            except Exception as err:
                print(f"Error: {err}")
                pass
            raise e

    def calculate_degree_v1(self, relationship_type: str, options: dict = None):
        """Calculate the degree centrality."""
        opts = options or {}

        config = {
            "nodeProjection": "*",
            "relationshipProjection": {
                relationship_type: {
                    "type": relationship_type,
                    "orientation": opts.get("orientation", "NATURAL")  # NATURAL, REVERSE, UNDIRECTED
                }
            },
            "relationshipWeightProperty": opts.get("relationshipWeightProperty", None)
        }

        # Retirer None values
        config = {k: v for k, v in config.items() if v is not None}

        query = """
            CALL gds.degree.stream(config: $config)
            YIELD nodeId, score
            RETURN nodeId as node_id, score
            ORDER BY score DESC
        """
        return self.execute_query(query, {"config": config})

    def calculate_degree(self, relationship_type: str, options: dict = None):
        opts = options or {}
        graph_name = opts.get("graph_name", f"temp_degree_{id(self)}")

        try:
            orientation = opts.get("orientation", "NATURAL")
            self.execute_query("""
                CALL gds.graph.project(
                    $graph_name,
                    '*',
                    {rel: {type: $relationship_type, orientation: $orientation}}
                )
            """, {
                "graph_name": graph_name,
                "relationship_type": relationship_type,
                "orientation": orientation
            })

            config = {}
            weight_prop = opts.get("relationshipWeightProperty")
            if weight_prop:
                config["relationshipWeightProperty"] = weight_prop

            query = """
            CALL gds.degree.stream($graph_name, $config)
            YIELD nodeId, score
            WHERE score > 0
            RETURN nodeId as node_id, score
            ORDER BY score DESC
            """
            results = self.execute_query(query, {"graph_name": graph_name, "config": config})
            self.drop_graph(graph_name)
            return results
        except Exception as e:
            try:
                self.drop_graph(graph_name)
            except Exception as err:
                print(f"Error: {err}")
                pass
            raise e

    def calculate_pagerank_v2(self, relationship_type: str, options: dict = None):
        """Calculate the PageRank"""
        opts = options or {"maxIterations": 20, "dampingFactor": 0.85}
        config = {
            "nodeProjection": "*",
            "relationshipProjection": relationship_type,
            "maxIterations": opts.get("maxIterations", 20),
            "dampingFactor": opts.get("dampingFactor", 0.85),
            "tolerance": opts.get("tolerance", 0.0000001)
        }

        query = """
            CALL gds.pageRank.stream(config: $config)
            YIELD nodeId, score
            RETURN nodeId, score
            ORDER BY score DESC
            """
        return self.execute_query(query, {"config": config})

    def calculate_pagerank(self, relationship_type: str, options: dict = None):
        opts = options or {}
        graph_name = opts.get("graph_name", f"temp_pagerank_{id(self)}")

        try:
            self.execute_query("""
                CALL gds.graph.project($graph_name, '*', $relationship_type)
            """, {"graph_name": graph_name, "relationship_type": relationship_type})

            config = {
                "maxIterations": opts.get("maxIterations", 20),
                "dampingFactor": opts.get("dampingFactor", 0.85),
                "tolerance": opts.get("tolerance", 0.0000001)
            }
            query = """
            CALL gds.pageRank.stream($graph_name, $config)
            YIELD nodeId, score
            WHERE score > 0
            RETURN nodeId as node_id, score
            ORDER BY score DESC
            """
            results = self.execute_query(query, {"graph_name": graph_name, "config": config})

            self.drop_graph(graph_name)
            return results
        except Exception as e:
            try:
                self.drop_graph(graph_name)
            except Exception as err:
                print(f"Error: {err}")
                pass
            raise e