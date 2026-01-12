

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AIMessage
from typing import Literal
from langchain_openai import ChatOpenAI
from . import utils
from .models import GraphState, CriticResult, GenerationAsset, ProductMetadata, ADCPSchema
from pathlib import Path
import os
import emoji
from dotenv import load_dotenv


class AdCreatorAgents:
    def __init__(self):
        load_dotenv()
        OPEN_API_KEY = os.getenv("OPENAI_API_KEY")
        self.graph = StateGraph(GraphState)
        self.graph.add_node(self.generator_node)
        self.graph.add_node(self.critic_node)
        self.graph.add_edge(START, "generator_node")
        self.graph.add_edge("generator_node", "critic_node")
        self.graph.add_conditional_edges("critic_node", self.should_continue, ["generator_node", END])
        self.graph = self.graph.compile()
        self.generator_llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key=OPEN_API_KEY).with_structured_output(GenerationAsset) #Structured output enforcement
        self.critic_llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key=OPEN_API_KEY).with_structured_output(CriticResult)
        self.final_state:GraphState = None

    def generator_node(self, state: GraphState):

        """Generate ad content for a product name and target audience. 
           If the critic node rejects the generated content, re-generate the content based on the feedback from the critic node."""
        system_prompt = utils.AD_GENERATION_PROMPT + f" {state.product_metadata}"
        if state.critic_result:
            if state.critic_result.accepted == False:
                system_prompt += f"""This is not first time you are generating the ad text. 
                                 You generated before and received the following feedback: {state.critic_result.feedback}"""
        
        generation_asset = self.generator_llm.invoke(system_prompt)
        #Deterministically generate content length.
        generation_asset.content_metadata.length = len(generation_asset.content)
        print(f"Generated content: {generation_asset.content}")
        return {
            "messages": [AIMessage(content=generation_asset.content)],
            "generation_asset": generation_asset
        }
    
    def critic_node(self, state: GraphState):

        """Evaulate the latest generated content for a given target audience and product name."""
        
        generated_ad = state.generation_asset.content
        word_count = len(generated_ad.split())
        emoji_count = len(emoji.emoji_list(generated_ad))

        critic_result = CriticResult(feedback="", accepted=False)

        errors = []
        if word_count > 15:
            errors.append("Word count is more than 15.")
        if emoji_count != 1:
            errors.append("Emoji count is not 1.")

        if errors:
            critic_result.feedback = " ".join(errors)
        else:
            system_prompt = (utils.CRITICS_PROMPT+ f"Generated content: {generated_ad}")
            critic_result = self.critic_llm.invoke(system_prompt)

        print(f"Accepted: {critic_result.accepted}")
        if not critic_result.accepted:
            print(f"Feedback: {critic_result.feedback}")
            state.iteration += 1

        return {
            "messages": [AIMessage(content=f"accepted={critic_result.accepted}\nfeedback={critic_result.feedback}")],
            "critic_result": critic_result,
            "iteration": state.iteration
        }

        
    def should_continue(self, state: GraphState) -> Literal["generator_node", END]:
        """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""
        critic_result = state.critic_result

        return "generator_node" if state.iteration < utils.MAX_ITER and not critic_result.accepted else END

            
    def run_agents(self, product_metadata):

        initial_state = GraphState(
            messages=[],
            iteration=0,
            product_metadata=product_metadata
        )
        result = self.graph.invoke(initial_state)
        
        
        if isinstance(result, dict):
            self.final_state = GraphState.model_validate(result)   # Pydantic v2
        # now `result` is a GraphState model
        else:
            self.final_state = result
        print(self.final_state.generation_asset.content)
        self.create_ADCP_schema()
        

    def create_ADCP_schema(self):
        adcp_instance = ADCPSchema(
            adcp_version = utils.ADCP_VERSION,
            task = utils.TASK,
            generation_asset = self.final_state.generation_asset  # instance
        )

        adcp_json_text = adcp_instance.model_dump_json(indent=2)
        output_path = Path("output")
        output_path.mkdir(parents=True, exist_ok=True)

        file_path = output_path / "adcp_schema.json"
        file_path.write_text(adcp_json_text, encoding="utf-8")
        print(adcp_json_text)


if __name__ == "__main__":

    
    parts = []

    while True:
        raw = input(
            "Enter product name. short product description and target audience:\n"
            "Format: Product Name, Product Description, Target Audience\n"
            "Example: Neon, Energy drink, Gen-Z Gamers\n"
        ).strip()

        parts = [p.strip() for p in raw.split(",")]

        if len(parts) == 3 and all(parts):
            break

        print("❌ Invalid format. Please try again.\n")
    product_metadata = ProductMetadata(product_name=parts[0], product_description= parts[1], target_audience=parts[2])
    ad_creators = AdCreatorAgents()
    ad_creators.run_agents(product_metadata)
    
    
           

         


