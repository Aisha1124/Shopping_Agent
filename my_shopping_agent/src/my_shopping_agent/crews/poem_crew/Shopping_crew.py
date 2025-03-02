from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.knowledge.source.excel_knowledge_source import ExcelKnowledgeSource
import os
from dotenv import load_dotenv

load_dotenv()

# llm configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_API_KEY_1 = os.getenv("GOOGLE_API_KEY_1")
GOOGLE_API_KEY_2 = os.getenv("GOOGLE_API_KEY_2")
GOOGLE_API_KEY_3 = os.getenv("GOOGLE_API_KEY_3")



# LLM initialization
llm1 = LLM(
    model="gemini/gemini-1.5-flash",
    api_key=GOOGLE_API_KEY_1,
    temperature=0.7
)

llm2 = LLM(
    model="gemini/gemini-1.5-flash",
    api_key=GOOGLE_API_KEY_2,
    temperature=0.7
)

llm3 = LLM(
    model="gemini/gemini-1.5-flash",
    api_key=GOOGLE_API_KEY_3,
    temperature=0.7
)

# Fix: Embedder configuration
embedder = {
    "provider": "google",
    "config": {
        "api_key": GEMINI_API_KEY,
        "model": "models/text-embedding-004"
    }
}

# Excel source configuration
excel_source = ExcelKnowledgeSource(
    file_paths=["spreadsheet.xlsx"],
    embedder=embedder
)

@CrewBase
class ShopCrew:
    """Shop Crew"""
    agents_config = "config/agents.yaml"
    tasks_config = "config/agents.yaml"
 
    
    @agent
    def Orchestrator(self) ->Agent:
        return Agent(
            config=self.agents_config['Orchestrator'],
            verbose=True,
            knowledge_sources=[excel_source],
            llm=llm1,
            embedder=embedder
        )
    
    @agent
    def Catalog(self) -> Agent:
        return Agent(
            config=self.agents_config['Catalog'],
            knowledge_sources=[excel_source],
            llm=llm2,
            verbose=True,
            embedder=embedder
        )
    
    @agent
    def Cart(self) -> Agent:
        return Agent(
            config=self.agents_config['Cart'],
            verbose=True,
            llm=llm3
        )
    @task
    def interact_with_user(self) -> Task:
        return Task(
            description="Interact with the user, understand their shopping needs and extract relevant details.",
            expected_output="Entract with user and Understand their shopping needs from the prompt of user",
            agent=self.Orchestrator()

    )
    
    @task
    def extract_product_from_catalog(self) -> Task:
        return Task(
            description="Search the product catalog based on requirements provided by the orchestrator.",
            expected_output="A structured matching product from the Catalog on the requirements of the user",
            agent=self.Catalog()
             
    )
    
    @task
    def add_to_cart(self) -> Task:
        return Task(
            description="Add user-confirmed products to a shopping cart and save the information in a text file.",
            expected_output=" A text file containing the shopping cart with all selected products and relevant details.",
            agent=self.Cart()

    )
    
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            knowledge_sources=[excel_source],
            process=Process.sequential,
            verbose=True,
            embedder=embedder
    )