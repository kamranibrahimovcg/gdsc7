# GDSC7 - BreakingRead Solution
## What is the GDSC?
The Capgemini Global Data Science Challenge (GDSC) is half training, half competition, and is a great opportunity for you to develop and grow your skills, contribute to make a difference, and have fun while doing it.
## About the project
### The grade-AI generation edition. Re-righting Education with data & AI!
![alt text](https://gdsc.ce.capgemini.com/static/webpage_banner_updated-85d74a400281e38bffbe260250303dc2.png)
**The 2024 Capgemini Global Data Science Challenge** aims to use AI-driven analysis of the PIRLS 2021 dataset to empower education stakeholders with insights for data-driven policies and practices that improve global children's reading proficiency and address the learning crisis.

## File Structure
```
├── src/
│   ├── static/
│   │   ├── __init__.py
│   │   ├── app.py
│   │   ├── ChatBedrockWrapper.py
│   │   ├── submission.py
│   │   └── util.py
│   ├── submission/
│   │   ├── crews/ 
│   │   │   ├── BreakingRead_agent.py    # The main Agent(Solution)
│   │   │   ├── util.py                  # The custom Agent Tools
│   │   │   └── __init__.py
│   │   ├── create_submission.py
│   │   └── __init__.py
│   └── __init__.py
├── README.md                       # Project documentation
└── requirements.txt                # Python dependencies
```

## Tools
- LLM: Anthropic Sonnet 3.5.
- LLM Orchestrator: LangChain, LangGraph ReAct agent.
- Database: PostgreSQL for the PIRLS dataset.
- AWS Cloud Platform: Amazon SageMaker, Bedrock, CodeCommit, ECS.
- Data Visualization: QuickChart for chart creation.

### Usage
Important: 
**requires AWS credentials** and **PIRLS database connection credentials**

*Installing the necessary libraries*
```
!pip install -r ./requirements.txt
```

*Load modules*
```
import dotenv

from src.static.ChatBedrockWrapper import ChatBedrockWrapper
from src.static.submission import Submission
from src.submission.crews.agentFOX_tools import AgentFOXPIRLSCrew

dotenv.load_dotenv()
```
## Explanation
The primary concept behind this solution is to create an assistant that is both stable and dynamic. **Stable** means that the assistant, powered by a large language model (LLM), maintains reliability, avoids generating inaccurate information (hallucinations), and adheres strictly to its designated functions. **Dynamic** refers to its flexibility in handling a wide range of queries and providing diverse types of outputs according to user requirements.

At the heart of this architecture is a **create_react_agent** from the LangChain library. This agent utilizes several tools, including **SQLDatabaseToolkit** for SQL-based queries, **generate_chart_url** for creating charts, and **TavilySearchResults** for web search. The agent intelligently decides which tool to use based on the user’s query, allowing it to be resource-efficient. For example, if a user’s query doesn’t require a chart, the agent skips the chart tool, conserving both time and processing resources. This selective tool usage contributes to the dynamic quality of the architecture.

Another notable aspect of this solution is its simplicity: it relies on just three tools, with two only used as needed. In many cases, the SQL toolkit alone suffices to answer the majority of questions, reflecting the stability of the design. After obtaining the initial query result, a straightforward LLM query is often enough to generate a polished and accurate final output for the user.

### Credits to:
* [Capgemini GDSC](https://gdsc.ce.capgemini.com/app/)
* [GitHub GDSC7](https://github.com/cg-gdsc/GDSC-7/)
* [PIRLS 2021 Study](https://pirls2021.org/)
