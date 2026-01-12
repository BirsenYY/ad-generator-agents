"""Integration tests that call real OpenAI API."""
import pytest
import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import logging
logger = logging.getLogger(__name__)

@pytest.mark.integration
def test_openai_api_connection(caplog):
    
    """Test that we can connect to OpenAI and get a structured response."""
    caplog.set_level(logging.INFO) 
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set; skipping integration test")
    
    llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key=api_key)
    
    # Simple test prompt
    from langchain_core.messages import HumanMessage
    message = HumanMessage(content="Response with 'Hi dude, how are you?'")
    
    response = llm.invoke([message])

    
    # Log the response (use logging instead of print)
    logger.info("API response: %s", getattr(response, "content", str(response)))

    # Assert the response object is non-empty / has content
    assert getattr(response, "content", "") != ""

    # Assert the log contains the response content
    assert "API response:" in caplog.text
    assert getattr(response, "content", "") in caplog.text

    # Optionally inspect individual LogRecord objects:
    recs = [r for r in caplog.records if r.levelname == "INFO"]
    assert any("API response:" in r.getMessage() for r in recs)
    