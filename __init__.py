from .ollama_node_base import OllamaNodeBase
from .ollama_vision_node_base import OllamaVisionNodeBase
from .ollama_preset_nodes import OllamaSavePresetNode, OllamaLoadPresetNode
from .ollama_model_node import OllamaModelNode
from .ollama_run_preset_node import OllamaRunPresetNode

NODE_CLASS_MAPPINGS = {
    "OllamaNodeBase": OllamaNodeBase,
    "OllamaVisionNodeBase": OllamaVisionNodeBase,
    "OllamaSavePresetNode": OllamaSavePresetNode,
    "OllamaLoadPresetNode": OllamaLoadPresetNode,
    "OllamaModelNode": OllamaModelNode,
    "OllamaRunPresetNode": OllamaRunPresetNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "OllamaNodeBase": "Ollama Base",
    "OllamaVisionNodeBase": "Ollama Vision Base",
    "OllamaSavePresetNode": "💾 Ollama Save Preset",
    "OllamaLoadPresetNode": "📂 Ollama Load Preset",
    "OllamaModelNode": "Ollama Model",
    "OllamaRunPresetNode": "Ollama Run Preset",
}
