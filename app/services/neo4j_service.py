from app.services.base_service import BaseService
from typing import List

class Neo4jService(BaseService):
    def get_graph_stats(self) -> dict:
        """Return graph statistics"""
        query = """
            MATCH (n)
            WITH COUNT(n) as nodes, labels(n) as label_list
            WITH nodes, COLLECT(DISTINCT label_list[0]) as labels
            MATCH ()-[r]->()
            WITH nodes, labels, COUNT(r) as relationships, type(r) as rel_type
            WITH nodes, labels, relationships, COLLECT(DISTINCT rel_type) as relationship_types
            RETURN {
                nodes: nodes,
                relationships: relationships,
                node_labels: labels,
                relationship_types: relationship_types,
                node_label_count: size(labels),
                relationship_type_count: size(relationship_types)
            } as stats
        """
        result = self.execute_query(query)
        return result[0]['stats'] if result else {}

    def get_node_by_id(self, node_id: str) -> dict:
        """Retrieve a node by its ID."""
        query = """
        MATCH (n) WHERE id(n) = $node_id
        RETURN id(n) as node_id, 
               labels(n) as labels, 
               properties(n) as properties
        """
        result = self.execute_query(query, {"node_id": node_id})
        return result[0] if result else None

    def get_detailed_stats(self) -> dict:
        """Returns detailed statistics by label and relationship type"""
        # Stats by label
        node_stats_query = """
        MATCH (n)
        WITH labels(n)[0] as label, COUNT(n) as count
        WHERE label IS NOT NULL
        RETURN collect({label: label, count: count}) as node_stats
        """

        # Stats by relationship type
        rel_stats_query = """
        MATCH ()-[r]->()
        WITH type(r) as rel_type, COUNT(r) as count
        RETURN collect({type: rel_type, count: count}) as relationship_stats
        """

        # Average degree
        degree_query = """
        MATCH (n)-[r]-()
        WITH n, COUNT(r) as degree
        RETURN {
            avg_degree: avg(degree),
            min_degree: min(degree),
            max_degree: max(degree),
            std_degree: stdev(degree)
        } as degree_stats
        """

        node_result = self.execute_query(node_stats_query)
        rel_result = self.execute_query(rel_stats_query)
        degree_result = self.execute_query(degree_query)

        return {
            "nodes_by_label": node_result[0]['node_stats'] if node_result else [],
            "relationships_by_type": rel_result[0]['relationship_stats'] if rel_result else [],
            "degree_statistics": degree_result[0]['degree_stats'] if degree_result else {}
        }

    def get_node_with_relationships(self, node_id: int, limit: int = 50) -> dict:
        """Retrieve a node with its relationships (incoming and outgoing)"""
        query = """
        MATCH (n) WHERE id(n) = $node_id
        OPTIONAL MATCH (n)-[r_out]->(target)
        WITH n, collect(DISTINCT {
            type: type(r_out),
            target_id: id(target),
            target_labels: labels(target),
            properties: properties(r_out)
        })[0..$limit] as outgoing
        OPTIONAL MATCH (source)-[r_in]->(n)
        WITH n, outgoing, collect(DISTINCT {
            type: type(r_in),
            source_id: id(source),
            source_labels: labels(source),
            properties: properties(r_in)
        })[0..$limit] as incoming
        RETURN {
            node: {
                id: id(n),
                labels: labels(n),
                properties: properties(n)
            },
            outgoing_relationships: outgoing,
            incoming_relationships: incoming,
            outgoing_count: size(outgoing),
            incoming_count: size(incoming)
        } as result
        """
        result = self.execute_query(query, {"node_id": node_id, "limit": limit})
        return result[0]['result'] if result else None

    def search_nodes(self, label: str = None, property_filters: dict = None,
                     limit: int = 100) -> List[dict]:
        """
        Search for nodes by label and/or properties

            Args:
                label: Node label (optional)
                property_filters: Dict of filters {property_name: value}
                limit: Maximum number of results
        """
        # Build the MATCH clause
        match_clause = f"MATCH (n:{label})" if label else "MATCH (n)"

        # Build the WHERE clauses
        where_clauses = []
        params = {"limit": limit}

        if property_filters:
            for key, value in property_filters.items():
                param_name = f"prop_{key}"
                where_clauses.append(f"n.{key} = ${param_name}")
                params[param_name] = value

        where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        query = f"""
        {match_clause}
        {where_clause}
        RETURN id(n) as node_id,
               labels(n) as labels,
               properties(n) as properties
        LIMIT $limit
        """

        return self.execute_query(query, params)

    def get_neighbors(self, node_id: int, relationship_type: str = None,
                      direction: str = "BOTH", limit: int = 50) -> List[dict]:
        """
        Retrieve a node’s neighbors

            Args:
                node_id: Source node ID
                relationship_type: Relationship type (optional)
                direction: "OUTGOING", "INCOMING", or "BOTH"
                limit: Maximum number of neighbors
        """
        rel_pattern = f"[r:{relationship_type}]" if relationship_type else "[r]"

        if direction == "OUTGOING":
            pattern = f"(n)-{rel_pattern}->(neighbor)"
        elif direction == "INCOMING":
            pattern = f"(n)<-{rel_pattern}-(neighbor)"
        else:  # BOTH
            pattern = f"(n)-{rel_pattern}-(neighbor)"

        query = f"""
        MATCH (n) WHERE id(n) = $node_id
        MATCH {pattern}
        RETURN DISTINCT id(neighbor) as neighbor_id,
               labels(neighbor) as labels,
               properties(neighbor) as properties,
               type(r) as relationship_type
        LIMIT $limit
        """

        return self.execute_query(query, {"node_id": node_id, "limit": limit})

    def get_subgraph(self, node_ids: List[int]) -> dict:
        """
        Retrieve a subgraph from a list of node IDs

        Returns the nodes AND the relationships between them
        """
        query = """
        MATCH (n) WHERE id(n) IN $node_ids
        WITH collect(n) as nodes
        UNWIND nodes as n1
        UNWIND nodes as n2
        OPTIONAL MATCH (n1)-[r]->(n2)
        WITH nodes, collect(DISTINCT {
            source: id(n1),
            target: id(n2),
            type: type(r),
            properties: properties(r)
        }) as relationships
        RETURN {
            nodes: [n IN nodes | {
                id: id(n),
                labels: labels(n),
                properties: properties(n)
            }],
            relationships: [r IN relationships WHERE r.type IS NOT NULL | r]
        } as subgraph
        """
        result = self.execute_query(query, {"node_ids": node_ids})
        return result[0]['subgraph'] if result else {"nodes": [], "relationships": []}

    def check_connection_exists(self, start_id: int, end_id: int,
                                relationship_type: str = None, max_hops: int = 5) -> bool:
        """Verify if two nodes are connected"""
        rel_pattern = f"[:{relationship_type}*..{max_hops}]" if relationship_type else f"[*..{max_hops}]"

        query = f"""
        MATCH (start) WHERE id(start) = $start_id
        MATCH (end) WHERE id(end) = $end_id
        RETURN EXISTS((start)-{rel_pattern}-(end)) as connected
        """

        result = self.execute_query(query, {"start_id": start_id, "end_id": end_id})
        return result[0]['connected'] if result else False

    def get_database_info(self) -> dict:
        """Retrieve information about the Neo4j database"""
        query = """
        CALL dbms.components() YIELD name, versions, edition
        RETURN {
            name: name,
            version: versions[0],
            edition: edition
        } as db_info
        """

        # Constraints
        constraints_query = """
        SHOW CONSTRAINTS
        YIELD name, type, entityType, labelsOrTypes, properties
        RETURN collect({
            name: name,
            type: type,
            entity_type: entityType,
            labels_or_types: labelsOrTypes,
            properties: properties
        }) as constraints
        """

        # Index
        indexes_query = """
        SHOW INDEXES
        YIELD name, type, entityType, labelsOrTypes, properties
        RETURN collect({
            name: name,
            type: type,
            entity_type: entityType,
            labels_or_types: labelsOrTypes,
            properties: properties
        }) as indexes
        """

        try:
            db_result = self.execute_query(query)
            constraints_result = self.execute_query(constraints_query)
            indexes_result = self.execute_query(indexes_query)

            return {
                "database": db_result[0]['db_info'] if db_result else {},
                "constraints": constraints_result[0]['constraints'] if constraints_result else [],
                "indexes": indexes_result[0]['indexes'] if indexes_result else []
            }
        except Exception as e:
            return {"error": str(e)}