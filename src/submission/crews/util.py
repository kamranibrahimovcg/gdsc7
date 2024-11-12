from typing import Optional
import os
from langchain_core.tools import tool
from langchain_community.tools.sql_database.tool import InfoSQLDatabaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_community.tools.tavily_search import TavilySearchResults

# Database
DB_PASSWORD=''
DB_USER=''
DB_ENDPOINT=''
DB_PORT=''
DB_NAME ='postgres'
DB_URL = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_ENDPOINT}:{DB_PORT}/{DB_NAME}'
DB_200_tables = SQLDatabase.from_uri(DB_URL, sample_rows_in_table_info=200)
DB_5_tables = SQLDatabase.from_uri(DB_URL, sample_rows_in_table_info=5)

# API key for Tavily Search tool
os.environ["TAVILY_API_KEY"] = ""

class InfoSQLDatabaseTool2(InfoSQLDatabaseTool):
    def _run(
        self,
        table_names: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Get the schema for tables in a comma-separated list."""
        tables = [
            'benchmarks', 'countries', 'studentscoreentries',
            'studentquestionnaireentries', 'schoolquestionnaireentries', 'homequestionnaireentries', 'curriculumquestionnaireentries',

            'students', 'studentquestionnaireanswers', 'studentscoreresults', 'studentteachers',
            'curricula', 'curriculumquestionnaireanswers', 
            'homes', 'homequestionnaireanswers', 
            'schools', 'schoolquestionnaireanswers',
            'teachers', 'teacherquestionnaireanswers', 'teacherquestionnaireentries']

        tables_schema = []
        for pt in tables:
            db_use = self.db
            if pt in ['benchmarks', 'countries', 'studentscoreentries', 'studentquestionnaireentries', 'schoolquestionnaireentries', 'homequestionnaireentries', 'curriculumquestionnaireentries']:
                db_use = DB_200_tables
            else: db_use = DB_5_tables
            tables_schema.append(db_use.get_table_info_no_throw([pt]))
        return "\n\n".join(tables_schema)

@tool

def generate_chart_url(
chart_type: str,
    labels: list[str],
    data: list[dict[str, list[int]]],
    title: str = None,
    width: int = 500,
    height: int = 300,
    device_pixel_ratio: int = 2,
    background_color: str = "transparent",
    version: str = "2.9.4",
    format: str = "png",
    encoding: str = "url"
) -> str:
    """
    Generates a QuickChart API URL for creating a variety of visualizations (bar, pie, line charts, etc.).

    Parameters:
    - chart_type (str): Type of chart (e.g., 'bar', 'line', 'pie').
    - labels (list): Labels for the x-axis or categories (e.g., months, years).
    - data (list of dicts): Data series, with each dataset as a dictionary containing 'label' and 'data' (e.g., [{"label": "Dataset1", "data": [10, 20, 30]}]).
    - title (str, optional): Title for the chart.
    - width (int): Width of the image in pixels (default 500).
    - height (int): Height of the image in pixels (default 300).
    - device_pixel_ratio (int): Device pixel ratio, typically 1 or 2 (default 2).
    - background_color (str): Background color in rgb, hex, or color name (default transparent).
    - version (str): Chart.js version to use (default 2.9.4).
    - format (str): Output format such as 'png', 'jpg', 'svg' (default png).
    - encoding (str): Encoding type, either 'url' or 'base64' (default url).

    Returns:
    - str: Fully formatted QuickChart API URL to generate the visualization.
    """

    # Validations for input parameters
    if not isinstance(chart_type, str):
        raise ValueError("chart_type must be a string.")
    if not isinstance(labels, list):
        raise ValueError("labels must be a list.")
    if not all(isinstance(dataset, dict) and 'label' in dataset and 'data' in dataset for dataset in data):
        raise ValueError("data must be a list of dictionaries, each with 'label' and 'data' keys.")

    # Create the chart configuration
    chart_config = {
        "type": chart_type,
        "data": {
            "labels": labels,
            "datasets": data
        },
        "options": {
            "title": {
                "display": bool(title),
                "text": title
            }
        }
    }

    # URL-encode the JSON configuration
    encoded_chart = urllib.parse.quote(json.dumps(chart_config))

    # Construct and return the full URL
    url = (
        f"https://quickchart.io/chart?c={encoded_chart}"
        f"&width={width}&height={height}"
        f"&devicePixelRatio={device_pixel_ratio}"
        f"&backgroundColor={urllib.parse.quote(background_color)}"
        f"&version={version}&format={format}&encoding={encoding}"
    )

    return url

@tool
def internet_search(query: str, num_results: int = 5) -> list[dict]:
    """
    Searches the internet using Tavily Search API and returns top results.

    Parameters:
    - query (str): The search term or question to query.
    - num_results (int, optional): Number of search results to return (default is 5).

    Returns:
    - list[dict]: List of search result dictionaries.
    """
    tavily_tool = TavilySearchResults(max_results=5)
    return tavily_tool.invoke(query)
