<div align="center">

# Hannes Göök

<a href="https://github.com/hannesgook">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=20&pause=1000&color=38BDF8&center=true&vCenter=true&width=600&lines=I+build+real-time+control+systems+from+scratch;Custom+ESP32+flight+controllers;Stereo+vision+and+visual+odometry;Reinforcement+learning+on+real+hardware" alt="Typing SVG" />
</a>

<br/>

<img src="https://img.shields.io/badge/Unga_Forskare_2026-Yale_SEA_Most_Outstanding_STEM_Exhibit-FFB800?style=for-the-badge&logo=trophy&logoColor=white" />
<br/>
<img src="https://img.shields.io/badge/Programming-7%2B_years-8B5CF6?style=for-the-badge" />
<img src="https://img.shields.io/badge/Professional-since_2021-10B981?style=for-the-badge" />

</div>

---

## About me

I build end-to-end **real-time control and machine-learning systems** across custom hardware and software: embedded firmware, wireless communication, computer vision, and reinforcement learning.

Recent projects: two from-scratch quadcopters with custom ESP32 flight controllers. **KattVis** uses onboard stereo vision for GPS-free motion and position estimation, while **PidraQRL** has a live RL agent tuning PID gains in real time on physical hardware.

> [!IMPORTANT]
> **Winner of the Yale SEA Most Outstanding STEM Exhibit** at the Unga Forskare 2026 National Final (Sweden's Young Researchers national championship)

---

## Projects

### KattVis &nbsp; <sub>2026 – present</sub>

<img src="https://img.shields.io/badge/ESP32-E7352C?style=flat-square&logo=espressif&logoColor=white" /> <img src="https://img.shields.io/badge/Raspberry_Pi_5-A22846?style=flat-square&logo=raspberrypi&logoColor=white" /> <img src="https://img.shields.io/badge/OpenCV-5C3EE8?style=flat-square&logo=opencv&logoColor=white" /> <img src="https://img.shields.io/badge/Flutter-02569B?style=flat-square&logo=flutter&logoColor=white" /> <img src="https://img.shields.io/badge/Unity-000000?style=flat-square&logo=unity&logoColor=white" /> <img src="https://img.shields.io/badge/Fusion_360-F58220?style=flat-square&logo=autodesk&logoColor=white" />

A stereo-vision quadcopter built from scratch, flying **without GPS or a barometer**, using onboard stereo cameras and an IMU instead.

<table>
  <tr>
    <td width="50%"><img src="https://raw.githubusercontent.com/hannesgook/kattvis/main/docs/drone_hero.jpg" alt="KattVis drone"/></td>
    <td width="50%"><img src="https://raw.githubusercontent.com/hannesgook/kattvis/main/docs/flight_mode.jpg" alt="Flutter ground station"/></td>
  </tr>
</table>

- Custom ESP32 flight controller with a cascaded PID loop at **250 Hz**, running independently of the vision workload
- Deadcat airframe with a tuned front/rear roll-mix to compensate for the front motors' extra torque leverage
- Raspberry Pi 5 running an onboard stereo-vision and visual-odometry pipeline (dual OV9281 global-shutter cameras, 12 cm baseline) for GPS-free motion and altitude estimation
- Custom Flutter ground station with the CAD-modeled airframe rendered live, PID tuning, a per-motor test mode, and built-in stereo calibration
- Prototyped the stereo pipeline in Unity before buying the physical cameras, to prove the approach out first
- Custom nylon airframe designed in Fusion 360, manufactured and sponsored by PCBWay

> [!TIP]
> **Status:** 10 seconds of controlled flight demonstrated so far. Altitude hold is functional and being tuned.

<a href="https://github.com/hannesgook/kattvis"><img src="https://img.shields.io/badge/View_repo-KattVis-181717?style=for-the-badge&logo=github" /></a>

---

### PidraQRL &nbsp; <sub>2025 – 2026</sub>

<img src="https://img.shields.io/badge/ESP32-E7352C?style=flat-square&logo=espressif&logoColor=white" /> <img src="https://img.shields.io/badge/PyTorch-EE4C2C?style=flat-square&logo=pytorch&logoColor=white" /> <img src="https://img.shields.io/badge/Unity_HDRP-000000?style=flat-square&logo=unity&logoColor=white" /> <img src="https://img.shields.io/badge/Flutter-02569B?style=flat-square&logo=flutter&logoColor=white" /> <img src="https://img.shields.io/badge/BLE-0082FC?style=flat-square&logo=bluetooth&logoColor=white" /> <img src="https://img.shields.io/badge/LoRa-1C8B8B?style=flat-square" />

A quadrotor built entirely from scratch with a **live SAC reinforcement learning agent** tuning roll-controller gains in real time, and a Unity HDRP digital twin mirroring live telemetry.

<table>
  <tr>
    <td width="50%"><img src="https://raw.githubusercontent.com/hannesgook/PidraQRL/main/docs/drone_hero.jpg" alt="PidraQRL drone"/></td>
    <td width="50%"><img src="https://raw.githubusercontent.com/hannesgook/PidraQRL/main/docs/system_setup.jpg" alt="System setup"/></td>
  </tr>
</table>

- Custom ESP32 flight controller with cascaded PID, Madgwick AHRS, and biquad filters (250 Hz loop)
- Full wireless chain: `Flutter app → BLE → Raspberry Pi → LoRa → ESP32` (+ direct BLE for RL)
- SAC RL agent tuning PID gains in real time on the physical drone, **no sim-to-real transfer**
- Custom single-axis test rig for safe RL training with live propellers
- Unity HDRP digital twin with Fusion 360 models, mirroring live IMU telemetry over UDP

> [!IMPORTANT]
> **Winner of the Yale SEA Most Outstanding STEM Exhibit** – Unga Forskare 2026 National Final

<details>
<summary><b>What the jury said</b></summary>
<br/>

> *"The project stands out through a very high level of technical ambition. The custom-built flight controller, the distributed communication chain, and the well-designed failsafe solution demonstrate a deep understanding of real-time systems, control theory, and system safety. The methodology is exemplarily clear and reproducible."*
> <br/>— Translated research jury feedback, Unga Forskare 2026

> *"In this project, the team members refused to take any shortcuts whatsoever. By rejecting ready-made frameworks and instead building everything from scratch, from communication to software, this work has demonstrated a technical dedication beyond the ordinary."*
> <br/>— Winners catalogue, Unga Forskare 2026 (translated)

</details>

<details>
<summary><b>Press and links</b></summary>
<br/>

- [Official winners list (Swedish)](https://ungaforskare.se/wp-content/uploads/2026/04/alla-vinnare-uuf-2026.pdf) (Drone Control System)
- [Winners announcement with photos (LinkedIn, Swedish)](https://www.linkedin.com/posts/grattis-till-alla-fantastiska-pristagare-ugcPost-7443214290331017216-65qc?utm_source=social_share_send&utm_medium=member_desktop_web&rcm=ACoAAExydk8B2cZze4JlFAEzUhzplSSweQ-0wBE)
- [Digital exhibition](https://events.projectboard.world/ungaforskare2026/project/222684)
- [Hulebäcksgymnasiet news (Swedish)](https://hulebacksgymnasiet.harryda.se/nyhetsarkiv/2026-02-27-tavlar-med-egenbyggd-dronare)
- [School video (Swedish)](https://youtu.be/nFjXQu7kyrs?si=i-YoVVQbaT2_d_f_)
- [Local press (Swedish)](https://www.lokalpressen.se/hulebackselever-till-final-i-forskningssm-6.2.6460.2d8ea205e6)

</details>

<a href="https://github.com/hannesgook/PidraQRL"><img src="https://img.shields.io/badge/View_repo-PidraQRL-181717?style=for-the-badge&logo=github" /></a>

---

### GDForge &nbsp; <sub>2025 – 2026</sub>

<img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" /> <img src="https://img.shields.io/badge/PyQt-41CD52?style=flat-square&logo=qt&logoColor=white" /> <img src="https://img.shields.io/badge/Audio_analysis-FF6F61?style=flat-square" /> <img src="https://img.shields.io/badge/Reverse_engineering-6B7280?style=flat-square" />

Generates a **playable Geometry Dash level from any song** using beat detection and physics simulation.

<table>
  <tr>
    <td width="50%"><img src="https://raw.githubusercontent.com/hannesgook/gdforge/main/docs/gui.png" alt="GDForge GUI"/></td>
    <td width="50%"><img src="https://raw.githubusercontent.com/hannesgook/gdforge/main/docs/result_cube.png" alt="GDForge result"/></td>
  </tr>
</table>

- Analyzes audio to detect beats and uses them to drive level generation
- Cube mode simulates ballistic arc physics reverse-engineered from observed in-game behavior
- Wave mode generates a diagonal path with rails and ramps sampled by arc length
- Reverse-engineered the `.gmd` format used by the GDShare mod to write valid level files importable directly into GD
- PyQt GUI with synchronized audio waveform and level geometry preview

<a href="https://github.com/hannesgook/gdforge"><img src="https://img.shields.io/badge/View_repo-GDForge-181717?style=for-the-badge&logo=github" /></a>

---

## Work Experience

> [!NOTE]
> **Software Developer** at **CPAC Systems**, recurring 2021 – 2025
> <br/>Five paid internships starting at age 15 across four years, building internal tools and simulators in C#, Python, and Unity.

- Optimized a Unity simulator, **doubling frame rate**
- Built a Python diagnostics tool adopted by senior engineers for root cause analysis
- Built a license management service (HTML, CSS, JS)
- Developed machine simulations with custom mesh generation in Unity
- Refactored Perl codebases and worked on a web application (HTML, SCSS, TypeScript)

---

## Tech Stack

<div align="center">

<img src="https://skillicons.dev/icons?i=cpp,arduino,raspberrypi,python,cs,unity,blender&perline=7" />
<br/>
<img src="https://skillicons.dev/icons?i=opencv,pytorch,flutter,dart,react,ts,linux,git&perline=8" />

</div>

<br/>

| Area | Skills |
|---|---|
| **Embedded systems** | C++, Arduino, PID control, IMU data filtering and handling, Fusion 360 |
| **Simulation & Graphics** | Unity, C#, procedural generation (noise combining), Blender |
| **Computer Vision** | OpenCV, stereo vision, visual odometry, feature tracking, camera calibration |
| **App** | Flutter (Dart), React, Python |
| **AI** | Reinforcement learning, YOLO, Torch, dataset generation |
| **Languages** | Swedish (native), English (fluent), French (basic) |
