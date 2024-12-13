from omikb.omikb import kb_toolbox
import yaml
from rdflib import Graph, Literal, URIRef
from discomat.cuds.cuds import Cuds
from discomat.ontology.namespaces import MISO, MIO


class YamlFetcher:
    def __init__(self, kb, filename="output.yaml"):
        self.kb = kb
        self.filename = filename

    def fetch_all_yaml_blobs(self):
        """
        Fetches all YAML blobs from the knowledge base and processes the results.
        """
        sparql_query = """
        PREFIX ns2: <http://materials-discovery.org/semantics/mio#>
        SELECT ?s ?p ?o
        WHERE {
            ?s ?p ?o .
        }
        """

        print("Fetching all properties from the Knowledge Base...")
        response = self.kb.query(sparql_query)

        if response.status_code == 200:
            results = response.json()
            print(f"SPARQL Query Response: {results}")

            if results['results']['bindings']:
                yaml_blobs = []
                # Process each result and check if the object is YAML data
                for binding in results['results']['bindings']:
                    subject = binding['s']['value']
                    predicate = binding['p']['value']
                    object_value = binding['o']['value']

                    if predicate.endswith("has_file"):  # Check for the has_file predicate
                        try:
                            # Parse the YAML content if it's in the object
                            yaml_data = yaml.safe_load(object_value)
                            yaml_blobs.append(yaml_data)
                        except yaml.YAMLError as e:
                            print(f"Error parsing YAML: {e}")
                    else:
                        print(f"Skipping non-YAML object: {object_value}")

                if yaml_blobs:
                    return yaml_blobs
                else:
                    print("No YAML blobs found.")
                    return None
            else:
                print("No properties found in the Knowledge Base.")
                return None
        else:
            raise RuntimeError(f"SPARQL query failed with status {response.status_code}: {response.text}")

    def save_yaml_to_file(self, yaml_data):
        """
        Saves parsed YAML data to a file.
        """
        with open(self.filename, 'w') as file:
            yaml.dump(yaml_data, file, default_flow_style=False)
        print(f"YAML data saved to {self.filename}")

    def run(self):
        """
        Runs the whole process: fetch YAML blobs and save them to a file.
        """
        if self.kb.is_online:
            yaml_blobs = self.fetch_all_yaml_blobs()
            if yaml_blobs:
                self.save_yaml_to_file(yaml_blobs[0])  # Save the first YAML blob, or modify if you want to combine
        else:
            print("Unable to connect to the knowledge base.")


def get_yaml(output="output.yaml"):
    """
    Run function that fetches YAML data from the knowledge base and saves it to a file.
    """
    # Initialize the knowledge base tool
    kb = kb_toolbox()

    # Create an instance of YamlFetcher with the desired filename
    fetcher = YamlFetcher(kb, filename=output)

    # Run the process
    fetcher.run()


def yaml2rdf(input_file: str, output_file: str):
    """
    Convert YAML data to RDF and serialize it.

    Args:
        input_file (str): The path to the input YAML file.
        output_file (str): The path where the RDF Turtle file will be saved.
    """

    # Load YAML data while preserving the structure and indentation
    def ordered_load(stream):
        """Load YAML file and preserve order in nested structures"""
        return yaml.load(stream, Loader=yaml.FullLoader)

    # Function to dump YAML and preserve the original formatting
    def ordered_dump(data, **kwargs):
        """Dump YAML while preserving formatting and indentation"""
        return yaml.dump(data, Dumper=yaml.Dumper, default_flow_style=False, allow_unicode=True, **kwargs)

    # Parse YAML file with explicit order preservation
    with open(input_file, "r") as yaml_file:
        yaml_content = ordered_load(yaml_file)

    # Convert the loaded YAML content back into a string with proper formatting and indentation
    yaml_blob = ordered_dump(yaml_content)

    # Create a Cuds object to represent the YAML blob
    data = Cuds(ontology_type=MIO.SimulationResult, description="data")
    data.add(MIO.has_file, Literal(yaml_blob, datatype=URIRef(
        'http://www.w3.org/2001/XMLSchema#string')))  # Store the YAML as a literal

    # RDF serialization setup
    rdf_results = [data.graph]

    # Create the total RDF graph
    g_total = Graph()
    g_total += data.graph

    # Add all individual simulation result graphs
    for g in rdf_results:
        g_total += g

    # Output the RDF graph to a Turtle file
    g_total.serialize(output_file, format="ttl")
    print(f"RDF data serialized to {output_file}")
