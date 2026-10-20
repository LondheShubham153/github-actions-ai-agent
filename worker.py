"""Start the Temporal worker. Registers the Ollama model under the alias the workflow uses."""
import asyncio
import os

from google.adk.models.lite_llm import LiteLlm
from google.adk.models.registry import LLMRegistry
from temporalio.client import Client
from temporalio.contrib.google_adk_agents import GoogleAdkPlugin
from temporalio.worker import Worker

from github_tools import GITHUB_ACTIVITIES
from memory import recall, remember
from workflow import MODEL_ALIAS, TriageWorkflow

TASK_QUEUE = "ci-triage"


class OllamaGemma(LiteLlm):
    def __init__(self, model: str = MODEL_ALIAS, **kwargs):
        super().__init__(model=f"ollama_chat/{os.environ.get('OLLAMA_MODEL', 'gemma4')}",
                         api_base=os.environ.get("OLLAMA_API_BASE", "http://localhost:11434"), **kwargs)

    async def generate_content_async(self, llm_request, stream=False):
        llm_request.model = self.model  # LiteLlm prefers llm_request.model, which holds the alias
        async for response in super().generate_content_async(llm_request, stream):
            yield response

    @classmethod
    def supported_models(cls):
        return [MODEL_ALIAS]


async def main():
    LLMRegistry.register(OllamaGemma)  # before the first model activity
    client = await Client.connect(os.environ.get("TEMPORAL_ADDRESS", "localhost:7233"),
                                  plugins=[GoogleAdkPlugin()])
    print("worker running on", TASK_QUEUE)
    await Worker(client, task_queue=TASK_QUEUE, workflows=[TriageWorkflow],
                 activities=[recall, remember, *GITHUB_ACTIVITIES]).run()


if __name__ == "__main__":
    asyncio.run(main())
