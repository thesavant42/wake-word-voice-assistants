## Task: 1. esp32-s3-box.yaml audio fix

### Description
The announcement and media pipelines for the esp32-s3-box are broken, resulting in a hardware race condition. The previous config lacked implementing any form of resampling and mixing of the media+announcement channels (which would allow them to shaere a single hardware speaker). The result is the hardware fighting itself for audio devices.

By charting the relationships between entities, the problem becomes more obvious: The announcement_resampling_speaker component was accidentally bypassed, preventing proper function.

## As it exists:

 `announcement_resampling_speaker` is unintentionally bypassed

```
graph TD
    subgraph "Audio Source (media_player)"
        A[Announcements]
        M[Media]
    end

    subgraph "Processing & Mixing"
        MRS[media_resampling_speaker]
        MIX[mixing_speaker]
        AMI[announcement_mixing_input]
        MMI[media_mixing_input]
    end

    subgraph "Unused Component"
        style Unused fill:#fdd,stroke:#333,stroke-width:2px
        ARS[announcement_resampling_speaker]
    end

    subgraph "Hardware Output"
        HW[box_speaker I2S]
    end

    %% Connections
    M -- "media_pipeline" --> MRS
    A -- "announcement_pipeline" --> AMI
    MRS -- "resampled media" --> MMI
    MMI -->|Input 2| MIX
    AMI -->|Input 1| MIX
    MIX -- "combined audio" --> HW

    %% Styling
    classDef component fill:#cde,stroke:#333,stroke-width:2px,color:#000
    classDef hardware fill:#f96,stroke:#333,stroke-width:2px,color:#000
    classDef source fill:#cfc,stroke:#333,stroke-width:2px,color:#000
    classDef virtual fill:#fff,stroke:#333,stroke-dasharray: 5 5,color:#000

    class A,M source
    class MRS,MIX component
    class ARS Unused
    class AMI,MMI virtual
    class HW hardware
```

Intended Implementation: announcement_resampling_speaker (185-195) is sandwiched between [announcement_pipeline] (203) and [announcement_mixing_input]

```
graph TD
    subgraph "Audio Source (media_player)"
        A[Announcements]
        M[Media]
    end

    subgraph "Processing & Mixing"
        ARS[announcement_resampling_speaker]
        MRS[media_resampling_speaker]
        MIX[mixing_speaker]
        AMI[announcement_mixing_input]
        MMI[media_mixing_input]
    end

    subgraph "Hardware Output"
        HW[box_speaker I2S]
    end

    %% Connections
    M -- "media_pipeline" --> MRS
    A -- "announcement_pipeline" --> ARS
    ARS -- "resampled announcement" --> AMI
    MRS -- "resampled media" --> MMI
    MMI -->|Input 2| MIX
    AMI -->|Input 1| MIX
    MIX -- "combined audio" --> HW

    %% Styling
    classDef component fill:#cde,stroke:#333,stroke-width:2px,color:#000
    classDef hardware fill:#f96,stroke:#333,stroke-width:2px,color:#000
    classDef source fill:#cfc,stroke:#333,stroke-width:2px,color:#000
    classDef virtual fill:#fff,stroke:#333,stroke-dasharray: 5 5,color:#000

    class A,M source
    class ARS,MRS,MIX component
    class AMI,MMI virtual
    class HW hardware
    ```

## Important Sections:

### line:161 # Hardware Speaker section begins

### lines:162:173 Box Speaker 

- This is the physical hardware output, single channel

### 174:184 mixing speaker

- merges inputs from media and announcements
- 2 channels (media, and announcement)

### 185:196 Announcement Resampling Speaker

- outputs to mixing speaker's announcement_mixing_input
- Used for text-to-speech notifications, AI chats

### 197:252 Media Player

- manages announcement pipeline
    - speaker:announcement  box_speaker # Should be media resampling speaker!
- manages media pipeline
    - speaker: media_resampling_speaker


