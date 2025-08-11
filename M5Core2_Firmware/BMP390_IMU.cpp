/**
 * BMP390_IMU Logger v3.4 - Water Rocket Research Project
 * 
 * Sistema di acquisizione dati per IMU MPU6886 e sensore barometrico BMP390
 * specificamente progettato per il monitoraggio dell'altitudine di water rocket.
 * 
 * Hardware: M5Core2
 * Funzionalità:
 * - Acquisizione dati IMU a 1kHz via FIFO (accelerometro + giroscopio)
 * - Acquisizione dati BMP390 a 100Hz via FIFO con calcolo altitudine barometrica
 * - Scrittura asincrona su SD card con buffer ottimizzati per alte frequenze
 * - Interfaccia touch per controllo logging pre/post lancio
 * - Sincronizzazione timestamp tra sensori per analisi di volo precisa
 * - Calcolo altitudine relativa con azzeramento automatico al decollo
 */

// ============================================================================
// INCLUDES
// ============================================================================

// M5Stack Core Libraries
#include <M5Unified.h>
#include "utility/imu/MPU6886_Class.hpp"
#include "utility/imu/IMU_Base.hpp"
#include "utility/I2C_Class.hpp"

// Bosch BMP3 Driver (Official)
extern "C" {
#include "bmp3.h"
}
#include "bmp3_defs.h"

// System Libraries
#include <Wire.h>
#include <math.h>
#include <SPI.h>
#include <SdFat.h>

// FreeRTOS Real-Time OS
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

// ============================================================================
// HARDWARE CONFIGURATION CONSTANTS
// ============================================================================

// SD Card SPI Configuration
#define SD_FAT_TYPE 3
#define SD_CS_PIN GPIO_NUM_4        // M5Core2 SD card chip select pin
#define SPI_CLOCK SD_SCK_MHZ(25)    // 25MHz SPI clock for fast writes

// Data Buffer and Queue Sizing
#define BUFFER_SIZE       8192      // Main buffer size for data accumulation
#define CHUNK_SIZE        1024      // Write chunk size (1KB blocks)
#define IMU_QUEUE_LEN     500       // IMU data queue length (high frequency)
#define BMP_QUEUE_LEN     500       // BMP390 data queue length

// BMP390 Calibration Parameters
#define WARMUP_SAMPLES    8         // Initial samples to discard for sensor stabilization
#define REF_SAMPLES       50        // Samples to average for reference pressure P0
#define SAMPLE_DELAY_MS   100       // Delay between calibration samples (~10Hz)

// User Interface Timing
const unsigned long DEBOUNCE_DELAY = 200;              // Touch debounce in ms
const unsigned long GRAPHICS_UPDATE_INTERVAL = 1000;   // Display refresh rate
const unsigned long FLUSH_INTERVAL_MS = 1000;          // SD card flush interval

// ============================================================================
// BINARY DATA STRUCTURES FOR HIGH-SPEED LOGGING
// ============================================================================

#pragma pack(push, 1)  // Pack structures to minimize storage space

// IMU data packet structure (accelerometer + gyroscope + timestamp)
struct BinaryIMUData {
    char header = 'I';                          // Packet type identifier
    m5::IMU_Base::imu_raw_data_t IMUdata;      // Raw IMU data from M5 library
    uint32_t timestamp;                         // Microsecond timestamp
};

// BMP390 data packet structure (altitude + timestamp)
struct BinaryBMPData {
    char header = 'B';                          // Packet type identifier
    float altitude;                             // Calculated relative altitude in meters
    uint32_t timestamp;                         // Microsecond timestamp
};

#pragma pack(pop)

// ============================================================================
// GLOBAL HARDWARE OBJECTS
// ============================================================================

// IMU sensor object
m5::MPU6886_Class imu;

// SD card filesystem objects
SdFs sd;
FsFile dataFile;

// BMP390 sensor objects and buffers
static bmp3_dev bmp3;                          // Main BMP3 device structure
static bmp3_fifo bmp3Fifo;                    // FIFO management structure
static uint8_t bmp_fifo_buffer[1024];         // Raw FIFO data buffer
static uint8_t bmp_i2c_addr = BMP3_ADDR_I2C_PRIM;  // I2C address (auto-detected)

// ============================================================================
// FREERTOS QUEUES FOR INTER-TASK COMMUNICATION
// ============================================================================

QueueHandle_t dataQueue;    // Queue for IMU data packets
QueueHandle_t bmpQueue;     // Queue for BMP390 data packets

// ============================================================================
// FILE MANAGEMENT VARIABLES
// ============================================================================

String filename;            // Generated log filename
int randomNum1;             // Random number for unique filename generation

// ============================================================================
// SENSOR CALIBRATION AND REFERENCE VALUES
// ============================================================================

float referencePressure = NAN;     // Reference pressure P0 in Pascals for altitude calculation
float baseAltitude = NAN;          // Base altitude offset for relative altitude measurement

// ============================================================================
// TIMESTAMP SYNCHRONIZATION VARIABLES
// ============================================================================
// These variables synchronize BMP390 internal sensor time with MCU microsecond timer

static bool bmp_firstSync = true;       // Flag for initial synchronization
static uint32_t bmp_t0_mcu = 0;         // MCU timestamp at sync point (microseconds)
static uint32_t bmp_t0_sensor = 0;      // Sensor timestamp at sync point (microseconds)

// ============================================================================
// SYSTEM STATE CONTROL VARIABLES
// ============================================================================

volatile bool loggingActive = false;    // Main logging state flag
volatile bool shutdownPending = false;  // Graceful shutdown request flag
volatile bool errorPending = false;     // Error state flag

// ============================================================================
// USER INTERFACE STATE VARIABLES
// ============================================================================

unsigned long lastGraphicsUpdate = 0;   // Last display update timestamp
unsigned long lastTouchTime = 0;        // Last touch event timestamp for debouncing

// ============================================================================
// BMP390 TIMING CALCULATION FUNCTIONS
// ============================================================================

/**
 * Calculates the effective sampling period of BMP390 in microseconds
 * Based on oversampling settings and ODR (Output Data Rate) configuration
 * 
 * This is critical for accurate timestamp reconstruction from FIFO data
 * 
 * @param dev Pointer to BMP3 device structure with current settings
 * @return Effective sampling period in microseconds
 */
uint32_t compute_bmp390_delta_us(const bmp3_dev* dev) {
    // Extract oversampling settings
    uint8_t osr_p = dev->settings.odr_filter.press_os;  // Pressure oversampling (0-5)
    uint8_t osr_t = dev->settings.odr_filter.temp_os;   // Temperature oversampling (0-5)
    bool press_en = dev->settings.press_en;             // Pressure measurement enabled
    bool temp_en  = dev->settings.temp_en;              // Temperature measurement enabled

    // Calculate conversion time according to BMP390 datasheet (microseconds)
    uint32_t Tconv = 234;  // Base conversion time
    if (press_en)
        Tconv += 392 + ((1U << osr_p) * 2020);  // Pressure conversion time
    if (temp_en)
        Tconv += 163 + ((1U << osr_t) * 2020);  // Temperature conversion time

    // ODR period lookup table (microseconds) - BMP390 datasheet Table 9
    static const uint32_t odr_periods_us[18] = {
        5000, 10000, 20000, 40000, 80000, 160000, 320000, 640000,
        1280000, 2560000, 5120000, 10240000, 20480000, 40960000,
        81920000, 163840000, 327680000, 655360000
    };
    uint32_t odr_period = odr_periods_us[dev->settings.odr_filter.odr];

    // Effective sampling period is the maximum of conversion time and ODR period
    return (Tconv > odr_period) ? Tconv : odr_period;
}

/**
 * Debug function to display effective ODR and timing information
 * Useful for verifying sensor configuration matches expected performance
 */
void debug_bmp390_odr(const bmp3_dev *dev) {
    uint8_t osr_p = dev->settings.odr_filter.press_os;
    uint8_t osr_t = dev->settings.odr_filter.temp_os;
    bool press_en = dev->settings.press_en;
    bool temp_en  = dev->settings.temp_en;

    // Calculate theoretical maximum conversion rate
    uint32_t Tconv = 234;
    if (press_en)
        Tconv += 392 + ((1U << osr_p) * 2020);
    if (temp_en)
        Tconv += 163 + ((1U << osr_t) * 2020);

    uint32_t delta_us = compute_bmp390_delta_us(dev);
    float odr_eff = 1e6f / (float)delta_us;

    Serial.printf("[BMP390 DEBUG] Conversion time: %u µs (%.2f Hz theoretical max)\n", 
                  Tconv, 1e6f / (float)Tconv);
    Serial.printf("[BMP390 DEBUG] Effective ODR: %.2f Hz (period: %u µs)\n", 
                  odr_eff, delta_us);
}

// ============================================================================
// AUDIO FEEDBACK SYSTEM
// ============================================================================

/**
 * Generates audio feedback patterns for user interaction
 * Different patterns indicate different system states (start/stop/error)
 * 
 * @param beeps Number of beeps to generate
 * @param on_ms Duration of each beep in milliseconds
 * @param off_ms Pause between beeps in milliseconds
 * @param freq_hz Beep frequency in Hz
 * @param blocking If true, blocks execution during beep sequence
 */
void beepPattern(uint8_t beeps = 1, int on_ms = 300, int off_ms = 50, int freq_hz = 2000, bool blocking = true) {
    if (!M5.Speaker.isEnabled()) {
        return;
    }
    
    for (uint8_t i = 0; i < beeps; i++) {
        M5.Speaker.tone(freq_hz, on_ms);
        if (blocking) {
            delay(on_ms);
        }
        delay(off_ms);
    }
    M5.Speaker.stop();
}

// ============================================================================
// FILE MANAGEMENT FUNCTIONS
// ============================================================================

/**
 * Generates unique filename based on RTC timestamp and random number
 * Format: /log_DD_04_2025_HH_MM_RPXXX.bin
 * 
 * The random number (RP) helps avoid filename conflicts and aids in 
 * correlating log files with specific rocket launches
 * 
 * @return Generated filename string
 */
String createFileName() {
    m5::rtc_time_t TimeStruct;
    m5::rtc_date_t DateStruct;
    M5.Rtc.getTime(&TimeStruct);
    M5.Rtc.getDate(&DateStruct);
    
    randomNum1 = random(0, 501);  // Random number 0-500 for unique identification
    
    String date_time = String(DateStruct.date) + "_04_2025_" + 
                       String(TimeStruct.hours) + "_" + 
                       String(TimeStruct.minutes) + 
                       "_RP" + String(randomNum1);
    
    filename = "/log_" + date_time + ".bin";
    return filename;
}

/**
 * FreeRTOS task for asynchronous SD card writing
 * 
 * This task runs on CPU core 0 while main loop runs on core 1,
 * ensuring high-frequency data acquisition doesn't block on SD writes.
 * 
 * Key features:
 * - Processes both IMU and BMP390 data queues
 * - Uses local buffer to minimize SD write operations
 * - Implements periodic flushing to ensure data persistence
 * - Handles graceful shutdown on logging stop
 * 
 * @param pvParameters FreeRTOS task parameters (unused)
 */
void sdWriteTask(void* pvParameters) {
    // Local buffer for accumulating data before SD writes
    const size_t local_buffer_size = 1024;
    uint8_t local_buffer[local_buffer_size];
    size_t local_buffer_index = 0;

    // Data structures for queue reception
    BinaryIMUData imuData;
    BinaryBMPData bmpData;

    // Timing for periodic flush operations
    TickType_t last_flush_time = xTaskGetTickCount();
    const TickType_t flush_interval = pdMS_TO_TICKS(FLUSH_INTERVAL_MS);

    while (1) {
        bool wrote_data = false;

        // Process IMU data queue (high priority - 1kHz)
        if (xQueueReceive(dataQueue, &imuData, 0) == pdTRUE) {
            size_t data_size = sizeof(BinaryIMUData);
            
            // Check if data fits in local buffer
            if (local_buffer_index + data_size > local_buffer_size) {
                // Buffer full - write to SD and reset
                dataFile.write(local_buffer, local_buffer_index);
                local_buffer_index = 0;
            }
            
            // Copy data to local buffer
            memcpy(local_buffer + local_buffer_index, &imuData, data_size);
            local_buffer_index += data_size;
            wrote_data = true;
        }

        // Process BMP390 data queue (100Hz)
        if (xQueueReceive(bmpQueue, &bmpData, 0) == pdTRUE) {
            size_t data_size = sizeof(BinaryBMPData);
            
            // Check if data fits in local buffer
            if (local_buffer_index + data_size > local_buffer_size) {
                // Buffer full - write to SD and reset
                dataFile.write(local_buffer, local_buffer_index);
                local_buffer_index = 0;
            }
            
            // Copy data to local buffer
            memcpy(local_buffer + local_buffer_index, &bmpData, data_size);
            local_buffer_index += data_size;
            wrote_data = true;
        }

        // Periodic flush or when buffer is half full
        // This ensures data is persisted regularly without excessive SD writes
        if (local_buffer_index > 0 && 
            (xTaskGetTickCount() - last_flush_time >= flush_interval ||
             local_buffer_index >= local_buffer_size/2))
        {
            dataFile.write(local_buffer, local_buffer_index);
            dataFile.flush();  // Force write to SD card
            local_buffer_index = 0;
            last_flush_time = xTaskGetTickCount();
            wrote_data = true;
        }

        // Handle graceful shutdown when logging stops
        if (shutdownPending) {
            // Write any remaining data and close file
            if (local_buffer_index > 0) {
                dataFile.write(local_buffer, local_buffer_index);
            }
            dataFile.flush();
            dataFile.close();
        }

        // Yield CPU if no work was done to prevent busy waiting
        if (!wrote_data) {
            vTaskDelay(pdMS_TO_TICKS(1));
        }
    }
}

// ============================================================================
// USER INTERFACE FUNCTIONS
// ============================================================================

/**
 * Displays error message on screen and sets error state
 * Used for critical errors that prevent normal operation
 * 
 * @param err Error message string to display
 */
void signalError(String err) {
    errorPending = true;
    M5.Display.fillRect(0, 0, M5.Display.width(), M5.Display.height(), TFT_BLACK);
    M5.Lcd.setTextSize(3);
    M5.Lcd.setCursor(10, 70);
    M5.Lcd.setTextColor(RED);
    M5.Lcd.println("Errore: " + err);
}

/**
 * Updates the main display with current system status
 * 
 * Shows:
 * - Logging state (REC/STOP) with color coding
 * - Current log filename
 * - File size in bytes
 * - Touch button for start/stop control
 */
void updateDisplay() {
    if (errorPending) {
        return;  // Don't overwrite error messages
    }
    
    // Clear main display area
    M5.Display.fillRect(0, 0, M5.Display.width(), 180, TFT_BLACK);
    M5.Display.setCursor(10, 10);
    
    // Display logging status with color indication
    M5.Display.setTextColor(loggingActive ? TFT_GREEN : TFT_RED);
    M5.Display.printf("Stato: %s", loggingActive ? "REC" : "STOP");
    
    // Display current filename
    M5.Display.setTextColor(TFT_WHITE);
    M5.Display.setCursor(10, 50);
    M5.Display.setTextSize(3);
    M5.Display.println("File: " + filename);
    
    // Display current file size
    M5.Display.setCursor(10, 125);
    M5.Display.setTextSize(2);
    M5.Display.printf("Dimensione: %lu bytes", dataFile.fileSize());
    
    // Draw touch button area
    M5.Display.fillRoundRect(60, 180, 200, 60, 10, loggingActive ? TFT_RED : TFT_GREEN);
    M5.Display.setTextSize(2);
    M5.Display.setTextColor(TFT_WHITE);
    M5.Display.setCursor(60 + (200 - 80)/2, 180 + 20);
    M5.Display.printf("%s", loggingActive ? "STOP" : "START");
}

/**
 * Toggles logging state between active and inactive
 * 
 * Provides audio feedback and updates display.
 * When stopping, initiates graceful shutdown sequence.
 */
void invertLoggingState() {
    lastTouchTime = millis();
    loggingActive = !loggingActive;
    
    if (loggingActive) {
        // Start logging - triple beep at high frequency
        beepPattern(3, 300, 100, 3000);
        Serial.println("=== LOGGING STARTED ===");
        Serial.printf("Launch timestamp: %lu ms\n", millis());
    } else {
        // Stop logging - double beep and initiate shutdown
        Serial.println("=== LOGGING STOPPED ===");
        shutdownPending = true;
        signalError(String(dataFile.fileSize()) + " bytes\nRP " + String(randomNum1));
        beepPattern(2, 100, 50, 2000);
        Serial.printf("Landing timestamp: %lu ms\n", millis());
    }
    updateDisplay();
}

// ============================================================================
// I2C INTERFACE FUNCTIONS FOR BMP3 DRIVER
// ============================================================================

/**
 * Custom I2C read function for BMP3 driver
 * Implements the I2C communication protocol required by Bosch BMP3 library
 * 
 * @param reg_addr Register address to read from
 * @param data Buffer to store read data
 * @param len Number of bytes to read
 * @param intf_ptr Pointer to I2C interface object
 * @return BMP3_OK on success, BMP3_E_COMM_FAIL on failure
 */
int8_t user_i2c_read(uint8_t reg_addr, uint8_t *data, uint32_t len, void *intf_ptr) {
    auto i2c = static_cast<m5::I2C_Class*>(intf_ptr);

    // Start I2C transaction and write register address
    if (!i2c->start(bmp_i2c_addr, false, 400000)) {
        return BMP3_E_COMM_FAIL;
    }
    if (!i2c->write(reg_addr)) {
        i2c->stop();
        return BMP3_E_COMM_FAIL;
    }

    // Repeated start condition for read operation
    if (!i2c->restart(bmp_i2c_addr, true, 400000)) {
        i2c->stop();
        return BMP3_E_COMM_FAIL;
    }

    // Read requested number of bytes
    if (!i2c->read(data, len, true)) {
        i2c->stop();
        return BMP3_E_COMM_FAIL;
    }

    i2c->stop();
    return BMP3_OK;
}

/**
 * Custom I2C write function for BMP3 driver
 * 
 * @param reg_addr Register address to write to
 * @param data Data buffer to write
 * @param len Number of bytes to write
 * @param intf_ptr Pointer to I2C interface object
 * @return BMP3_OK on success, BMP3_E_COMM_FAIL on failure
 */
int8_t user_i2c_write(uint8_t reg_addr, const uint8_t *data, uint32_t len, void *intf_ptr) {
    auto i2c = static_cast<m5::I2C_Class*>(intf_ptr);

    // Start I2C transaction and write register address
    if (!i2c->start(bmp_i2c_addr, false, 400000)) {
        return BMP3_E_COMM_FAIL;
    }
    if (!i2c->write(reg_addr)) {
        i2c->stop();
        return BMP3_E_COMM_FAIL;
    }

    // Write payload data
    if (!i2c->write(data, len)) {
        i2c->stop();
        return BMP3_E_COMM_FAIL;
    }

    i2c->stop();
    return BMP3_OK;
}

/**
 * Custom delay function for BMP3 driver
 * 
 * @param period Delay period in microseconds
 * @param intf_ptr Interface pointer (unused)
 */
void user_delay_us(uint32_t period, void *intf_ptr) {
    (void)intf_ptr;
    delayMicroseconds(period);
}

// ============================================================================
// BMP390 INITIALIZATION AND CALIBRATION
// ============================================================================

/**
 * Calibrates reference pressure for relative altitude measurements
 * 
 * This function:
 * 1. Initializes the BMP390 sensor with custom I2C functions
 * 2. Performs warm-up to stabilize sensor readings
 * 3. Takes multiple samples to establish reference pressure (P0)
 * 
 * The reference pressure is used for calculating relative altitude changes,
 * which is more accurate for rocket flight analysis than absolute altitude.
 */
void setReferencePressure() {
    Serial.println("=== BMP390 CALIBRATION START ===");

    // Configure BMP3 device structure with custom I2C interface
    bmp3.intf = BMP3_I2C_INTF;
    bmp3.read = user_i2c_read;
    bmp3.write = user_i2c_write;
    bmp3.delay_us = user_delay_us;
    bmp3.intf_ptr = &M5.Ex_I2C;  // External I2C bus
    bmp3.fifo = &bmp3Fifo;
    bmp3.fifo->data.buffer = bmp_fifo_buffer;

    // Initialize sensor - reads calibration coefficients from sensor EEPROM
    Serial.println("Initializing BMP390 sensor...");
    if (bmp3_init(&bmp3) != BMP3_OK) {
        signalError("BMP390 init failed!");
        return;
    }

    // Sensor warm-up phase
    // First readings after power-on can be unstable, so we discard them
    Serial.println("BMP390 sensor warm-up phase...");
    for (int i = 0; i < WARMUP_SAMPLES; ++i) {
        bmp3_data comp;
        if (bmp3_get_sensor_data(BMP3_PRESS | BMP3_TEMP, &comp, &bmp3) != BMP3_OK) {
            signalError("Calibration read failed");
            return;
        }
        delay(SAMPLE_DELAY_MS);
    }

    // Reference pressure calibration
    // Average multiple readings to get stable reference pressure P0
    Serial.printf("Calibrating reference pressure (%d samples)...\n", REF_SAMPLES);
    bmp3_data comp;
    float pressure_sum = 0;
    
    for (int i = 0; i < REF_SAMPLES; ++i) {
        if (bmp3_get_sensor_data(BMP3_PRESS | BMP3_TEMP, &comp, &bmp3) != BMP3_OK) {
            signalError("Calibration read failed");
            return;
        }
        pressure_sum += comp.pressure * 100.0f; // Convert hPa to Pa
        delay(10); // 100Hz sampling during calibration
    }
    
    referencePressure = pressure_sum / REF_SAMPLES;
    Serial.printf("Reference pressure P0: %.2f Pa (%.2f hPa)\n", 
                  referencePressure, referencePressure/100.0f);
    Serial.println("=== CALIBRATION COMPLETE ===");
}

/**
 * Configures BMP390 for high-frequency FIFO-based data acquisition
 * 
 * Configuration optimized for rocket flight monitoring:
 * - 100Hz sampling rate for good altitude resolution
 * - FIFO mode to prevent data loss during high-g events
 * - IIR filtering to reduce noise while maintaining responsiveness
 * - Oversampling for improved precision
 */
void initBMP390() {
    // First calibrate reference pressure
    setReferencePressure();
    
    Serial.println("Configuring BMP390 FIFO system...");

    // FIFO Configuration for continuous data streaming
    bmp3.fifo->settings.mode = BMP3_FIFO_MODE_MSK;        // Enable streaming mode
    bmp3.fifo->settings.press_en = BMP3_ENABLE;           // Store pressure data
    bmp3.fifo->settings.temp_en = BMP3_ENABLE;            // Store temperature data
    bmp3.fifo->settings.time_en = BMP3_ENABLE;            // Store sensor timestamps
    bmp3.fifo->settings.fwtm_en = BMP3_ENABLE;            // Enable watermark interrupt
    bmp3.fifo->settings.ffull_en = BMP3_DISABLE;          // Disable full interrupt
    bmp3.fifo->settings.stop_on_full_en = BMP3_ENABLE;    // Stop on FIFO full

    // Configure number of frames to read per FIFO access
    // 50 frames ≈ 0.5 seconds of data at 100Hz
    bmp3.fifo->data.req_frames = 50;

    // Apply FIFO settings to sensor
    if (bmp3_set_fifo_settings(
        BMP3_SEL_FIFO_MODE | BMP3_SEL_FIFO_PRESS_EN | BMP3_SEL_FIFO_TEMP_EN |
        BMP3_SEL_FIFO_TIME_EN | BMP3_SEL_FIFO_FWTM_EN | BMP3_SEL_FIFO_FULL_EN |
        BMP3_SEL_FIFO_STOP_ON_FULL_EN, &bmp3) != BMP3_OK) {
        Serial.println("ERROR: FIFO settings configuration failed");
    }

    if (bmp3_set_fifo_watermark(&bmp3) != BMP3_OK) {
        Serial.println("ERROR: FIFO watermark configuration failed");
    }

    // Main sensor configuration for optimal rocket flight monitoring
    bmp3.settings.press_en = BMP3_ENABLE;                          // Enable pressure measurement
    bmp3.settings.temp_en = BMP3_ENABLE;                           // Enable temperature measurement
    bmp3.settings.odr_filter.odr = BMP3_ODR_100_HZ;              // 100Hz sample rate
    bmp3.settings.odr_filter.iir_filter = BMP3_IIR_FILTER_COEFF_7; // Strong IIR filtering
    bmp3.settings.odr_filter.press_os = BMP3_OVERSAMPLING_2X;      // 2x oversampling for precision
    bmp3.settings.odr_filter.temp_os = BMP3_NO_OVERSAMPLING;       // No temp oversampling (saves time)

    // Apply sensor configuration
    if (bmp3_set_sensor_settings(
            BMP3_SEL_PRESS_EN | BMP3_SEL_TEMP_EN | BMP3_SEL_ODR |
            BMP3_SEL_IIR_FILTER | BMP3_SEL_PRESS_OS, &bmp3) != BMP3_OK) {
        Serial.println("ERROR: Sensor settings configuration failed");
    }

    // Set sensor to normal mode (continuous operation)
    bmp3.settings.op_mode = BMP3_MODE_NORMAL;
    if (bmp3_set_op_mode(&bmp3) != BMP3_OK) {
        Serial.println("ERROR: Failed to set normal operating mode");
    }

    Serial.println("BMP390 FIFO system initialized successfully");
    
    // Display timing information for verification
    debug_bmp390_odr(&bmp3);
    
    // Audio confirmation of successful initialization
    beepPattern();
}

// ============================================================================
// MAIN SYSTEM INITIALIZATION
// ============================================================================

void setup() {
    Serial.begin(115200);
    delay(500);
    Serial.println("========================================");
    Serial.println("Water Rocket Data Logger v3.4 Starting");
    Serial.println("========================================");

    // Configure M5Core2 hardware
    auto cfg = M5.config();
    cfg.clear_display = true;   // Clear screen on startup
    cfg.internal_spk = true;    // Enable internal speaker
    M5.begin(cfg);
    M5.Speaker.setVolume(255);  // Maximum volume for outdoor use

    // Initialize IMU (Inertial Measurement Unit)
    Serial.println("Initializing IMU MPU6886...");
    imu.begin(&M5.In_I2C);
    imu.setGyroFsr(imu.GFS_2000DPS);     // ±2000°/s - high range for rocket rotation
    imu.setAccelFsr(imu.AFS_16G);        // ±16g - high range for rocket acceleration
    imu.enableFIFO(imu.ODR_1kHz);        // 1kHz sampling rate with FIFO buffering

    // Initialize SD Card system for high-speed data logging
    Serial.println("Initializing SD Card system...");
    SPI.begin(18, 38, 23, SD_CS_PIN);    // Initialize SPI bus (SCK, MISO, MOSI, CS)
    
    if (!sd.begin(SdSpiConfig(SD_CS_PIN, DEDICATED_SPI, SPI_CLOCK))) {
        signalError("SD Card initialization failed");
        return;
    }
    Serial.println("SD Card initialized successfully");

    // Create unique log file with binary format header
    dataFile = sd.open(createFileName().c_str(), O_RDWR | O_CREAT | O_AT_END);
    if (!dataFile) {
        signalError("Failed to create log file");
        return;
    }
    
    // Write file header for binary format identification
    uint8_t header[4] = {'M','5','1','0'};  // File format identifier
    dataFile.write(header, 4);
    dataFile.flush();
    Serial.println("Log file created: " + filename);

    // Create FreeRTOS queues for inter-task communication
    Serial.println("Creating data processing queues...");
    dataQueue = xQueueCreate(4000, sizeof(BinaryIMUData));  // High capacity for 1kHz IMU
    bmpQueue = xQueueCreate(4000, sizeof(BinaryBMPData));   // High capacity for 100Hz BMP
    
    if (dataQueue == NULL || bmpQueue == NULL) {
        signalError("Failed to create data queues");
        return;
    }

    // Launch SD card writing task on CPU core 0 (separate from main loop on core 1)
    Serial.println("Starting asynchronous SD writing task...");
    xTaskCreatePinnedToCore(sdWriteTask, "SDTask", 8192, NULL, 2, NULL, 0);

    // Initialize I2C buses
    Serial.println("Initializing I2C communication buses...");
    M5.Ex_I2C.begin(I2C_NUM_1, 32, 33);  // External I2C for BMP390 (SDA=32, SCL=33)
    M5.In_I2C.begin(I2C_NUM_0, 21, 22);  // Internal I2C for IMU (SDA=21, SCL=22)

    // Auto-detect BMP390 I2C address
    Serial.println("Scanning for BMP390 sensor...");
    if (M5.Ex_I2C.scanID(BMP3_ADDR_I2C_PRIM)) {
        bmp_i2c_addr = BMP3_ADDR_I2C_PRIM;  // 0x76
        Serial.println("BMP390 found at address 0x76");
    } else if (M5.Ex_I2C.scanID(BMP3_ADDR_I2C_SEC)) {
        bmp_i2c_addr = BMP3_ADDR_I2C_SEC;   // 0x77
        Serial.println("BMP390 found at address 0x77");
    } else {
        signalError("BMP390 sensor not found");
        return;
    }

    // Initialize and calibrate BMP390 barometric sensor
    Serial.println("Initializing BMP390 barometric sensor...");
    initBMP390();
    
    // Initialize display with current system status
    updateDisplay();
    
    Serial.println("========================================");
    Serial.println("System ready - Touch screen to start logging");
    Serial.println("System ready for water rocket launch!");
    Serial.println("========================================");
}

// ============================================================================
// MAIN EXECUTION LOOP
// ============================================================================

void loop() {
    // Update M5Core2 hardware state (touch, buttons, etc.)
    M5.update();
    
    // === USER INTERFACE MANAGEMENT ===
    
    // Handle touch screen input for logging control
    if (M5.Touch.getDetail().isPressed()) {
        auto touchPoint = M5.Touch.getDetail();
        // Check if touch is in button area (bottom of screen) with debounce
        if (touchPoint.y > 180 && millis() - lastTouchTime > DEBOUNCE_DELAY) {
            invertLoggingState();
        }
    }
    
    // Handle power button as alternative to touch (useful with gloves)
    if (M5.BtnPWR.wasClicked()) {
        invertLoggingState();
    }

    // Update display periodically to show current status and file size
    if (millis() - lastGraphicsUpdate > GRAPHICS_UPDATE_INTERVAL) {
        updateDisplay();
        lastGraphicsUpdate = millis();
    }

    // === HIGH-FREQUENCY DATA ACQUISITION ===
    
    // Only acquire data when logging is active (after launch button pressed)
    if (loggingActive) {
        
        // --- IMU Data Acquisition (1kHz) ---
        // Get raw accelerometer and gyroscope data from FIFO buffer
        BinaryIMUData sensorData;
        auto result = imu.getImuRawData(&(sensorData.IMUdata));
        
        if (result != m5::IMU_Base::imu_spec_none) {
            // Add high-precision timestamp in microseconds
            sensorData.timestamp = micros();
            
            // Send to queue - don't block if queue is full (prevents data loss)
            xQueueSend(dataQueue, &sensorData, 0);
        }
        
        // --- BMP390 FIFO Data Acquisition (100Hz) ---
        
        // Check if FIFO contains new data
        uint16_t fifo_length = 0;
        if (bmp3_get_fifo_length(&fifo_length, &bmp3) == BMP3_OK && fifo_length > 0) {
            
            // Download all FIFO data into internal buffer
            if (bmp3_get_fifo_data(&bmp3) != BMP3_OK) {
                Serial.println("ERROR: BMP390 FIFO read failed");
                return;
            }
            
            // Extract and decode individual frames from FIFO data
            bmp3_data frames[50];  // Buffer for decoded pressure/temperature frames
            if (bmp3_extract_fifo_data(frames, &bmp3) != BMP3_OK) {
                Serial.println("ERROR: BMP390 FIFO data extraction failed");
                return;
            }
            
            // --- Timestamp Synchronization Algorithm ---
            // Synchronize sensor internal time with MCU microsecond timer
            uint32_t sensor_ticks = bmp3.fifo->data.sensor_time;
            uint32_t sensor_time_us = sensor_ticks * 39;  // Convert to microseconds (39 µs/tick)
            
            // Perform initial synchronization on first FIFO read
            if (bmp_firstSync) {
                bmp_t0_mcu = micros();           // MCU reference time
                bmp_t0_sensor = sensor_time_us;  // Sensor reference time
                bmp_firstSync = false;
                Serial.println("BMP390 timestamp synchronization established");
            }
            
            // Calculate current synchronized timestamp
            uint32_t last_timestamp_us = bmp_t0_mcu + (sensor_time_us - bmp_t0_sensor);
            
            // Calculate time between samples based on current ODR settings
            uint32_t delta_us = compute_bmp390_delta_us(&bmp3);
            
            // --- Process Each FIFO Frame ---
            // Frames are stored in reverse chronological order (newest first)
            for (uint8_t i = 0; i < bmp3.fifo->data.parsed_frames; ++i) {
                
                // Convert pressure from hPa to Pa for barometric altitude calculation
                float pressure_pa = frames[i].pressure * 100.0f;
                
                // Calculate altitude using international barometric formula
                // h = 44330 * ((P0/P)^0.1903 - 1)  where P0 = reference pressure
                float absolute_altitude = 44330.0f * (powf(referencePressure / pressure_pa, 0.1903f) - 1.0f);
                
                // Establish baseline altitude on first valid reading
                // This gives us relative altitude change from launch point
                if (isnan(baseAltitude)) {
                    baseAltitude = absolute_altitude;
                    Serial.printf("Baseline altitude established: %.2f m\n", baseAltitude);
                }
                
                // Prepare data packet for logging
                BinaryBMPData bmpData;
                bmpData.altitude = absolute_altitude - baseAltitude;  // Relative altitude
                
                // Calculate precise timestamp for this specific frame
                // Account for frame position in FIFO (reverse chronological order)
                int frame_offset = (bmp3.fifo->data.parsed_frames - 1 - i);
                bmpData.timestamp = last_timestamp_us - (uint32_t)(frame_offset * delta_us);
                
                // Send to logging queue (non-blocking to prevent data loss)
                xQueueSend(bmpQueue, &bmpData, 0);
            }
            
            // Yield processor time to SD writing task for optimal performance
            taskYIELD();
        }
    }
}