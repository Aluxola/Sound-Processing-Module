# Sound Processing Module (SPM) on FPGA

This project presents a **Sound Processing Module (SPM)** implemented using **Verilog HDL** and simulated using **Xilinx Vivado** and **Icarus Verilog (iverilog)**. The SPM performs **real-time minimum and maximum amplitude extraction** from 16-bit signed audio signals and applies **statistical filtering** on segmented intervals. This system is designed for applications such as **noise reduction**, **peak detection**, **dynamic range control**, and **loudspeaker protection**.

---

## 📌 Project Overview

The Sound Processing Module consists of two main functional sections:

### 1. **Min-Max Amplitude Detector**
- Continuously calculates the global minimum and maximum amplitudes of an incoming audio stream.
- Implemented as a finite state machine (FSM) with efficient sequential comparison logic.

### 2. **Interval-Based Min-Max Amplitude Detector**
- Segments the audio stream into predefined intervals (e.g., 1s = 44,100 samples).
- Computes min/max values for each interval.
- Applies statistical filtering using standard deviation to remove outliers.

---

## 🧠 Background and Applications

This project supports real-world audio processing tasks such as:

- **Impulsive Noise Reduction:** Removing clicks, pops, and transients using min/max filters.
- **Speech and Music Analysis:** Identifying peaks and low-energy regions.
- **Hardware Protection:** Preventing speaker damage from amplitude spikes.

---

## 🛠️ Technologies Used

- **Hardware Description Language:** Verilog
- **Simulation Tools:** Xilinx Vivado, Icarus Verilog
- **Waveform Visualization:** GTKWave
- **Reference Software (Golden Measure):** Python + PyOpenCL

---

## 🧪 Methodology

### A. Simulation Details
- Audio Format: 16-bit signed PCM, mono, 44.1kHz (up to 48kHz)
- Clock Frequency: 100 MHz
- Input: WAV file samples fed into testbench
- Output: Min and Max amplitudes (per interval and globally)

### B. Verification with Golden Measure
- Python and PyOpenCL implementations used as reference models
- Results from Verilog simulation compared against golden measure outputs
- Error metrics: Absolute error, relative error, mean squared error (MSE)

### C. Statistical Filtering
- For each interval:
  - Compute mean and standard deviation of min/max values
  - Remove outliers beyond 1σ
- Filtering verified to match software reference output

---

## 📊 Results Summary

### ✅ Global Min-Max Test
- **Total Samples Processed:** 441,000
- **Min Amplitude:** -32,768  
- **Max Amplitude:** 32,767  
- **Simulation Time:** 4.41s @ 100 MHz

### ✅ Interval-Based Test
- **10 Intervals of 1s Each**
- **Outlier Filtering Passed**
- **FPGA Results Matched Software Reference**

