"""Serviço de geração de embeddings usando Google Gemini."""
import os
import google.generativeai as genai
from typing import Protocol


class EmbeddingGenerator:
    """Gera embeddings usando o modelo de embedding do Google Gemini."""
    
    def __init__(self, api_key: str):
        """
        Inicializa o serviço de embeddings.
        
        Args:
            api_key: Chave da API do Google Gemini
        """
        genai.configure(api_key=api_key)
        # Para embeddings, usamos o modelo text-embedding-004
        # Mas o Gemini também pode gerar embeddings através do modelo de embedding
        self.model = None  # Será configurado quando necessário
    
    def generate(self, text: str) -> list[float]:
        """
        Gera um embedding para um texto.
        
        Args:
            text: Texto para gerar embedding
        
        Returns:
            Lista de floats representando o vetor de embedding
        """
        try:
            # Google Gemini usa o modelo text-embedding-004 para embeddings
            # O método embed_content retorna um objeto com o embedding
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_document"
            )
            
            # O resultado pode ser um dict ou um objeto com atributo 'embedding'
            if isinstance(result, dict):
                embedding = result.get('embedding', [])
            else:
                embedding = getattr(result, 'embedding', [])
            
            if not embedding:
                raise ValueError("Embedding não foi gerado")
            
            return embedding
        except Exception as e:
            # Fallback: tenta usar o modelo genérico se o específico falhar
            try:
                result = genai.embed_content(
                    model="models/embedding-001",
                    content=text
                )
                if isinstance(result, dict):
                    embedding = result.get('embedding', [])
                else:
                    embedding = getattr(result, 'embedding', [])
                return embedding if embedding else []
            except:
                raise ValueError(f"Erro ao gerar embedding: {str(e)}")

