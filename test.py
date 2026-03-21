# import os 
# from pathlib import Path
# from src.document_analyzer.data_ingestion import DocumentHandler
# from src.document_analyzer.data_analysis import DocumentAnalyzer

# #Path of the pdf you want to test
# pdf_path = "/Users/yuvrajsingh/Developer/Document-Portal/data/document_analysis/NIPS-2017-attention-is-all-you-need-Paper.pdf"


# #file wrapper to simulate uploaded file
# class DummyFile:
#         def __init__(self, file_path):
#             self.name = Path(file_path).name
#             self._file_path = file_path
#         def getbuffer(self):
#             return open(self._file_path, "rb").read()


# def main():
#     try:
#         # --------Step 1: Data ingestion--------
#         print("Starting data ingestion")
#         dummy_pdf = DummyFile(pdf_path)

#         handler = DocumentHandler(session_id="test_session")
#         saved_path = handler.save_pdf(dummy_pdf)
#         print(f"PDF saved to: {saved_path}")

#         text_content = handler.read_pdf(saved_path)
#         print(f"Extracted text content: {len(text_content)} characters")

#         # --------Step 2: Data analysis--------
#         print("Starting data analysis")
#         analyzer = DocumentAnalyzer()  #Load LLM + parser 
#         analysis_result = analyzer.analyze_document(text_content)

#         # --------Step 3: Print analysis results--------
#         for key, value in analysis_result.items():
#             print(f"{key}: {value}")
#     except Exception as e:
#         print(f"Test failed: {e}")


# if __name__ == "__main__":
#     main() 


# import io
# from pathlib import Path
# from src.document_compare.data_ingestion import DocumentIngestion
# from src.document_compare.document_comparator import DocumentComparatorLLM

# def load_fake_uploaded_file(file_path:Path):
#     return io.BytesIO(file_path.read_bytes())

# def test_compare_documents():
#     ref_path = Path("/Users/yuvrajsingh/Developer/Document-Portal/data/document_compare/ipl_document_B.pdf")
#     actual_path = Path("/Users/yuvrajsingh/Developer/Document-Portal/data/document_compare/ipl_document_A.pdf")

#     class FakeUpload:
#         def __init__(self, file_path:Path):
#             self.name = file_path.name
#             self._buffer = file_path.read_bytes()

#         def getbuffer(self):
#             return self._buffer

#     comparator = DocumentIngestion()
#     ref_upload = FakeUpload(ref_path)
#     actual_upload = FakeUpload(actual_path)

#     ref_file, actual_file = comparator.save_uploaded_files(ref_upload, actual_upload) 
#     combined_text = comparator.combine_document()
#     comparator.clean_old_seassions(keep_latest = 3)

#     print("\n\n COMBINED TEXT: \n\n")
#     print(combined_text[:1000])
#     print("\n\n")

#     llm_comparator = DocumentComparatorLLM()
#     comparison_result = llm_comparator.compare_documents(combined_text)

#     print("\n\n COMPARISON RESULT: \n\n")
#     print(comparison_result.head())

# if __name__ == "__main__":
#     test_compare_documents()


# Testing code for document chat functionality

import sys
from pathlib import Path
from langchain_community.vectorstores import FAISS
from src.single_document_chat.data_ingestion import SingleDocIngestor
from src.single_document_chat.retrieval import ConversationalRAG
from utils.model_loader import ModelLoader

FAISS_INDEX_PATH = Path("faiss_index")


def test_conversational_rag_on_pdf(pdf_path:str, question:str):
    try:
        model_loader = ModelLoader()

        if FAISS_INDEX_PATH.exists():
            print("Loading existing FAISS index...")
            embeddings = model_loader.load_embeddings()
            vectorstore = FAISS.load_local(folder_path=str(FAISS_INDEX_PATH), embeddings=embeddings, allow_dangerous_deserialization=True)
            retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k":5})
        else:
            print("FAISS index not found. ingesting pdf and creating index")
            with open(pdf_path, "rb") as f:
                uploaded_files = [f]
                ingestor = SingleDocIngestor()
                retriever = ingestor.ingest_files(uploaded_files)
        print("Running conversational RAG...")
        session_id = "test_conversational_rag"
        rag = ConversationalRAG(retriever=retriever, session_id=session_id)

        response = rag.invoke(question)
        print(f"\nQuestion: {question} \nAnswer: {response}")
        
    except Exception as e:
        print(f"Test failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    
    #Example pdf path and question
    pdf_path = "/Users/yuvrajsingh/Developer/Document-Portal/data/single_document_chat/NIPS-2017-attention-is-all-you-need-Paper.pdf"
    question = "What is attention mechanism?"

    if not Path(pdf_path).exists():
        print(f"PDF file does not exist at: {pdf_path}")
        sys.exit(1)

    #Run the test
    test_conversational_rag_on_pdf(pdf_path, question)


    







        


