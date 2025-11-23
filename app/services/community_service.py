from app.services.base_service import BaseService

class CommunityService(BaseService):
    def detect_louvain_v1(self, relationship_type: str, options: dict = None):
        """Detect communities with Louvain"""
        opts = options or {"iterations": 10}
        config = {
            "nodeProjection": "*",
            "relationshipProjection": relationship_type,
            "maxIterations": opts.get("maxIterations", 10),
            "tolerance": opts.get("tolerance", 0.0001),
            "includeIntermediateCommunities": opts.get("includeIntermediateCommunities", False),
            "seedProperty": opts.get("seedProperty", None)
        }

        config = {k: v for k, v in config.items() if v is not None}

        query = """
            CALL gds.louvain.stream(config: $config)
            YIELD nodeId, communityId, intermediateCommunityIds
            RETURN communityId as community, collect(nodeId) as nodes
            """
        return self.execute_query(query, {"config": config})

    def detect_greedy_v1(self, relationship_type: str, options: dict = None):
        """Detect community with Label Propagation (same as Greedy within GDS)"""
        opts = options or {}

        config = {
            "nodeProjection": "*",
            "relationshipProjection": relationship_type,
            "maxIterations": opts.get("maxIterations", 10),
            "seedProperty": opts.get("seedProperty", None)
        }

        config = {k: v for k, v in config.items() if v is not None}

        query = """
        CALL gds.labelPropagation.stream(config: $config)
        YIELD nodeId, communityId
        RETURN communityId as community, collect(nodeId) as nodes
        """
        return self.execute_query(query, {"config": config})

    def detect_weakly_connected_components_v1(self, relationship_type: str, options: dict = None):
        """Detect weakly connected components"""
        opts = options or {}

        config = {
            "nodeProjection": "*",
            "relationshipProjection": relationship_type,
            "threshold": opts.get("threshold", 0),
            "consecutiveIds": opts.get("consecutiveIds", False)
        }

        query = """
            CALL gds.wcc.stream(config: $config)
            YIELD nodeId, componentId
            RETURN componentId as component, collect(nodeId) as nodes
        """
        return self.execute_query(query, {"config": config})

    def detect_louvain(self, relationship_type: str, options: dict = None):
        opts = options or {}
        graph_name = opts.get("graph_name", f"temp_louvain_{id(self)}")

        try:
            self.execute_query("""
                CALL gds.graph.project($graph_name, '*', $relationship_type)
            """, {"graph_name": graph_name, "relationship_type": relationship_type})

            config = {
                "maxIterations": opts.get("maxIterations", 10),
                "tolerance": opts.get("tolerance", 0.0001),
                "includeIntermediateCommunities": opts.get("includeIntermediateCommunities", False)
            }
            seed_prop = opts.get("seedProperty")
            if seed_prop:
                config["seedProperty"] = seed_prop

            query = """
            CALL gds.louvain.stream($graph_name, $config)
            YIELD nodeId, communityId
            RETURN communityId as community, collect(nodeId) as nodes
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

    def detect_greedy(self, relationship_type: str, options: dict = None):
        opts = options or {}
        graph_name = opts.get("graph_name", f"temp_lpa_{id(self)}")

        try:
            self.execute_query("""
                CALL gds.graph.project($graph_name, '*', $relationship_type)
            """, {"graph_name": graph_name, "relationship_type": relationship_type})

            config = {"maxIterations": opts.get("maxIterations", 10)}
            seed_prop = opts.get("seedProperty")
            if seed_prop:
                config["seedProperty"] = seed_prop

            query = """
            CALL gds.labelPropagation.stream($graph_name, $config)
            YIELD nodeId, communityId
            RETURN communityId as community, collect(nodeId) as nodes
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

    def detect_weakly_connected_components(self, relationship_type: str, options: dict = None):
        opts = options or {}
        graph_name = opts.get("graph_name", f"temp_wcc_{id(self)}")

        try:
            self.execute_query("""
                CALL gds.graph.project($graph_name, '*', $relationship_type)
            """, {"graph_name": graph_name, "relationship_type": relationship_type})

            config = {
                "threshold": opts.get("threshold", 0),
                "consecutiveIds": opts.get("consecutiveIds", False)
            }
            query = """
            CALL gds.wcc.stream($graph_name, $config)
            YIELD nodeId, componentId
            RETURN componentId as component, collect(nodeId) as nodes
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