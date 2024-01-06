import os, re, json, asyncio
from crewai import Agent, Task, Crew, Process
from langchain.tools import DuckDuckGoSearchRun

idea = "Django programming with React frontend managed with an API"
goal = "develop a Customer Relationship Management system"

with open("./api_key.txt", 'r') as f:
    key = f.read().strip()
    os.environ["OPENAI_API_KEY"] = key
    api_key = key

def parse_roles(input_string, search_tool):
  pattern = r'"role":\s*"(.*?)",\s*"goal":\s*"(.*?)",\s*"backstory":\s*"(.*?)"'
  matches = re.findall(pattern, input_string, re.DOTALL)
  main = [
    Agent(role=match[0], goal=match[1], backstory=match[2], verbose=True, allow_delegation=True, tools=[search_tool]) 
    for match in matches]
  return main

async def parse_tasks(input_string, choices, agents):
  pattern = r'"description":\s*"(.*?)",\s*"agent":\s*"(.*?)"'
  matches = re.findall(pattern, input_string, re.DOTALL)
  choiceformat = json.dumps({'choice': "<role title>"})
  choicesAsString = json.dumps([{'choice': choice} for choice in choices])
  agentList = []
  for match in matches:
    matchString = match[1]
    prompt="(("+ choicesAsString + ")) ((("+ matchString +"))) Which of ((these choices)) is most similar to (((this)))? Return const format = " + choiceformat
    # closest_match = await find_closest_match_openai(prompt=prompt, api_key=api_key)
    index = None
    agent = None
    try:
      index = [ agent.role for agent in agents].index(matchString)
      agent = agents[index]
    except:
       agent = imagineer
    agentList.append({'description': match[0],'agent': agent})
  main = [
    Task(description=task['description'], agent=task['agent']) 
    for task in agentList
  ]
  return main

# Begin Setup

search_tool = DuckDuckGoSearchRun()

imagineer = Agent(
  role='Creative Wizard',
  goal='Unlock the deep secrets of the universe through creative thought, novel connections, and concrete manifestations.',
  backstory="""Much like Mr. Wonka, you dream and create universes in your mind. There are no limits to the new connections you could make.""",
  verbose=True,
  allow_delegation=False,
  tools=[search_tool]
  # llm=OpenAI(temperature=0.7, model_name="gpt-4"). It uses langchain.chat_models, default is GPT4
)

teamMemberFormat = json.dumps({
    'role': "<the teammate's title as string>",
    'goal': "<a concise focus statement that describes the perspective of the teammate>",
    'backstory': "<a longer description of the teammate's story and goal not to exceed 200 words>"
})

taskFormat = json.dumps({
    'description': '<a single, actionable goal for the ideal agent to perform>',
    'agent': '<One of the members from the (((team)))>'
})

async def main():
# Create tasks for your agents
  task1 = Task(
    description="""Imagine the ideal team for """ + idea + """. Return a list of individuals who will form this team. Each individual
    return const format = """ + teamMemberFormat,
    agent=imagineer
  )

  task1_Crew = Crew(
    agents=[imagineer],
    tasks=[task1],
    verbose=2, 
    process=Process.sequential 
  )
  task1_response = task1_Crew.kickoff()
  teamMates = parse_roles(task1_response, search_tool)
  teamMates_string = json.dumps([{'role': member.role, 'goal': member.goal, 'backstory': member.backstory} for member in teamMates])

  task2 = Task(
      description="""(((""" + teamMates_string +"""))) Consider (((this team))). Imagine the ideal sequential task list that maximizes their contribution to """ + goal + """. Each task 
      return const format = """ + taskFormat,
      agent=imagineer
  )
  task2_Crew = task1_Crew
  task2_Crew.tasks = [task2]
  task2_response = task2_Crew.kickoff()

  choices = [ member.role for member in teamMates]
  teamTasks = await parse_tasks(input_string=task2_response, choices=choices, agents=teamMates)
  task3_Crew = Crew(
     agents=[member for member in teamMates],
     tasks=teamTasks,
     verbose=2,
     process=Process.sequential
  )
  task3_response = task3_Crew.kickoff()

if __name__ == "__main__":
   asyncio.run(main())