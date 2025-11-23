from app.services.base_service import BaseService

class AnomalyService(BaseService):
    def detect_outliers_v0(self, node_label: str, options: dict = None):
        """Detect anomalies nodes"""
        opts = options or {}
        query = f"""
            CALL gds.degree.stream(config: {{
                nodeProjection: '{node_label}',
                relationshipProjection: '*'
            }})
            YIELD nodeId, score
            WITH score, percentileCont(score, 0.95) as p95
            MATCH (n) WHERE id(n) IN [nodeId] AND score > p95
            RETURN id(n) as node_id, score
            ORDER BY score DESC
        """
        return self.execute_query(query, {"options": opts})

    def detect_outliers_v1(self, node_label: str, relationship_type: str = None, options: dict = None):
        """
        Detect anomalous nodes based on degree (manual implementation)
        Options:
        method: 'iqr' (Interquartile Range) or 'zscore' (Z-Score) or 'percentile'
        threshold: for zscore (default: 3), for percentile (default: 0.95)
        orientation: 'INCOMING', 'OUTGOING', 'BOTH' (default: 'BOTH')
        """
        opts = options or {}
        method = opts.get("method", "percentile")  # iqr, zscore, percentile
        threshold = opts.get("threshold", 0.95 if method == "percentile" else 3)
        orientation = opts.get("orientation", "BOTH")
        rels_type = {
            relationship_type: {
                "orientation": orientation
            }
        }
        all_rels = {
            "*": {
                "orientation": orientation
            }
        }
        relationshipProjection = rels_type if relationship_type else all_rels

        if method == "percentile":
            query = f"""
            MATCH (n:{node_label})
            CALL gds.degree.stream(config: {{
                nodeProjection: '{node_label}',
                relationshipProjection: {relationshipProjection},
                relationshipWeightProperty: $weightProperty
            }})
            YIELD nodeId, score
            WITH nodeId, score, percentileCont(score, $threshold) as percentile_threshold
            WHERE score > percentile_threshold
            RETURN nodeId as node_id, score, 
                   (score - percentile_threshold) as deviation,
                   'percentile' as detection_method
            ORDER BY score DESC
            """
            params = {
                "threshold": threshold,
                "weightProperty": opts.get("weightProperty", None)
            }

        elif method == "zscore":
            # Z-Score method (statistic detection)
            query = f"""
            MATCH (n:{node_label})
            CALL gds.degree.stream(config: {{
                nodeProjection: '{node_label}',
                relationshipProjection: {relationshipProjection}
            }})
            YIELD nodeId, score
            WITH collect({{nodeId: nodeId, score: score}}) as data,
                 avg(score) as mean_score,
                 stdev(score) as std_score
            UNWIND data as item
            WITH item.nodeId as nodeId, 
                 item.score as score,
                 mean_score,
                 std_score,
                 abs(item.score - mean_score) / CASE WHEN std_score = 0 THEN 1 ELSE std_score END as zscore
            WHERE zscore > $threshold
            RETURN nodeId as node_id, score, zscore as deviation, 'zscore' as detection_method
            ORDER BY zscore DESC
            """
            params = {"threshold": threshold}

        elif method == "iqr":
            # IQR Method (Interquartile Range)
            query = f"""
            MATCH (n:{node_label})
            CALL gds.degree.stream(config: {{
                nodeProjection: '{node_label}',
                relationshipProjection: {relationshipProjection}
            }})
            YIELD nodeId, score
            WITH collect({{nodeId: nodeId, score: score}}) as data,
                 percentileCont(score, 0.25) as q1,
                 percentileCont(score, 0.75) as q3
            UNWIND data as item
            WITH item.nodeId as nodeId,
                 item.score as score,
                 q1, q3,
                 (q3 - q1) as iqr
            WITH nodeId, score, q1, q3, iqr,
                 q1 - (1.5 * iqr) as lower_bound,
                 q3 + (1.5 * iqr) as upper_bound
            WHERE score < lower_bound OR score > upper_bound
            RETURN nodeId as node_id, score,
                   CASE 
                     WHEN score < lower_bound THEN lower_bound - score
                     ELSE score - upper_bound
                   END as deviation,
                   'iqr' as detection_method
            ORDER BY deviation DESC
            """
            params = {}

        else:
            raise ValueError(f"Unknown method: {method}. Use 'iqr', 'zscore', or 'percentile'")

        return self.execute_query(query, params)

    def detect_outliers(self, node_label: str, relationship_type: str = None, options: dict = None):
        opts = options or {}
        method = opts.get("method", "percentile")
        threshold = opts.get("threshold", 0.95 if method == "percentile" else 3)
        orientation = opts.get("orientation", "BOTH")
        graph_name = opts.get("graph_name", f"temp_anomaly_{id(self)}")
        rel_type = relationship_type if relationship_type else '*'

        try:
            self.execute_query("""
                CALL gds.graph.project(
                    $graph_name,
                    $node_label,
                    {rel: {type: $rel_type, orientation: $orientation}}
                )
            """, {
                "graph_name": graph_name,
                "node_label": node_label,
                "orientation": orientation,
                "rel_type": rel_type
            })

            if method == "percentile":
                query = f"""
                CALL gds.degree.stream($graph_name)
                YIELD nodeId, score
                WITH nodeId, score, percentileCont(score, $threshold) as percentile_threshold
                WHERE score > percentile_threshold
                RETURN nodeId as node_id, score, 
                       (score - percentile_threshold) as deviation,
                       'percentile' as detection_method
                ORDER BY score DESC
                """
                params = {"graph_name": graph_name, "threshold": threshold}

            elif method == "zscore":
                query = f"""
                CALL gds.degree.stream($graph_name)
                YIELD nodeId, score
                WITH collect({{nodeId: nodeId, score: score}}) as data,
                     avg(score) as mean_score,
                     stdev(score) as std_score
                UNWIND data as item
                WITH item.nodeId as nodeId, 
                     item.score as score,
                     mean_score,
                     std_score,
                     abs(item.score - mean_score) / CASE WHEN std_score = 0 THEN 1 ELSE std_score END as zscore
                WHERE zscore > $threshold
                RETURN nodeId as node_id, score, zscore as deviation, 'zscore' as detection_method
                ORDER BY zscore DESC
                """
                params = {"graph_name": graph_name, "threshold": threshold}

            elif method == "iqr":
                query = f"""
                CALL gds.degree.stream($graph_name)
                YIELD nodeId, score
                WITH collect({{nodeId: nodeId, score: score}}) as data,
                     percentileCont(score, 0.25) as q1,
                     percentileCont(score, 0.75) as q3
                UNWIND data as item
                WITH item.nodeId as nodeId,
                     item.score as score,
                     q1, q3,
                     (q3 - q1) as iqr
                WITH nodeId, score, q1, q3, iqr,
                     q1 - (1.5 * iqr) as lower_bound,
                     q3 + (1.5 * iqr) as upper_bound
                WHERE score < lower_bound OR score > upper_bound
                RETURN nodeId as node_id, score,
                       CASE 
                         WHEN score < lower_bound THEN lower_bound - score
                         ELSE score - upper_bound
                       END as deviation,
                       'iqr' as detection_method
                ORDER BY deviation DESC
                """
                params = {"graph_name": graph_name}
            else:
                raise ValueError(f"Unknown method: {method}")

            results = self.execute_query(query, params)
            self.drop_graph(graph_name)
            return results

        except Exception as e:
            try:
                self.drop_graph(graph_name)
            except Exception as err:
                print(f"Error: {err}")
                pass
            raise e