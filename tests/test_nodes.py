# tests/test_nodes.py
from unittest.mock import Mock
import pytest

from app.ad_creator import AdCreatorAgents
from app.models import (
    GraphState,
    ProductMetadata,
    GenerationAsset,
    ContentMetadata,
    CriticResult,
)
from langgraph.graph import END


@pytest.fixture
def sample_product_metadata():
    return ProductMetadata(target_audience="Adults", product_description = "milk chocolate bar", product_name="Cadbury Dairy Milk")


@pytest.fixture
def empty_state(sample_product_metadata):
    # messages can be an empty list; nodes will append SystemMessage/AIMessage
    return GraphState(messages=[], product_metadata=sample_product_metadata, iteration=0)


def make_fake_asset():
    content = "Indulge in Cadbury Chocolate Bar 🍫 for a sweet escape anytime, anywhere!"
    return GenerationAsset(
        type="text_ad",
        content=content,
        content_metadata=ContentMetadata(length=len(content), sentiment="energetic"),
        brand_safety_check="passed",
    )


def make_fake_critic(accepted: bool, feedback: str = ""):
    return CriticResult(accepted=accepted, feedback=feedback)


def test_generator_node_sets_generation_asset_and_appends_message(empty_state):
    agent = AdCreatorAgents()
    # Replace the real LLM on the agent with a Mock that returns a Pydantic instance
    fake_asset = make_fake_asset()
    agent.generator_llm = Mock()
    agent.generator_llm.invoke = Mock(return_value=fake_asset)

    # Call node directly with a GraphState instance
    state = empty_state
    result = agent.generator_node(state)

    # The node should attach the structured model to the state
    assert result['generation_asset'] == fake_asset

    # The node should append an AIMessage whose content is the asset content string
    messages_contents = [getattr(m, "content", None) for m in result['messages']]
    assert fake_asset.content in messages_contents


def test_critic_node_sets_critic_result_and_routes(empty_state):
    agent = AdCreatorAgents()
    fake_asset = make_fake_asset()
    # Pre-fill state with a generated asset (what critic node expects)
    state = empty_state
    state.generation_asset = fake_asset

    fake_critic = make_fake_critic(accepted=True, feedback="")
    agent.critic_llm = Mock()
    agent.critic_llm.invoke = Mock(return_value=fake_critic)

    result = agent.critic_node(state)

    # Critic result attached to state
    assert result['critic_result'] == fake_critic
    state.critic_result = fake_critic
    # should_continue should return END when accepted == True
    assert agent.should_continue(state) == END


def test_critic_node_rejection_routes_back_to_generator(empty_state):
    agent = AdCreatorAgents()
    fake_asset = make_fake_asset()
    state = empty_state
    state.generation_asset = fake_asset

    # Critic rejects and provides actionable feedback
    fake_critic = make_fake_critic(accepted=False, feedback="Rule 1: too long; shorten to <=15 words.")
    agent.critic_llm = Mock()
    agent.critic_llm.invoke = Mock(return_value=fake_critic)

    result = agent.critic_node(state)
    state.critic_result = fake_critic
    assert result['critic_result'] == fake_critic
    assert "Rule 1" in result['messages'][-1].content  # last appended message contains feedback

    # When not accepted, should_continue should route to the generator node
    assert agent.should_continue(state) == "generator_node"