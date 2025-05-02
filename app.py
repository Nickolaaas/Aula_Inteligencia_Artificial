# app.py
import os
import google.generativeai as genai
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
import secrets # For generating a secure secret key

# Load environment variables from .env file
load_dotenv()

# --- Base de Conhecimento Específica sobre Reciclagem ---
# (Exemplo simples - pode ser expandido ou carregado de um arquivo/DB)
KNOWLEDGE_BASE = {
    "economia de energia": "Reciclar materiais como alumínio e papel economiza uma quantidade significativa de energia em comparação com a produção a partir de matérias-primas virgens. Por exemplo, reciclar alumínio usa cerca de 95% menos energia.",
    "redução de aterros": "A reciclagem desvia resíduos que iriam para aterros sanitários, prolongando a vida útil desses locais e reduzindo a poluição do solo e da água associada a eles.",
    "conservação de recursos": "Ao reciclar, utilizamos materiais já existentes, diminuindo a necessidade de extrair novos recursos naturais (como árvores, minérios, petróleo), o que ajuda a conservar o meio ambiente.",
    "criação de empregos": "A indústria da reciclagem, incluindo coleta, processamento e fabricação de produtos reciclados, gera empregos em diversas áreas.",
    "poluição": "A reciclagem ajuda a reduzir a poluição do ar e da água, pois o processo de fabricação a partir de materiais reciclados geralmente emite menos poluentes do que a produção com matérias-primas.",
    "alumínio": "Reciclar latas de alumínio é muito eficiente, economizando cerca de 95% da energia necessária para fazer alumínio novo a partir da bauxita.",
    "papel": "Reciclar papel salva árvores, água e energia. Cada tonelada de papel reciclado pode poupar cerca de 17 árvores.",
    "plástico": "A reciclagem de plástico ajuda a reduzir a quantidade de lixo nos oceanos e aterros, além de conservar petróleo, que é usado na sua fabricação. No entanto, nem todos os tipos de plástico são facilmente recicláveis.",
    "vidro": "O vidro pode ser reciclado infinitamente sem perder qualidade. Reciclar vidro economiza energia e reduz a extração de areia e outras matérias-primas.",
    "geral": "A reciclagem é um componente chave da gestão de resíduos e da economia circular, ajudando a proteger o meio ambiente, conservar recursos naturais e economizar energia."
}

# --- Função Simples para Encontrar Contexto Relevante ---
def find_relevant_context(user_message):
    """Busca palavras-chave da mensagem do usuário na base de conhecimento."""
    relevant_texts = []
    message_lower = user_message.lower()
    # Busca muito simples baseada em palavras-chave (pode ser melhorada)
    for keyword, text in KNOWLEDGE_BASE.items():
        if keyword in message_lower:
            relevant_texts.append(text)

    # Se nenhuma palavra-chave específica for encontrada, talvez retornar info geral?
    if not relevant_texts and "reciclagem" in message_lower:
         relevant_texts.append(KNOWLEDGE_BASE.get("geral", "A reciclagem é importante para o meio ambiente."))

    print(f"Contexto encontrado para '{user_message}': {len(relevant_texts)} trecho(s)")
    return "\n".join(relevant_texts) if relevant_texts else None

# Configure Flask app
app = Flask(__name__)
# Generate a secure random key for sessions, or set a fixed one for development
app.secret_key = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(16))

# Configure Google Generative AI
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found. Please set it in the .env file.")

genai.configure(api_key=api_key)

# --- Model Configuration ---
# Choose the Gemini model (e.g., 'gemini-1.5-flash', 'gemini-pro')
# Flash is generally faster and cheaper for chat.
MODEL_NAME = "gemini-1.5-flash"
model = genai.GenerativeModel(MODEL_NAME)

# --- In-memory storage for chat sessions (Simple approach for demo) ---
# WARNING: This will lose history if the server restarts and doesn't scale well.
# For production, consider using a database or more robust session management.
user_chats = {}

def get_user_chat():
    """Gets or creates a chat session for the current user."""
    session_id = session.get('session_id')
    if not session_id:
        session['session_id'] = secrets.token_hex(16) # Simple session identifier
        session_id = session['session_id']

    if session_id not in user_chats:
        # Start a new chat session with optional history (if needed for context)
        print(f"Creating new chat session for {session_id}")
        user_chats[session_id] = model.start_chat(history=[]) # Start with empty history
    return user_chats[session_id]

@app.route("/")
def index():
    """Serves the main chat page."""
    # Ensure a session ID is created when the user first visits
    if 'session_id' not in session:
        session['session_id'] = secrets.token_hex(16)
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    """
    Handles incoming chat messages.
    Prioritizes answering from KNOWLEDGE_BASE.
    If no relevant context found, falls back to Gemini's general knowledge.
    """
    try:
        user_message = request.json.get("message")
        if not user_message:
            return jsonify({"error": "Nenhuma mensagem fornecida"}), 400

        # 1. Tentar encontrar contexto relevante na base específica
        context = find_relevant_context(user_message)

        # 2. Preparar o prompt para o Gemini
        if context:
            # CASO 1: Contexto encontrado - Instruir Gemini a usar APENAS o contexto
            prompt = f"""Você é um assistente especializado em benefícios da reciclagem.
            Responda à pergunta do usuário estritamente com base no seguinte contexto fornecido.
            Não adicione informações que não estejam no contexto.
            Se o contexto não for suficiente para responder, diga que você não tem essa informação específica nos dados fornecidos sobre reciclagem.

            Contexto:
            ---
            {context}
            ---

            Pergunta do Usuário: {user_message}

            Resposta:"""
            print("INFO: Contexto encontrado na KNOWLEDGE_BASE. Usando prompt restrito.")

        else:
            # CASO 2: Contexto NÃO encontrado - Instruir Gemini a usar conhecimento geral
            # Avisamos que a busca local falhou e pedimos para responder de forma geral.
            prompt = f"""Você é um assistente prestativo. Tentei encontrar informações sobre a pergunta do usuário na minha base de conhecimento específica sobre os benefícios da reciclagem, mas não encontrei nada relevante.
            Agora, por favor, responda à pergunta do usuário da melhor forma possível, usando seu conhecimento geral.

            Pergunta do Usuário: {user_message}

            Resposta:"""
            print("INFO: Contexto NÃO encontrado na KNOWLEDGE_BASE. Usando prompt geral.")


        # 3. Obter sessão de chat (mantido para estrutura, mas prompt é chave)
        # chat_session = get_user_chat() # Opcional se usar generate_content

        # 4. Enviar o prompt construído para o Gemini
        print(f"Enviando prompt para Gemini (truncado): {prompt[:250]}...")
        try:
            # Usar generate_content é mais direto para garantir que o prompt atual seja usado
            # sem interferência de histórico da sessão (importante para alternar entre restrito/geral)
            response = model.generate_content(prompt)
            ai_response = response.text

             # Verificar se a resposta foi bloqueada (ex: segurança)
            if not response.candidates:
                 # Tentar obter o motivo do bloqueio se disponível
                 block_reason = "Não especificado"
                 if hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
                    block_reason = response.prompt_feedback.block_reason.name # ou .name
                 print(f"WARN: Resposta bloqueada pela API Gemini. Razão: {block_reason}")
                 ai_response = f"Desculpe, não posso gerar uma resposta para isso devido às políticas de conteúdo ({block_reason})."
            else:
                # Acessar o texto da resposta do primeiro candidato (geralmente o único)
                # Adicionado verificação se 'parts' existe e não está vazio
                 candidate = response.candidates[0]
                 if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts') and candidate.content.parts:
                     ai_response = candidate.content.parts[0].text
                 else:
                     # Fallback se a estrutura for inesperada ou a resposta estiver vazia
                     ai_response = "Não consegui gerar uma resposta válida."
                     print("WARN: Estrutura da resposta Gemini inesperada ou vazia.")


        except Exception as generation_error:
             print(f"Erro ao gerar conteúdo com Gemini: {generation_error}")
             # Tentar extrair mensagens de erro específicas da API
             error_detail = str(generation_error)
             if 'SAFETY' in error_detail.upper():
                  ai_response = "Desculpe, não posso gerar uma resposta para essa solicitação devido às políticas de segurança."
             else:
                 ai_response = "Ocorreu um erro ao processar sua solicitação com a IA."

        print(f"Recebido do Gemini: {ai_response}")

        return jsonify({"response": ai_response})

    except Exception as e:
        print(f"Erro GERAL durante o chat: {e}")
        import traceback
        traceback.print_exc() # Log completo do erro no console do servidor
        return jsonify({"error": "Ocorreu um erro interno ao processar sua mensagem."}), 500

@app.route("/clear", methods=["POST"])
def clear_chat():
    """Clears the chat history for the current user."""
    session_id = session.get('session_id')
    if session_id and session_id in user_chats:
        del user_chats[session_id] # Remove the chat object
        print(f"Cleared chat session for {session_id}")
        # Optionally, you could re-initialize it:
        # user_chats[session_id] = model.start_chat(history=[])
        return jsonify({"status": "Chat history cleared"}), 200
    return jsonify({"status": "No active chat to clear"}), 200


if __name__ == "__main__":
    # Use debug=True for development only (enables auto-reload and debugger)
    # Use host='0.0.0.0' to make it accessible on your network
    app.run(debug=True, host='0.0.0.0', port=5000)
    # For production, use a proper WSGI server like Gunicorn or Waitress
    # Example: gunicorn -w 4 app:app