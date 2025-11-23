from app.services.base_service import BaseService
from typing import Dict, Any

class PathService(BaseService):
    def find_shortest_path(self, start_id: int, end_id: int,
                          relationship_type: str, max_hops: int = 10):
        """Find the shortest path"""
        query = f"""
        MATCH path = shortestPath(
            (start)-[:{relationship_type}*..{max_hops}]-(end)
        )
        WHERE id(start) = $start_id AND id(end) = $end_id
        RETURN [n IN nodes(path) | id(n)] as path,
               length(path) as hops
        """
        return self.execute_query(query, {"start_id": start_id, "end_id": end_id})

    def find_all_paths(self, start_id: int, end_id: int,
                      relationship_type: str, max_hops: int = 10):
        """Find all paths"""
        query = f"""
        MATCH path = (start)-[:{relationship_type}*..{max_hops}]-(end)
        WHERE id(start) = $start_id AND id(end) = $end_id
        RETURN [n IN nodes(path) | id(n)] as path_ids,
               length(path) as hops
        LIMIT 100
        """
        return self.execute_query(query, {"start_id": start_id, "end_id": end_id})

    def find_shortest_path_dijkstra(self, start_id: int, end_id: int,
                                    relationship_type: str, options: dict = None):
        """
        Find the shortest path using Dijkstra’s algorithm (GDS)
            Advantages vs native Cypher:
            - Supports relationship weights
            - More efficient on large graphs
            - Returns the total path cost

            Options:
            - relationshipWeightProperty: property containing the weight (default: None = weight 1)
            - graph_name: name of the projected graph (auto-generated if not provided)
        """
        # opts = options or {}
        # weight_property = opts.get("relationshipWeightProperty", {})
        # graph_name = opts.get("graph_name", f"temp_dijkstra_{start_id}_{end_id}")

        # try:
        #     # Step 1: Create a projected graph with weights
        #     if weight_property:
        #         create_graph_query = """
        #         CALL gds.graph.project(
        #             $graph_name,
        #             '*',
        #             {
        #                 rel_type: {
        #                     type: $relationship_type,
        #                     properties: $weight_property
        #                 }
        #             }
        #         )
        #         YIELD graphName, nodeCount, relationshipCount
        #         RETURN graphName, nodeCount, relationshipCount
        #         """
        #         self.execute_query(create_graph_query, {
        #             "graph_name": graph_name,
        #             "relationship_type": relationship_type,
        #             "weight_property": weight_property
        #         })
        #     else:
        #         # Without weights, all relationships have a cost of 1
        #         create_graph_query = """
        #         CALL gds.graph.project(
        #             $graph_name,
        #             '*',
        #             $relationship_type
        #         )
        #         YIELD graphName, nodeCount, relationshipCount
        #         RETURN graphName, nodeCount, relationshipCount
        #         """
        #         self.execute_query(create_graph_query, {
        #             "graph_name": graph_name,
        #             "relationship_type": relationship_type
        #         })

        #     # Step 2: execute Dijkstra
        #     dijkstra_config: Dict[str, Any] = {
        #         "sourceNode": start_id,
        #         "targetNode": end_id
        #     }

        #     if weight_property:
        #         dijkstra_config["relationshipWeightProperty"] = weight_property

        #     dijkstra_query = """
        #     CALL gds.shortestPath.dijkstra.stream($graph_name, $config)
        #     YIELD index, sourceNode, targetNode, totalCost, nodeIds, costs, path
        #     RETURN nodeIds as path, 
        #            totalCost as total_cost,
        #            size(nodeIds) - 1 as hops,
        #            costs as step_costs
        #     """

        #     results = self.execute_query(dijkstra_query, {
        #         "graph_name": graph_name,
        #         "config": dijkstra_config
        #     })

        #     # Step 3: cleanup the projected graph
        #     try:
        #         self.drop_graph(graph_name)
        #     except Exception as err:
        #         print(f"Error: {err}")
        #         pass

        #     return results
        opts = options or {}
        weight_property = opts.get("relationshipWeightProperty")
        graph_name = opts.get("graph_name", f"temp_dijkstra_{start_id}_{end_id}")

        try:
            # Step 1: Create a projected graph with or without weights
            if weight_property:
                create_graph_query = """
                CALL gds.graph.project(
                    $graph_name,
                    '*',
                    {
                        rel: {
                            type: $relationship_type,
                            orientation: 'UNDIRECTED',
                            properties: $weight_property
                        }
                    }
                )
                """
                params = {
                    "graph_name": graph_name,
                    "relationship_type": relationship_type,
                    "weight_property": weight_property
                }
            else:
                create_graph_query = """
                CALL gds.graph.project(
                    $graph_name,
                    '*',
                    {
                        rel: {
                            type: $relationship_type,
                            orientation: 'UNDIRECTED'
                        }
                    }
                )
                """
                params = {
                    "graph_name": graph_name,
                    "relationship_type": relationship_type
                }

            self.execute_query(create_graph_query, params)

            # Step 2: Execute Dijkstra
            dijkstra_config = {
                "sourceNode": start_id,
                "targetNode": end_id
            }

            if weight_property:
                dijkstra_config["relationshipWeightProperty"] = weight_property

            dijkstra_query = """
            CALL gds.shortestPath.dijkstra.stream($graph_name, $config)
            YIELD index, sourceNode, targetNode, totalCost, nodeIds, costs
            RETURN nodeIds AS path,
                totalCost AS total_cost,
                size(nodeIds) - 1 AS hops,
                costs AS step_costs
            """

            results = self.execute_query(
                dijkstra_query,
                {"graph_name": graph_name, "config": dijkstra_config}
            )

            # Step 3: Cleanup
            try:
                self.drop_graph(graph_name)
            except Exception as err:
                print(f"Cleanup error: {err}")

            return results
        except Exception as e:
            # Cleanup in case of error
            try:
                self.drop_graph(graph_name)
            except Exception as err:
                print(f"Error: {err}")
                pass
            raise e

    def find_all_shortest_paths_dijkstra(self, start_id: int, relationship_type: str,
                                         options: dict = None):
        """
        Find all shortest paths from a source node (Single-Source Shortest Path)

            Options:
            - relationshipWeightProperty: weight property
            - max_distance: maximum distance (default: infinity)
        """
        opts = options or {}
        weight_property = opts.get("relationshipWeightProperty", {})
        graph_name = opts.get("graph_name", f"temp_sssp_{start_id}")

        try:
            # Create projected graph
            if weight_property:
                create_query = """
                CALL gds.graph.project($graph_name, '*', {
                    rel: {type: $relationship_type, properties: $weight_property}
                })
                """
                self.execute_query(create_query, {
                    "graph_name": graph_name,
                    "relationship_type": relationship_type,
                    "weight_property": weight_property
                })
            else:
                create_query = """
                CALL gds.graph.project($graph_name, '*', $relationship_type)
                """
                self.execute_query(create_query, {
                    "graph_name": graph_name,
                    "relationship_type": relationship_type
                })

            # Single-Source Shortest Path with Dijkstra
            config: Dict[str, Any] = {"sourceNode": start_id}
            if weight_property:
                config["relationshipWeightProperty"] = weight_property

            sssp_query = """
            CALL gds.allShortestPaths.dijkstra.stream($graph_name, $config)
            YIELD index, sourceNode, targetNode, totalCost, nodeIds, costs
            RETURN targetNode as target_node_id,
                   totalCost as total_cost,
                   nodeIds as path,
                   size(nodeIds) - 1 as hops
            ORDER BY totalCost
            """

            results = self.execute_query(sssp_query, {
                "graph_name": graph_name,
                "config": config
            })

            # Cleanup
            try:
                self.drop_graph(graph_name)
            except Exception as err:
                print(f"Error: {err}")
                pass

            return results

        except Exception as e:
            try:
                self.drop_graph(graph_name)
            except Exception as err:
                print(f"Error: {err}")
                pass
            raise e