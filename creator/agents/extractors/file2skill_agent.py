from typing import Any, Dict, List, Optional
import langchain
from langchain.cache import SQLiteCache
from langchain.chains.llm import LLMChain
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.manager import CallbackManagerForChainRun
from langchain.schema import HumanMessage
from creator.callbacks.streaming_stdout import FunctionCallStreamingStdOut
from creator.schema.skill import CodeSkill, BaseSkillMetadata
from creator.schema.library import config


langchain.llm_cache = SQLiteCache(database_path=f"{config.skill_extract_agent_cache_path}/.langchain.db")


_SYSTEM_TEMPLATE = """Extract one skill object from the above file content.
Follow the guidelines below:
1. Only extract the properties mentioned in the 'extract_formmated_skill' function
[User Info]
Name: {username}
CWD: {current_working_directory}
OS: {operating_system}
"""


def convert_codefile2langchain_format(file_content):
    chat_messages = [HumanMessage(content=file_content)]
    # add system message
    chat_messages.append(("system", _SYSTEM_TEMPLATE))
    prompt = ChatPromptTemplate.from_messages(chat_messages)
    return prompt


class SkillExtractorAgent(LLMChain):
    @property
    def _chain_type(self):
        return "SkillExtractorAgent"

    @property
    def input_keys(self) -> List[str]:
        return ["username", "current_working_directory", "operating_system", "file_content"]

    def _call(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Dict[str, Any]:
        file_content = inputs.pop("file_content")
        prompt = convert_codefile2langchain_format(file_content)
        self.prompt = prompt
        response = self.generate([inputs], run_manager=run_manager)
        extracted_skill = self.create_outputs(response)[0]["extracted_skill"]
        extracted_skill["skill_metadata"] = BaseSkillMetadata(author=inputs["username"]).model_dump()
        extracted_skill["conversation_history"] = {
            "role": "user",
            "content": file_content
        }
        return {
            "extracted_skill": extracted_skill
        }


def create_skill_extractor_agent(llm):
    code_skill_json_schema = CodeSkill.to_skill_function_schema()
    function_schema = {
        "name": "extract_formmated_skill",
        "description": "a function that extracts a skill from a file content",
        "parameters": code_skill_json_schema
    }
    llm_kwargs = {"functions": [function_schema], "function_call": {"name": function_schema["name"]}}
    output_parser = JsonOutputFunctionsParser()
    # dummy prompt
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", _SYSTEM_TEMPLATE),
        ]
    )
    chain = SkillExtractorAgent(
        llm=llm,
        prompt=prompt,
        llm_kwargs=llm_kwargs,
        output_parser=output_parser,
        output_key="extracted_skill",
        verbose=False
    )
    return chain


skill_extractor_agent = create_skill_extractor_agent(ChatOpenAI(temperature=0, model=config.skill_extract_agent_model, streaming=True, verbose=True, callback_manager=CallbackManager([FunctionCallStreamingStdOut()])))

