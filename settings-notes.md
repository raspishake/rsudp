## settings
- **port**: The port number where the Raspberry Shake data server is listening for connections.

- **station**: The station code for your Raspberry Shake device.

- **output_dir**: The directory where the output files will be saved.

- **debug**: If set to true, enables debug mode, which provides detailed logging for troubleshooting.

## printdata
enabled: If false, disables the printing of incoming data to the console. If true, it would print the incoming data to the console.

## write
enabled: If false, disables writing incoming data to disk.
channels: Specifies which channels' data to write to disk. ["all"] means all channels' data will be written.

## plot
enabled: If true, enables real-time plotting of the data.
duration: The duration of the plot window in seconds (e.g., 90 seconds).
spectrogram: If true, includes a spectrogram in the plot.
fullscreen: If true, the plot window will open in fullscreen mode.
kiosk: If true, the plot will be displayed in kiosk mode, which is a fullscreen mode without window borders.
eq_screenshots: If true, automatically takes screenshots of the plot when an earthquake is detected.
channels: Specifies which channels' data to plot. ["all"] means all channels' data will be plotted.
deconvolve: If true, applies deconvolution to the data for better clarity.
units: The units of the data to be plotted. "CHAN" typically means the channel data as it is.

## forward
enabled: If false, disables forwarding of data to another address.
address: The IP address to forward data to.
port: The port number on the forward address to send data to.
channels: Specifies which channels' data to forward. ["all"] means all channels' data will be forwarded.
fwd_data: If true, forwards the raw data.
fwd_alarms: If false, does not forward alarm data.

## alert
enabled: If true, enables the alert system for detecting seismic events.
channel: The channel to monitor for alerts (e.g., "HZ").
sta: Short-term average window length in seconds. It is used to calculate the average amplitude of the seismic signal over a short period.
lta: Long-term average window length in seconds. It is used to calculate the average amplitude of the seismic signal over a longer period.
threshold: The threshold value for triggering an alert.
reset: The reset value for deactivating an alert.
highpass: The high-pass filter frequency in Hz.
lowpass: The low-pass filter frequency in Hz.
deconvolve: If false, does not apply deconvolution to the alert data.
units: The units of the alert data (e.g., "VEL" for velocity).

## alertsound
enabled: If false, disables the alert sound.
mp3file: The file name of the MP3 file to play when an alert is triggered.
custom
enabled: If false, disables custom code execution.
codefile: The file name of the custom code to run.
win_override: If false, does not override the default window settings.
tweets
enabled: If false, disables tweeting alerts.
tweet_images: If true, includes images in the tweets.
api_key: The API key for accessing Twitter.
api_secret: The API secret for accessing Twitter.
access_token: The access token for accessing Twitter.
access_secret: The access token secret for accessing Twitter.
extra_text: Additional text to include in the tweets.

## telegram
enabled: If false, disables sending alerts via Telegram.
send_images: If true, includes images in the Telegram messages.
token: The bot token for accessing Telegram.
chat_id: The chat ID for sending Telegram messages.
extra_text: Additional text to include in the Telegram messages.

## rsam
- enabled: If false, disables RSAM (Real-time Seismic Amplitude Measurement) calculations.
- quiet: If true, suppresses RSAM output in the console.
- fwaddr: The IP address to forward RSAM data to.
- fwport: The port number on the forward address to send RSAM data to.
- fwformat: The format of the forwarded RSAM data (e.g., "LITE").
- channel: The channel to calculate RSAM for (e.g., "HZ").
- interval: The interval in seconds for RSAM calculation.
- deconvolve: If false, does not apply deconvolution to the RSAM data.
- units: The units of the RSAM data (e.g., "VEL" for velocity).settings

## Concepts

sta (Short-Term Average): This is the length of the short-term average window in seconds. It is used to calculate the average amplitude of the seismic signal over a short period.

lta (Long-Term Average): This is the length of the long-term average window in seconds. It is used to calculate the average amplitude of the seismic signal over a longer period.

3

1 - 4

highpass: The high-pass filter frequency in Hz. This filter removes low-frequency components of the seismic signal below the specified frequency. It is used to eliminate noise from long-period events, such as tides or slow earth movements.
lowpass: The low-pass filter frequency in Hz. This filter removes high-frequency components of the seismic signal above the specified frequency. It is used to eliminate noise from short-period events, such as electrical interference or vibrations from machinery.

units: Specifies the units of the data used for alert detection. Common units include:
VEL: Velocity, which measures the speed of ground motion.
ACC: Acceleration, which measures the change in velocity of ground motion.
DIS: Displacement, which measures the distance the ground has moved.
CHAN: Raw channel data, often used as it is without conversion.

alert.deconvolve
deconvolve: If set to true, the raw seismic data will be deconvolved to convert it into the specified units (e.g., from raw counts to velocity or displacement). Deconvolution is a signal processing technique used to reverse the effects of the instrument response on the recorded data.
alert.threshold
threshold: This value sets the threshold for triggering an alert. It is a ratio of the STA to the LTA. When the STA/LTA ratio exceeds this threshold, an alert is triggered.

## Current calculation process

The STA/LTA algorithm is a commonly used method in seismology to detect seismic events. It works by comparing the short-term average (STA) of the seismic signal to the long-term average (LTA). When the STA becomes significantly higher than the LTA, it indicates a sudden increase in seismic activity, which could be an earthquake or another significant event.

How alert.threshold Works
The system continuously calculates the STA and LTA for the incoming seismic data.
The ratio of STA to LTA is monitored.
When this ratio exceeds the specified threshold value, it indicates a significant increase in seismic activity, suggesting a potential seismic event.
For example, if the threshold is set to 3.95, an alert will be triggered when the STA is 3.95 times greater than the LTA.
Summary of the Alert Process
Filtering: The seismic data is filtered using the specified high-pass and low-pass filters to remove unwanted noise.
Calculation: The STA and LTA are calculated over their respective time windows.
Comparison: The ratio of STA to LTA is continuously monitored.
Trigger: If the STA/LTA ratio exceeds the threshold, an alert is triggered, indicating a possible seismic event.

By configuring these settings appropriately, you can fine-tune the sensitivity and responsiveness of your Raspberry Shake system to detect seismic events with the desired characteristics.

Open settings: rs-settings
Run with custom config: rs-client config.json

Install with pip:

- PyQt5

Install with brew: 
- freetype
