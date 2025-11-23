from app.services.base_service import BaseService

class PredictionService(BaseService):
    def predict_links_v0(self, node_id: int, relationship_type: str, options: dict = None):
        """Predict future links (Node Similarity)"""
        opts = options or {"topK": 10}
        config = {
            "nodeProjection": "*",
            "relationshipProjection": relationship_type,
            "topK": opts.get("topK", 10),
            "similarityCutoff": opts.get("similarityCutoff", 0.0),
            "degreeCutoff": opts.get("degreeCutoff", 1),
            "similarityMetric": opts.get("similarityMetric", "JACCARD") # JACCARD, COSINE, OVERLAP
        }

        query = """
            CALL gds.nodeSimilarity.stream(config: $config)
            YIELD node1, node2, similarity
            WHERE node1 = $node_id
            RETURN node2 as target_node_id, similarity
            ORDER BY similarity DESC
            """
        return self.execute_query(query, {"config": config, "node_id": node_id})

    def predict_links(self, node_id: int, relationship_type: str, options: dict = None):
        opts = options or {}
        graph_name = opts.get("graph_name", f"temp_similarity_{id(self)}")

        try:
            self.execute_query("""
                CALL gds.graph.project($graph_name, '*', $relationship_type)
            """, {"graph_name": graph_name, "relationship_type": relationship_type})

            config = {
                "topK": opts.get("topK", 10),
                "similarityCutoff": opts.get("similarityCutoff", 0.0),
                "degreeCutoff": opts.get("degreeCutoff", 1),
                "similarityMetric": opts.get("similarityMetric", "JACCARD")
            }
            query = """
            CALL gds.nodeSimilarity.stream($graph_name, $config)
            YIELD node1, node2, similarity
            WHERE node1 = $node_id
            RETURN node2 as target_node_id, similarity
            ORDER BY similarity DESC
            """
            results = self.execute_query(query, {
                "graph_name": graph_name,
                "config": config,
                "node_id": node_id
            })

            self.drop_graph(graph_name)
            return results
        except Exception as e:
            try:
                self.drop_graph(graph_name)
            except Exception as err:
                print(f"Error: {err}")
                pass
            raise e

    # def predict_node_properties_v1(self, node_label: str, options: dict = None):
    #     """Predict node properties."""
    #     opts = options or {}
    #     query = f"""
    #     MATCH (n:{node_label})
    #     WITH collect(n) as nodes
    #     CALL apoc.ml.predictMissing(nodes, $options)
    #     YIELD node, predictions
    #     RETURN id(node) as node_id, predictions
    #     """
    #     return self.execute_query(query, {"options": opts})

    def predict_node_properties(self, node_label: str, property_name: str, options: dict = None):
        """
        Predict missing node properties (manual implementation)
        Uses FastRP (embeddings) + KNN to predict missing properties
        Options:
            - embedding_dimension: dimension of embeddings (default: 128)
            - knn_k: number of neighbors for KNN (default: 10)
            - train_fraction: fraction of nodes with property used for training (default: 0.8)
        """
        opts = options or {}
        knn_k = opts.get("knn_k", 10)

        # Step 1: Create embeddings with FastRP for all nodes
        # Step 2: Use KNN to find similar nodes
        # Step 3: Predict the property based on neighbors

        query = f"""
        // 1. Identify nodes with and without the property
        MATCH (n:{node_label})
        WITH n, 
             CASE WHEN n.{property_name} IS NOT NULL THEN 'train' ELSE 'predict' END as dataset

        // 2. For nodes without the property, find the K most similar neighbors
        WITH collect(CASE WHEN dataset = 'predict' THEN n ELSE null END) as predict_nodes,
             collect(CASE WHEN dataset = 'train' THEN n ELSE null END) as train_nodes

        UNWIND predict_nodes as target

        // 3. Compute similarity based on shared relationships
        MATCH (target)-[r1]-(common)-[r2]-(similar)
        WHERE similar IN train_nodes AND similar.{property_name} IS NOT NULL
        WITH target, similar, count(common) as common_neighbors
        ORDER BY common_neighbors DESC
        LIMIT $knn_k

        // 4. Aggregate predictions (mean for numeric, mode for categorical)
        WITH target, 
             collect(similar.{property_name}) as neighbor_values,
             avg(toFloat(similar.{property_name})) as predicted_value_numeric,
             head(collect(similar.{property_name})) as predicted_value_categorical

        RETURN id(target) as node_id,
               CASE 
                 WHEN predicted_value_numeric IS NOT NULL THEN predicted_value_numeric
                 ELSE predicted_value_categorical
               END as predicted_value,
               neighbor_values as evidence,
               size(neighbor_values) as confidence_score
        """

        return self.execute_query(query, {"knn_k": knn_k})

    # def predict_node_properties_with_gds_v1(self, node_label: str, property_name: str,
    #                                      relationship_type: str, options: dict = None):
    #     """
    #     Predict properties using GDS FastRP + KNN (advanced method)
    #
    #     Requires:
    #         1. Create a projected graph
    #         2. Compute FastRP embeddings
    #         3. Use KNN to predict
    #     """
    #     opts = options or {}
    #     graph_name = opts.get("graph_name", f"graph_{node_label}")
    #     embedding_dim = opts.get("embedding_dimension", 128)
    #     knn_k = opts.get("knn_k", 10)
    #
    #     # Step 1: Create a projected graph (if it does not already exist)
    #     create_graph_query = f"""
    #     CALL gds.graph.project(
    #         '{graph_name}',
    #         '{node_label}',
    #         '{relationship_type}'
    #     )
    #     """
    #
    #     # Step 2: Compute FastRP embeddings
    #     fastrp_query = f"""
    #     CALL gds.fastRP.stream('{graph_name}', {{
    #         embeddingDimension: {embedding_dim},
    #         randomSeed: 42
    #     }})
    #     YIELD nodeId, embedding
    #     RETURN nodeId, embedding
    #     """
    #
    #     # Step 3: Use KNN based on embeddings to predict the property
    #     knn_query = f"""
    #     CALL gds.knn.stream('{graph_name}', {{
    #         nodeProperties: ['embedding'],
    #         topK: {knn_k},
    #         randomSeed: 42,
    #         concurrency: 1,
    #         sampleRate: 1.0,
    #         deltaThreshold: 0.0
    #     }})
    #     YIELD node1, node2, similarity
    #     MATCH (n1) WHERE id(n1) = node1 AND n1.{property_name} IS NULL
    #     MATCH (n2) WHERE id(n2) = node2 AND n2.{property_name} IS NOT NULL
    #     WITH n1, collect(n2.{property_name}) as neighbor_values
    #     RETURN id(n1) as node_id,
    #            avg(toFloat(neighbor_values[0])) as predicted_value,
    #            neighbor_values as evidence
    #     """
    #
    #     try:
    #         # Note: In production, you need to handle creation/deletion of the projected graph
    #         results = self.execute_query(knn_query)
    #         return results
    #     except Exception as e:
    #         # Fallback to the simple method
    #         print(f"Error: {e}")
    #         return self.predict_node_properties(node_label, property_name, options)

    def predict_node_properties_with_gds(self, node_label: str, property_name: str,
                                         relationship_type: str, options: dict = None):
        """
        Predict properties using GDS FastRP + KNN (advanced method)

        Full pipeline:
        1. Create a projected graph
        2. Compute FastRP embeddings
        3. Store embeddings as a temporary property
        4. Use KNN to predict
        5. Clean up the projected graph
        """
        opts = options or {}
        graph_name = opts.get("graph_name", f"temp_graph_{node_label}_{property_name}")
        embedding_dim = opts.get("embedding_dimension", 128)
        knn_k = opts.get("knn_k", 10)

        try:
            # Check if the graph already exists; if not, create it
            check_graph_query = """
            CALL gds.graph.exists($graph_name) YIELD exists
            RETURN exists
            """
            graph_exists = self.execute_query(check_graph_query, {"graph_name": graph_name})

            if not graph_exists or not graph_exists[0]["exists"]:
                # Create the projected graph
                create_graph_query = f"""
                CALL gds.graph.project(
                    $graph_name,
                    '{node_label}',
                    '{relationship_type}'
                )
                YIELD graphName, nodeCount, relationshipCount
                RETURN graphName, nodeCount, relationshipCount
                """
                self.execute_query(create_graph_query, {"graph_name": graph_name})

            # Step 2: Compute and store FastRP embeddings as a node property
            fastrp_write_query = """
            CALL gds.fastRP.write($graph_name, {
                embeddingDimension: $embedding_dim,
                randomSeed: 42,
                writeProperty: 'fastrp_embedding'
            })
            YIELD nodePropertiesWritten
            RETURN nodePropertiesWritten
            """
            self.execute_query(fastrp_write_query, {
                "graph_name": graph_name,
                "embedding_dim": embedding_dim
            })

            # Step 3: Create a new graph using the embeddings
            graph_with_embeddings = f"{graph_name}_with_embeddings"
            create_embedding_graph_query = f"""
            CALL gds.graph.project(
                $graph_with_embeddings,
                {{
                    {node_label}: {{
                        properties: ['fastrp_embedding']
                    }}
                }},
                '*'
            )
            YIELD graphName
            RETURN graphName
            """
            self.execute_query(create_embedding_graph_query, {
                "graph_with_embeddings": graph_with_embeddings
            })

            # Step 4: Use KNN to predict missing properties
            knn_predict_query = f"""
            CALL gds.knn.stream($graph_with_embeddings, {{
                nodeProperties: ['fastrp_embedding'],
                topK: $knn_k,
                randomSeed: 42,
                concurrency: 1,
                sampleRate: 1.0,
                deltaThreshold: 0.0
            }})
            YIELD node1, node2, similarity
            WITH node1, node2, similarity
            MATCH (n1:{node_label}) WHERE id(n1) = node1 AND n1.{property_name} IS NULL
            MATCH (n2:{node_label}) WHERE id(n2) = node2 AND n2.{property_name} IS NOT NULL
            WITH n1, collect({{value: n2.{property_name}, similarity: similarity}}) as neighbors
            WHERE size(neighbors) > 0
            WITH n1, neighbors,
                 reduce(s = 0.0, n IN neighbors | s + n.similarity) as total_similarity
            UNWIND neighbors as neighbor
            WITH id(n1) as node_id,
                 sum(toFloat(neighbor.value) * neighbor.similarity / total_similarity) as predicted_value_weighted,
                 collect(neighbor.value) as neighbor_values,
                 size(neighbors) as confidence_score
            RETURN node_id,
                   predicted_value_weighted as predicted_value,
                   neighbor_values as evidence,
                   confidence_score
            ORDER BY confidence_score DESC
            """

            results = self.execute_query(knn_predict_query, {
                "graph_with_embeddings": graph_with_embeddings,
                "knn_k": knn_k
            })

            # Step 5: Clean up projected graphs and temporary properties
            # cleanup_queries = [
            #     f"CALL gds.graph.drop($graph_with_embeddings) YIELD graphName",
            #     f"CALL gds.graph.drop($graph_name) YIELD graphName",
            #     f"MATCH (n:{node_label}) REMOVE n.fastrp_embedding"
            # ]

            try:
                self.drop_graph(graph_with_embeddings)
                self.drop_graph(graph_name)
                self.execute_query(f"MATCH (n:{node_label}) REMOVE n.fastrp_embedding")
                # self.execute_query(cleanup_query, {
                #     "graph_name": graph_name,
                #     "graph_with_embeddings": graph_with_embeddings
                # })
            except Exception as e:
                print(f"Error: {e}")
                pass  # Ignore cleanup errors

            return results

        except Exception as e:
            # Cleanup in case of errors
            try:
                self.drop_graph(graph_name + "_with_embeddings")
                self.drop_graph(graph_name)
                # self.execute_query(f"CALL gds.graph.drop($graph_name)", {"graph_name": graph_name})
                # self.execute_query(f"CALL gds.graph.drop($graph_with_embeddings)",
                #                    {"graph_with_embeddings": f"{graph_name}_with_embeddings"})
            except Exception as err:
                print(f"Error: {err}")
                pass

            # Fallback to the simple method
            print(f"GDS method failed: {str(e)}, falling back to simple KNN")
            return self.predict_node_properties(node_label, property_name, options)