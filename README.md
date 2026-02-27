# Hannes Göök

I build realtime control systems from first principles.
Embedded firmware, wireless stacks, Unity simulators. Programming for 7+ years, professionally since 2021.

Unga Forskare 2026 national finalist

My personal projects include embedded C++, Unity simulators and multiplayer-solutions, full-stack RC systems, synthetic data generation in Unity.

Currently in my final year at Hulebäcksgymnasiet (Teknikprogrammet), a Swedish upper-secondary school, graduating 2026.

## Projects

### Quadcopter BLE-LoRa Controller
A complete drone control system built entirely from first principles without flight control frameworks. Achieved stable hover several meters above ground and several controlled landings.

- Custom Arduino flight controller with cascaded PID stabilization and Madgwick IMU filter (~250 Hz loop frequency)
- Full wireless chain: Flutter app -> BLE -> Raspberry Pi -> LoRa -> Arduino flight controller (60 ms latency)
- Custom CAD airframe designed in Fusion 360 and 3D-printed (PLA plastic)
- Modified RadioHead library at source level for real-time motor control requirements
- :medal_sports: **Qualified for the national final of Unga Forskare - Sweden's national science competition for young researchers**

*"The project stands out through a very high level of technical ambition. The custom-built flight controller, the distributed communication chain, and the well-designed failsafe solution demonstrate a deep understanding of real-time systems, control theory, and system safety. The methodology is exemplarily clear and reproducible."* - Translated research jury feedback, Unga Forskare 2026

**📰 Press (Swedish):** [Hulebäcksgymnasiet](https://hulebacksgymnasiet.harryda.se/nyhetsarkiv/2026-02-27-tavlar-med-egenbyggd-dronare), [Video](https://youtu.be/nFjXQu7kyrs?si=LQH_s4t5zsvco7_y) *(I'm on the far left)*

**Drone & Pi repo:** [quadcopter-ble-lora-controller](https://github.com/hannesgook/quadcopter-ble-lora-controller)
**App repo:** [PidraQ](https://github.com/hannesgook/pidraq)
  
![Full system setup](https://raw.githubusercontent.com/hannesgook/quadcopter-ble-lora-controller/main/images/full_system_setup.jpg)

## Work Experience

**Programmer** - CPAC Systems - Recurring, 2021-2025

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

**AI:** YOLO, Torch, dataset generation

**Languages:** Swedish (native), English (fluent), French (basic)
