import PyPDF2
import docx
import io
import os
from moderator.models import Document

class DocumentService:
    def process_document(self, file_obj, title, group, user):
        """Process and store a document"""
        # Save the file temporarily to process it
        temp_path = f'media/temp_{file_obj.name}'
        os.makedirs('media', exist_ok=True)
        
        with open(temp_path, 'wb+') as destination:
            for chunk in file_obj.chunks():
                destination.write(chunk)

        try:
            # Extract text from the document
            content_text = self.extract_text(temp_path, file_obj.name)

            # Create document record
            document = Document.objects.create(
                title=title,
                file=file_obj,
                curso=group,  
                uploaded_by=user,
                content_text=content_text  
            )

            return document

        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def extract_text(self, file_path, filename):
        """Extract text from various file types"""
        try:
            if filename.lower().endswith('.pdf'):
                return self._extract_from_pdf(file_path)
            elif filename.lower().endswith('.docx'):
                return self._extract_from_docx(file_path)
            else:
                # For text files
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            print(f"Error extracting text: {str(e)}")
            return ""  

    def _extract_from_pdf(self, file_path):
        """Extract text from PDF"""
        with open(file_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text

    def _extract_from_docx(self, file_path):
        """Extract text from DOCX"""
        doc = docx.Document(file_path)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
