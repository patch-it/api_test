# api_test

This workspace provides tools and scripts for interacting with the Interactive Brokers (IBKR) Client 

## Project Structure

### Key Directories and Files
- **accees_IBKR.py**: Python script for accessing IBKR.
- **config.toml**: Configuration file for project settings.
- **start_gateway_and_open.sh**: Shell script to start the IBKR Gateway and open the client portal.
- **clientportal.gw/**: Contains the IBKR Client Portal Gateway, including:
  - **bin/**: Scripts to run the gateway (`run.sh`, `run.bat`).
  - **build/**: Compiled libraries and runtime files.
  - **doc/**: Documentation, including:
    - `GettingStarted.md`: Guide to getting started.
    - `RealtimeSubscription.md`: Real-time data subscription info.
  - **logs/**: Log files from the gateway.
  - **root/**: Main configuration and web application files.
    - **conf*.yaml**: Various configuration files for different environments.
    - **webapps/demo/**: Demo web application, including `gateway.demo.js`.

## Usage

1. **Configure the Gateway**  
   Edit the relevant YAML files in `clientportal.gw/root/` to match your IBKR setup.

2. **Start the Gateway**  
   Use the provided shell script:
   ```sh
   ./start_gateway_and_open.sh