import os
import google.generativeai as genai
from django.conf import settings
from .models import ChatSession, ChatMessage
from moderator.models import Document

class ChatbotService:
    def __init__(self, user=None):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
        }
        
        self.current_document = None
        if user and user.is_authenticated:
            self.load_document_for_user(user)

    def load_document_for_user(self, user):
        """Load appropriate document based on user's course and type"""
        try:
            print(f"Loading document for user: {user.username} (type: {user.user_type})")
            
            if user.user_type == 'student':
                # Get user's courses
                user_courses = user.member_courses.all()
                print(f"User courses: {[course.id for course in user_courses]}")
                
                # Get documents for user's courses
                self.current_document = Document.objects.filter(
                    curso__in=user_courses
                ).first()
                
                if self.current_document:
                    print(f"Found document: {self.current_document.title}")
                    print(f"Content text: {self.current_document.content_text}")
                    if not self.current_document.content_text:
                        print("Document has no content_text")
                        self.current_document = None
                else:
                    print("No document found for user's courses")
            else:
                print(f"User type {user.user_type} not allowed to access documents")
                
        except Exception as e:
            print(f"Error loading document: {str(e)}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            self.current_document = None

    def get_current_document(self):
        """Return the current document being used for instructions"""
        return self.current_document

    def get_or_create_session(self, user):
        """Get existing session or create a new one"""
        session, created = ChatSession.objects.get_or_create(user=user)
        return session

    def get_chat_history(self, session):
        """Convert database messages to Gemini chat history format"""
        messages = session.messages.all().order_by('created_at')
        history = []
        for msg in messages:
            if msg.role == "user":
                history.append({
                    "role": "user",
                    "parts": [{"text": msg.content}]
                })
            elif msg.role == "model":
                history.append({
                    "role": "model",
                    "parts": [{"text": msg.content}]
                })
        return history

    def send_message(self, user, message_text):
        """Send a message and get response"""
        try:
            # Get or create session
            session = self.get_or_create_session(user)
            
            # Save user message
            ChatMessage.objects.create(
                session=session,
                role="user",
                content=message_text
            )
            
            # Get chat history
            chat_history = self.get_chat_history(session)
            
            # Prepare the prompt with document context and chat history
            if self.current_document and self.current_document.content_text:
                prompt = f"""Instrucciones: Actúa como un profesor virtual especializado en enseñar a niños desde kinder hasta 3° básico.
                Debes ser amigable, paciente y utilizar un lenguaje simple y claro adecuado para niños pequeños.
                
                Basándote en el siguiente documento educativo:
                {self.current_document.content_text}
                
                Historial de la conversación:
                {self._format_chat_history_for_prompt(chat_history)}
                
                Sigue estas reglas en tu interacción:
                1. Si el mensaje del estudiante parece ser una respuesta a una pregunta anterior:
                   - Verifica si es correcta con una respuesta corta (máximo 2 líneas)
                   - Si es correcta: "¡Muy bien! [breve explicación]"
                   - Si es incorrecta: "¡Casi! La respuesta es [respuesta correcta] porque [explicación breve]"
                   - Luego, haz una nueva pregunta sobre un tema diferente
                
                2. Si es un nuevo mensaje o pregunta del estudiante:
                   - Responde de manera breve y amigable (máximo 3 líneas)
                   - Haz una pregunta educativa basada en el documento
                   - Incluye una imagen relacionada usando el formato: [IMAGE:"término de búsqueda para Google"]
                   - Usa el formato especial para botones: [BUTTON:"texto del botón"]
                   - Presenta tres alternativas usando el formato:
                     [BUTTON:"a) alternativa 1."]
                     [BUTTON:"b) alternativa 2."]
                     [BUTTON:"c) alternativa 3."]
                
                3. En todo momento:
                   - Sé conciso y directo
                   - Usa máximo 1-2 emojis por mensaje
                   - Evita explicaciones largas
                   - Usa el formato [BUTTON:"texto"] para cualquier opción clickeable
                   - Incluye una imagen relevante para cada pregunta usando [IMAGE:"término de búsqueda"]
                   - Las búsquedas de imágenes deben ser específicas y educativas
                   - Evita términos de búsqueda muy generales
                
                Mensaje del estudiante: {message_text}
                
                Responde como un profesor amigable y crea una nueva pregunta educativa siguiendo las instrucciones anteriores."""
            else:
                if user.user_type == 'student':
                    prompt = "Lo siento, no hay documentos disponibles para tu curso en este momento. Por favor, contacta a tu profesor."
                else:
                    prompt = message_text

            # Send message with context
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            
            if response.text:
                # Save model response
                ChatMessage.objects.create(
                    session=session,
                    role="model",
                    content=response.text
                )
                return response.text
            else:
                raise Exception("Empty response from model")
            
        except Exception as e:
            print(f"Error in send_message: {str(e)}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            return "Lo siento, hubo un error al procesar tu mensaje. Por favor, intenta de nuevo."

    def _format_chat_history_for_prompt(self, chat_history):
        """Format chat history into a readable string for the prompt"""
        formatted_history = []
        for msg in chat_history[-10:]:  # Only include last 5 messages to keep context manageable
            role = "Estudiante" if msg["role"] == "user" else "Profesor"
            formatted_history.append(f"{role}: {msg['parts'][0]['text']}")
        return "\n".join(formatted_history)

    def get_recent_messages(self, user, limit=10):
        """Get recent messages for a user"""
        session = self.get_or_create_session(user)
        return session.messages.all()[:limit]
