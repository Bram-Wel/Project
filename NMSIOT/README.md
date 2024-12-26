# NMSIOT
NMSIOT is a device firmware for the ESP32 board, designed to connect to a remote server with an optimal IoT database. It facilitates the collection of temperature and humidity readings using the DHT11 sensor and allows remote control of actuators and LEDs. Additionally, it supports alarm execution for various conditions.

## Features

- **Device Firmware**: Contains firmware for ESP32 board.
- **Real-time Monitoring**: Track temperature and humidity readings using DHT11 sensor.
- **Remote Control**: Drive actuators and LEDs using remote input.
- **Alerts and Notifications**: Execute alarms for any anomalies or issues.

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/NMSIOT.git
    ```
2. Navigate to the project directory:
    ```bash
    cd NMSIOT
    ```
3. Install dependencies:
    ```bash
    npm install
    ```
4. Build the source code and upload it to the ESP32 board using PlatformIO, Arduino IDE, or a similar tool.
5. On first-time setup, connect to the device at IP address `192.168.4.1` to add WiFi credentials.

## Usage

1. Compile the firmware and upload it to the ESP32 board.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License.
