#Pydantic Models to ensure each LangGraph LLM node produces structured output.

from typing_extensions import  Annotated
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel
from typing import Optional
  
    
class ContentMetadata(BaseModel):
    length: int
    sentiment: str
    
class CriticResult(BaseModel):
    accepted: bool
    feedback: str

class ProductMetadata(BaseModel):
    target_audience: str
    product_name:str
    product_description:str 

class GenerationAsset(BaseModel):
    type: str
    content: str
    content_metadata: ContentMetadata 
    brand_safety_check: str
    
class ADCPSchema(BaseModel):
    adcp_version:str
    task: str
    generation_asset: GenerationAsset
    
class GraphState(BaseModel):
    messages: Annotated[list[AnyMessage], add_messages]
    iteration:int
    product_metadata: ProductMetadata
    generation_asset: Optional[GenerationAsset] = None
    critic_result: Optional[CriticResult] = None