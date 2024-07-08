import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('TkAgg')

file_path = r'C:\Users\dell\Desktop\saved_data.xlsx'
df = pd.read_excel(file_path)

time_data = df.iloc[:, 0]
voltage_data = df.iloc[:, 1]

baseline = voltage_data[:10].mode()[0]

threshold = baseline * 0.99


start_indices = []
end_indices = []

in_waveform = False
for i, voltage in enumerate(voltage_data):
    if not in_waveform and voltage < threshold:
        start_indices.append(i)
        in_waveform = True
    elif in_waveform and voltage >= threshold:
        end_indices.append(i)
        in_waveform = False

if len(start_indices) > len(end_indices):
    end_indices.append(len(voltage_data) - 1)

waveforms = [(start, end) for start, end in zip(start_indices, end_indices)]

plt.figure(figsize=(10, 6))
plt.plot(time_data, voltage_data, color='blue')

for start, end in waveforms:
    plt.plot(time_data[start:end+1], voltage_data[start:end+1], color='red')

plt.xlabel('Time')
plt.ylabel('Voltage')
plt.title('Voltage Waveforms')
plt.show()