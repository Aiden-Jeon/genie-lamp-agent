"""Build prompts for LLM to generate Genie space configurations."""

from pathlib import Path
from typing import Optional


class PromptBuilder:
    """Builds prompts for generating Genie space configurations."""
    
    def __init__(
        self,
        context_doc_path: str,
        output_doc_path: str,
        input_data_path: str,
        workspace_root: Optional[str] = None
    ):
        """
        Initialize the prompt builder.
        
        Args:
            context_doc_path: Path to the context document (curate_effective_genie.md)
            output_doc_path: Path to the output format document (genie_api.md)
            input_data_path: Path to the input data (demo_requirements.md)
            workspace_root: Root directory of the workspace (defaults to current directory)
        """
        if workspace_root is None:
            workspace_root = Path.cwd()
        else:
            workspace_root = Path(workspace_root)
            
        self.context_doc_path = workspace_root / context_doc_path
        self.output_doc_path = workspace_root / output_doc_path
        self.input_data_path = workspace_root / input_data_path
        
        # Set paths to template files
        templates_dir = Path(__file__).parent / "templates"
        self.guide_prompt_path = templates_dir / "guide_prompt.md"
        self.guide_prompt_with_reasoning_path = templates_dir / "guide_prompt_with_reasoning.md"
        
    def _read_file(self, path: Path) -> str:
        """Read file contents."""
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def build_prompt(self) -> str:
        """
        Build the complete prompt for the LLM.
        
        Returns:
            The formatted prompt string
        """
        # Read all documents
        context_content = self._read_file(self.context_doc_path)
        output_content = self._read_file(self.output_doc_path)
        input_content = self._read_file(self.input_data_path)
        
        # Read the guide prompt template
        guide_template = self._read_file(self.guide_prompt_path)
        
        # Format the template with the content
        prompt = guide_template.format(
            context_content=context_content,
            output_content=output_content,
            input_content=input_content
        )
        
        return prompt
    
    def build_prompt_with_reasoning(self) -> str:
        """
        Build a prompt that includes reasoning in the response.
        
        Returns:
            The formatted prompt string that asks for reasoning
        """
        # Read all documents
        context_content = self._read_file(self.context_doc_path)
        output_content = self._read_file(self.output_doc_path)
        input_content = self._read_file(self.input_data_path)
        
        # Read the guide prompt with reasoning template
        guide_template = self._read_file(self.guide_prompt_with_reasoning_path)
        
        # Format the template with the content
        prompt = guide_template.format(
            context_content=context_content,
            output_content=output_content,
            input_content=input_content
        )
        
        return prompt
