from .ollama_node_base import OllamaNodeBase
from .ollama_vision_node_base import OllamaVisionNodeBase
from .ollama_preset_nodes import OllamaSavePresetNode, OllamaLoadPresetNode
from .ollama_model_node import OllamaModelNode
from .ollama_run_preset_node import OllamaRunPresetNode
from .ollama_reasoning_node import OllamaReasoningNode
from .ollama_reasoning_model_node import OllamaReasoningModelNode

NODE_CLASS_MAPPINGS = {
    "OllamaNodeBase": OllamaNodeBase,
    "OllamaVisionNodeBase": OllamaVisionNodeBase,
    "OllamaSavePresetNode": OllamaSavePresetNode,
    "OllamaLoadPresetNode": OllamaLoadPresetNode,
    "OllamaModelNode": OllamaModelNode,
    "OllamaRunPresetNode": OllamaRunPresetNode,
    "OllamaReasoningNode": OllamaReasoningNode,
    "OllamaReasoningModelNode": OllamaReasoningModelNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "OllamaNodeBase": "Ollama Base",
    "OllamaVisionNodeBase": "Ollama Vision Base",
    "OllamaSavePresetNode": "💾 Ollama Save Preset",
    "OllamaLoadPresetNode": "📂 Ollama Load Preset",
    "OllamaModelNode": "Ollama Model",
    "OllamaRunPresetNode": "Ollama Run Preset",
    "OllamaReasoningNode": "Ollama Reasoning",
    "OllamaReasoningModelNode": "Reasoning Model",
}
