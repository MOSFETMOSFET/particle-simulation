import openpyxl

def load_waveform_from_sheet(ws):
    times = []
    voltages = []
    for row in ws.iter_rows(min_row=2, values_only=True):  # Skip the header
        time, voltage, _ = row
        times.append(time)
        voltages.append(voltage)
    return times, voltages

def save_waveform_to_sheet(ws, times, voltages):
    ws.append(["Time", "Voltage", "Label"])
    for time, voltage in zip(times, voltages):
        ws.append([time, voltage, 0])

def average_waveforms(waveform1, waveform2):
    length = min(len(waveform1[0]), len(waveform2[0]))  # Use the length of the shorter waveform
    averaged_times = []
    averaged_voltages = []
    for i in range(length):
        avg_time = (waveform1[0][i] + waveform2[0][i]) / 2
        avg_voltage = (waveform1[1][i] + waveform2[1][i]) / 2
        averaged_times.append(avg_time)
        averaged_voltages.append(avg_voltage)
    return averaged_times, averaged_voltages

def combine_waveforms(input_filename, output_filename):
    wb_input = openpyxl.load_workbook(input_filename)
    wb_output = openpyxl.Workbook()

    sheetnames = wb_input.sheetnames

    for i in range(len(sheetnames) - 1):
        ws1 = wb_input[sheetnames[i]]
        ws2 = wb_input[sheetnames[i + 1]]

        waveform1 = load_waveform_from_sheet(ws1)
        waveform2 = load_waveform_from_sheet(ws2)

        averaged_waveform = average_waveforms(waveform1, waveform2)

        ws_output = wb_output.create_sheet(title=f'Combined_{i + 1}')
        save_waveform_to_sheet(ws_output, *averaged_waveform)

    # Remove the default sheet if exists
    if 'Sheet' in wb_output.sheetnames:
        del wb_output['Sheet']

    wb_output.save(output_filename)

input_filename = r'C:\Users\dell\Desktop\training_data\training_data_1.xlsx'
output_filename = r'C:\Users\dell\Desktop\training_data\training_data_2.xlsx'

combine_waveforms(input_filename, output_filename)

print(f'Combined waveforms saved to {output_filename}')