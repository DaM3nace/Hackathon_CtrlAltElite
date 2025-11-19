import os
import PyPDF2
import pandas as pd
from docx import Document
from pathlib import Path
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        self.supported_formats = {'.pdf', '.docx', '.doc', '.txt', '.md', '.xlsx', '.xls'}
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
            return ""
    
    def extract_text_from_docx(self, file_path: str) -> str:
        try:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting text from DOCX {file_path}: {str(e)}")
            return ""
    
    def extract_text_from_txt(self, file_path: str) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            logger.error(f"Error extracting text from TXT {file_path}: {str(e)}")
            return ""
    
    def extract_text_from_excel(self, file_path: str) -> str:
        try:
            df = pd.read_excel(file_path, sheet_name=None)
            text = ""
            for sheet_name, sheet_data in df.items():
                text += f"Sheet: {sheet_name}\n"
                text += sheet_data.to_string(index=False) + "\n\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting text from Excel {file_path}: {str(e)}")
            return ""
    
    def process_document(self, file_path: str) -> Dict[str, Any]:
        file_path = Path(file_path)
        
        if file_path.suffix.lower() not in self.supported_formats:
            logger.warning(f"Unsupported file format: {file_path.suffix}")
            return None
        
        document_metadata = {
            'file_name': file_path.name,
            'file_path': str(file_path),
            'file_size': file_path.stat().st_size,
            'file_extension': file_path.suffix.lower(),
            'content': ''
        }
        
        try:
            if file_path.suffix.lower() == '.pdf':
                content = self.extract_text_from_pdf(str(file_path))
            elif file_path.suffix.lower() in ['.docx', '.doc']:
                content = self.extract_text_from_docx(str(file_path))
            elif file_path.suffix.lower() in ['.txt', '.md']:
                content = self.extract_text_from_txt(str(file_path))
            elif file_path.suffix.lower() in ['.xlsx', '.xls']:
                content = self.extract_text_from_excel(str(file_path))
            else:
                logger.warning(f"No handler for file type: {file_path.suffix}")
                return None
            
            document_metadata['content'] = content
            logger.info(f"Successfully processed: {file_path.name}")
            return document_metadata
            
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {str(e)}")
            return None
    
    def process_directory(self, directory_path: str) -> List[Dict[str, Any]]:
        directory = Path(directory_path)
        
        if not directory.exists():
            logger.error(f"Directory does not exist: {directory_path}")
            return []
        
        documents = []
        for file_path in directory.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in self.supported_formats:
                document = self.process_document(str(file_path))
                if document and document['content'].strip():
                    documents.append(document)
        
        logger.info(f"Processed {len(documents)} documents from {directory_path}")
        return documents