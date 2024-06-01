import obspy
import numpy as np
from rsudp.client import Client

class PGVAlert:
    def __init__(self, threshold):
        self.threshold = threshold  # Richter magnitude threshold

    def process(self, data):
        # Create a Stream object from the incoming data
        st = obspy.Stream(obspy.Trace(data))
        # Remove mean and linear trends
        st.detrend("demean")
        st.detrend("linear")
        # Apply bandpass filter to isolate frequencies of interest
        st.filter("bandpass", freqmin=0.1, freqmax=20.0)
        # Integrate to convert displacement to velocity
        st.integrate()
        # Find Peak Ground Velocity (PGV)
        pgv = max(abs(st[0].data))
        # Convert PGV from m/s to cm/s
        pgv_cm_s = pgv * 100
        # Estimate Richter magnitude using the empirical relationship
        magnitude = np.log10(pgv_cm_s) + 2.4

        # Trigger alert if magnitude exceeds threshold
        if magnitude >= self.threshold:
            self.trigger_alert(magnitude)

    def trigger_alert(self, magnitude):
        print(f"Earthquake detected! Estimated Richter Magnitude: {magnitude}")

# Initialize and start the client with the custom alert
client = Client()
alert = PGVAlert(threshold=4.0)
client.add_listener(alert.process)
client.run()
