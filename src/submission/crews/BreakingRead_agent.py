from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain import hub
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.prebuilt import create_react_agent
from src.submission.crews.util import InfoSQLDatabaseTool2, generate_chart_url, internet_search

import os
import time
import requests
import boto3

# Database
DB_PASSWORD=''
DB_USER=''
DB_ENDPOINT=''
DB_PORT=''
DB_NAME ='postgres'
DB_URL = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_ENDPOINT}:{DB_PORT}/{DB_NAME}'
DB = SQLDatabase.from_uri(DB_URL, sample_rows_in_table_info=500)


class BreakingReadPIRLS(Submission):

  def __init__(self, llm: ChatBedrockWrapper):
      self.llm = llm


  def run(self, question: str) -> str:

      # Formulate query prompt for the agent
      querying_prompt = f"""
      # Data Engineer for PIRLS Project

      ## Role
      You are the Data Engineer for the Progress in International Reading Literacy Study (PIRLS) project.

      ## Goal
      Your primary objective is to retrieve accurate and relevant data from the PIRLS 2021 dataset to answer questions from the Lead Data Analyst, and to return this information to the requestor in a clear and concise manner.
      Sometimes you can asked to visualize the data in that cases use "generate_chart_url" tool.
      If answering question requires additional info which does not have PIRSL 2021, use "internet_search" tool.


      ## Expertise and Skills
      - Expert in PostgreSQL, particularly adept at writing efficient and effective queries
      - Proficient in data retrieval, manipulation, and analysis
      - Strong understanding of the PIRLS 2021 dataset structure and relationships

      ## Core Responsibilities
      1. Interpret and analyze data requests from the Lead Data Analyst
      2. Craft precise PostgreSQL queries to extract the required information
      3. Provide clear explanations of your data retrieval process and findings
      4. Suggest alternative data sources or approaches when direct answers are not available

      ## Query Guidelines
      - Always limit your queries to return only the necessary data
      - NEVER return more than 100 rows of data in a single query result
      - Write queries that produce the final required results with minimal steps (e.g., return mean values directly rather than lists of individual values)
      - Utilize appropriate joins, aggregations, and filtering to ensure accuracy and efficiency

      ## Response Format
      For each data request, provide:
      1. The PostgreSQL query used to retrieve the data
      2. A concise summary of the results
      3. An explanation of how you arrived at the answer and any assumptions made
      4. If applicable, visualizations or formatted tables to present the data clearly

      Additional info about database:

      About Countries table:
      Some countries are mentioned not in conventional way, like: Norway (5), BFL Belgium (Flemish), Belgium (French), South Africa, South Africa (6)
      And some countries mentioned also with cities, like: (Alberta, Canada), (British Columbia, Canada), (Newfoundland & Labrador, Canada), (Quebec, Canada), (Moscow City, Russian Federation), (Dubai, United Arab Emirates), (Abu Dhabi, United Arab Emirates)

      # Content & Connections
      Generally Entries tables contain questions themselves and Answers tables contain answers to those question.
      For example StudentQuestionnaireEntries table contains questions asked in the students' questionnaire and
      StudentQuestionnaireAnswers table contains answers to those question.

      All those tables usually can be joined using the Code column present in both Entries and Answers.

      Example connections:
      Students with StudentQuestionnaireAnswers on Student_ID and StudentQuestionnaireAnswers with StudentQuestionnaireEntries on Code.
      Schools with SchoolQuestionnaireAnswers on School_ID and SchoolQuestionnaireAnswers with SchoolQuestionnaireEntries on Code.
      Teachers with TeacherQuestionnaireAnswers on Teacher_ID and TeacherQuestionnaireAnswers with TeacherQuestionnaireEntries on Code.
      Homes with HomeQuestionnaireAnswers on Home_ID and HomeQuestionnaireAnswers with HomeQuestionnaireEntries on Code.
      Curricula with CurriculumQuestionnaireAnswers on Home_ID and CurriculumQuestionnaireAnswers with CurriculumQuestionnaireEntries on Code.

      Benchmarks table cannot be joined with any other table but it keeps useful information about how to interpret
      student score as one of the 4 categories.


      ## Example query
      A students' gender is stored as an answer to one of the questions in StudentQuestionnaireEntries table.
      The code of the question is "ASBG01" and the answer to this question can be "Boy", "Girl",
      "nan", "<Other>" or "Omitted or invalid".

      A simple query that returns the gender for each student can look like this:
      ```
      SELECT S.Student_ID,
          CASE
              WHEN SQA.Answer = 'Boy' THEN 'Male'
              WHEN SQA.Answer = 'Girl' THEN 'Female'
          ELSE NULL
      END AS "gender"
      FROM Students AS S
      JOIN StudentQuestionnaireAnswers AS SQA ON SQA.Student_ID = S.Student_ID
      JOIN StudentQuestionnaireEntries AS SQE ON SQE.Code = SQA.Code
      WHERE SQA.Code = 'ASBG01'
      ```
      ## Example question and query

      Which country had all schools closed for more than eight weeks?
      ```
      WITH schools_all AS (
      SELECT C.Name, COUNT(S.School_ID) AS schools_in_country
      FROM Schools AS S
      JOIN Countries AS C ON C.Country_ID = S.Country_ID
      GROUP BY C.Name
      ),
      schools_closed AS (
          SELECT C.Name, COUNT(DISTINCT SQA.School_ID) AS schools_in_country_morethan8
          FROM SchoolQuestionnaireEntries AS SQE
          JOIN SchoolQuestionnaireAnswers AS SQA ON SQA.Code = SQE.Code
          JOIN Schools AS S ON S.School_ID = SQA.School_ID
          JOIN Countries AS C ON C.Country_ID = S.Country_ID
          WHERE SQE.Code = 'ACBG19' AND SQA.Answer = 'More than eight weeks of instruction'
          GROUP BY C.Name
      ),
      percentage_calc AS (
          SELECT A.Name, schools_in_country_morethan8 / schools_in_country::float * 100 AS percentage
          FROM schools_all A
          JOIN schools_closed CL ON A.Name = CL.Name
      )
      SELECT *
      FROM percentage_calc
      WHERE percentage = 100;
      ```

      Remember, your role is crucial in ensuring the accuracy and reliability of the PIRLS project data analysis. Always strive for precision, efficiency, and clarity in your work.
      {question}

"""

    # Adjustments to the SQLDatabaseToolkit
    toolkit = SQLDatabaseToolkit(db=DB, llm=self.llm)
    tools = toolkit.get_tools()
    tools[1] = InfoSQLDatabaseTool2(db=DB, description=tools[1].description)
    
     # Pull prompt from LangChain
    prompt_template = hub.pull("langchain-ai/sql-agent-system-prompt")
    system_message = prompt_template.format(dialect="SQLite", top_k=1000)
    # Create agent executor
    agent_executor = create_react_agent(self.llm, tools+[generate_chart_url, internet_search], state_modifier=system_message)
    
    # Run agent with query
    agent_output = agent_executor.invoke(
      {"messages": [HumanMessage(content=querying_prompt)]},
      {"recursion_limit": 150}
    )    
    
    # Extract query and visualization URL from agent's output
    url=''
    query=''
    for x in agent_output['messages']:
      if isinstance(x, AIMessage):
        try:
          query = x.tool_calls[0]['args']['query']
        except:
          pass
      if isinstance(x, ToolMessage) and x.name=='generate_chart_url':
        try:
          filename = f"chart_{round(time.time())}"
          img_data = requests.get(x.content).content

          from io import BytesIO
          img_data = BytesIO(img_data)

          # Upload the image to S3
          session = boto3.Session()
          s3 = session.client('s3')
          bucket_name = ''
          s3.upload_fileobj(img_data, bucket_name, filename)

          # Build and return the S3 URL
          s3_url = f'https://{bucket_name}.s3.amazonaws.com/{filename}'
          url = f"For visualisation use ![chart_name]({s3_url}) to show the plot"
        except Exception as e:
          print(f"An error occurred: {str(e)}")
    
    # Prepare final response prompt with query results
    result = agent_output['messages'][-1].content

    final_output_prompt=f"""
      Given the following scenario:
      
      A curious data analyst is exploring a company database. He has a burning question:
      
      {question}
      
      To find the answer, data analyst crafts this SQL query:
      
      ```sql
      {query}
      
      After running the query, the database returns the following result:
      {result}
      
      Your task:
      
      Interpret the data as if you were data analyst, uncovering the story hidden in these numbers and facts.
      Answer data analyst's original question in a clear and engaging way.
      {url}
      If applicable, suggest a follow-up question or area for data analyst to explore next in a style like:
      Do you know learn more about this topic? Ask me a following question: 'question'
      
      Present your response in a well-formatted markdown structure, using headers, bullet points, or tables as appropriate to make the information easily digestible.
      Don't overuse these methods output should be short and simple.
      Remember, don't show your input data, you're not just providing raw data - you're helping data analyst understand the narrative behind the numbers!
      # Always output numbers in numbers, never in words.
      # Always output short and relevant answer, maximum 10 sentences.
      # If you asked about different topic, unrelated to you role, goal, expertise, skills and core responsibilities politely refuse to answer.
    """
    
    # Send final prompt to language model for structured response
    message = [
      ("system", final_output_prompt),
      ("human", question)]
    
    response = self.llm.invoke(message, config={"recursion_limit": 150})

    return f"{response.content} \n\n\n[**DISCLAIMER**: *This response is generated by an AI language model.*]"
    
