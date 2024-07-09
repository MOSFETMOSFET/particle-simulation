import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import openpyxl

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

waveforms = []
for start, end in zip(start_indices, end_indices):
    if start < end:
        waveform_info = {
            'start_time': time_data[start],
            'end_time': time_data[end],
            'time_data': time_data[start:end+1].tolist(),
            'voltage_data': voltage_data[start:end+1].tolist(),
            'label': 0
        }
        waveforms.append(waveform_info)

output_file_path = r'C:\Users\dell\Desktop\waveform_data_with_labels.xlsx'
with pd.ExcelWriter(output_file_path, engine='openpyxl') as writer:
    for i, waveform in enumerate(waveforms):
        if len(waveform['time_data']) > 0:
            waveform_df = pd.DataFrame({
                'Time': waveform['time_data'],
                'Voltage': waveform['voltage_data'],
                'Label': [waveform['label']] * len(waveform['time_data'])
            })
            waveform_df.to_excel(writer, sheet_name=f'Waveform_{i+1}', index=False)

plt.figure(figsize=(10, 6))
plt.plot(time_data, voltage_data, color='blue')

for waveform in waveforms:
    plt.plot(waveform['time_data'], waveform['voltage_data'], color='red')

plt.xlabel('Time')
plt.ylabel('Voltage')
plt.title('Voltage Waveforms')
plt.show()

for waveform in waveforms:
    print(f"Waveform from {waveform['start_time']} to {waveform['end_time']}")