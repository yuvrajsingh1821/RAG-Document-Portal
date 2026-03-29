from multiprocessing import Value
import os
import sys
from typing import List, Optional
from operator import itemgetter
from langchain_core import chat_history
from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_community.vectorstores import FAISS

from utils.model_loader import ModelLoader
from exception.custom_exception import DocumentPortalException
from logger.custom_logger import CustomLogger
from prompt.prompt_library import PROMPT_REGISTRY
from models.models import PromptType


class ConversationalRAG:

    def __init__(self, session_id:str, retriever=None):
        try:
            self.log = CustomLogger().get_logger(__name__)
            self.session_id = session_id
            self.contextualize_prompt = PROMPT_REGISTRY[PromptType.CONTEXTUALIZE_QUESTION.value]
            self.qa_prompt = PROMPT_REGISTRY[PromptType.CONTEXT_QA.value]
            if retriever is None:
                raise ValueError("Retriever cannot be None")
            self.retriever = retriever
            self.llm = self._load_llm()
            self._build_lcel_chain()
            self.log.info("ConversationalRAG initialized", session_id=self.session_id)

        except Exception as e:
            self.log.error("Failed to initialize ConversationalRAG", error=str(e))
            raise DocumentPortalException("Error in initializing ConversationalRAG", sys)

    def load_retriever_from_faiss(self, index_path):
        """
        Load a FAISS vectorstore from disk and convert to retriever
        """
        try:
            embeddings = ModelLoader().load_embeddings()
            if not os.path.isdir(index_path):
                raise FileNotFoundError(f"FAISS directory not found: {index_path}")
            vectorstore = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
            self.retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs= {"k":5})
            return self.retriever

        except Exception as e:
            self.log.error("Failed to load retriever from FAISS", error=str(e))
            raise DocumentPortalException("Retriever loading error in ConversationalRAG", sys)


    def invoke(self, user_input:str, chat_history:Optional[List[BaseMessage]]=None) -> str :
        try:
            chat_history = chat_history or []
            payload = {
                "input":user_input,
                "chat_history": chat_history
            }
            answer = self.chain.invoke(payload)
            if not answer:
                self.log.warning("No answer generated", user_input=user_input, session_id = self.session_id)
                return "No answer generated"
            self.log.info("Chain invoked successfully", user_input=user_input, session_id = self.session_id, answer_preview = answer[:150])
            return answer
        except Exception as e:
            self.log.error("Failed to invoke ConversationalRAG", error=str(e))
            raise DocumentPortalException("Invokation error in ConversationalRAG", sys)
        

    def _load_llm(self):
        try:
            llm = ModelLoader().load_llm()
            if not llm:
                raise ValueError("LLM cannot be loaded")
            self.log.info("LLM loaded successfully", session_id = self.session_id)
            return llm
        except Exception as e:
            self.log.error("Failed to load LLM", error=str(e))
            raise DocumentPortalException("LLM loading error in ConversationalRAG", sys)
    
    @staticmethod
    def _format_docs(docs):
        return "\n\n".join(d.page_content for d in docs)


    def _build_lcel_chain(self):
        try:
            question_rewriter = (
                {"input": itemgetter("input"), "chat_history": itemgetter("chat_history")}
                | self.contextualize_prompt
                | self.llm
                | StrOutputParser()
            )
            retrieved_docs = question_rewriter | self.retriever | self._format_docs
            self.chain = (
                {
                   "context" : retrieved_docs,
                   "input": itemgetter("input"),
                   "chat_history": itemgetter("chat_history")
                }
                | self.qa_prompt
                | self.llm
                | StrOutputParser()
            )
            self.log.info("LCEL chain built successfully", session_id=self.session_id)

        except Exception as e:
            self.log.error("Failed to build LCEL chain", error=str(e))
            raise DocumentPortalException("Chain building error in ConversationalRAG", sys)

    
