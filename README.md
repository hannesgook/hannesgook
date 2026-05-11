# Hannes Göök
I build realtime control systems from first principles.
Embedded firmware, wireless stacks, reinforcement learning, Unity simulators. Programming for 7+ years, professionally since 2021.

🏆 Winner of the Yale SEA Most Outstanding STEM Exhibit - Unga Forskare 2026 National Final

My personal projects include embedded C++, Unity simulators and multiplayer-solutions, full-stack RC systems, synthetic data generation in Unity.

Currently in my final year at Hulebäcksgymnasiet (Teknikprogrammet), a Swedish upper-secondary school, graduating 2026.

## Projects

### PidraQRL
A quadrotor built entirely from scratch with a live SAC reinforcement learning agent tuning roll-controller gains in real time and a Unity HDRP digital twin mirroring live telemetry.
- Custom ESP32 flight controller with cascaded PID, Madgwick AHRS, and biquad filters (250 Hz loop)
- Full wireless chain: Flutter app -> BLE -> Raspberry Pi -> LoRa -> ESP32 (+ direct BLE for RL)
- SAC RL agent tuning PID gains in real time on the physical drone, no sim-to-real transfer
- Custom single-axis test rig for safe RL training with live propellers
- Unity HDRP digital twin with Fusion 360 models, mirroring live IMU telemetry over UDP
- **Winner of the Yale SEA Most Outstanding STEM Exhibit** - Unga Forskare 2026 National Final (Sweden's Young Researchers national championship)

>🏅 [Official winners list (Swedish)](https://ungaforskare.se/wp-content/uploads/2026/04/alla-vinnare-uuf-2026.pdf)
>
>🗞️ [Winners announcement with photos (LinkedIn) (Swedish)](https://www.linkedin.com/posts/grattis-till-alla-fantastiska-pristagare-ugcPost-7443214290331017216-65qc?utm_source=social_share_send&utm_medium=member_desktop_web&rcm=ACoAAExydk8B2cZze4JlFAEzUhzplSSweQ-0wBE)
>
>🌐 [Digital exhibition](https://events.projectboard.world/ungaforskare2026/project/222684)
>
>*"The project stands out through a very high level of technical ambition. The custom-built flight controller, the distributed communication chain, and the well-designed failsafe solution demonstrate a deep understanding of real-time systems, control theory, and system safety. The methodology is exemplarily clear and reproducible."* - Translated research jury feedback, Unga Forskare 2026
>
>*"In this project, the team members refused to take any shortcuts whatsoever. By rejecting ready-made frameworks and instead building everything from scratch, from communication to software, this work has demonstrated a technical dedication beyond the ordinary."* - Winners catalogue, Unga Forskare 2026 (translated) - [Link (Swedish)](https://ungaforskare.se/wp-content/uploads/2026/04/alla-vinnare-uuf-2026.pdf)
>
>**📰 Press:** [Hulebäcksgymnasiet news (Swedish)](https://hulebacksgymnasiet.harryda.se/nyhetsarkiv/2026-02-27-tavlar-med-egenbyggd-dronare), [School video (Swedish)](https://youtu.be/nFjXQu7kyrs?si=i-YoVVQbaT2_d_f_), [Local press (Swedish)](https://www.lokalpressen.se/hulebackselever-till-final-i-forskningssm-6.2.6460.2d8ea205e6)

**Repo:** [PidraQRL](https://github.com/hannesgook/PidraQRL)

![Drone](https://raw.githubusercontent.com/hannesgook/PidraQRL/main/docs/drone_hero.jpg)
![System setup](https://raw.githubusercontent.com/hannesgook/PidraQRL/main/docs/system_setup.jpg)

---

### GDForge
Generates a playable Geometry Dash level from any song using beat detection and physics simulation.
- Analyzes audio to detect beats and uses them to drive level generation
- Cube mode simulates ballistic arc physics reverse-engineered from observed in-game behavior
- Wave mode generates a diagonal path with rails and ramps sampled by arc length
- Reverse-engineered the `.gmd` format used by the GDShare mod to write valid level files importable directly into GD
- PyQt GUI with synchronized audio waveform and level geometry preview

**Repo:** [GDForge](https://github.com/hannesgook/gdforge)

![GDForge GUI](https://raw.githubusercontent.com/hannesgook/gdforge/main/docs/gui.png)
![GDForge Result](https://raw.githubusercontent.com/hannesgook/gdforge/main/docs/result_cube.png)

## Work Experience

**Software Developer** - CPAC Systems - Recurring, 2021-2025

Five paid internships starting at age 15 across four years building internal tools and simulators in C#, Python, and Unity.

- Optimized a Unity simulator, doubling frame rate
- Built a Python diagnostics tool adopted by senior engineers for root cause analysis
- Built a license management service (HTML, CSS, JS)
- Developed machine simulations with custom mesh generation in Unity
- Refactored Perl codebases and worked on a web application (HTML, SCSS, TypeScript)

## Skills

**Embedded systems:** C++, Arduino, PID control, IMU data filtering and handling, Fusion 360

**Simulation & Graphics:** Unity, C#, procedural generation (noise combining), Blender

**App:** Flutter (dart), React, Python

**AI:** Reinforcement learning, YOLO, Torch, dataset generation

**Languages:** Swedish (native), English (fluent), French (basic)
