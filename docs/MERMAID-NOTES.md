# Mermaid Notes

## Analysis of the Issue

The script `mermaid.py` generates Mermaid diagrams from ESPHome YAML configurations. When executed on `home-assistant-voice.yaml`, it produced `box.mmd` containing multiple diagrams concatenated with separator lines of equals signs. This concatenation causes a syntax error because Mermaid parsers expect a single, valid graph definition per file or properly formatted input.

The specific error "Parse error on line 22: ...width:2px,color:#000=================... Expecting 'SEMI', 'NEWLINE', 'SPACE', 'EOF', 'COLON', 'STYLE', 'NUM', 'COMMA', 'NODE_STRING', 'UNIT', 'BRKT', 'PCT', got 'LINK'" indicates that the parser encounters the separator line (`=================`) while attempting to parse the graph, treating it as invalid syntax within the graph definition.

Additionally, subgraph titles in the generated diagrams contain parentheses (e.g., "Input (Microphone)"), which can cause parsing issues in some Mermaid implementations or renderers.

The script was originally designed for YAML files like `esp32-s3-box.yaml`, which contain sections for `esp32`, `i2c`, `spi`, `binary_sensor`, etc. Running it on `home-assistant-voice.yaml` (which lacks these sections) results in incomplete or default diagrams, but the syntax issues persist.

## Fixes Applied

1. **Modified `mermaid.py`**:
   - Removed parentheses from subgraph titles to prevent parsing conflicts (e.g., "Input (Microphone)" → "Input Microphone").
   - Changed the output mechanism to generate separate `.mmd` files for each diagram instead of concatenating them with separators.
   - Updated the main execution block to write individual files: `{base}-core.mmd`, `{base}-audio.mmd`, `{base}-va.mmd`, `{base}-display.mmd`.

2. **Fixed `box.mmd`**:
   - Split the concatenated content into four separate files: `box-core.mmd`, `box-audio.mmd`, `box-va.mmd`, `box-display.mmd`.
   - Removed separator lines and fixed parentheses in subgraph titles within the new files.

3. **Validation**:
   - Ensured each generated diagram is a standalone, syntactically valid Mermaid graph.
   - Verified that HTML-like tags (e.g., `<br/>`) in node labels are preserved, as they are supported by Mermaid.

## References

- [Mermaid Documentation](https://mermaid.js.org/): Official syntax and best practices for graph definitions.
- ESPHome YAML Configuration: Structure and components for IoT devices.
- GitHub Repository: thesavant42/wake-word-voice-assistants – Source of YAML configs and diagrams.

## Future Improvements

- Enhance the script to better handle different YAML structures or add validation for required sections.
- Consider integrating Mermaid validation tools (e.g., via `mermaid-cli`) to check generated diagrams automatically.
- Explore using a single diagram with nested subgraphs if multiple views are needed.