# ESP32-S3-Box Audio Pipeline Fix Notes

## Problem Analysis
- The announcement pipeline in media_player is bypassing the announcement_resampling_speaker
- Currently: announcement_pipeline -> announcement_mixing_input (direct)
- Should be: announcement_pipeline -> announcement_resampling_speaker -> announcement_mixing_input
- Media pipeline is correctly configured: media_pipeline -> media_resampling_speaker -> media_mixing_input

## Research Findings
- Used Context7 library ID: /esphome/esphome-docs for ESPHome documentation
- Retrieved media_player and speaker component documentation
- Confirmed speaker pipeline structure:
  - resampler speaker: platform: resampler, output_speaker: target_speaker_id
  - mixer speaker: platform: mixer, output_speaker: hardware_speaker, source_speakers: [input_ids]

## Current YAML Structure (relevant parts)
```
speaker:
  - platform: resampler
    id: announcement_resampling_speaker
    output_speaker: announcement_mixing_input
    sample_rate: 48000
    bits_per_sample: 16
  - platform: mixer
    id: mixing_speaker
    output_speaker: box_speaker
    source_speakers:
      - id: announcement_mixing_input
      - id: media_mixing_input

media_player:
  - platform: speaker
    announcement_pipeline:
      speaker: announcement_mixing_input  # WRONG - should be announcement_resampling_speaker
    media_pipeline:
      speaker: media_resampling_speaker  # CORRECT
```

## Fixes Applied
✅ **COMPLETED**: Changed in media_player announcement_pipeline:
- speaker: announcement_mixing_input
to:
- speaker: announcement_resampling_speaker

✅ **COMPLETED**: Fixed speaker.is_playing ambiguity in voice_assistant on_end:
- speaker.is_playing:
to:
- speaker.is_playing: box_speaker

## Validation
✅ **PASSED**: ESPHome config validation successful
- Configuration is valid!
- Announcement pipeline now correctly routes through resampler
- Speaker ID ambiguity resolved

## Expected Behavior After Fix
1. Announcement audio (TTS) flows: announcement_pipeline -> announcement_resampling_speaker -> announcement_mixing_input -> mixing_speaker -> box_speaker
2. Media audio flows: media_pipeline -> media_resampling_speaker -> media_mixing_input -> mixing_speaker -> box_speaker
3. Both streams are resampled to 48000 Hz before mixing
4. Hardware speaker race conditions eliminated
5. Simultaneous announcement + media playback supported

## Next Steps
- Flash the updated configuration to ESP32-S3-Box device
- Test voice assistant announcements (TTS)
- Test media playback
- Test simultaneous announcement + media playback
- Monitor for any remaining audio issues