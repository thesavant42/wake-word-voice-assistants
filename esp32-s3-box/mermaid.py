import yaml
import sys
from yaml.loader import SafeLoader

# --- Custom constructor for the !lambda tag ---
def lambda_constructor(loader, node):
    """Treats a !lambda tag as a simple string."""
    return f"lambda: {node.value}"

# Add the constructor to the SafeLoader
SafeLoader.add_constructor('!lambda', lambda_constructor)


# --- Helper function to create styled MermaidJS code ---
def get_mermaid_template(title, graph_definition):
    """Creates a complete, styled MermaidJS diagram string."""
    header = f"""%% ---- {title} ---- %%
graph TD
"""
    styling = """
    %% --- Styling --- %%
    classDef component fill:#cde,stroke:#333,stroke-width:2px,color:#000
    classDef hardware fill:#f96,stroke:#333,stroke-width:2px,color:#000
    classDef logic fill:#cfc,stroke:#333,stroke-width:2px,color:#000
    classDef trigger fill:#fdf,stroke:#333,stroke-width:2px,color:#000
    classDef io fill:#fec,stroke:#333,stroke-width:2px,color:#000
"""
    return header + graph_definition + styling

# --- Diagram Generation Functions ---

def generate_core_diagram(data):
    """Generates the diagram for Core System, Connectivity, and Hardware IO."""
    board = data.get('esp32', {}).get('board', 'esp32')
    graph = f'    subgraph "Core System"\n'
    graph += f'        A["`**{board}**`"]\n'
    graph += f'    end\n\n'
    
    graph += '    subgraph "Connectivity"\n'
    if 'wifi' in data:
        graph += '        WIFI[WiFi]\n'
    if 'api' in data:
        graph += '        API[API Server]\n'
    if 'ota' in data:
        graph += '        OTA[OTA Updates]\n'
    if 'logger' in data:
        graph += '        LOG[Logger]\n'
    graph += '    end\n\n'

    graph += '    subgraph "Hardware I/O"\n'
    if 'i2c' in data:
        graph += f'        I2C(I2C<br/>SCL: {data["i2c"]["scl"]}<br/>SDA: {data["i2c"]["sda"]})\n'
    if 'spi' in data:
        graph += f'        SPI(SPI<br/>CLK: {data["spi"][0]["clk_pin"]}<br/>MOSI: {data["spi"][0]["mosi_pin"]})\n'
    if 'binary_sensor' in data:
        for sensor in data.get('binary_sensor', []):
            if sensor.get('platform') == 'gpio':
                 graph += f'        BS_{sensor["id"]}[Button<br/>{sensor["id"]}<br/>Pin: {sensor["pin"]["number"]}]\n'
    graph += '    end\n\n'

    graph += '    A --> WIFI & API & OTA & LOG\n'
    graph += '    A --> I2C & SPI & BS_left_top_button\n'

    # Apply classes
    graph += '\n    class A hardware\n'
    graph += '    class WIFI,API,OTA,LOG component\n'
    graph += '    class I2C,SPI,BS_left_top_button io\n'

    return get_mermaid_template("Core System & Hardware", graph)

def generate_audio_diagram(data):
    """Generates the diagram for the full Audio Input/Output pipeline."""
    graph = '    subgraph "Input (Microphone)"\n'
    graph += '        ADC[es7210 ADC]\n'
    graph += '        MIC[i2s_audio mic<br/>id: box_mic]\n'
    graph += '    end\n\n'

    graph += '    subgraph "Output (Speaker Pipeline)"\n'
    graph += '        MEDIA[media_player]\n'
    graph += '        ARS[resampler<br/>id: announcement_resampling_speaker]\n'
    graph += '        MRS[resampler<br/>id: media_resampling_speaker]\n'
    graph += '        MIX[mixer<br/>id: mixing_speaker]\n'
    graph += '        SPK_HW[i2s_audio speaker<br/>id: box_speaker]\n'
    graph += '    end\n\n'
    
    graph += '    subgraph "Central Logic"\n'
    graph += '        VA(voice_assistant)\n'
    graph += '    end\n\n'

    graph += '    %% --- Connections --- %%\n'
    graph += '    ADC -->|"16kHz/16bit"| MIC\n'
    graph += '    MIC -->|"To Voice Assistant"| VA\n'
    graph += '    MEDIA --"Announcement Pipeline"--> ARS\n'
    graph += '    MEDIA --"Media Pipeline"--> MRS\n'
    graph += '    ARS & MRS -->|"Resampled to 48kHz"| MIX\n'
    graph += '    MIX -->|"Combined Stream"| SPK_HW\n'
    graph += '    VA -->|"Plays audio via"| MEDIA\n'
    
    # Apply classes
    graph += '\n    class ADC,MIC,SPK_HW hardware\n'
    graph += '    class MEDIA,ARS,MRS,MIX component\n'
    graph += '    class VA logic\n'

    return get_mermaid_template("Audio Pipeline", graph)

def generate_va_diagram(data):
    """Generates the diagram for the Voice Assistant logic and triggers."""
    graph = '    subgraph "Inputs"\n'
    graph += '        MIC[mic: box_mic]\n'
    graph += '        MWW[micro_wake_word]\n'
    graph += '    end\n\n'

    graph += '    subgraph "Core Logic"\n'
    graph += '        VA(voice_assistant)\n'
    graph += '    end\n\n'
    
    graph += '    subgraph "Outputs"\n'
    graph += '        MP[media_player]\n'
    graph += '    end\n\n'

    graph += '    subgraph "Triggers & Actions"\n'
    graph += '        T_LISTEN[on_listening]\n'
    graph += '        T_STT_END[on_stt_end]\n'
    graph += '        T_TTS_START[on_tts_start]\n'
    graph += '        T_END[on_end]\n'
    graph += '        T_ERR[on_error]\n'
    graph += '        S_DRAW[script: draw_display]\n'
    graph += '        S_WAKE[script: start/stop_wake_word]\n'
    graph += '    end\n\n'
    
    graph += '    %% --- Connections --- %%\n'
    graph += '    MWW --"Wake Word Detected"--> VA\n'
    graph += '    MIC -->|"Audio Stream"| VA\n'
    graph += '    VA -->|"Plays TTS/Media"| MP\n'
    graph += '    VA --> T_LISTEN & T_STT_END & T_TTS_START & T_END & T_ERR\n'
    graph += '    T_LISTEN & T_STT_END & T_TTS_START & T_ERR -->|"Calls"| S_DRAW\n'
    graph += '    T_END -->|"Calls"| S_WAKE\n'
    
    # Apply classes
    graph += '\n    class VA logic\n'
    graph += '    class MIC,MWW,MP io\n'
    graph += '    class T_LISTEN,T_STT_END,T_TTS_START,T_END,T_ERR trigger\n'
    graph += '    class S_DRAW,S_WAKE component\n'
    
    return get_mermaid_template("Voice Assistant Logic", graph)
    
def generate_display_diagram(data):
    """Generates the diagram for the Display and UI logic."""
    graph = '    subgraph "Hardware & Assets"\n'
    graph += '        LCD[display: ili9xxx<br/>id: s3_box_lcd]\n'
    graph += '        FONTS[Fonts]\n'
    graph += '        IMAGES[Images]\n'
    graph += '    end\n\n'
    
    graph += '    subgraph "UI Logic"\n'
    graph += '        DRAW[script: draw_display]\n'
    graph += '        PAGES[Display Pages<br/>(idle, listening, etc.)]\n'
    graph += '    end\n\n'
    
    graph += '    subgraph "Event Triggers"\n'
    graph += '        T_BOOT[on_boot]\n'
    graph += '        T_VA[voice_assistant events]\n'
    graph += '        T_WIFI[wifi/api events]\n'
    graph += '    end\n\n'
    
    graph += '    %% --- Connections --- %%\n'
    graph += '    T_BOOT & T_VA & T_WIFI -->|"Call"| DRAW\n'
    graph += '    DRAW -->|"Shows"| PAGES\n'
    graph += '    PAGES -->|"Renders on"| LCD\n'
    graph += '    FONTS & IMAGES -->|"Used by"| PAGES\n'
    
    # Apply classes
    graph += '\n    class LCD hardware\n'
    graph += '    class FONTS,IMAGES,PAGES,DRAW component\n'
    graph += '    class T_BOOT,T_VA,T_WIFI trigger\n'

    return get_mermaid_template("Display & UI Logic", graph)


# --- Main Execution ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_diagrams.py <path_to_yaml_file>")
        sys.exit(1)

    file_path = sys.argv[1]
    
    try:
        # Open the file with UTF-8 encoding to handle special characters
        with open(file_path, 'r', encoding='utf-8') as f:
            # Use the modified SafeLoader to handle the !lambda tag
            data = yaml.load(f, Loader=SafeLoader)
            
            print(generate_core_diagram(data))
            print("\n" + "="*80 + "\n")
            print(generate_audio_diagram(data))
            print("\n" + "="*80 + "\n")
            print(generate_va_diagram(data))
            print("\n" + "="*80 + "\n")
            print(generate_display_diagram(data))

    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")