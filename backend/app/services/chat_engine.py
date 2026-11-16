import json
import time
import uuid
import urllib.request
import urllib.error
from typing import List, Dict, Any, AsyncGenerator, Optional

from app.services.text_model_manager import TextModelManager
from app.services.web_search_service import WebSearchService
from app.services.multimedia_parser import MultimediaParser


class ChatEngine:
    """
    Motor central de ejecución y orquestación de Chat LLM.
    - Administra la comunicación con el daemon local de Ollama (http://127.0.0.1:11434).
    - Inyecta de forma transparente el System Prompt personalizado y los hiperparámetros del modelo.
    - Aplica RAG Web dinámico (Búsqueda en Internet) en tiempo real si el usuario lo activa.
    - Adjunta elementos multimedia (documentos, hojas de cálculo en Markdown e imágenes en Base64).
    - Emite tokens en streaming continuo (Server-Sent Events) para el HUD Cyberpunk.
    """

    @classmethod
    async def stream_chat_completion(
        cls,
        model: str,
        messages: List[Dict[str, Any]],
        web_search: bool = False,
        attached_docs: Optional[List[Dict[str, Any]]] = None,
        attached_images: Optional[List[str]] = None,
        override_settings: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generador asíncrono que transmite tokens de respuesta en formato Server-Sent Events (SSE).
        """
        start_time = time.perf_counter()
        profile = TextModelManager.get_model_profile(model)
        if override_settings:
            profile.update(override_settings)

        # 1. Recuperar directivas personalizadas
        system_prompt = profile.get("system_prompt", "").strip()
        core = profile.get("core", "custom")
        temp = float(profile.get("temperature", 0.7))
        top_p = float(profile.get("top_p", 0.9))
        ctx_window = int(profile.get("context_window", 4096))
        max_tokens = int(profile.get("max_tokens", 2048))
        rep_penalty = float(profile.get("repeat_penalty", 1.1))

        # 2. Obtener el último mensaje del usuario para búsqueda web o inyección de archivos
        user_query = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                user_query = m.get("content", "")
                break

        # 3. Acceso a Internet mediante API si está activado
        web_context = ""
        web_sources = []
        if web_search and user_query:
            try:
                search_results = WebSearchService.execute_search(user_query, max_results=4)
                if search_results:
                    web_context = WebSearchService.format_search_context(search_results)
                    web_sources = search_results
            except Exception as e:
                print(f"[ChatEngine] Error ejecutando búsqueda web: {e}")

        # 4. Procesar documentos multimedia adjuntos (PDF, Word, Excel, CSV)
        doc_context = ""
        if attached_docs:
            doc_blocks = []
            for doc in attached_docs:
                fname = doc.get("filename", "Archivo")
                content = doc.get("content", "")
                doc_blocks.append(f"### [DOCUMENTO ADJUNTO: {fname}]\n```\n{content}\n```")
            if doc_blocks:
                doc_context = "\n\n".join(doc_blocks)

        # 5. Normalizar imágenes en Base64 para modelos de visión
        images_payload = []
        if attached_images:
            for b64 in attached_images:
                processed = MultimediaParser.process_image_base64(b64)
                if processed:
                    images_payload.append(processed)

        # 6. Estructurar mensajes para Ollama
        ollama_messages = []

        # System message con instrucciones del modelo + fuentes web + documentos
        combined_system = system_prompt
        if web_context:
            combined_system += f"\n\n{web_context}"
        if doc_context:
            combined_system += f"\n\n--- CONTENIDO DE ARCHIVOS ADJUNTOS ---\n{doc_context}\n---------------------------------------"

        if combined_system:
            ollama_messages.append({"role": "system", "content": combined_system})

        # Agregar historial previo
        for m in messages[:-1]:
            ollama_messages.append({
                "role": m.get("role", "user"),
                "content": m.get("content", "")
            })

        # Último mensaje del usuario con imágenes si aplican
        last_user_payload: Dict[str, Any] = {
            "role": "user",
            "content": user_query
        }
        if images_payload:
            last_user_payload["images"] = images_payload

        ollama_messages.append(last_user_payload)

        # 7. Verificar disponibilidad de Ollama
        ollama_url = f"{TextModelManager.get_ollama_url()}/api/chat"
        is_live = TextModelManager.is_ollama_available()

        if not is_live:
            # Fallback amigable explicativo si Ollama no está corriendo
            msg = (
                f"[SISTEMA // CYBER-IA]: El demonio local de **Ollama** no está respondiendo en `{TextModelManager.get_ollama_url()}`.\n\n"
                f"**Pasos para activar tus modelos:**\n"
                f"1. Inicia Ollama en tu sistema ejecutando `ollama serve` en una terminal o abriendo la aplicación de Ollama.\n"
                f"2. Para descargar un modelo compatible, ejecuta: `ollama pull {model}` (o `ollama pull llama3.2:3b`).\n"
                f"3. La interfaz reconocerá automáticamente el core y la familia del modelo apenas esté en línea."
            )
            for word in msg.split(" "):
                yield f"data: {json.dumps({'token': word + ' ', 'done': False})}\n\n"
            yield f"data: {json.dumps({'token': '', 'done': True, 'sources': web_sources})}\n\n"
            return

        # 8. Petición a Ollama con Streaming
        ollama_request_body = {
            "model": model,
            "messages": ollama_messages,
            "stream": True,
            "options": {
                "temperature": temp,
                "top_p": top_p,
                "num_ctx": ctx_window,
                "num_predict": max_tokens,
                "repeat_penalty": rep_penalty
            }
        }

        try:
            req = urllib.request.Request(
                ollama_url,
                data=json.dumps(ollama_request_body).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "CYBER-IA/1.2.0"}
            )

            # Transmisión directa línea a línea de Ollama hacia el cliente
            with urllib.request.urlopen(req, timeout=120) as resp:
                for line in resp:
                    if not line:
                        continue
                    line_str = line.decode("utf-8", errors="ignore").strip()
                    if not line_str:
                        continue

                    try:
                        chunk = json.loads(line_str)
                        token = chunk.get("message", {}).get("content", "")
                        done = chunk.get("done", False)

                        payload = {
                            "token": token,
                            "done": done
                        }
                        if done:
                            payload["total_duration"] = chunk.get("total_duration", 0)
                            payload["eval_count"] = chunk.get("eval_count", 0)
                            payload["sources"] = web_sources

                        yield f"data: {json.dumps(payload)}\n\n"

                        if done:
                            break
                    except Exception as json_err:
                        print(f"[ChatEngine] Error parseando chunk: {json_err}")

        except urllib.error.HTTPError as http_err:
            err_body = http_err.read().decode("utf-8", errors="ignore")
            err_msg = f"\n\n[ERROR OLLAMA {http_err.code}]: {err_body}"
            yield f"data: {json.dumps({'token': err_msg, 'done': True})}\n\n"
        except Exception as e:
            err_msg = f"\n\n[ERROR DE CONEXIÓN OLLAMA]: {str(e)}"
            yield f"data: {json.dumps({'token': err_msg, 'done': True})}\n\n"

