import yaml
import sys
from yaml.loader import SafeLoader

# --- Custom constructor for the !lambda tag ---
def lambda_constructor(loader, node):
    """Treats a !lambda tag as a simple string."""
    return f"lambda: {node.value}"

# --- Custom constructor for the !secret tag ---
def secret_constructor(loader, node):
    """Treats a !secret tag as a simple string."""
    return f"secret: {node.value}"

# Add the constructors to the SafeLoader
SafeLoader.add_constructor('!lambda', lambda_constructor)
SafeLoader.add_constructor('!secret', secret_constructor)


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
    sensor_ids = []
    if 'binary_sensor' in data:
        for sensor in data.get('binary_sensor', []):
            if sensor.get('platform') == 'gpio':
                sid = sensor["id"]
                sensor_ids.append(f'BS_{sid}')
                graph += f'        BS_{sid}[Button<br/>{sid}<br/>Pin: {sensor["pin"]["number"]}]\n'
    graph += '    end\n\n'

    graph += '    A --> WIFI & API & OTA & LOG\n'
    if sensor_ids:
        graph += f'    A --> {" & ".join(sensor_ids)}\n'
    if 'i2c' in data:
        graph += '    A --> I2C\n'
    if 'spi' in data:
        graph += '    A --> SPI\n'

    # Apply classes
    graph += '\n    class A hardware\n'
    graph += '    class WIFI,API,OTA,LOG component\n'
    graph += f'    class {" ".join(sensor_ids)} io\n' if sensor_ids else ''
    graph += '    class I2C,SPI io\n'

    return get_mermaid_template("Core System & Hardware", graph)

def has_ducking(data):
    """Check if the YAML configuration includes ducking logic."""
    import json
    yaml_str = json.dumps(data)
    return 'apply_ducking' in yaml_str

def generate_audio_diagram(data):
    """Generates the diagram for the full Audio Input/Output pipeline."""
    # Extract IDs from YAML data
    mic_id = data.get('microphone', [{}])[0].get('id', 'mic')
    speaker_hw_id = next((s['id'] for s in data.get('speaker', []) if s.get('platform') == 'i2s_audio'), 'speaker')
    media_player_id = data.get('media_player', [{}])[0].get('id', 'media_player')
    va_id = data.get('voice_assistant', {}).get('id', 'voice_assistant')
    
    # Assume resampler IDs are standard
    ann_resample_id = 'announcement_resampling_speaker'
    media_resample_id = 'media_resampling_speaker'
    mixer_id = 'mixing_speaker'
    
    graph = '    subgraph "Input Microphone"\n'
    graph += f'        ADC[External ADC]\n'
    graph += f'        MIC[i2s_audio mic<br/>id: {mic_id}]\n'
    graph += '    end\n\n'

    graph += '    subgraph "Output Speaker Pipeline"\n'
    graph += f'        MEDIA[media_player<br/>id: {media_player_id}]\n'
    graph += f'        ARS[resampler<br/>id: {ann_resample_id}]\n'
    graph += f'        MRS[resampler<br/>id: {media_resample_id}<br/>media_mixing_input]\n'
    graph += f'        MIX[mixer<br/>id: {mixer_id}]\n'
    graph += f'        SPK_HW[i2s_audio speaker<br/>id: {speaker_hw_id}]\n'
    graph += '    end\n\n'
    
    graph += '    subgraph "Central Logic"\n'
    graph += f'        VA(voice_assistant<br/>id: {va_id})\n'
    graph += '    end\n\n'

    if has_ducking(data):
        graph += '    subgraph "Ducking Logic"\n'
        graph += '        DUCK_START[VA on_start<br/>Apply 20dB reduction<br/>duration: 0.0s]\n'
        graph += '        DUCK_ANNOUNCE[Media on_announcement<br/>Apply 20dB reduction<br/>duration: 0.0s]\n'
        graph += '        DUCK_END[VA on_end<br/>Remove reduction<br/>duration: 1.0s]\n'
        graph += '        DUCK_STATE[Media on_state<br/>Conditional unduck<br/>if not announcing & not VA running]\n'
        graph += '    end\n\n'

    graph += '    %% --- Connections --- %%\n'
    graph += '    ADC -->|"16kHz/16bit"| MIC\n'
    graph += '    MIC -->|"Audio Stream"| VA\n'
    graph += '    MEDIA --"Announcement Pipeline"--> ARS\n'
    graph += '    MEDIA --"Media Pipeline"--> MRS\n'
    graph += '    ARS & MRS -->|"Resampled to 48kHz"| MIX\n'
    graph += '    MIX -->|"Combined Stream"| SPK_HW\n'
    graph += '    VA -->|"Plays audio via"| MEDIA\n'
    
    if has_ducking(data):
        graph += '    VA -->|"on_start"| DUCK_START\n'
        graph += '    MEDIA -->|"on_announcement"| DUCK_ANNOUNCE\n'
        graph += '    VA -->|"on_end"| DUCK_END\n'
        graph += '    MEDIA -->|"on_state"| DUCK_STATE\n'
        graph += '    DUCK_START -->|"Duck Media Input"| MRS\n'
        graph += '    DUCK_ANNOUNCE -->|"Duck Media Input"| MRS\n'
        graph += '    DUCK_END -->|"Unduck Media Input"| MRS\n'
        graph += '    DUCK_STATE -->|"Unduck Media Input"| MRS\n'
    
    # Apply classes
    graph += '\n    class ADC,MIC,SPK_HW hardware\n'
    graph += '    class MEDIA,ARS,MRS,MIX component\n'
    graph += '    class VA logic\n'
    if has_ducking(data):
        graph += '    class DUCK_START,DUCK_ANNOUNCE,DUCK_END,DUCK_STATE trigger\n'

    return get_mermaid_template("Audio Pipeline", graph)

def generate_va_diagram(data):
    """Generates the diagram for the Voice Assistant logic and triggers."""
    mic_id = data.get('microphone', [{}])[0].get('id', 'mic')
    mww_id = data.get('micro_wake_word', {}).get('id', 'micro_wake_word')
    media_player_id = data.get('media_player', [{}])[0].get('id', 'media_player')
    va_id = data.get('voice_assistant', {}).get('id', 'voice_assistant')
    
    graph = '    subgraph "Inputs"\n'
    graph += f'        MIC[mic: {mic_id}]\n'
    graph += f'        MWW[{mww_id}]\n'
    graph += '    end\n\n'

    graph += '    subgraph "Core Logic"\n'
    graph += f'        VA({va_id})\n'
    graph += '    end\n\n'
    
    graph += '    subgraph "Outputs"\n'
    graph += f'        MP[{media_player_id}]\n'
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
    if 'display' not in data:
        return get_mermaid_template("Display & UI Logic", "    subgraph \"No Display Configured\"\n    end\n")
    
    display_id = data.get('display', [{}])[0].get('id', 'display')
    display_platform = data.get('display', [{}])[0].get('platform', 'unknown')
    
    graph = '    subgraph "Hardware & Assets"\n'
    graph += f'        LCD[display: {display_platform}<br/>id: {display_id}]\n'
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
            
            import os
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            
            core_file = f"{base_name}-core.mmd"
            with open(core_file, 'w', encoding='utf-8') as f:
                f.write(generate_core_diagram(data))
            
            audio_file = f"{base_name}-audio.mmd"
            with open(audio_file, 'w', encoding='utf-8') as f:
                f.write(generate_audio_diagram(data))
            
            va_file = f"{base_name}-va.mmd"
            with open(va_file, 'w', encoding='utf-8') as f:
                f.write(generate_va_diagram(data))
            
            display_file = f"{base_name}-display.mmd"
            with open(display_file, 'w', encoding='utf-8') as f:
                f.write(generate_display_diagram(data))

            print(f"Generated diagrams: {core_file}, {audio_file}, {va_file}, {display_file}")

    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")